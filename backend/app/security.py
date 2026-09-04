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


# Hash beneran (bcrypt cost 12) buat akun palsu -- lihat dummy_verify_password().
_DUMMY_PASSWORD_HASH = b"$2b$12$4eI57Fwoz4TYyX8KfSQkzesOw/PuAOC9VGwTZ29HSMw/vApaHDdS6"


def hash_password(password: str) -> str:
    """Ubah password plain jadi hash -- ini yang disimpan ke database, bukan plain text."""
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Cek password yang diinput user cocok sama hash yang tersimpan."""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def dummy_verify_password() -> None:
    """Bakar waktu kira-kira sama dengan verify_password(), tanpa user beneran.

    Dipakai di /login pas akun nggak ketemu. Tanpa ini, respons buat akun
    yang nggak ada bakal jauh lebih cepat daripada akun yang ada (karena
    bcrypt-nya di-skip) -- dari selisih waktu itu orang bisa nebak email
    atau username mana yang terdaftar.
    """
    bcrypt.checkpw(b"password-palsu", _DUMMY_PASSWORD_HASH)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Bikin JWT token. `data` berisi {"sub": str(id_user)}.

    Sengaja pakai ID, bukan email/username: kalau nanti user ganti email
    atau username, token yang udah terlanjur dibagikan tetap nunjuk ke
    akun yang benar.
    """
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
