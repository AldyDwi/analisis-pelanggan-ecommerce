from flask import Flask, render_template, request, redirect, jsonify
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.dialects.mysql import insert
from config import Config
from etl_pipeline import run_etl_process
import datetime
import oci
import os
import logging
from logging.handlers import TimedRotatingFileHandler
from hdfs import InsecureClient

# Konfigurasi Logging
if not os.path.exists('logs'):
    os.makedirs('logs')

log_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
log_file = "logs/app.log"

# Handler untuk rotasi harian (setiap tengah malam)
file_handler = TimedRotatingFileHandler(
    log_file, 
    when="midnight", 
    interval=1, 
    backupCount=7,
    encoding='utf-8'
)
file_handler.setFormatter(log_formatter)
file_handler.suffix = "%Y-%m-%d" # Format akhiran file log lama: app.log.2026-06-07

# Handler untuk output ke console
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)

logging.basicConfig(
    level=logging.INFO,
    handlers=[file_handler, console_handler]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)

# Inisialisasi Engine Database
engine_oltp = create_engine(app.config['SQLALCHEMY_OLTP_URI'])
engine_star = create_engine(app.config['SQLALCHEMY_STAR_URI'])

# Inisialisasi HDFS Client
hdfs_client = InsecureClient(app.config['HDFS_URL'], user=app.config['HDFS_USER'])

# Konfigurasi OCI Object Storage
try:
    # Mengecek apakah kita sedang di VM Production (dari docker-compose environment)
    USE_INSTANCE_PRINCIPAL = os.environ.get('USE_INSTANCE_PRINCIPAL', 'False') == 'True'

    if USE_INSTANCE_PRINCIPAL:
        # MODE PRODUKSI (VM ORACLE): Menggunakan identitas VM tanpa file config
        signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
        object_storage_client = oci.object_storage.ObjectStorageClient(config={}, signer=signer)
        logger.info("Berhasil terhubung ke OCI menggunakan Instance Principals.")
    else:
        # MODE LOKAL (LAPTOP): Membaca file ~/.oci/config yang di-mount ke dalam Docker
        # Karena di dalam Docker berjalan sebagai root, lokasinya ada di /root/.oci/config
        oci_config = oci.config.from_file("/root/.oci/config", "DEFAULT")
        object_storage_client = oci.object_storage.ObjectStorageClient(oci_config)
        logger.info("Berhasil terhubung ke OCI menggunakan File Konfigurasi Lokal.")

    NAMESPACE = object_storage_client.get_namespace().data
    BUCKET_NAME = "ecommerce-raw-data"
    OCI_AVAILABLE = True

except Exception as e:
    logger.warning(f"Koneksi OCI Object Storage belum siap/gagal. ({e})")
    OCI_AVAILABLE = False

