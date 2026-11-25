"""Adapter subprocess dengan batas waktu dan pencatatan terpusat."""

from dataclasses import dataclass
from pathlib import Path
import logging
import subprocess


@dataclass(frozen=True)
class HasilProses:
    perintah: tuple
    kode_keluar: int
    stdout: str
    stderr: str


class PelaksanaProses:
    def __init__(self, batas_waktu, log=None):
        self.batas_waktu = batas_waktu
        self.log = log or logging.getLogger("newmotion.proses")

    def jalankan(self, perintah, direktori_kerja, lingkungan=None):
        daftar = tuple(str(bagian) for bagian in perintah)
        self.log.info("Menjalankan proses: %s", " ".join(daftar))
        try:
            hasil = subprocess.run(daftar, cwd=Path(direktori_kerja), env=lingkungan,
                                   capture_output=True, text=True,
                                   timeout=self.batas_waktu, check=False)
        except subprocess.TimeoutExpired as galat:
            raise TimeoutError(f"Proses melewati batas waktu {self.batas_waktu} detik") from galat
        if hasil.returncode:
            self.log.error("Proses gagal (kode=%s): %s", hasil.returncode, hasil.stderr[-2000:])
        return HasilProses(daftar, hasil.returncode, hasil.stdout, hasil.stderr)
