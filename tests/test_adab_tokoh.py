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


def test_genre_lain_tidak_menerapkan_penjaga_tokoh_kisah_islami():
    from newmotion.domain.genre import PaketGenre, daftarkan
    from newmotion.application.validasi_job import validasi_job, GalatValidasiJob

    nama = "genre_adab_uji"
    daftarkan(PaketGenre(nama=nama, bawaan={"uji": True}))
    # Hook penjaga tidak terpasang pada paket tiruan; validasi job tidak boleh menerapkan aturan Islami.
    assert PaketGenre(nama="genre_adab_uji_lain", bawaan={"uji": True}).penjaga_tokoh is None


def test_validasi_job_menolak_pelanggaran_adab_sebelum_render(tmp_path):
    from newmotion.application.validasi_job import validasi_job, GalatValidasiJob

    spec = tmp_path / "rencana.json"
    spec.write_text(json.dumps(_rencana(
        [{"id": "nabi", "nama": "Nabi Nuh", "kategori": "nabi", "tampil": "nur"}],
        {"tokoh": [{"peran": "nabi"}]},
    )), encoding="utf-8")
    with pytest.raises(GalatValidasiJob, match="adab penggambaran"):
        validasi_job(spec, tmp_path / "hasil.mp4")
