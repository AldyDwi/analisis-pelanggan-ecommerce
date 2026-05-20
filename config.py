import os

# class Config:
#     # Pengaturan untuk Flask
#     SECRET_KEY = os.environ.get('SECRET_KEY') or 'kunci-rahasia-yang-sangat-aman-123'
#     MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # Batasan maksimal upload file: 100 MB
    
#     # Pengaturan Database OLTP & Star Schema
#     # Format: mysql+pymysql://username:password@IP_Private/nama_database
#     DB_USER = 'admin'
#     DB_PASS = '@Tugascloud123'
#     DB_HOST = '172.16.2.107'
    
#     SQLALCHEMY_OLTP_URI = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/db_oltp"
#     SQLALCHEMY_STAR_URI = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/db_starschema"


# Untuk Dummy Test di lokal
# class Config:
#     MAX_CONTENT_LENGTH = 800 * 1024 * 1024  
    
#     # --- KONFIGURASI LOKAL (DUMMY TEST) ---
#     DB_USER = 'root'
#     DB_PASS = ''
#     DB_HOST = '127.0.0.1'
    
#     SQLALCHEMY_OLTP_URI = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/db_oltp"
#     SQLALCHEMY_STAR_URI = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/db_starschema"


# UNTUK PRODUCTION (DOCKER)
class Config:
    MAX_CONTENT_LENGTH = 800 * 1024 * 1024  

    DB_USER = 'root'
    DB_PASS = 'Tugascloud123'
    DB_HOST = 'mysql-db'
    
    SQLALCHEMY_OLTP_URI = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/db_oltp"
    SQLALCHEMY_STAR_URI = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/db_starschema"
