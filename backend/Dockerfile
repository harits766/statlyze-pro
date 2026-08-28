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

# Bikin tabel database dulu (aman dijalanin berkali-kali, cuma bikin
# kalau belum ada), baru start server-nya. --host 0.0.0.0 WAJIB di
# dalam container (bukan 127.0.0.1) biar bisa diakses dari luar container.
# echo di antara dua perintah biar keliatan jelas transisi antar fase di log.
CMD echo "=== [1/2] Init database ===" && python -m app.init_db && echo "=== [2/2] Starting Uvicorn di port ${PORT} ===" && uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --log-level debug
