"""Validasi awal job tanpa menjalankan penjaga genre.

Penjaga tokoh dan dalil dijalankan satu kali oleh gerbang renderer
(mesin-video/papan_buat.py::jaga_spek), yang memiliki spesifikasi lengkap
sebelum aset disematkan. Menjalankannya di sini juga akan menggandakan
pemeriksaan saat job diteruskan ke renderer melalui subprocess.
"""

import json
from pathlib import Path

from newmotion.domain.genre import dari_rencana


class GalatValidasiJob(ValueError):
    """Masukan job tidak memenuhi kontrak minimum."""


def validasi_job(spesifikasi, keluaran):
    sumber = Path(spesifikasi).resolve()
    tujuan = Path(keluaran).resolve()
    if not sumber.is_file():
        raise GalatValidasiJob(f"Spesifikasi tidak ditemukan: {sumber}")
    if tujuan.suffix.lower() != ".mp4":
        raise GalatValidasiJob("Keluaran render harus menggunakan ekstensi .mp4")
    try:
        with sumber.open("r", encoding="utf-8") as berkas:
            data = json.load(berkas)
    except (OSError, UnicodeError, json.JSONDecodeError) as galat:
        raise GalatValidasiJob(f"Spesifikasi bukan JSON yang valid: {galat}") from galat
    if not isinstance(data, dict):
        raise GalatValidasiJob("Akar spesifikasi JSON harus berupa objek")
    try:
        dari_rencana(data)
    except (ValueError, TypeError, ImportError) as galat:
        raise GalatValidasiJob(f"Genre pada spesifikasi tidak valid: {galat}") from galat
    return sumber, tujuan
