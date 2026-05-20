from sqlalchemy import create_engine, text
from config import Config

def initialize_databases():
    print("Mulai inisialisasi database...")

    # 1. KONEKSI KE SERVER UTAMA (Tanpa menentukan nama DB terlebih dahulu)
    # Ini diperlukan untuk membuat database 'db_oltp' dan 'db_starschema' jika belum ada
    base_uri = f"mysql+pymysql://{Config.DB_USER}:{Config.DB_PASS}@{Config.DB_HOST}"
    base_engine = create_engine(base_uri)

    try:
        with base_engine.connect() as conn:
            conn.execute(text("CREATE DATABASE IF NOT EXISTS db_oltp;"))
            conn.execute(text("CREATE DATABASE IF NOT EXISTS db_starschema;"))
            conn.commit()
        print("Database db_oltp dan db_starschema siap atau sudah ada.")
    except Exception as e:
        print(f"Gagal membuat database utama: {e}")
        return

    # ==========================================
    # 2. SKRIP PEMBUATAN TABEL UNTUK DB_OLTP
    # ==========================================
    sql_oltp_tables = """
    USE db_oltp;

    CREATE TABLE IF NOT EXISTS geolocation (
        geolocation_zip_code_prefix VARCHAR(10),
        geolocation_lat DECIMAL(10, 8),
        geolocation_lng DECIMAL(11, 8),
        geolocation_city VARCHAR(100),
        geolocation_state CHAR(2)
    );

    CREATE TABLE IF NOT EXISTS customers (
        customer_id VARCHAR(50) PRIMARY KEY,
        customer_unique_id VARCHAR(50),
        customer_zip_code_prefix VARCHAR(10),
        customer_city VARCHAR(100),
        customer_state CHAR(2)
    );

    CREATE TABLE IF NOT EXISTS sellers (
        seller_id VARCHAR(50) PRIMARY KEY,
        seller_zip_code_prefix VARCHAR(10),
        seller_city VARCHAR(100),
        seller_state CHAR(2)
    );

    CREATE TABLE IF NOT EXISTS products (
        product_id VARCHAR(50) PRIMARY KEY,
        product_category_name VARCHAR(100),
        product_name_lenght INT,
        product_description_lenght INT,
        product_photos_qty INT,
        product_weight_g INT,
        product_length_cm INT,
        product_height_cm INT,
        product_width_cm INT
    );

    CREATE TABLE IF NOT EXISTS product_category_translation (
        product_category_name VARCHAR(100) PRIMARY KEY,
        product_category_name_english VARCHAR(100)
    );

    CREATE TABLE IF NOT EXISTS orders (
        order_id VARCHAR(50) PRIMARY KEY,
        customer_id VARCHAR(50),
        order_status VARCHAR(20),
        order_purchase_timestamp DATETIME,
        order_approved_at DATETIME,
        order_delivered_carrier_date DATETIME,
        order_delivered_customer_date DATETIME,
        order_estimated_delivery_date DATETIME
    );

    CREATE TABLE IF NOT EXISTS order_items (
        order_id VARCHAR(50),
        order_item_id INT,
        product_id VARCHAR(50),
        seller_id VARCHAR(50),
        shipping_limit_date DATETIME,
        price DECIMAL(10, 2),
        freight_value DECIMAL(10, 2),
        PRIMARY KEY (order_id, order_item_id)
    );

    CREATE TABLE IF NOT EXISTS order_payments (
        order_id VARCHAR(50),
        payment_sequential INT,
        payment_type VARCHAR(20),
        payment_installments INT,
        payment_value DECIMAL(10, 2),
        PRIMARY KEY (order_id, payment_sequential)
    );

    CREATE TABLE IF NOT EXISTS order_reviews (
        review_id VARCHAR(50) PRIMARY KEY,
        order_id VARCHAR(50),
        review_score INT,
        review_comment_title VARCHAR(255),
        review_comment_message TEXT,
        review_creation_date DATETIME,
        review_answer_timestamp DATETIME
    );
    """

    # ==========================================
    # 3. SKRIP PEMBUATAN TABEL UNTUK DB_STARSCHEMA
    # ==========================================
    sql_star_tables = """
    USE db_starschema;

    CREATE TABLE IF NOT EXISTS dim_product (
        product_id VARCHAR(50) PRIMARY KEY,
        category_name_portuguese VARCHAR(100),
        category_name_english VARCHAR(100)
    );

    CREATE TABLE IF NOT EXISTS dim_customer (
        customer_id VARCHAR(50) PRIMARY KEY,
        customer_city VARCHAR(100),
        customer_state CHAR(2)
    );

    CREATE TABLE IF NOT EXISTS dim_date (
        date_id INT PRIMARY KEY,
        full_date DATE,
        year INT,
        month INT,
        month_name VARCHAR(20),
        day_of_week VARCHAR(20),
        hour INT
    );

    CREATE TABLE IF NOT EXISTS fact_sales (
        order_id VARCHAR(50),
        product_id VARCHAR(50),
        customer_id VARCHAR(50),
        date_id INT,
        revenue DECIMAL(12, 2),
        quantity INT,
        review_score INT,
        PRIMARY KEY (order_id, product_id),
        INDEX (date_id),
        INDEX (product_id)
    );
    """

    # Eksekusi skrip tabel db_oltp
    try:
        engine_oltp = create_engine(Config.SQLALCHEMY_OLTP_URI)
        with engine_oltp.connect() as conn:
            # Memisahkan perintah SQL berdasarkan titik koma (;) karena SQLAlchemy 
            # execute() secara default mengeksekusi satu pernyataan per panggilan
            statements = sql_oltp_tables.split(';')
            for statement in statements:
                if statement.strip():
                    conn.execute(text(statement))
            conn.commit()
        print("Seluruh tabel pada 'db_oltp' berhasil dibuat.")
    except Exception as e:
        print(f"Gagal membuat tabel pada db_oltp: {e}")

    # Eksekusi skrip tabel db_starschema
    try:
        engine_star = create_engine(Config.SQLALCHEMY_STAR_URI)
        with engine_star.connect() as conn:
            statements = sql_star_tables.split(';')
            for statement in statements:
                if statement.strip():
                    conn.execute(text(statement))
            conn.commit()
        print("Seluruh tabel pada 'db_starschema' berhasil dibuat.")
    except Exception as e:
        print(f"Gagal membuat tabel pada db_starschema: {e}")

    print("Proses inisialisasi selesai.")

if __name__ == '__main__':
    initialize_databases()