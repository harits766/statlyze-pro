"""Pydantic schemas: bentuk data yang masuk (request) & keluar (response) API.

Ini beda sama models.py (SQLAlchemy) -- models.py itu bentuk tabel di
database, schemas.py ini bentuk JSON yang dilihat/dikirim user lewat API.

Semua aturan validasi username/email/password ditaruh di sini (bukan di
main.py) biar ada satu sumber kebenaran: endpoint tinggal terima objek
yang udah pasti valid & udah dinormalisasi.
"""
from __future__ import annotations

import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator

USERNAME_MIN_LENGTH = 3
USERNAME_MAX_LENGTH = 20
PASSWORD_MIN_LENGTH = 8
# bcrypt cuma baca 72 byte pertama dan versi barunya langsung error kalau
# lebih -- jadi ditolak di sini biar user dapat pesan jelas, bukan error 500.
PASSWORD_MAX_BYTES = 72

# Harus mulai dari huruf, sisanya boleh huruf/angka/underscore. Angka di depan
# dilarang biar username nggak pernah bentrok sama ID user (dipakai di JWT).
_USERNAME_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")

# Kata yang dipesan buat path endpoint atau akun sistem -- jangan sampai ada
# user bikin username "admin" atau "login".
RESERVED_USERNAMES = frozenset(
    {
        "admin", "administrator", "root", "superuser", "system", "statlyze",
        "support", "help", "api", "auth", "login", "logout", "register",
        "me", "user", "users", "account", "settings", "dataset", "datasets",
        "insight", "insights", "docs", "redoc", "static", "null", "undefined",
    }
)


def normalize_username(value: str) -> str:
    """Rapihin + validasi username. Dipakai bareng sama /register."""
    v = value.strip().lower()

    if not v:
        raise ValueError("Username wajib diisi")
    if len(v) < USERNAME_MIN_LENGTH:
        raise ValueError(f"Username minimal {USERNAME_MIN_LENGTH} karakter")
    if len(v) > USERNAME_MAX_LENGTH:
        raise ValueError(f"Username maksimal {USERNAME_MAX_LENGTH} karakter")
    if not _USERNAME_PATTERN.match(v):
        raise ValueError(
            "Username harus diawali huruf dan cuma boleh berisi huruf, angka, "
            "atau underscore (_)"
        )
    if v in RESERVED_USERNAMES:
        raise ValueError("Username ini sudah dipesan sistem, pilih yang lain")
    return v


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        return normalize_username(v)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        # Disimpan huruf kecil semua biar "Budi@Mail.com" nggak bisa dipakai
        # daftar ulang setelah "budi@mail.com" terdaftar.
        return v.strip().lower()

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < PASSWORD_MIN_LENGTH:
            raise ValueError(f"Password minimal {PASSWORD_MIN_LENGTH} karakter")
        if len(v.encode("utf-8")) > PASSWORD_MAX_BYTES:
            raise ValueError(f"Password maksimal {PASSWORD_MAX_BYTES} karakter")
        return v


class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class DatasetOut(BaseModel):
    id: int
    filename: str
    status: str
    size_bytes: int | None
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InsightOut(BaseModel):
    id: int
    category: str
    text: str
    priority: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
