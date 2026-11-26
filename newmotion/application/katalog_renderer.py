"""Katalog benda renderer, dibaca langsung dari mesin-video/papan/cerita.js.

Setiap cabang `j === "nama"` di fungsi benda() menjadi satu entri: nama jenis, komentar
penjelasnya (bila ada), dan parameter `o.<kunci>` yang dibaca cabang itu. Katalog ini
dipakai skill sutradara (LLM hanya boleh memilih jenis yang ada) dan validator rencana
(parameter keadaan yang diminta harus benar-benar dibaca renderer).
"""
from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

AKAR = Path(__file__).resolve().parents[2]
CERITA_JS = AKAR / "mesin-video" / "papan" / "cerita.js"

# Parameter umum yang dipakai renderer untuk semua jenis (posisi/tampilan), bukan keadaan cerita.
UMUM = frozenset({"x", "y", "s", "op", "at", "jenis", "kabur", "depan", "belakang", "hias", "seed", "warna"})

# Jenis yang bukan objek cerita (dikendalikan mesin, bukan dipilih sutradara).
BUKAN_SUBJEK = frozenset({"kartu_dalil", "stempel", "logo_app", "bingkai", "tanda", "rincian", "chat",
                          "kalender", "studio", "gelap", "cahaya"})


@lru_cache(maxsize=4)
def _baca(jalur: str) -> dict[str, dict]:
    teks = Path(jalur).read_text(encoding="utf-8")
    pola = re.compile(r'(?:if|else if) \((j === "[a-z_0-9]+"(?: \|\| j === "[a-z_0-9]+")*)\) \{(?: *//([^\n]*))?')
    cocok = list(pola.finditer(teks))
    katalog: dict[str, dict] = {}
    for i, m in enumerate(cocok):
        akhir = cocok[i + 1].start() if i + 1 < len(cocok) else min(len(teks), m.end() + 4000)
        badan = teks[m.end():akhir]
        param = sorted(set(re.findall(r"\bo\.([a-z_][a-z_0-9]*)", badan)) - UMUM)
        ket = (m.group(2) or "").strip()
        for nama in re.findall(r'"([a-z_0-9]+)"', m.group(1)):
            if nama not in katalog:
                katalog[nama] = {"keterangan": ket[:220], "parameter": param}
    return katalog


def katalog(jalur: Path = CERITA_JS) -> dict[str, dict]:
    """Semua jenis benda yang dikenali renderer."""
    return _baca(str(jalur))


def katalog_subjek(jalur: Path = CERITA_JS) -> dict[str, dict]:
    """Jenis yang boleh dipilih sutradara sebagai subjek/latar cerita."""
    return {k: v for k, v in katalog(jalur).items() if k not in BUKAN_SUBJEK}


def teks_katalog(jalur: Path = CERITA_JS) -> str:
    """Katalog ringkas untuk dimasukkan ke skill (satu baris per jenis)."""
    baris = []
    for nama, d in sorted(katalog_subjek(jalur).items()):
        param = f" [keadaan: {', '.join(d['parameter'][:8])}]" if d["parameter"] else ""
        baris.append(f"- {nama}: {d['keterangan'] or '-'}{param}")
    return "\n".join(baris)
