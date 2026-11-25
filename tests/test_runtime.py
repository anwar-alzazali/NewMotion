from pathlib import Path
import sys

import pytest

from newmotion.runtime.konfigurasi import Konfigurasi
from newmotion.runtime.lingkungan import periksa_lingkungan
from newmotion.infrastructure.proses.subprocess import PelaksanaProses


def test_konfigurasi_profil_test(tmp_path):
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "test.toml").write_text(
        '[runtime]\ndirektori_hasil = "keluaran"\ntingkat_log = "WARNING"\nbatas_waktu_subproses = 30\n',
        encoding="utf-8",
    )
    konfigurasi = Konfigurasi.muat("test", tmp_path)
    assert konfigurasi.profil == "test"
    assert konfigurasi.direktori_hasil == (tmp_path / "keluaran").resolve()
    assert konfigurasi.batas_waktu_subproses == 30


def test_batas_waktu_tidak_valid(tmp_path, monkeypatch):
    monkeypatch.setenv("NEWMOTION_SUBPROCESS_TIMEOUT", "0")
    with pytest.raises(ValueError):
        Konfigurasi.muat("test", tmp_path)


def test_pemeriksaan_lingkungan_memuat_python():
    hasil = periksa_lingkungan()
    assert hasil[0].nama == "Python"
    assert hasil[0].tersedia is True


def test_pelaksana_proses_mengembalikan_kode_keluar(tmp_path):
    hasil = PelaksanaProses(10).jalankan(
        [sys.executable, "-c", "print('berhasil')"], tmp_path
    )
    assert hasil.kode_keluar == 0
    assert hasil.stdout.strip() == "berhasil"


def test_pelaksana_proses_menghormati_timeout(tmp_path):
    with pytest.raises(TimeoutError):
        PelaksanaProses(0.05).jalankan(
            [sys.executable, "-c", "import time; time.sleep(1)"], tmp_path
        )
