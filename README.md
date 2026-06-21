# Analisis Pelanggan E-Commerce

## Penjelasan Project

Proyek ini adalah aplikasi web berbasis Flask yang dirancang untuk melakukan proses *Extract, Transform, Load* (ETL) dan visualisasi analisis data pelanggan e-commerce. Aplikasi ini mengimplementasikan arsitektur *Dual-Storage* modern dan *Containerization* dengan fitur utama sebagai berikut:

* **Penyimpanan Cloud & Big Data:** Mengunggah dan mencadangkan data CSV mentah secara bersamaan ke **Oracle Cloud Infrastructure (OCI) Object Storage** dan klaster **Hadoop (HDFS)**.
* **Pemrosesan ETL:** Membaca data CSV menggunakan Pandas dan memprosesnya menggunakan SQLAlchemy untuk didistribusikan ke dalam database.
* **Data Warehousing:** Menyimpan data terstruktur ke dalam MySQL menggunakan pemodelan **Star Schema** (`db_starschema` untuk tabel dimensi dan fakta) serta penyimpanan tabel mentah (`db_oltp`).
* **Visualisasi Dashboard:** Menyediakan *endpoint* API untuk menampilkan metrik analitik pelanggan ke antarmuka pengguna melalui grafik interaktif.
* **Microservices Architecture:** Seluruh ekosistem (Flask Web, MySQL, Hadoop NameNode, dan DataNode) dibungkus dan diisolasi menggunakan Docker.

---

## Cara Menjalankan Project (Versi Docker - Direkomendasikan)

Ini adalah cara paling praktis karena Anda tidak perlu menginstal Python, MySQL, atau Hadoop secara manual di mesin Anda.

### Syarat Utama:
* Pastikan aplikasi **Docker Desktop** (atau *Docker Engine* di Linux) sudah terinstal dan dalam keadaan menyala (Running).

### Langkah-langkah:
1. Buka terminal pada folder proyek.
2. Pastikan di dalam `docker-compose.yml`, variabel `USE_INSTANCE_PRINCIPAL=False` (jika dijalankan di laptop lokal).
3. Bangun dan nyalakan seluruh *container* (Web, Database, dan Hadoop) di latar belakang dengan perintah:
   ```bash
   docker compose up -d --build
   ```
4. Setelah semua *container* berstatus *Up* (bisa dicek dengan `docker compose ps`), jalankan skrip ini untuk membuat tabel otomatis di dalam database MySQL Docker:
   ```bash
   docker compose exec web python init_db.py
   ```
5. Buka *browser* dan akses aplikasi pada: **`http://localhost:5000`**
   *(Catatan: Anda juga bisa mengakses Web UI Hadoop NameNode pada `http://localhost:9870`).*

> **Tips:** Untuk mematikan dan menghapus seluruh *container* beserta datanya, gunakan perintah: `docker compose down -v`

---

## Cara Menjalankan Project (Versi Lokal / Tanpa Docker)

Jika Anda ingin menjalankan atau mengembangkan aplikasi langsung di laptop (mode tradisional), ikuti langkah-langkah berikut:

### 1. Membuat Virtual Environment (venv)
Buka terminal pada folder project, lalu jalankan:
```bash
python -m venv venv
```

### 2. Masuk ke Virtual Environment

**Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate
```

**Windows (CMD):**
```cmd
venv\Scripts\activate
```
*(Jika berhasil, akan muncul tulisan `(venv)` di awal baris terminal).*

### 3. Install Library dari requirements.txt
Jalankan perintah berikut untuk mengunduh semua pustaka yang dibutuhkan:
```bash
pip install -r requirements.txt
```

### 4. Inisialisasi Database
Sebelum menjalankan perintah ini, pastikan MySQL lokal (misal: XAMPP/Laragon) menyala dan database kosong (`db_oltp` dan `db_starschema`) sudah dibuat secara manual.
```bash
python init_db.py
```
*(Catatan: Pastikan juga Anda sudah menyesuaikan IP, username, dan password database lokal di dalam file `config.py` sebelum mengeksekusi skrip ini).*

### 5. Menjalankan Aplikasi
Jalankan file `app.py` dengan perintah:
```bash
python app.py
```