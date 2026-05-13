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

## 4. Menjalankan Aplikasi

Jalankan file `app.py` dengan perintah:

```bash
python app.py
```
