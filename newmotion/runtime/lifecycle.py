"""Pengelolaan siklus hidup runtime."""

from contextlib import AbstractContextManager
from newmotion.runtime.logging import siapkan_logging


class Runtime(AbstractContextManager):
    def __init__(self, konfigurasi):
        self.konfigurasi = konfigurasi
        self.log = None

    def __enter__(self):
        self.log = siapkan_logging(self.konfigurasi.tingkat_log)
        self.log.info("Runtime NewMotion dimulai (profil=%s)", self.konfigurasi.profil)
        return self

    def __exit__(self, jenis, nilai, jejak):
        if self.log:
            if nilai is None:
                self.log.info("Runtime NewMotion dihentikan")
            else:
                self.log.error("Runtime berakhir karena galat: %s", nilai)
        return False
