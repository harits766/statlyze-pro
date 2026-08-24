"""Setup koneksi database & base class buat semua model.

Default pakai SQLite biar gampang dites lokal tanpa install apa-apa.
Pas udah siap production, tinggal ganti DATABASE_URL ke Postgres lewat
environment variable -- kode model & query-nya nggak perlu diubah.
"""
from __future__ import annotations

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./statlyze.db")

# SQLite butuh connect_args ini biar bisa dipakai lintas thread (FastAPI jalan async).
# Postgres/database lain nggak butuh ini.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency buat FastAPI: buka session per-request, tutup otomatis setelahnya."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
