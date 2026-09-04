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


def _cek_email_kembar(conn) -> None:
    """Batalin migrasi kalau ada email yang bentrok setelah di-lowercase.

    Dicek SEBELUM apa pun diubah. Kalau dibiarin, UPDATE ... LOWER(email)
    bakal nabrak UNIQUE index email dan yang muncul cuma error constraint
    mentah -- di container itu artinya crash loop tanpa petunjuk.
    """
    kembar = conn.execute(
        text(
            "SELECT LOWER(email) AS e, COUNT(*) AS n FROM users "
            "GROUP BY LOWER(email) HAVING COUNT(*) > 1"
        )
    ).fetchall()
    if kembar:
        daftar = ", ".join(f"{e} ({n} akun)" for e, n in kembar)
        raise RuntimeError(
            "Migrasi dibatalkan: ada email yang kembar kalau disamain jadi "
            f"huruf kecil -- {daftar}. Gabungin atau hapus salah satu akun "
            "dulu, baru jalanin migrasi ini lagi. Nggak ada data yang diubah."
        )


def migrate() -> None:
    """Idempotent & bisa dilanjutin kalau percobaan sebelumnya gagal di tengah.

    Sengaja NGGAK cuma ngecek "kolom username udah ada?" buat mutusin selesai
    atau belum. Alasannya: di SQLite, ALTER TABLE langsung ke-commit walau
    transaksinya dibatalkan -- jadi migrasi yang gagal di tengah bisa ninggalin
    kolom kosong tanpa isi dan tanpa index. Kalau patokannya cuma keberadaan
    kolom, percobaan kedua bakal salah nyimpulin "udah beres" dan ninggalin
    database setengah jadi. Makanya tiap langkah dicek sendiri-sendiri.
    """
    inspector = inspect(engine)
    if "users" not in inspector.get_table_names():
        print("Tabel users belum ada -- nggak ada yang perlu dimigrasi.")
        print("Jalanin `python -m app.init_db` buat bikin tabelnya dari awal.")
        return

    punya_kolom = "username" in {c["name"] for c in inspector.get_columns("users")}
    punya_index = any(
        i["name"] == "ix_users_username" for i in inspector.get_indexes("users")
    )
    is_sqlite = engine.dialect.name == "sqlite"

    with engine.begin() as conn:
        belum_terisi = (
            conn.execute(
                text("SELECT COUNT(*) FROM users WHERE username IS NULL OR username = ''")
            ).scalar()
            if punya_kolom
            else conn.execute(text("SELECT COUNT(*) FROM users")).scalar()
        )

        if punya_kolom and punya_index and not belum_terisi:
            print("Database udah termigrasi -- nggak ada yang diubah.")
            return

        # Semua pengecekan yang bisa bikin gagal ditaruh paling depan, sebelum
        # ada satu pun perubahan.
        _cek_email_kembar(conn)

        if not punya_kolom:
            print("Nambahin kolom username...")
            conn.execute(text("ALTER TABLE users ADD COLUMN username VARCHAR(20)"))
        else:
            print("Kolom username udah ada -- lanjut ngecek isinya.")

        # Login sekarang nyocokin email dalam huruf kecil semua, jadi email
        # lama yang masih campur kapital disamain.
        conn.execute(text("UPDATE users SET email = LOWER(email)"))

        # Cuma isi yang masih kosong; user yang udah punya username nggak
        # ditimpa. Yang udah kepakai dikumpulin dulu biar nggak bentrok.
        terpakai = {
            u
            for (u,) in conn.execute(
                text("SELECT username FROM users WHERE username IS NOT NULL AND username != ''")
            )
        }
        kosong = conn.execute(
            text(
                "SELECT id, email FROM users "
                "WHERE username IS NULL OR username = '' ORDER BY id"
            )
        ).fetchall()

        for user_id, email in kosong:
            username = _make_unique(_username_from_email(email or "", user_id), terpakai)
            terpakai.add(username)
            conn.execute(
                text("UPDATE users SET username = :u WHERE id = :i"),
                {"u": username, "i": user_id},
            )
            print(f"  user #{user_id} ({email}) -> username '{username}'")

        if not punya_index:
            conn.execute(
                text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_username ON users (username)")
            )

        if not is_sqlite:
            # SQLite nggak bisa nambahin NOT NULL ke kolom yang udah ada tanpa
            # bikin ulang tabelnya; database lain bisa langsung.
            conn.execute(text("ALTER TABLE users ALTER COLUMN username SET NOT NULL"))

    print(f"Selesai. {len(kosong)} user dikasih username.")
    if is_sqlite:
        print(
            "Catatan: di SQLite kolom username belum NOT NULL di level database, "
            "tapi aplikasi selalu ngisinya (nullable=False di models.py)."
        )


if __name__ == "__main__":
    migrate()
