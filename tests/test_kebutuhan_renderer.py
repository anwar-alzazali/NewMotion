"""Uji antrean kebutuhan renderer tanpa layanan eksternal."""
import json

from newmotion.application.kebutuhan_renderer import (
    catat,
    dari_rencana,
    dari_temuan,
    normalisasi,
    validasi_kebutuhan,
)
from newmotion.application.katalog_renderer import katalog_subjek
from newmotion.paket_genre.kisah_islami.rencana_sutradara import validasi_rencana


def test_validator_menerima_kebutuhan_baru_dengan_bukti_narasi():
    narasi = ["Pedagang menimbang gandum di pasar."]
    rencana = {
        "objek_inti": None,
        "belum_ada": [],
        "beat": [{
            "beat": 1, "bukti": "menimbang gandum",
            "subjek": [{"jenis": "kerumunan", "tempat": "tengah"}],
            "belum_ada": [{"nama": "timbangan gandum", "alasan": "alat timbang tidak tersedia",
                           "bukti": "menimbang gandum"}],
            "kamu": "tidak", "kamera": {"bidikan": "lebar", "aksen": None},
            "teks_layar": None, "klimaks": False,
        }],
    }
    assert validasi_rencana(rencana, narasi) == []


def test_validator_menolak_nama_yang_sudah_ada_di_katalog():
    tersedia = next(iter(katalog_subjek()))
    assert any("sudah ada di katalog" in e
               for e in validasi_kebutuhan([{"nama": tersedia.upper(), "alasan": "uji",
                                             "bukti": "bukti"}]))


def test_validator_menolak_bukti_kebutuhan_di_luar_narasi():
    narasi = ["Pedagang menimbang gandum."]
    rencana = {
        "objek_inti": None,
        "beat": [{
            "beat": 1, "bukti": "menimbang gandum",
            "subjek": [{"jenis": "kerumunan", "tempat": "tengah"}],
            "belum_ada": [{"nama": "alat timbang khusus", "alasan": "alat tidak tersedia",
                           "bukti": "kapal terbang"}],
            "kamu": "tidak", "kamera": {"bidikan": "lebar", "aksen": None},
            "teks_layar": None, "klimaks": False,
        }],
    }
    assert any("bukti harus potongan narasi" in e for e in validasi_rencana(rencana, narasi))


def test_antrean_menggabungkan_nama_mirip_dan_menghitung_kemunculan(tmp_path):
    jalur = tmp_path / "kebutuhan.json"
    catat([{"nama": "Timbangan gandum", "alasan": "alat timbang", "bukti": "menimbang"}],
          sumber="sutradara", kisah="Kisah A", jalur=jalur)
    hasil = catat([{"nama": "timbangan-gandum", "alasan": "alat tidak ada", "bukti": "ditimbang"}],
                  sumber="pemeriksa", kisah="Kisah B", jalur=jalur)
    entri = hasil["kebutuhan"][normalisasi("Timbangan gandum")]
    assert entri["jumlah"] == 2
    assert entri["status"] == "menunggu"
    assert set(entri["sumber"]) == {"sutradara", "pemeriksa"}
    assert {x["kisah"] for x in entri["contoh"]} == {"Kisah A", "Kisah B"}
    assert json.loads(jalur.read_text(encoding="utf-8")) == hasil


def test_kebutuhan_tingkat_rencana_dan_beat_dikumpulkan():
    rencana = {
        "belum_ada": [{"nama": "sumur batu", "alasan": "tidak ada bentuk", "bukti": "sumur"}],
        "beat": [{"beat": 2, "belum_ada": [
            {"nama": "timba sumur", "alasan": "alat tidak ada", "bukti": "menimba"},
        ]}],
    }
    daftar = dari_rencana(rencana)
    assert [x["nama"] for x in daftar] == ["sumur batu", "timba sumur"]
    assert daftar[1]["beat"] == 2


def test_temuan_pemeriksa_dapat_menjadi_kebutuhan():
    temuan = {"temuan": [{
        "beat": 3, "berat": "berat", "masalah": "objek tidak tergambar",
        "kebutuhan": {"nama": "jembatan gantung", "alasan": "renderer tidak punya bentuk",
                      "bukti": "menyeberangi jembatan"},
    }]}
    [hasil] = dari_temuan(temuan)
    assert hasil["nama"] == "jembatan gantung" and hasil["beat"] == 3
