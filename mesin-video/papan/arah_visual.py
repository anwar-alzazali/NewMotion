"""Kompatibilitas impor lama; implementasi visual berada di paket genre Kisah Islami."""

from pathlib import Path
import sys

AKAR_REPO = str(Path(__file__).resolve().parents[2])
if AKAR_REPO not in sys.path:
    sys.path.insert(0, AKAR_REPO)


from newmotion.paket_genre.kisah_islami import arah_visual as _mod

__all__ = [nama for nama in dir(_mod) if not nama.startswith("__")]


def __getattr__(nama):
    return getattr(_mod, nama)


def __dir__():
    return sorted(set(globals()) | set(dir(_mod)))
