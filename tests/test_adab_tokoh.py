"""Uji aturan adab tokoh paket genre Kisah Islami NewMotion."""
import json

import pytest

from newmotion.paket_genre.kisah_islami.penjaga_tokoh import periksa_adab_tokoh


def _rencana(peran, shot):
    return {
        "genre": "kisah_islami",
        "peran": peran,
        "beat": [{"shot": [shot]}],
    }


def test_nabi_harus_pilar_nur_dan_tidak_boleh_masuk_tokoh_bertubuh():
    r = _rencana(
        [{"id": "nuh", "nama": "Nabi Nuh", "kategori": "nabi", "tampil": "nur"}],
        {"tokoh": [{"peran": "nuh"}]},
    )
    kode = {x.kode for x in periksa_adab_tokoh(r)}
    assert "TOKOH_SUCI_BERTUBUH" in kode


def test_nabi_lulus_jika_hanya_ditampilkan_sebagai_pilar_nur():
    r = _rencana(
        [{"id": "nuh", "nama": "Nabi Nuh", "kategori": "nabi", "tampil": "nur"}],
        {"nur": [{"peran": "nuh", "x": 500, "y": 1500}]},
    )
    assert periksa_adab_tokoh(r) == []


def test_malaikat_wajib_berkas_cahaya_dan_bukan_pilar_nur():
    peran = [{"id": "jibril", "nama": "Malaikat Jibril", "kategori": "malaikat", "tampil": "cahaya_malaikat"}]
    r = _rencana(peran, {"nur": [{"peran": "jibril"}]})
    assert "PILAR_NUR_BUKAN_NABI" in {x.kode for x in periksa_adab_tokoh(r)}
    r = _rencana(peran, {"cahaya_malaikat": [{"peran": "jibril"}]})
    assert periksa_adab_tokoh(r) == []


def test_malaikat_tidak_boleh_digambar_sebagai_tubuh():
    r = _rencana(
        [{"id": "jibril", "nama": "Jibril", "kategori": "malaikat", "tampil": "cahaya_malaikat"}],
        {"tokoh": [{"peran": "jibril"}]},
    )
    assert "TOKOH_SUCI_BERTUBUH" in {x.kode for x in periksa_adab_tokoh(r)}


def test_sahabat_harus_tubuh_dengan_wajah_cahaya():
    peran = [{"id": "abu_bakar", "nama": "Abu Bakar", "kategori": "sahabat", "tampil": "wajah_cahaya"}]
    benar = _rencana(peran, {"tokoh": [{"peran": "abu_bakar", "mode": "wajah_cahaya"}]})
    salah = _rencana(peran, {"tokoh": [{"peran": "abu_bakar", "mode": "pakaian"}]})
    assert periksa_adab_tokoh(benar) == []
    assert "SAHABAT_TANPA_WAJAH_CAHAYA" in {x.kode for x in periksa_adab_tokoh(salah)}


def test_sahabat_tidak_boleh_diganti_pilar_nur_atau_siluet():
    peran = [{"id": "abu_bakar", "nama": "Abu Bakar", "kategori": "sahabat", "tampil": "wajah_cahaya"}]
    r = _rencana(peran, {"nur": [{"peran": "abu_bakar"}]})
    assert "PILAR_NUR_BUKAN_NABI" in {x.kode for x in periksa_adab_tokoh(r)}


def test_allah_tidak_boleh_divisualisasikan():
    r = _rencana(
        [{"id": "allah", "nama": "Allah", "kategori": "allah", "tampil": "nur"}],
        {"nur": [{"peran": "allah"}]},
    )
    assert "ALLAH_TIDAK_DIVISUALKAN" in {x.kode for x in periksa_adab_tokoh(r)}


def test_bentuk_cahaya_khusus_tidak_boleh_dipakai_manusia_biasa():
    r = _rencana(
        [{"id": "warga", "nama": "Warga", "kategori": "manusia", "tampil": "nur"}],
        {"nur": [{"peran": "warga"}]},
    )
    kode = {x.kode for x in periksa_adab_tokoh(r)}
    assert "BENTUK_CAHAYA_SALAH" in kode
    assert "PILAR_NUR_BUKAN_NABI" in kode


def test_genre_lain_tidak_menerapkan_penjaga_tokoh_kisah_islami(tmp_path):
    from newmotion.domain.genre import PaketGenre, daftarkan
    from newmotion.application.validasi_job import validasi_job

    nama = "genre_adab_uji"
    daftarkan(PaketGenre(nama=nama, bawaan={"uji": True}))
    spec = tmp_path / "rencana.json"
    # Data yang ditolak pada Kisah Islami boleh diproses genre lain yang tidak memasang penjaga tersebut.
    spec.write_text(json.dumps({
        "genre": nama,
        "peran": [{"id": "nabi", "nama": "Nabi Nuh", "kategori": "nabi", "tampil": "pakaian"}],
        "beat": [{"shot": [{"tokoh": [{"peran": "nabi"}]}]}],
    }), encoding="utf-8")
    assert validasi_job(spec, tmp_path / "hasil.mp4")[0] == spec.resolve()


