FROM python:3.12-slim

WORKDIR /app

# WAJIB: tanpa ini, output print()/log Python bisa "ketahan" di buffer dan
# nggak muncul di log Railway sampai proses selesai (atau malah ilang kalau
# proses keburu mati) -- ini beberapa kali bikin kita salah diagnosa masalah
# lain karena log terakhir yang sukses tampil bukan yang sebenarnya terakhir
# dieksekusi.
ENV PYTHONUNBUFFERED=1

# Copy requirements dulu (terpisah dari kode) biar layer ini di-cache
# dan nggak perlu install ulang tiap kali cuma kode yang berubah.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy sisa kode (app/ dan modules/)
COPY . .

# Port di-set lewat environment variable PORT (dikasih otomatis sama
# kebanyakan hosting kayak Railway/Render). Default 8001 buat lokal.
ENV PORT=8001
EXPOSE 8001

# Urutan start-nya penting:
#   [1] init_db     -> bikin tabel yang belum ada (database baru)
#   [2] migrate     -> tambahin kolom yang belum ada di tabel LAMA
#   [3] uvicorn     -> baru start server
#
# Langkah [2] nggak bisa digantiin [1]: create_all() cuma bikin tabel yang
# belum ada, dia NGGAK nambahin kolom baru ke tabel yang udah terlanjur
# jalan. Tanpa ini, database production yang tabel users-nya udah ada bakal
# kehilangan kolom `username` dan SEMUA query auth balikin 500.
# Dua-duanya aman dijalanin tiap kali container restart.
#
# --host 0.0.0.0 WAJIB di dalam container (bukan 127.0.0.1) biar bisa
# diakses dari luar container. echo di antara tiap perintah biar keliatan
# jelas transisi antar fase di log.
CMD echo "=== [1/3] Init database ===" && python -m app.init_db && echo "=== [2/3] Migrasi kolom username ===" && python -m app.migrate_add_username && echo "=== [3/3] Starting Uvicorn di port ${PORT} ===" && uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --log-level debug
