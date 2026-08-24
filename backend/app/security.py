"""Hashing password & JWT token -- semua logic keamanan auth ada di sini.

Dipisah dari main.py biar gampang dites sendiri, dan biar main.py fokus
cuma ke routing endpoint.
"""
from __future__ import annotations

import os
import warnings
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

_DEFAULT_SECRET_KEY = "ganti-ini-di-production-pakai-env-var"

# WAJIB di-override lewat environment variable SECRET_KEY pas production.
# Nilai default ini cuma buat development lokal.
SECRET_KEY = os.getenv("SECRET_KEY", _DEFAULT_SECRET_KEY)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # token berlaku 1 hari

if SECRET_KEY == _DEFAULT_SECRET_KEY:
    warnings.warn(
        "SECRET_KEY masih pakai nilai default. Ini oke buat development, "
        "tapi WAJIB diganti lewat environment variable SECRET_KEY sebelum "
        "deploy ke production -- generate string acak lewat: "
        "python -c \"import secrets; print(secrets.token_hex(32))\"",
        stacklevel=2,
    )


def hash_password(password: str) -> str:
    """Ubah password plain jadi hash -- ini yang disimpan ke database, bukan plain text."""
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Cek password yang diinput user cocok sama hash yang tersimpan."""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Bikin JWT token. `data` biasanya berisi {"sub": email_user}."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    """Baca isi token. Return None kalau token invalid/kedaluwarsa/dipalsuin."""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None
