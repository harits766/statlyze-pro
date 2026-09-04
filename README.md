# 📊 Statlyze

**Analisis statistik otomatis untuk data tabular — murni matematika, nol dependensi AI/LLM.**

Upload CSV/Excel, dan Statlyze otomatis melakukan EDA, memilih uji statistik yang tepat (parametrik vs non-parametrik, tergantung distribusi data), merekomendasikan analisis lanjutan yang relevan (regresi, clustering, atau PCA), lalu menerjemahkan semuanya jadi insight berbahasa natural — semua dihitung lokal pakai `scipy`, `numpy`, dan `statsmodels`, **tanpa memanggil API AI/LLM sama sekali**.

🔗 **[Coba langsung](https://successful-manifestation-production-236a.up.railway.app)** · 📖 **[API Docs](https://statlyze-pro-production.up.railway.app/docs)**

---

## Kenapa ini beda dari "AI insight generator" kebanyakan

Banyak tool sejenis nembak dataset ke LLM dan minta dia "kasih insight". Statlyze sengaja **tidak** begitu:

- Setiap insight bisa ditelusuri balik ke angka statistik yang jelas (p-value, r, R², VIF, dll) — bukan tebakan model bahasa.
- Metode uji dipilih otomatis berdasarkan **asumsi data yang sebenarnya** (uji normalitas Shapiro-Wilk dulu, baru tentuin Pearson/Spearman, t-test/Mann-Whitney, dst), bukan di-hardcode.
- Hasilnya reproducible: dataset yang sama akan selalu menghasilkan insight yang sama persis.

## ✨ Fitur

**Exploratory Data Analysis**
- Auto-deteksi tipe kolom (numerik/kategorikal/datetime/teks) dan profiling deskriptif
- Deteksi outlier (IQR) dan data hilang
- Korelasi numerik-numerik dengan pemilihan Pearson/Spearman otomatis
- Uji beda rata-rata numerik-kategorikal (Welch t-test/Mann-Whitney/ANOVA/Kruskal-Wallis, otomatis sesuai jumlah grup & normalitas)
- Uji asosiasi kategorikal-kategorikal (Chi-square + Cramér's V)
- Deteksi multikolinearitas (VIF)

**Rekomendasi & analisis lanjutan** *(rule-based, bukan machine learning prediktif)*
- Mesin rekomendasi baca karakteristik dataset (kekuatan korelasi, VIF, jumlah variabel) dan menyarankan analisis yang relevan
- Regresi linear & logistik (statsmodels) — koefisien, p-value, R²/pseudo-R², bukan cuma skor akurasi
- Hierarchical clustering dengan jumlah cluster optimal ditentukan lewat silhouette score
- PCA (dekomposisi matriks kovarians manual pakai numpy) untuk meringkas variabel yang saling redundan

**Aplikasi**
- Auth JWT: register pakai username unik + email, login bisa pakai **email atau username**
- Rate limiting (5 percobaan register/login per menit per IP), validasi input
- Upload dataset, riwayat dataset per user
- Insight diranking berdasarkan signifikansi & kekuatan efek, ditampilkan berbahasa natural

## 🧠 Cara kerja

1. **EDA** — Profiling, korelasi, deteksi pola
2. **Rekomendasi** — Baca karakteristik data, pilih analisis yang relevan
3. **Analisis lanjutan** — Regresi, clustering, atau PCA (sesuai rekomendasi)
4. **Insight** — Interpretasi otomatis + angka pendukung

Tahap 2 murni rule-based (if/else atas hasil tahap 1) — bukan model ML, jadi tiap rekomendasi bisa dijelaskan alasannya (misal: *"income dan spending berkorelasi kuat (r=0.95) → rekomendasi regresi linear"*).

## 🛠️ Tech stack

| Layer | Teknologi |
|---|---|
| Statistical engine | Python, `pandas`, `numpy`, `scipy`, `statsmodels` |
| Backend | FastAPI, SQLAlchemy, JWT (`python-jose`), `bcrypt`, `slowapi` (rate limiting) |
| Frontend | React, Vite |
| Deployment | Docker, Railway |

## 📁 Struktur project

- **`backend/`**
  - `app/` — FastAPI: auth, endpoint dataset, security, rate limiting
  - `modules/` — Statistical engine
    - `data_loader.py` — Load & deteksi tipe kolom
    - `profiling.py` — Descriptive stats & outlier
    - `stats_engine.py` — Korelasi, uji beda rata-rata, asosiasi kategorikal, VIF
    - `recommender.py` — Rule-based recommender analisis lanjutan
    - `regression.py` — Regresi linear & logistik (statsmodels)
    - `clustering.py` — Hierarchical clustering + silhouette score
    - `multivariate.py` — PCA
    - `insight_engine.py` — Terjemahin hasil statistik jadi kalimat + ranking
  - `requirements.txt`
  - `Dockerfile`
- **`frontend/`** — React + Vite
  - `Dockerfile`

## 🚀 Menjalankan secara lokal

**Backend**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env      # isi SECRET_KEY (python -c "import secrets; print(secrets.token_hex(32))")
python -m app.init_db
python -m app.migrate_add_username   # cuma perlu kalau DB-nya udah ada sebelum fitur username
uvicorn app.main:app --reload --port 8001
```

**Frontend**
```bash
cd frontend
npm install
npm run dev
```

Detail lebih lengkap (Docker, deploy ke Railway) ada di `backend/README.md`.

## 🔐 Akun & login

- Register butuh **username + email + password**. Username unik, 3–20 karakter, diawali huruf, isinya huruf/angka/underscore, dan sebagian kata dipesan sistem (`admin`, `login`, `api`, dll).
- Login menerima **email atau username**. Keduanya disimpan huruf kecil semua, jadi tidak case-sensitive.
- Token JWT berisi ID user (bukan email), sehingga tetap valid kalau nanti ada fitur ganti email/username.
- Pesan login gagal disamakan untuk semua kasus dan hashing tetap dijalankan walau akun tidak ditemukan — supaya selisih waktu respons tidak membocorkan email/username mana yang terdaftar.

Kolom `username` ditambahkan ke tabel yang sudah ada lewat `app/migrate_add_username.py` — `create_all()` hanya membuat tabel baru, tidak menambah kolom. Migrasi ini idempotent dan sudah dijalankan otomatis sebagai langkah `[2/3]` di `Dockerfile`, jadi deploy tidak perlu tindakan manual.

## 📖 API Reference

Swagger UI otomatis tersedia di `/docs` — [lihat versi live](https://statlyze-pro-production.up.railway.app/docs).

## 🗺️ Roadmap

- [ ] MANOVA untuk kategorikal vs multi-outcome numerik
- [ ] Export hasil analisis ke PDF/Excel
- [ ] Visualisasi (scatter plot, dendrogram, biplot PCA)
- [ ] Pindah dari SQLite ke PostgreSQL untuk persistensi production

---

Dibangun sebagai eksplorasi: seberapa jauh insight otomatis bisa dibuat tanpa LLM, murni dari statistik klasik.
