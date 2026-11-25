"""Adapter sumber resmi/lokal yang dipakai penjaga dalil NewMotion."""
from __future__ import annotations

import os

from . import hadis
from .quran import QuranBertingkat

_KLIEN_QURAN = None


def _quran():
    global _KLIEN_QURAN
    if _KLIEN_QURAN is None:
        # Secret dipakai bila tersedia; tanpa secret, gunakan endpoint publik Quran.com
        # milik ekosistem Quran Foundation. Tidak pernah mencetak kredensial.
        if os.environ.get("QURAN_FOUNDATION_CLIENT_ID") and os.environ.get("QURAN_FOUNDATION_CLIENT_SECRET"):
            _KLIEN_QURAN = QuranBertingkat()
        else:
            _KLIEN_QURAN = QuranBertingkat(utama=None)
    return _KLIEN_QURAN


def ambil_ayat(surah: int, ayat: int) -> dict:
    hasil = _quran().ayat(surah, ayat)
    if hasil is None or not hasil.ar:
        raise RuntimeError(f"ayat {surah}:{ayat} tidak ditemukan pada sumber Quran")
    return {
        "teks_arab": hasil.ar,
        "terjemah": hasil.terjemah,
        "nama_surah": hasil.nama_surah,
        "sumber": hasil.sumber_terjemah,
        "rujukan": hasil.tautan,
    }


def ambil_hadis(kitab: str, nomor: int | str) -> dict:
    riwayat = hadis.cari(kitab, nomor)
    if not riwayat:
        raise RuntimeError(f"hadis {kitab}:{nomor} tidak ditemukan pada dataset")
    entri = riwayat[0]
    derajat, berbeda = hadis.derajat(kitab, entri.penilaian)
    if derajat not in ("sahih", "hasan"):
        raise RuntimeError(f"hadis {kitab}:{nomor} tidak lolos: derajat {derajat}")
    return {
        "teks_arab": entri.ar,
        "terjemah": entri.id or entri.en,
        "kitab": hadis.KITAB[entri.kitab],
        "nomor": entri.nomor + entri.sub,
        "derajat": derajat,
        "penilaian_berbeda": berbeda,
        "rujukan": entri.tautan,
    }


class SumberDalilResmi:
    """Antarmuka kompatibel untuk penjaga kartu dalil mesin-video."""

    def teks_ayat(self, surah: int, ayat: int) -> str:
        return ambil_ayat(surah, ayat)["teks_arab"]

    def teks_hadis(self, kitab: str, nomor: int) -> str:
        return ambil_hadis(kitab, nomor)["teks_arab"]
