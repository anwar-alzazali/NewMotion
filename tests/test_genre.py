"""Uji batas paket genre terhadap inti NewMotion."""

from pathlib import Path

import pytest

from newmotion.domain.genre import (
    PaketGenre,
    ambil,
    daftar,
    daftarkan,
    dari_rencana,
    nama_dari_rencana,
)


def test_rencana_lama_tetap_memakai_kisah_islami():
    assert nama_dari_rencana({}) == "kisah_islami"
    assert dari_rencana({}).nama == "kisah_islami"


def test_manifest_kisah_islami_memuat_referensi_kompatibilitas():
    paket = ambil("kisah_islami")
    assert paket.nama == "kisah_islami"
    assert set(paket.modul_legacy) == {
        "pengarah", "arah_visual", "penjaga_dalil", "penjaga_tokoh_suci"
    }


def test_paket_genre_tiruan_dapat_didaftarkan_tanpa_mengubah_inti():
    nama = "genre_tiruan_uji"

    def komponen_tiruan(*args, **kwargs):
        return {"hasil": "siap"}

    paket = PaketGenre(
        nama=nama,
        komponen_visual={"benda.lingkaran": komponen_tiruan},
        bawaan={"warna": "biru"},
    )
    daftarkan(paket)
    try:
        assert nama in daftar()
        assert ambil(nama).komponen_visual["benda.lingkaran"]() == {"hasil": "siap"}
    finally:
        from newmotion.domain import genre
        genre._PAKET.pop(nama, None)


def test_paket_genre_tiruan_dapat_dimuat_dari_rencana():
    nama = "genre_rencana_uji"
    paket = PaketGenre(nama=nama, bawaan={"mode": "uji"})
    daftarkan(paket)
    try:
        assert dari_rencana({"genre": nama}) is paket
    finally:
        from newmotion.domain import genre
        genre._PAKET.pop(nama, None)


def test_manifest_dibekukan_setelah_dibuat():
    bawaan = {"tema": {"warna": "biru"}}
    paket = PaketGenre(nama="genre_beku_uji", bawaan=bawaan)
    bawaan["tema"]["warna"] = "merah"
    assert paket.bawaan["tema"]["warna"] == "biru"
    with pytest.raises(TypeError):
        paket.bawaan["tema"]["warna"] = "hijau"


@pytest.mark.parametrize("nama", ["", "../keluar", "Kisah Islami", "genre-baru"])
def test_nama_genre_tidak_boleh_mengandung_path_atau_spasi(nama):
    with pytest.raises(ValueError, match="nama genre"):
        PaketGenre(nama=nama, bawaan={"mode": "uji"})


def test_genre_tidak_dikenal_ditolak():
    with pytest.raises(ValueError, match="genre tidak dikenal"):
        ambil("genre_yang_tidak_ada")


def test_inti_tidak_mengimpor_paket_kisah_islami_secara_langsung():
    akar = Path(__file__).resolve().parents[1] / "newmotion"
    sumber = (akar / "domain" / "genre.py").read_text(encoding="utf-8")
    assert "newmotion.paket_genre.kisah_islami" not in sumber
    assert "import newmotion.paket_genre.kisah_islami" not in sumber


def test_validasi_job_memilih_genre_dari_spesifikasi(tmp_path):
    from newmotion.application.validasi_job import validasi_job

    spesifikasi = tmp_path / "cerita.json"
    spesifikasi.write_text('{"genre": "kisah_islami"}', encoding="utf-8")
    validasi_job(spesifikasi, tmp_path / "hasil.mp4")


def test_validasi_job_menolak_genre_yang_tidak_tersedia(tmp_path):
    from newmotion.application.validasi_job import GalatValidasiJob, validasi_job

    spesifikasi = tmp_path / "cerita.json"
    spesifikasi.write_text('{"genre": "genre_tidak_tersedia"}', encoding="utf-8")
    with pytest.raises(GalatValidasiJob, match="Genre pada spesifikasi tidak valid"):
        validasi_job(spesifikasi, tmp_path / "hasil.mp4")



def test_manifest_kisah_islami_mendaftarkan_kedua_penjaga():
    paket = ambil("kisah_islami")
    assert callable(paket.penjaga_tokoh)
    assert callable(paket.penjaga_dalil)


def test_kontrak_menolak_penjaga_dalil_yang_bukan_fungsi():
    with pytest.raises(TypeError, match="penjaga_dalil"):
        PaketGenre(nama="genre_penjaga_salah_uji", penjaga_dalil="bukan-fungsi")


def test_renderer_memanggil_penjaga_dari_kontrak_tanpa_cabang_nama_genre():
    akar = Path(__file__).resolve().parents[1]
    sumber = (akar / "mesin-video" / "papan_buat.py").read_text(encoding="utf-8")
    assert "paket.penjaga_dalil(spec)" in sumber
    assert 'if paket.nama == "kisah_islami"' not in sumber
