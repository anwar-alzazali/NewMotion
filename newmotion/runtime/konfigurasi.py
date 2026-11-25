"""Pemuatan konfigurasi runtime berbasis TOML."""

from dataclasses import dataclass
from pathlib import Path
import os
import tomllib


@dataclass(frozen=True)
class Konfigurasi:
    profil: str
    akar_proyek: Path
    direktori_hasil: Path
    tingkat_log: str
    batas_waktu_subproses: int

    @classmethod
    def muat(cls, profil=None, akar_proyek=None):
        akar = Path(akar_proyek or os.environ.get("NEWMOTION_ROOT", Path.cwd())).resolve()
        nama_profil = profil or os.environ.get("NEWMOTION_PROFILE", "development")
        jalur = akar / "config" / f"{nama_profil}.toml"
        data = {}
        if jalur.is_file():
            with jalur.open("rb") as berkas:
                data = tomllib.load(berkas)
        runtime = data.get("runtime", {})
        hasil = Path(os.environ.get("NEWMOTION_OUTPUT_DIR", runtime.get("direktori_hasil", "hasil")))
        if not hasil.is_absolute():
            hasil = akar / hasil
        batas = int(os.environ.get("NEWMOTION_SUBPROCESS_TIMEOUT", runtime.get("batas_waktu_subproses", 3600)))
        if batas <= 0:
            raise ValueError("batas_waktu_subproses harus lebih besar dari nol")
        tingkat = os.environ.get("NEWMOTION_LOG_LEVEL", runtime.get("tingkat_log", "INFO")).upper()
        if tingkat not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise ValueError(f"tingkat log tidak dikenal: {tingkat}")
        return cls(nama_profil, akar, hasil.resolve(), tingkat, batas)