# Fungsi Bantuan untuk melakukan Upsert di MySQL
def mysql_upsert(table, conn, keys, data_iter):
    """
    Fungsi ini mengubah 'if_exists=append' biasa menjadi:
    INSERT INTO ... ON DUPLICATE KEY UPDATE ...
    """
    data = [dict(zip(keys, row)) for row in data_iter]
    if not data:
        return
        
    insert_stmt = insert(table.table).values(data)
    # Update semua kolom jika Primary Key bentrok
    update_dict = {c.name: c for c in insert_stmt.inserted if c.name not in table.table.primary_key.columns.keys()}
    
    if update_dict:
        upsert_stmt = insert_stmt.on_duplicate_key_update(**update_dict)
    else:
        upsert_stmt = insert_stmt # Jika tabel hanya berisi PK (jarang terjadi)
        
    conn.execute(upsert_stmt)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    if 'files[]' not in request.files:
        return redirect(request.url)
    
    files = request.files.getlist('files[]')
    
    file_to_table = {
        'olist_customers_dataset.csv': 'customers',
        'olist_geolocation_dataset.csv': 'geolocation',
        'olist_products_dataset.csv': 'products',
        'olist_order_items_dataset.csv': 'order_items',
        'olist_order_payments_dataset.csv': 'order_payments',
        'olist_order_reviews_dataset.csv': 'order_reviews',
        'olist_orders_dataset.csv': 'orders',
        'olist_sellers_dataset.csv': 'sellers',
        'product_category_name_translation.csv': 'product_category_translation'
    }

    for file in files:
        if file.filename in file_to_table:
            # 1. GENERATE NAMA FILE BARU (Contoh: olist_orders_dataset_20260429_201530.csv)
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            nama_asli, ekstensi = os.path.splitext(file.filename)
            nama_file_backup = f"{nama_asli}_{timestamp}{ekstensi}"
            
            # 2. UPLOAD KE OCI OBJECT STORAGE (Jika konfigurasi tersedia)
            file_content = file.read()
            if OCI_AVAILABLE:
                try:
                    object_storage_client.put_object(
                        NAMESPACE, 
                        BUCKET_NAME, 
                        nama_file_backup, 
                        file_content
                    )
                    logger.info(f"Backup berhasil: {nama_file_backup} tersimpan di OCI Object Storage.")
                except Exception as e:
                    logger.error(f"Gagal backup ke OCI Object Storage: {e}")
            
            # 3. UPLOAD KE HDFS (Data Lake)
            try:
                hdfs_path = f"/ecommerce/raw_data/{nama_file_backup}"
                with hdfs_client.write(hdfs_path, overwrite=True) as writer:
                    writer.write(file_content)
                logger.info(f"HDFS upload berhasil: {hdfs_path}")
            except Exception as e:
                logger.error(f"Gagal upload ke HDFS: {e}")

            # Kembalikan posisi kursor pembacaan file ke awal
            file.seek(0)
            
            # 4. PROSES KE DATABASE OLTP DENGAN UPSERT
            df = pd.read_csv(file)
            table_name = file_to_table[file.filename]
            
            try:
                df.to_sql(table_name, con=engine_oltp, if_exists='append', index=False, method=mysql_upsert, chunksize=10000)
                logger.info(f"Berhasil Ingest {file.filename} ke tabel MySQL OLTP: {table_name}")
            except Exception as e:
                logger.error(f"Gagal Ingest {file.filename} ke MySQL OLTP: {e}")

    # Setelah semua file OLTP masuk, jalankan proses ETL
    try:
        run_etl_process()
        return "Upload, Backup OCI, dan Proses ETL Berhasil!"
    except Exception as e:
        return f"Proses database berhasil, tapi ETL gagal: {str(e)}"

@app.route('/api/dashboard')
def api_dashboard():
    try:
        with engine_star.connect() as conn:

            # Total transaksi
            total_transaksi = pd.read_sql("""
                SELECT COUNT(*) as total
                FROM fact_sales
            """, conn).iloc[0]['total']

            # Total revenue
            total_revenue = pd.read_sql("""
                SELECT COALESCE(SUM(revenue), 0) as revenue
                FROM fact_sales
            """, conn).iloc[0]['revenue']

            # Total produk terjual
            total_qty = pd.read_sql("""
                SELECT COALESCE(SUM(quantity), 0) as qty
                FROM fact_sales
            """, conn).iloc[0]['qty']

            # Average rating
            avg_rating = pd.read_sql("""
                SELECT ROUND(AVG(review_score), 2) as avg
                FROM fact_sales
                WHERE review_score IS NOT NULL
            """, conn).iloc[0]['avg']

            # Tren bulanan
            tren_bulanan = pd.read_sql("""
                SELECT 
                    DATE_FORMAT(d.full_date, '%%b') as bulan,
                    COUNT(*) as total_transaksi
                FROM fact_sales fs
                JOIN dim_date d
                    ON fs.date_id = d.date_id
                GROUP BY DATE_FORMAT(d.full_date, '%%Y-%%m'), bulan
                ORDER BY DATE_FORMAT(d.full_date, '%%Y-%%m') DESC
                LIMIT 7
            """, conn)

            # Produk terlaris
            produk_terlaris = pd.read_sql("""
                SELECT 
                    p.category_name_english AS product_name,
                    SUM(fs.quantity) as total_terjual
                FROM fact_sales fs
                JOIN dim_product p
                    ON fs.product_id = p.product_id
                GROUP BY p.category_name_english
                ORDER BY total_terjual DESC
                LIMIT 5
            """, conn)

        return jsonify({
            "status": "success",
            "data": {
                "total_transaksi": int(total_transaksi),
                "total_revenue": float(total_revenue),
                "total_produk_terjual": int(total_qty),
                "avg_rating": float(avg_rating or 0),
                "tren_bulanan": tren_bulanan.to_dict('records'),
                "produk_terlaris": produk_terlaris.to_dict('records')
            }
        })

    except Exception as e:
        logger.error(f"ERROR DASHBOARD: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)