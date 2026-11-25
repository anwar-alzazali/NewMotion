"""Klasifikasi sinyal isi dan kebutuhan kebijakan tanpa mengubah genre pilihan.

Modul ini tidak menebak genre produksi dan tidak menetapkan konteks sensitif
secara diam-diam. Hasilnya berupa sinyal terstruktur untuk gerbang kebijakan
atau permintaan klarifikasi kepada pemilik.
"""
from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from newmotion.domain.genre import (
    KONTEKS_KONTEN_ISLAMI,
    KONTEKS_KONTEN_DIKENAL,
    nama_genre_untuk_naskah,
)

# Istilah dipakai sebagai sinyal awal, bukan bukti final tentang isi cerita.
_ENTITAS = {
    "nabi_rasul": (
        r"\bnabi\s+[\w'-]+", r"\brasulullah\b", r"\brasul\b",
    ),
    "sahabat": (
        r"\bsahabat\s+[\w'-]+", r"\bkhulafaur\s+rasyidin\b",
        r"\babu\s+bakar\b", r"\bumar\s+bin\s+khattab\b",
        r"\butsman\s+bin\s+affan\b", r"\bali\s+bin\s+abi\s+thalib\b",
    ),
    "malaikat": (r"\bmalaikat\b", r"\bjibril\b", r"\bmikail\b", r"\bisrafil\b"),
    "tokoh_gaib_islami": (r"\biblis\b", r"\bsyaitan\b", r"\bsetan\b", r"\bdajjal\b"),
}
_KLAIM = (
    r"\ballah\b", r"\bfirman\b", r"\bwahyu\b", r"\bal[- ]qur'?an\b",
    r"\bhadis\b", r"\bhadits\b", r"\bsunnah\b", r"\bakhirat\b",
    r"\bsurga\b", r"\bneraka\b", r"\bkiamat\b", r"\bsyariat\b",
)
_POLA = {k: tuple(re.compile(p, re.I) for p in v) for k, v in _ENTITAS.items()}
_POLA_KLAIM = tuple(re.compile(p, re.I) for p in _KLAIM)


def _teks_naskah(naskah: Mapping[str, Any]) -> str:
    """Ambil teks dari bidang narasi dan metadata cerita yang dikenal."""
    bagian: list[str] = []
    for k in ("judul", "inti", "sinopsis", "tema", "deskripsi"):
        v = naskah.get(k)
        if isinstance(v, str):
            bagian.append(v)
    for k in ("beat", "adegan"):
        daftar = naskah.get(k)
        if not isinstance(daftar, list):
            continue
        for item in daftar:
            if isinstance(item, str):
                bagian.append(item)
            elif isinstance(item, Mapping):
                for kolom in ("narasi", "teks", "dialog", "deskripsi", "nama"):
                    v = item.get(kolom)
                    if isinstance(v, str):
                        bagian.append(v)
                for kolom in ("peran", "tokoh", "entitas"):
                    v = item.get(kolom)
                    if isinstance(v, str):
                        bagian.append(v)
                    elif isinstance(v, list):
                        bagian.extend(x for x in v if isinstance(x, str))
    return "\n".join(bagian)


def klasifikasikan_konten(
    naskah: Mapping[str, Any], *, genre_pilihan: str | None = None
) -> dict[str, Any]:
    """Kembalikan genre tetap, sinyal isi, dan keputusan konteks yang aman.

    Konteks tidak pernah dinaikkan otomatis dari 'umum' menjadi 'islami'.
    Sinyal kuat yang bertentangan dengan konteks eksplisit meminta tinjauan.
    """
    if not isinstance(naskah, Mapping):
        raise ValueError("naskah harus berupa objek")

    genre = nama_genre_untuk_naskah(naskah, pilihan=genre_pilihan)
    teks = _teks_naskah(naskah)
    entitas = sorted(
        nama for nama, pola in _POLA.items()
        if any(rx.search(teks) for rx in pola)
    )
    klaim = any(rx.search(teks) for rx in _POLA_KLAIM)
    ada_sinyal_islami = bool(entitas or klaim)

    konteks_input = naskah.get("konteks_konten")
    if konteks_input is not None and konteks_input not in KONTEKS_KONTEN_DIKENAL:
        raise ValueError("konteks_konten tidak dikenal")

    if genre == "kisah_islami":
        konteks = "islami" if konteks_input is None else konteks_input
        if konteks not in KONTEKS_KONTEN_ISLAMI:
            raise ValueError("genre kisah_islami wajib memakai konteks konten Islami")
        keputusan = "ditetapkan"
        perlu_klarifikasi = False
    elif konteks_input is None:
        konteks = None
        keputusan = "perlu_klarifikasi" if ada_sinyal_islami else "konteks_belum_dipilih"
        perlu_klarifikasi = True
    elif konteks_input == "umum" and ada_sinyal_islami:
        konteks = "umum"
        keputusan = "konflik_perlu_tinjauan"
        perlu_klarifikasi = True
    else:
        konteks = konteks_input
        keputusan = "ditetapkan"
        perlu_klarifikasi = False

    return {
        "genre": genre,
        "konteks_konten": konteks,
        "sinyal_islami": {
            "terdeteksi": ada_sinyal_islami,
            "entitas_dilindungi": entitas,
            "indikasi_klaim_keagamaan": klaim,
        },
        "kebijakan": {
            "kandidat_islami": ada_sinyal_islami,
            "aktifkan_kebijakan_islami": konteks in KONTEKS_KONTEN_ISLAMI,
        },
        "keputusan": keputusan,
        "perlu_klarifikasi": perlu_klarifikasi,
    }
