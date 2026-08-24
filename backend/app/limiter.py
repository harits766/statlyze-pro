"""Rate limiter terpusat.

Dipisah ke file sendiri (bukan langsung di main.py) karena main.py dan
datasets.py sama-sama butuh instance limiter yang sama -- kalau
didefinisiin di main.py, bakal circular import pas datasets.py coba
import balik dari main.py.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
