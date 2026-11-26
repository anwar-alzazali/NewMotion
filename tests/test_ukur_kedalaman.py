"""Alat ukur kedalaman spek papan dibanding referensi Nuh 1, Mahsyar 1, Ya'juj 1-2."""
import copy
import json

import pytest

from newmotion.application import ukur_kedalaman as U


@pytest.fixture(scope="module")
def referensi():
    return U.muat_referensi()


def _papan(shot, **lain):
    return {"cerita": {"shot": shot}, **lain}


def test_nilai_beranimasi_mengikuti_aturan_renderer():
    assert U._beranimasi([1.0, 1.1])
    assert not U._beranimasi([1.0, 1.0])
    assert U._beranimasi([[0, "berdiri"], [1.2, "tunjuk"]])
    assert not U._beranimasi([[0, 5], [2, 5]])
    assert not U._beranimasi(540)


def test_referensi_lebih_tinggi_daripada_papan_latar_berulang(referensi):
    patok = U.patokan(referensi)
    latar = [{"at": i * 4.0, "kamera": {"z": [1, 1.05]}, "langit": 0.1,
              "benda": [{"jenis": "bintang"}, {"jenis": "gunung"}, {"jenis": "batu"}],
              "boneka": [{"x": 540, "y": 1700, "pose": [[0, "berdiri"], [1, "tunjuk"]]}]}
             for i in range(12)]
    miskin = U.bandingkan(U.ukur(_papan(latar)), patok)
    for nama in ("nuh1", "yajuj1"):
        assert U.bandingkan(referensi[nama], patok)["skor_gabungan"] > miskin["skor_gabungan"] + 15
    assert miskin["skor_aspek"]["cerita"] < 40


def test_kesesuaian_narasi_menghitung_tiap_benda_yang_disebut():
    shot = [{"at": 0, "benda": [{"jenis": "ombak"}], "_adegan": 0},
            {"at": 3, "benda": [{"jenis": "bahtera"}, {"jenis": "ombak"}], "_adegan": 0}]
    spek = _papan(shot, rencana_cerita={"adegan": [{"id": "b1", "teks": "Kapal itu berlayar di tengah ombak."}]})
    nilai, rincian = U._kesesuaian_narasi(spek, shot)
    assert nilai == 0.75  # shot 1: ombak saja (0,5); shot 2: kapal dan ombak (1,0)
    assert rincian[0]["tidak_tergambar"] and not rincian[1]["tidak_tergambar"]


def test_narasi_referensi_dibaca_dari_berkas_waktu(referensi):
    # Mahsyar 1 menyimpan narasi di .waktu.json terpisah, bukan di cerita.tengah.
    assert referensi["mahsyar1"]["cerita"]["kesesuaian_narasi"] is not None
    assert referensi["mahsyar1"]["ritme"]["durasi_total"] > 60


def test_spek_tanpa_shot_ditolak():
    with pytest.raises(ValueError, match="cerita.shot"):
        U.ukur({"cerita": {"shot": []}})


def test_tolok_ukur_menjalankan_pengarah_pada_keempat_naskah():
    hasil = U.tolok_ukur()
    assert set(hasil) == set(U.REFERENSI)
    for h in hasil.values():
        assert 0 <= h["skor_gabungan"] <= 100
        assert h["skor_referensi"] is not None
    assert "yajuj1" in U.teks_tolok_ukur(hasil)


def test_hasil_ukur_dapat_diserialisasi(referensi):
    json.dumps(copy.deepcopy(referensi), ensure_ascii=False)


def test_cli_ukur_berkas(capsys):
    from newmotion.cli import main
    assert main(["ukur", str(U.FOLDER_REFERENSI / "yajuj1.json")]) == 0
    assert "Skor kedalaman gabungan" in capsys.readouterr().out


def test_arus_adalah_kerumunan_bukan_air():
    # Di cerita.js, jenis `arus` = kerumunan siluet berlari (Ya'juj keluar), bukan air.
    shot = [{"at": 0, "benda": [{"jenis": "arus"}], "_adegan": 0},
            {"at": 3, "benda": [{"jenis": "arus"}], "_adegan": 1}]
    spek = _papan(shot, rencana_cerita={"adegan": [
        {"id": "b1", "teks": "Mereka meminum habis air danau itu."},
        {"id": "b2", "teks": "Air mata Rasulullah menetes."},
    ]})
    nilai, rincian = U._kesesuaian_narasi(spek, shot)
    assert nilai == 0.0  # air tidak digambar dengan kerumunan
    assert [r["shot"] for r in rincian] == [0]  # "air mata" bukan penyebutan air
