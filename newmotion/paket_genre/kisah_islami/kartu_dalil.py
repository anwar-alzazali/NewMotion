"""Kartu dalil yang pas di layar (diadopsi dari motion-studio-ai `cardfit.py` + `translate_cerita._card`, 15 Nov 2026).

Aturan yang dibawa:
- Kartu hanya untuk ayat/hadis yang TERBACA di HP: Arab muat 1 baris (>= 42 px) atau 2 baris seimbang
  (>= 34 px), terjemahan <= KARTU_MAKS_HURUF. Dalil yang lebih panjang tampil sebagai label sumber (`sub`)
  di teks layar, bukan kartu yang menutupi adegan.
- Ukuran kartu dihitung (tiruan tata letak `kartu_dalil` di cerita.js), lalu diskalakan agar muat di zona aman
  y 170..1300; Arab langsung tampil (kartu tidak pernah kosong), terjemahan menyusul.
- Lebar huruf Arab dikalibrasi untuk font Amiri Quran yang ditanam di papan_buat.py.
"""
from __future__ import annotations

import re
import unicodedata

ARAB_MIN_1, ARAB_MIN_2, ARAB_MAKS = 42.0, 34.0, 56.0
KARTU_MAKS_HURUF = 200
LATAR_KARTU = 0.4  # latar kartu tembus pandang (27 Nov, permintaan pemilik): adegan tetap terlihat di belakang
ZONA_ATAS, ZONA_TINGGI = 170, 1130


def lebar_arab(teks: str) -> float:
    """Lebar (em) teks Arab dalam Amiri Quran: harakat tidak menambah lebar."""
    dasar = sum(1 for c in teks if not unicodedata.combining(c) and not c.isspace() and unicodedata.category(c) != "Cf")
    arab = sum(1 for c in teks if "؀" <= c <= "ۿ")
    per = 0.44 if arab * 2 >= len(teks.replace(" ", "")) else 0.64
    return per * dasar + 0.27 * teks.count(" ")


def tata_arab(teks: str) -> tuple[float, list[str]] | None:
    """(ukuran px, baris) agar Arab muat 1 baris >= 42 px atau 2 baris seimbang >= 34 px; None = terlalu panjang."""
    kata = (teks or "").split()
    if not kata:
        return None
    satu = min(ARAB_MAKS, 640 / max(1.0, lebar_arab(teks)))
    if satu >= ARAB_MIN_1:
        return round(satu, 1), [" ".join(kata)]
    terbaik = None
    for k in range(1, len(kata)):
        a, b = " ".join(kata[:k]), " ".join(kata[k:])
        w = max(lebar_arab(a), lebar_arab(b))
        if terbaik is None or w < terbaik[0]:
            terbaik = (w, [a, b])
    if terbaik is None:
        return None
    uk = min(ARAB_MAKS, 640 / max(1.0, terbaik[0]))
    return (round(uk, 1), terbaik[1]) if uk >= ARAB_MIN_2 else None


def tata_kartu(teks: str, ada_arab: bool, tambah_arab: float = 0.0) -> tuple[int, float]:
    """Tiruan hitungan kartu_dalil di cerita.js -> (ukuran huruf terjemahan, tinggi kartu px)."""
    kata = re.sub(r"\s+", " ", teks or "").strip().split(" ")
    uk, baris = 30, 1
    for uk in range(54, 28, -2):
        mk, lh, baris, cur = int(690 / (uk * 0.6)), uk * 1.3, 0, ""
        for w in kata:
            if cur and len(cur + " " + w) > mk:
                baris += 1
                cur = w
            else:
                cur = (cur + " " + w) if cur else w
        if cur:
            baris += 1
        if baris * lh <= (380 - tambah_arab if ada_arab else 520):
            break
    return uk, 330 + (200 + tambah_arab if ada_arab else 0) + baris * uk * 1.3 + 80


def alasan_tidak_layak(teks: str | None, arab: str | None) -> str | None:
    """None = layak jadi kartu; selain itu alasan (dalil tetap tampil sebagai label sumber)."""
    if not teks:
        return "tanpa terjemahan resmi"
    if len(teks) > KARTU_MAKS_HURUF:
        return f"terjemahan {len(teks)} huruf (maks {KARTU_MAKS_HURUF})"
    if not arab:
        return "tanpa teks Arab"
    if tata_arab(arab) is None:
        return "Arab terlalu panjang untuk terbaca (maks 2 baris)"
    return None


def buat_kartu(dalil: dict, *, at: float = 0.0) -> dict:
    """Benda kartu_dalil yang muat di zona aman. `dalil` = {kitab, teks, arab, label} (sudah terverifikasi)."""
    teks, arab = dalil.get("teks") or "", dalil.get("arab")
    ta = tata_arab(arab) if arab else None
    uk, tinggi = tata_kartu(teks, bool(ta), (len(ta[1]) - 1) * ta[0] * 1.5 if ta else 0)
    s = min(1.2, ZONA_TINGGI / tinggi)
    y = ZONA_ATAS + (ZONA_TINGGI - tinggi * s) / 2 + tinggi * s / 2
    kartu = {"jenis": "kartu_dalil", "x": 540, "y": round(y, 1), "s": round(s, 3), "at": round(at, 2),
             "kitab": dalil.get("kitab", ""), "label": dalil.get("label") or "DALIL", "teks": teks,
             "ukuran": uk, "tulis_at": 0.4, "latar": LATAR_KARTU}
    if dalil.get("no"):
        kartu["no"] = str(dalil["no"])  # nomor hadis (penjaga dalil mewajibkannya)
    if ta:
        kartu.update(arab=arab, arab_ukuran=ta[0], arab_baris=ta[1], arab_at=0.15)
    return kartu
