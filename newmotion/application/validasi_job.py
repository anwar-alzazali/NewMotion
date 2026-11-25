"""Validasi awal job tanpa menjalankan penjaga genre.

Penjaga tokoh dan dalil dijalankan satu kali oleh gerbang renderer
(mesin-video/papan_buat.py::jaga_spek), yang memiliki spesifikasi lengkap
sebelum aset disematkan. Menjalankannya di sini juga akan menggandakan
pemeriksaan saat job diteruskan ke renderer melalui subprocess.
"""

import json
from pathlib import Path

from newmotion.domain.genre import (
    ambil,
    dari_rencana,
    konteks_konten_untuk_naskah,
    nama_genre_untuk_naskah,
)


class GalatValidasiJob(ValueError):
    """Masukan job tidak memenuhi kontrak minimum."""


def validasi_job(spesifikasi, keluaran, *, wajib_genre=False, genre_pilihan=None):
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
        if wajib_genre:
            nama_genre = nama_genre_untuk_naskah(data, pilihan=genre_pilihan)
            ambil(nama_genre)
        else:
            nama_genre = dari_rencana(data).nama
        konteks_konten_untuk_naskah(
            data, genre=nama_genre, wajib_eksplisit=wajib_genre
        )
    except (ValueError, TypeError, ImportError) as galat:
        raise GalatValidasiJob(f"Genre pada spesifikasi tidak valid: {galat}") from galat
    return sumber, tujuan
