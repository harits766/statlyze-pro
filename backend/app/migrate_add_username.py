"""Migrasi: tambahin kolom `username` ke tabel users yang udah terlanjur jalan.

Kenapa perlu: Base.metadata.create_all() cuma bikin tabel yang BELUM ada --
dia nggak nambahin kolom baru ke tabel yang udah ada. Jadi database lama
(statlyze.db yang udah dipakai) harus di-update manual lewat file ini.

Cara pakai (dari folder backend/):
    python -m app.migrate_add_username

Aman dijalanin berkali-kali: kalau kolomnya udah ada, dia langsung berhenti
tanpa ngubah apa-apa.

User lama yang belum punya username dikasih username otomatis dari bagian
depan email-nya (budi@mail.com -> budi). Kalau bentrok, dikasih angka di
belakang (budi2, budi3, ...). User bebas ganti sendiri nanti.
"""
from __future__ import annotations

import re

from sqlalchemy import inspect, text

from .database import engine
from .schemas import USERNAME_MAX_LENGTH, USERNAME_MIN_LENGTH, RESERVED_USERNAMES

_INVALID_CHARS = re.compile(r"[^a-z0-9_]")


def _username_from_email(email: str, user_id: int) -> str:
    """Bikin kandidat username dari email, ngikutin aturan di schemas.py."""
    base = _INVALID_CHARS.sub("", email.split("@")[0].lower())
    # Aturannya harus diawali huruf; kalau sisa karakternya nggak memenuhi,
    # jatuh ke pola aman "user<id>" yang pasti valid.
    base = base.lstrip("0123456789_")
    if len(base) < USERNAME_MIN_LENGTH or base in RESERVED_USERNAMES:
        base = f"user{user_id}"
    return base[:USERNAME_MAX_LENGTH]


def _make_unique(base: str, taken: set[str]) -> str:
    if base not in taken:
        return base
    n = 2
    while True:
        suffix = str(n)
        candidate = base[: USERNAME_MAX_LENGTH - len(suffix)] + suffix
        if candidate not in taken:
            return candidate
        n += 1


def migrate() -> None:
    inspector = inspect(engine)
    if "users" not in inspector.get_table_names():
        print("Tabel users belum ada -- nggak ada yang perlu dimigrasi.")
        print("Jalanin `python -m app.init_db` buat bikin tabelnya dari awal.")
        return

    columns = {c["name"] for c in inspector.get_columns("users")}
    if "username" in columns:
        print("Kolom username udah ada -- nggak ada yang diubah.")
        return

    is_sqlite = engine.dialect.name == "sqlite"

    with engine.begin() as conn:
        print("Nambahin kolom username...")
        conn.execute(text("ALTER TABLE users ADD COLUMN username VARCHAR(20)"))

        # Email lama mungkin masih campur huruf besar-kecil. Sekarang login
        # nyocokin email dalam huruf kecil semua, jadi yang lama disamain.
        conn.execute(text("UPDATE users SET email = LOWER(email)"))

        rows = conn.execute(text("SELECT id, email FROM users ORDER BY id")).fetchall()
        taken: set[str] = set()
        for user_id, email in rows:
            username = _make_unique(_username_from_email(email or "", user_id), taken)
            taken.add(username)
            conn.execute(
                text("UPDATE users SET username = :u WHERE id = :i"),
                {"u": username, "i": user_id},
            )
            print(f"  user #{user_id} ({email}) -> username '{username}'")

        conn.execute(
            text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_username ON users (username)")
        )

        if not is_sqlite:
            # SQLite nggak bisa nambahin NOT NULL ke kolom yang udah ada tanpa
            # bikin ulang tabelnya; database lain bisa langsung.
            conn.execute(text("ALTER TABLE users ALTER COLUMN username SET NOT NULL"))

    print(f"Selesai. {len(rows)} user dimigrasi.")
    if is_sqlite:
        print(
            "Catatan: di SQLite kolom username belum NOT NULL di level database, "
            "tapi aplikasi selalu ngisinya (nullable=False di models.py)."
        )


if __name__ == "__main__":
    migrate()
