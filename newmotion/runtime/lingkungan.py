"""Pemeriksaan prasyarat runtime dan alat eksternal."""

from dataclasses import dataclass
from importlib.util import find_spec
import shutil


@dataclass(frozen=True)
class Pemeriksaan:
    nama: str
    tersedia: bool
    keterangan: str


def periksa_lingkungan(periksa_render=False):
    hasil = [
        Pemeriksaan("Python", True, "Interpreter Python aktif"),
        Pemeriksaan("FFmpeg", shutil.which("ffmpeg") is not None, "Diperlukan untuk keluaran video"),
        Pemeriksaan("FFprobe", shutil.which("ffprobe") is not None, "Diperlukan untuk pemeriksaan media"),
    ]
    if periksa_render:
        for modul in ("PIL", "numpy", "playwright"):
            hasil.append(Pemeriksaan(modul, find_spec(modul) is not None, "Modul Python"))
    return hasil
