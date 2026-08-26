FROM python:3.12-slim

WORKDIR /app

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
CMD python -m app.init_db && uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
