"""Validasi masukan job sebelum proses render."""

import json
from pathlib import Path


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
    return sumber, tujuan
