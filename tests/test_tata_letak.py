"""Lapisan tata letak: subjek utuh, tidak tertutup, figuran tidak berdempetan."""
from itertools import pairwise

from newmotion.application.katalog_renderer import katalog_subjek
from newmotion.application.tata_letak import (
    _irisan,
    _luas,
    bidang,
    kotak_benda,
    kotak_boneka,
    tata_shot,
    ukuran,
)

KAMERA = {"z": 1.0, "x": 540, "y": 960}


def test_ukuran_mencakup_hampir_semua_jenis_subjek():
    hilang = set(katalog_subjek()) - set(ukuran())
    assert len(hilang) <= 3, f"jalankan mesin-video/papan/ukur_benda.py; belum terukur: {sorted(hilang)}"


def test_subjek_terpotong_tepi_digeser_ke_dalam():
    kursi = {"jenis": "kursi", "x": 1040, "y": 1700, "s": 1.2}
    shot = {"kamera": KAMERA, "benda": [kursi], "boneka": []}
    tata_shot(shot, [kursi])
    kt, bd = kotak_benda(kursi), bidang(shot)
    assert bd[0] <= kt[0] and kt[2] <= bd[2]


def test_dua_subjek_tidak_saling_menutupi():
    rumah = {"jenis": "rumah_kampung", "x": 400, "y": 1320, "s": 0.82}
    bayang = {"jenis": "bayang_misteri", "x": 520, "y": 1320, "s": 0.82, "besar": 1.4}
    shot = {"kamera": {"z": 1.25, "x": 540, "y": 1120}, "benda": [rumah, bayang], "boneka": []}
    tata_shot(shot, [rumah, bayang])
    a, b = kotak_benda(rumah), kotak_benda(bayang)
    assert _irisan(a, b) / min(_luas(a), _luas(b)) <= 0.25


def test_kamu_tidak_menutupi_subjek_dan_figuran_tidak_berdempetan():
    gedung = {"jenis": "rumah", "x": 540, "y": 1500, "s": 1}
    kamu = {"x": 540, "y": 1700, "s": 0.9}
    fig = [{"npc": i, "x": 300 + i * 20, "y": 1720, "s": 0.78} for i in range(3)]
    shot = {"kamera": KAMERA, "benda": [gedung], "boneka": [kamu, *fig]}
    catatan = tata_shot(shot, [gedung])
    assert _irisan(kotak_boneka(kamu), kotak_benda(gedung)) / _luas(kotak_benda(gedung)) <= 0.25
    xs = sorted(b["x"] for b in fig)
    assert all(b - a >= 0.85 * 190 * 0.78 - 1 for a, b in pairwise(xs))
    assert catatan


def test_benda_selebar_latar_tidak_dipindah():
    ngarai = {"jenis": "ngarai", "x": 540, "y": 1500, "s": 1}
    shot = {"kamera": KAMERA, "benda": [ngarai], "boneka": []}
    assert tata_shot(shot, [ngarai]) == [] and ngarai["x"] == 540
