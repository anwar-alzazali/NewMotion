"""Adapter kompatibilitas ke mesin-video/papan_buat.py."""

from pathlib import Path
import sys

from newmotion.infrastructure.proses.subprocess import PelaksanaProses


class AdapterPapanLama:
    def __init__(self, akar_proyek, batas_waktu, log=None):
        self.akar = Path(akar_proyek).resolve()
        self.skrip = self.akar / "mesin-video" / "papan_buat.py"
        self.pelaksana = PelaksanaProses(batas_waktu, log)

    def render(self, spesifikasi, keluaran, argumen_tambahan=()):
        if not self.skrip.is_file():
            raise FileNotFoundError(f"Entry point renderer lama tidak ditemukan: {self.skrip}")
        berkas_spec = Path(spesifikasi)
        if not berkas_spec.is_absolute():
            berkas_spec = (Path.cwd() / berkas_spec).resolve()
        if not berkas_spec.is_file():
            raise FileNotFoundError(f"Spesifikasi tidak ditemukan: {berkas_spec}")
        berkas_hasil = Path(keluaran).resolve()
        berkas_hasil.parent.mkdir(parents=True, exist_ok=True)
        perintah = [sys.executable, str(self.skrip), str(berkas_spec), "-o", str(berkas_hasil)]
        perintah.extend(str(arg) for arg in argumen_tambahan)
        return self.pelaksana.jalankan(perintah, self.akar)
