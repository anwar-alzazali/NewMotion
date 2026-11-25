"""Uji klasifikasi konteks konten yang tidak mengubah genre produksi."""

import pytest

from newmotion.application.pengklasifikasi_konten import klasifikasikan_konten


def test_genre_komedi_tetap_komedi_dengan_sinyal_sahabat():
    hasil = klasifikasikan_konten({
        "genre": "komedi",
        "konteks_konten": "islami",
        "beat": [{"narasi": "Sahabat Abu Bakar menolong tetangganya."}],
    })
    assert hasil["genre"] == "komedi"
    assert hasil["konteks_konten"] == "islami"
    assert hasil["kebijakan"]["aktifkan_kebijakan_islami"] is True
    assert "sahabat" in hasil["sinyal_islami"]["entitas_dilindungi"]


def test_genre_tidak_ditebak_dari_kata_dalam_naskah():
    with pytest.raises(ValueError, match="Genre naskah belum ditentukan"):
        klasifikasikan_konten({"judul": "Cerita Nabi", "beat": []})


def test_konten_umum_tanpa_sinyal_tidak_mendapat_pagar_islami():
    hasil = klasifikasikan_konten({
        "genre": "komedi", "konteks_konten": "umum",
        "beat": [{"narasi": "Seorang pengendara terpeleset di jembatan."}],
    })
    assert hasil["genre"] == "komedi"
    assert hasil["kebijakan"]["aktifkan_kebijakan_islami"] is False
    assert hasil["keputusan"] == "ditetapkan"


def test_sinyal_keagamaan_tanpa_konteks_meminta_klarifikasi():
    hasil = klasifikasikan_konten({
        "genre": "komedi",
        "beat": [{"narasi": "Sahabat Umar mendengar firman Allah."}],
    })
    assert hasil["genre"] == "komedi"
    assert hasil["konteks_konten"] is None
    assert hasil["keputusan"] == "perlu_klarifikasi"
    assert hasil["perlu_klarifikasi"] is True


def test_konteks_umum_tidak_diam_diam_diubah_meski_ada_sinyal_islami():
    hasil = klasifikasikan_konten({
        "genre": "komedi", "konteks_konten": "umum",
        "beat": [{"narasi": "Malaikat Jibril menyampaikan wahyu."}],
    })
    assert hasil["genre"] == "komedi"
    assert hasil["konteks_konten"] == "umum"
    assert hasil["keputusan"] == "konflik_perlu_tinjauan"
    assert hasil["perlu_klarifikasi"] is True
    assert hasil["kebijakan"]["aktifkan_kebijakan_islami"] is False


def test_kisah_islami_selalu_mengaktifkan_kebijakan_islami():
    hasil = klasifikasikan_konten({
        "genre": "kisah_islami",
        "beat": [{"narasi": "Perjalanan seorang tokoh."}],
    })
    assert hasil["konteks_konten"] == "islami"
    assert hasil["kebijakan"]["aktifkan_kebijakan_islami"] is True
    assert hasil["perlu_klarifikasi"] is False


def test_konteks_tidak_dikenal_ditolak():
    with pytest.raises(ValueError, match="konteks_konten tidak dikenal"):
        klasifikasikan_konten({
            "genre": "komedi", "konteks_konten": "campuran",
        })
