# Statlyze Pro — paket gabungan

Ini gabungan dari semua increment (backend + auth + integration + security +
cors) jadi satu struktur siap pakai. Detail lihat catatan di bawah.

## Struktur
```
statlyze-pro/
├── backend/
│   ├── app/         # FastAPI: auth, datasets, security, rate limiting
│   ├── modules/     # Statistical engine (data_loader, profiling, stats_engine, insight_engine)
│   ├── requirements.txt
│   └── .env.example
└── frontend/        # React + Vite
    └── .env         # sudah di-set ke http://127.0.0.1:8001
```

## Cara jalanin

### 1. Backend
```
cd backend
python -m venv venv
venv\Scripts\activate          (Windows)  /  source venv/bin/activate (Mac/Linux)
pip install -r requirements.txt
copy .env.example .env         (isi SECRET_KEY, generate lewat: python -c "import secrets; print(secrets.token_hex(32))")
python -m app.init_db          (sekali aja, bikin tabel)
py -m uvicorn app.main:app --reload --port 8001
```
Buka http://127.0.0.1:8001/docs — harus muncul Swagger UI.

**Kalau database-nya udah pernah dipakai sebelum fitur username ada**, jalanin
migrasi ini sekali (aman diulang, otomatis skip kalau udah pernah):
```
python -m app.migrate_add_username
```
User lama otomatis dikasih username dari bagian depan email-nya
(budi@mail.com -> `budi`).

### 2. Frontend
```
cd frontend
npm install
npm run dev
```
Buka alamat yang muncul di terminal (biasanya http://localhost:5173).

## Kenapa port 8001, bukan 8000
Port 8000 kemarin nyangkut catatan koneksi lama di netstat padahal prosesnya
udah mati (gejala umum kalau server distop paksa/Ctrl+C tanpa nunggu cleanup).
Pindah ke 8001 itu jalan pintas paling aman ketimbang ngebersihin port lama.
Kalau mau balik ke 8000 nanti, tinggal ganti `--port 8001` jadi `--port 8000`
DAN ganti isi `frontend/.env` (`VITE_API_URL`) biar tetap nyambung.

## Akun & login
- Daftar butuh **username + email + password**. Username unik, 3-20 karakter,
  diawali huruf, isinya huruf/angka/underscore.
- Login boleh pakai **email ATAU username** — dua-duanya nggak case-sensitive
  karena disimpan huruf kecil semua.
- Token JWT isinya ID user, jadi tetap valid walau nanti email/username diganti.
- Percobaan register & login dibatasi 5x per menit per IP. Kalau lagi ngetes
  berulang-ulang di lokal, set `RATE_LIMIT_ENABLED=0` di `.env`.

## Catatan penting
- `app/main.py` pakai versi dari langkah security (CORS + rate limiter
  sekaligus). Jangan timpa pakai `statlyze-cors-update` lagi — itu versi lama
  yang rate limiter-nya belum ada.
- `frontend/src/api.js` sudah versi terbaru (penanganan pesan error validasi
  dari FastAPI/Pydantic lebih rapi).
