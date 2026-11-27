"""Validator papan manual: kesalahan JSON tulisan AI chat ditolak sebelum narasi dibuat."""
import json
from pathlib import Path

import pytest

from newmotion.application import jalur_manual as J
from newmotion.application.validasi_papan_manual import periksa

AKAR = Path(__file__).resolve().parents[1]


def _papan(*shot, rekaman=None):
    return {"cerita": {"shot": list(shot)}, "rekaman": rekaman or []}


def _galat(spek):
    return periksa(spek)[0]


def test_papan_firaun1_bersih():
    spek = json.loads((AKAR / "mesin-video/papan/kisah/firaun1.json").read_text(encoding="utf-8"))
    assert _galat(spek) == []


def test_parameter_dibungkus_o_digabung_satu_butir():
    b = {"jenis": "pantai", "x": 540, "y": 1500, "o": {"tinggi": 900}}
    g = _galat(_papan({"narasi": "Laut tenang.", "benda": [b]}, {"narasi": "Laut lagi.", "benda": [dict(b)]}))
    assert len([x for x in g if '"o"' in x]) == 1
    assert '"tinggi": 900' in g[0]


def test_benda_sebagai_kunci_shot():
    g = _galat(_papan({"narasi": "Pagi.", "surya": {"x": 540}}))
    assert any('"surya" adalah benda' in x for x in g)


def test_kata_bertanda_hubung_dan_kemunculan_kedua():
    g = _galat(_papan({"narasi": "Sekali-kali tidak.", "teks": [{"at": "@sekali", "teks": "TIDAK"}]}))
    assert any("@sekalikali" in x for x in g)
    g = _galat(_papan({"narasi": "Laut terbelah."}, {"narasi": "Laut menutup.", "teks": [{"at": "@laut", "teks": "TUTUP"}]}))
    assert any("@laut#2" in x for x in g)
    assert _galat(_papan({"narasi": "Laut terbelah."}, {"narasi": "Laut menutup.", "teks": [{"at": "@laut#2", "teks": "TUTUP"}]})) == []


def test_kartu_dalil_tanpa_kitab_dan_arab_di_terjemahan():
    g = _galat(_papan({"narasi": "Musa menjawab.", "benda": [{"jenis": "kartu_dalil", "teks": "قَالَ كَلَّا"}]}))
    assert any('"kitab" wajib' in x for x in g)
    assert any('"arab"' in x for x in g)
    g = _galat(_papan({"narasi": "Rasulullah bersabda.", "benda": [{"jenis": "kartu_dalil", "kitab": "HR. Tirmidzi", "teks": "arti"}]}))
    assert any("nomor hadis" in x for x in g)


def test_judul_terlalu_lebar_dan_yang_dipecah_lolos():
    g = _galat(_papan({"narasi": "Jalan kering.", "teks": [{"teks": "JALAN KERING DI DASAR LAUT", "ukuran": 70}]}))
    assert any("terlalu lebar" in x for x in g)
    assert _galat(_papan({"narasi": "Jalan kering.", "teks": [{"teks": "JALAN KERING\nDI DASAR LAUT", "ukuran": 70}]})) == []


def test_benda_khusus_mahsyar_dan_efek_tidak_ada():
    g = _galat(_papan({"narasi": "Firaun tenggelam.", "benda": [{"jenis": "genangan_tubuh", "tinggi": 400}]},
                      rekaman=[{"berkas": "../../aset/suara/ombak_pelan.mp3", "at": 0}]))
    assert any("khusus kisah mahsyar" in x for x in g)
    assert any("ombak_pelan" in x for x in g)
    assert not any("khusus" in x for x in _galat(_papan({"narasi": "Keringat di Padang Mahsyar.",
                                                          "benda": [{"jenis": "genangan_tubuh", "tinggi": 400}]})))


def test_ditolak_sebelum_tts(tmp_path, monkeypatch):
    p = AKAR / "mesin-video/papan/kisah/_uji_validasi.json"
    p.write_text(json.dumps(_papan({"narasi": "Pagi.", "surya": {"x": 540}})), encoding="utf-8")
    dipanggil = []
    try:
        with pytest.raises(ValueError, match="kredit aman"):
            J.siapkan(p, tts_fn=lambda *a, **k: dipanggil.append(1))
    finally:
        p.unlink()
    assert dipanggil == []
