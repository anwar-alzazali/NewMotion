"""Uji logika lembar katalog renderer tanpa membuka browser."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from newmotion.application.katalog_renderer import katalog


AKAR = Path(__file__).resolve().parents[1]
JALUR = AKAR / "mesin-video" / "papan" / "lembar_semua_benda.py"
SPESIFIKASI = importlib.util.spec_from_file_location("lembar_semua_benda", JALUR)
assert SPESIFIKASI and SPESIFIKASI.loader
LEMBAR = importlib.util.module_from_spec(SPESIFIKASI)
SPESIFIKASI.loader.exec_module(LEMBAR)


def test_semua_jenis_katalog_mendapat_dua_keadaan_yang_berbeda_jika_animasi():
    for nama, info in katalog().items():
        properti, parameter, nilai = LEMBAR.keadaan(nama, info)
        if info["animasi"]:
            assert parameter in info["animasi"]
            assert properti[parameter] == nilai
            assert nilai[0] != nilai[1]
        else:
            assert properti == {}
            assert parameter is None
            assert nilai is None


def test_rentang_konsep_abstrak_mewakili_keadaan_awal_dan_akhir():
    assert LEMBAR.keadaan("genangan_tubuh", katalog()["genangan_tubuh"])[2] == [35, 440]
    assert LEMBAR.keadaan("resapan_tanah", katalog()["resapan_tanah"])[2] == [0.15, 1.0]
    assert LEMBAR.keadaan("naungan_kelompok", katalog()["naungan_kelompok"])[2] == [0.2, 1.0]
    assert LEMBAR.keadaan("timbangan", katalog()["timbangan"])[2] == [-18, 18]


def test_penempatan_menggunakan_bbox_agar_benda_muat_di_panel():
    ukuran = json.loads((AKAR / "newmotion" / "application" / "data" / "ukuran_benda.json").read_text(encoding="utf-8"))
    for nama, kotak in ukuran.items():
        x, y, skala = LEMBAR.penempatan(kotak)
        assert skala > 0, nama
        assert max(kotak[2] - kotak[0], kotak[3] - kotak[1]) * skala <= 620.01, nama
        assert isinstance(x, float) and isinstance(y, float)
