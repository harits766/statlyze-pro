"""Rate limiter terpusat.

Dipisah ke file sendiri (bukan langsung di main.py) karena main.py dan
datasets.py sama-sama butuh instance limiter yang sama -- kalau
didefinisiin di main.py, bakal circular import pas datasets.py coba
import balik dari main.py.
"""
import os

from slowapi import Limiter
from slowapi.util import get_remote_address

# Set RATE_LIMIT_ENABLED=0 buat matiin rate limit -- berguna pas lagi
# ngetes flow register/login berkali-kali di lokal, biar nggak kekunci
# sendiri setelah 5 percobaan. JANGAN dimatiin di production.
_enabled = os.getenv("RATE_LIMIT_ENABLED", "1").strip().lower() not in {"0", "false", "no"}

limiter = Limiter(key_func=get_remote_address, enabled=_enabled)