def test_penjaga_format_lama_menolak_siluet_sahabat_dan_pilar_malaikat():
    from newmotion.paket_genre.kisah_islami.penjaga_tokoh_legacy import periksa_tokoh_suci

    sahabat = {"cerita": {"shot": [{"boneka": [{"nama": "Abu Bakar", "gaya": "siluet"}]}]}}
    malaikat = {"isi": [{"jenis": "nur", "nama": "Malaikat Jibril"}]}
    assert periksa_tokoh_suci(sahabat)
    assert periksa_tokoh_suci(malaikat)


def test_validasi_job_tidak_menggandakan_penjaga_adab_renderer(tmp_path):
    from newmotion.application.validasi_job import validasi_job

    spec = tmp_path / "rencana.json"
    spec.write_text(json.dumps(_rencana(
        [{"id": "nabi", "nama": "Nabi Nuh", "kategori": "nabi", "tampil": "nur"}],
        {"tokoh": [{"peran": "nabi"}]},
    )), encoding="utf-8")
    # Validasi awal hanya memeriksa format dan pemilihan genre.
    # Gerbang renderer adalah satu-satunya tempat penjaga tokoh/dalil dijalankan.
    assert validasi_job(spec, tmp_path / "hasil.mp4")[0] == spec.resolve()


def test_penjaga_adab_format_lama_dipanggil_melalui_kait_paket():
    rencana_lama = {
        "cerita": {"shot": [{"boneka": [{"nama": "Abu Bakar", "gaya": "siluet"}]}]}
    }
    temuan = periksa_adab_tokoh(rencana_lama)
    assert temuan
    assert all(item.kode == "TOKOH_SAKRAL_FORMAT_LAMA" for item in temuan)


@pytest.mark.parametrize(
    ("nama", "kategori"),
    [
        ("Malaikat Jibril", "malaikat"),
        ("Jibril", "malaikat"),
        ("Nabi Musa", "nabi"),
        ("Rasulullah", "nabi"),
        ("Musa", "nabi"),
    ],
)
def test_kategori_nur_mengenali_nama_tokoh_dengan_batas_kata(nama, kategori):
    from newmotion.paket_genre.kisah_islami.penjaga_tokoh_legacy import _kategori_nur

    assert _kategori_nur(nama) == kategori


def test_manifest_mengaktifkan_adapter_penjaga_dalil_legacy():
    from newmotion.paket_genre.kisah_islami import buat_paket

    paket = buat_paket()
    assert paket.penjaga_dalil({}) == []


def test_penjaga_adab_mendeteksi_pemimpin_manusia_yang_merujuk_rasulullah():
    papan = {
        "genre": "kisah_islami",
        "cerita": {
            "shot": [{
                "_narasi": "Rasulullah, pemimpin umat ini, berdiri di depan para sahabat.",
                "benda": [{"jenis": "pemimpin"}],
            }]
        },
    }
    kode = {item.kode for item in periksa_adab_tokoh(papan)}
    assert "BENDA_MANUSIA_TOKOH_SAKRAL" in kode


def test_penjaga_adab_mendeteksi_kerumunan_yang_dapat_menggambarkan_sahabat():
    papan = {
        "genre": "kisah_islami",
        "cerita": {
            "shot": [{
                "_narasi": "Para sahabat berkumpul di sekitar Rasulullah.",
                "benda": [{"jenis": "kerumunan"}],
            }]
        },
    }
    kode = {item.kode for item in periksa_adab_tokoh(papan)}
    assert "BENDA_MANUSIA_TOKOH_SAKRAL" in kode


def test_penjaga_adab_mengizinkan_pemuka_kaum_di_kalimat_terpisah():
    papan = {
        "genre": "kisah_islami",
        "cerita": {
            "shot": [{
                "_narasi": "Nabi Nuh membuat kapal. Pemuka kaumnya lewat dan mengejek.",
                "benda": [{"jenis": "pemimpin"}],
            }]
        },
    }
    assert "BENDA_MANUSIA_TOKOH_SAKRAL" not in {
        item.kode for item in periksa_adab_tokoh(papan)
    }



def test_penjaga_adab_mendeteksi_sosok_manusia_pada_narasi_malaikat():
    papan = {
        "genre": "kisah_islami",
        "cerita": {
            "shot": [{
                "_narasi": "Malaikat Jibril datang sebagai pemimpin rombongan.",
                "benda": [{"jenis": "pemimpin"}],
            }]
        },
    }
    kode = {item.kode for item in periksa_adab_tokoh(papan)}
    assert "BENDA_MANUSIA_TOKOH_SAKRAL" in kode


def test_penjaga_adab_mendeteksi_penggali_dalam_narasi_sahabat():
    papan = {
        "genre": "kisah_islami",
        "cerita": {
            "shot": [{
                "_narasi": "Para sahabat menggali tanah bersama-sama.",
                "benda": [{"jenis": "penggali"}],
            }]
        },
    }
    kode = {item.kode for item in periksa_adab_tokoh(papan)}
    assert "BENDA_MANUSIA_TOKOH_SAKRAL" in kode
