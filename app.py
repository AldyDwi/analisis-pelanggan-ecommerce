from flask import Flask, render_template, request, redirect, flash
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.dialects.mysql import insert
from config import Config
from etl_pipeline import run_etl_process
import datetime
import oci
import os

app = Flask(__name__)
app.config.from_object(Config)

# Inisialisasi Engine Database
engine_oltp = create_engine(app.config['SQLALCHEMY_OLTP_URI'])

# Konfigurasi OCI Object Storage (Gunakan Try-Except agar Dummy Test lokal tidak terganggu)
try:
    # Jika di lokal, ini akan membaca file konfigurasi OCI CLI (~/.oci/config)
    # Jika di server nantinya, kita akan ubah menggunakan Instance Principals
    oci_config = oci.config.from_file()
    object_storage_client = oci.object_storage.ObjectStorageClient(oci_config)
    NAMESPACE = object_storage_client.get_namespace().data
    BUCKET_NAME = "ecommerce-raw-data"
    OCI_AVAILABLE = True
except Exception as e:
    print(f"Peringatan: Koneksi OCI Object Storage belum dikonfigurasi di lokal. ({e})")
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
                    print(f"Backup berhasil: {nama_file_backup} tersimpan di Object Storage.")
                except Exception as e:
                    print(f"Gagal backup ke Object Storage: {e}")
            
            # Kembalikan posisi kursor pembacaan file ke awal (karena sudah dibaca oleh file.read() sebelumnya)
            file.seek(0)
            
            # 3. PROSES KE DATABASE OLTP DENGAN UPSERT
            df = pd.read_csv(file)
            table_name = file_to_table[file.filename]
            
            # Menggunakan method=mysql_upsert agar tidak error saat ada data ganda
            df.to_sql(table_name, con=engine_oltp, if_exists='append', index=False, method=mysql_upsert)
            print(f"Berhasil Upsert {file.filename} ke tabel {table_name}")

    # Setelah semua file OLTP masuk, jalankan proses ETL
    try:
        run_etl_process()
        return "Upload, Backup OCI, dan Proses ETL Berhasil!"
    except Exception as e:
        return f"Proses database berhasil, tapi ETL gagal: {str(e)}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)