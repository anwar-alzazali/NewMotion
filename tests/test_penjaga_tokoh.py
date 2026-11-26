"""Uji penjaga adab untuk kontrak roster semantik NewMotion."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest

from newmotion.paket_genre.kisah_islami.penjaga_tokoh import periksa_adab_tokoh


def _spek(tokoh, boneka=None):
    return {
        "genre": "kisah_islami",
        "konteks_konten": "islami",
        "rencana_cerita": {"tokoh": [tokoh], "adegan": []},
        "cerita": {"shot": [{"at": 0, "boneka": boneka or [], "benda": []}]},
    }


def test_roster_nabi_dengan_konvensi_nur_tidak_digambar_otomatis():
    temuan = periksa_adab_tokoh(_spek({
        "id": "tokoh-nabi", "nama": "Nabi", "kategori": "nabi", "tampil": "nur"
    }))
    assert temuan == []


def test_roster_allah_selalu_ditolak():
    temuan = periksa_adab_tokoh(_spek({
        "id": "tokoh-allah", "nama": "Allah", "kategori": "allah"
    }))
    assert "ALLAH_TIDAK_DIVISUALKAN" in {item.kode for item in temuan}


def test_tokoh_sakral_ditolak_jika_dimasukkan_ke_boneka_renderer():
    temuan = periksa_adab_tokoh(_spek(
        {"id": "tokoh-nabi", "nama": "Nabi", "kategori": "nabi", "tampil": "nur"},
        [{"id": "tokoh-nabi", "x": 400, "y": 1500}],
    ))
    assert "TOKOH_SAKRAL_BERTUBUH" in {item.kode for item in temuan}


def test_sahabat_belum_boleh_masuk_boneka_sebelum_adapter_visual_tersedia():
    temuan = periksa_adab_tokoh(_spek(
        {"id": "tokoh-sahabat", "nama": "Sahabat", "kategori": "sahabat", "tampil": "wajah_cahaya"},
        [{"id": "tokoh-sahabat", "x": 400, "y": 1500}],
    ))
    assert "TOKOH_SAKRAL_BERTUBUH" in {item.kode for item in temuan}


def test_tokoh_biasa_tidak_boleh_memakai_bentuk_cahaya_khusus():
    temuan = periksa_adab_tokoh(_spek({
        "id": "tokoh-umum", "nama": "Penolong", "kategori": "manusia", "tampil": "nur"
    }))
    assert "BENTUK_CAHAYA_SALAH" in {item.kode for item in temuan}


def test_gerbang_renderer_membaca_roster_semantik_dan_menolak_allah():
    akar = Path(__file__).resolve().parents[1]
    sumber = akar / "mesin-video" / "papan_buat.py"
    spec_modul = spec_from_file_location("newmotion_uji_papan_buat_semantik", sumber)
    modul_render = module_from_spec(spec_modul)
    spec_modul.loader.exec_module(modul_render)

    with pytest.raises(modul_render.SpekDitolak):
        modul_render.jaga_spek(_spek({
            "id": "tokoh-allah", "nama": "Allah", "kategori": "allah"
        }))
