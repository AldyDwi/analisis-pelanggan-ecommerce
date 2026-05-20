# Cara Menjalankan Project

## 1. Membuat Virtual Environment (venv)

Buka terminal pada folder project, lalu jalankan:

```bash
python -m venv venv
```

---

## 2. Masuk ke Virtual Environment

### Windows (PowerShell)

```powershell
.\venv\Scripts\Activate
```

### Windows (CMD)

```cmd
venv\Scripts\activate
```

Jika berhasil, akan muncul `(venv)` pada terminal.

---

## 3. Install Library dari requirements.txt

Jalankan perintah berikut:

```bash
pip install -r requirements.txt
```

---

## 4. Inisialisasi Database

Sebelum menjalankan aplikasi utama, pastikan database (db_oltp dan db_starschema) beserta seluruh tabelnya sudah dibuat. Jalankan perintah berikut:

```bash
python init_db.py
```

(Catatan: Pastikan Anda sudah menyesuaikan IP, username, dan password database di dalam file config.py sebelum menjalankan perintah ini).

---

## 5. Menjalankan Aplikasi

Jalankan file `app.py` dengan perintah:

```bash
python app.py
```
