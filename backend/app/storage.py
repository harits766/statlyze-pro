"""Penyimpanan file dataset yang diupload.

Sekarang disimpen di disk lokal (folder storage/). Pas mau pindah ke
S3-compatible bucket nanti, cuma file ini yang perlu diubah -- endpoint
di datasets.py nggak perlu disentuh sama sekali.
"""
from __future__ import annotations

import os
import uuid
from pathlib import Path

from fastapi import UploadFile

STORAGE_DIR = Path(os.getenv("STORAGE_DIR", "storage"))
STORAGE_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}
MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB


def save_upload(file: UploadFile, owner_id: int) -> tuple[str, int]:
    """Simpan file upload ke disk, return (file_path, size_bytes).

    Nama file di-random-in (uuid) -- bukan nama asli dari user -- biar
    nggak ada dua dataset yang tabrakan nama file dan biar orang nggak
    bisa nebak-nebak nama file dataset orang lain.
    """
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Tipe file '{ext}' nggak didukung. Pakai CSV atau Excel.")

    # Cek ukuran dari metadata dulu (kalau browser ngasih tau) SEBELUM baca
    # seluruh isi file ke memory -- biar file yang kegedean langsung
    # ditolak tanpa nge-boroskan memory server buat nampung isinya dulu.
    if file.size is not None and file.size > MAX_FILE_SIZE_BYTES:
        raise ValueError("Ukuran file kelebihan batas maksimal 20 MB.")

    contents = file.file.read()

    # Cek ulang ukuran beneran setelah dibaca -- jaga-jaga kalau metadata
    # di atas nggak akurat/nggak ada.
    if len(contents) > MAX_FILE_SIZE_BYTES:
        raise ValueError("Ukuran file kelebihan batas maksimal 20 MB.")
    if len(contents) == 0:
        raise ValueError("File kosong.")

    user_dir = STORAGE_DIR / str(owner_id)
    user_dir.mkdir(parents=True, exist_ok=True)

    unique_name = f"{uuid.uuid4().hex}{ext}"
    file_path = user_dir / unique_name

    with open(file_path, "wb") as f:
        f.write(contents)

    return str(file_path), len(contents)
