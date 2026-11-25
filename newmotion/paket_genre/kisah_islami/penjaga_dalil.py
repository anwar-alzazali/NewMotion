"""Adapter penjaga dalil format papan lama milik paket genre Kisah Islami.

Implementasi pemeriksaan kartu dalil masih berada di mesin-video selama migrasi.
Inti renderer hanya mengenal kait penjaga_dalil pada kontrak PaketGenre.
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Any


def periksa_dalil_legacy(spek: Any):
    """Jalankan penjaga kartu dalil lama melalui adapter kompatibilitas paket."""
    akar = Path(__file__).resolve().parents[3]
    jalur_mesin_video = str(akar / "mesin-video")
    if jalur_mesin_video not in sys.path:
        sys.path.insert(0, jalur_mesin_video)
    modul = importlib.import_module("papan.penjaga_dalil")
    return modul.periksa_dalil(spek)


__all__ = ["periksa_dalil_legacy"]
