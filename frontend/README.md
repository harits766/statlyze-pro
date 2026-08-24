# statlyze-frontend

Langkah 5 dari roadmap: frontend React yang consume API backend
(`statlyze-pro`). Tiga halaman sesuai wireframe: Login/Register, Dataset
(upload + list), Insights (dashboard).

## Struktur

```
statlyze-frontend/
├── src/
│   ├── api.js           # semua fungsi fetch() ke backend, satu tempat
│   ├── App.jsx           # atur login state & navigasi antar halaman
│   ├── index.css         # semua styling
│   └── pages/
│       ├── Login.jsx      # login + register (toggle satu form)
│       ├── Datasets.jsx   # upload file + daftar dataset
│       └── Insights.jsx   # daftar insight untuk satu dataset
├── .env.example
└── package.json
```

Sudah dites otomatis (4 skenario): validasi form kosong, login ditolak
kalau salah password, alur register sampai masuk halaman dataset (lawan
backend Python asli), dan alur penuh upload → analisis → lihat insight →
kembali → logout.

## Cara jalanin

### 1. Install Node.js (kalau belum ada)

Sama kayak Python kemarin, ini juga sering ada drama PATH. Download dari
[nodejs.org](https://nodejs.org/) (pilih versi LTS), install, lalu **tutup
total dan buka ulang VS Code**. Cek di terminal:

```bash
node --version
npm --version
```

Kalau muncul angka versi, beres. Kalau "not recognized", install ulang
dan pastikan opsi PATH-nya ke-centang (mirip kasus Python kemarin).

### 2. Install dependencies & jalanin

```bash
cd statlyze-frontend
npm install
npm run dev
```

Setelah `npm run dev`, muncul alamat kayak `http://localhost:5173` --
buka itu di browser.

**Penting:** backend (`statlyze-pro`) harus lagi jalan bersamaan di
`localhost:8000` (`py -m uvicorn app.main:app --reload`), dan backend-nya
harus sudah versi terbaru yang ada CORS-nya (lihat paket
`statlyze-cors-update` yang terpisah) -- kalau nggak, browser bakal nolak
semua request dari frontend ke backend.

## Konfigurasi alamat backend

Default-nya frontend manggil `http://localhost:8000`. Kalau backend-nya
jalan di alamat lain, copy `.env.example` jadi `.env` dan ubah
`VITE_API_URL`.

## Kalau upload gagal / dataset nggak muncul

Cek 2 hal ini dulu:
1. Backend beneran lagi jalan (buka `localhost:8000/docs`, harus muncul
   Swagger)
2. Backend-nya udah pakai `main.py` versi dengan CORS (lihat paket
   `statlyze-cors-update`)

## Langkah selanjutnya

Testing lebih lanjut (edge case, validasi tambahan), lalu security
hardening (rate limiting, validasi file lebih ketat) dan deploy (Docker +
hosting), sesuai roadmap yang udah dibahas.
