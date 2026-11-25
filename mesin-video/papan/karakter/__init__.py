"""Kontrak karakter NewMotion.

Python menyediakan nama aksi dan validasi data. cerita.js memiliki satu-satunya
implementasi rangka, pose, interpolasi, dan penggambaran karakter.
"""
from .gerak import GERAK_BERULANG, GERAK_STATIS, SEMUA, jadwal_gerak

__all__ = ["GERAK_BERULANG", "GERAK_STATIS", "SEMUA", "jadwal_gerak"]
