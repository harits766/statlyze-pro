"""Jalanin file ini buat bikin semua tabel di database sesuai model.

Cara pakai:
    python -m app.init_db

Aman dijalanin berkali-kali -- create_all cuma bikin tabel yang belum ada,
nggak nimpa tabel yang udah ada.
"""
from .database import Base, engine
from . import models  # noqa: F401  (import biar semua model ke-register ke Base)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    print("Tabel berhasil dibuat:", list(Base.metadata.tables.keys()))


if __name__ == "__main__":
    init_db()
