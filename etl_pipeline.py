from sqlalchemy import create_engine, text
from config import Config

def run_etl_process():
    engine_oltp = create_engine(Config.SQLALCHEMY_OLTP_URI)
    engine_star = create_engine(Config.SQLALCHEMY_STAR_URI)

    with engine_star.connect() as conn:
        # 1. Mengisi Dimensi Produk
        query_dim_product = text("""
            INSERT IGNORE INTO db_starschema.dim_product (product_id, category_name_portuguese, category_name_english)
            SELECT p.product_id, p.product_category_name, t.product_category_name_english
            FROM db_oltp.products p
            LEFT JOIN db_oltp.product_category_translation t 
            ON p.product_category_name = t.product_category_name
        """)
        conn.execute(query_dim_product)

        # 2. Mengisi Dimensi Pelanggan (Bagian yang baru ditambahkan)
        query_dim_customer = text("""
            INSERT IGNORE INTO db_starschema.dim_customer (customer_id, customer_city, customer_state)
            SELECT customer_id, customer_city, customer_state
            FROM db_oltp.customers
        """)
        conn.execute(query_dim_customer)

        # 3. Mengisi Dimensi Waktu
        query_dim_date = text("""
            INSERT IGNORE INTO db_starschema.dim_date (date_id, full_date, year, month, month_name, day_of_week, hour)
            SELECT 
                DATE_FORMAT(order_purchase_timestamp, '%Y%m%d'),
                DATE(order_purchase_timestamp),
                YEAR(order_purchase_timestamp),
                MONTH(order_purchase_timestamp),
                MONTHNAME(order_purchase_timestamp),
                DAYNAME(order_purchase_timestamp),
                HOUR(order_purchase_timestamp)
            FROM db_oltp.orders
            WHERE order_purchase_timestamp IS NOT NULL
        """)
        conn.execute(query_dim_date)

        # 4. Mengisi Tabel Fakta Penjualan
        query_fact_sales = text("""
            INSERT IGNORE INTO db_starschema.fact_sales (order_id, product_id, customer_id, date_id, revenue, quantity)
            SELECT 
                i.order_id, i.product_id, o.customer_id, 
                DATE_FORMAT(o.order_purchase_timestamp, '%Y%m%d'),
                (i.price + i.freight_value), 1
            FROM db_oltp.order_items i
            JOIN db_oltp.orders o ON i.order_id = o.order_id
        """)
        conn.execute(query_fact_sales)
        
        conn.commit()
    print("Proses ETL dari OLTP ke Star Schema selesai.")