"""Uji kontrak sumber dalil paket Kisah Islami tanpa akses jaringan."""

from newmotion.paket_genre.kisah_islami.dalil import hadis
from newmotion.paket_genre.kisah_islami.dalil import sumber
from newmotion.paket_genre.kisah_islami.dalil.unduh_hadis import susun


def test_manifest_genre_mendaftarkan_modul_dalil():
    from newmotion.paket_genre.kisah_islami import buat_paket
    paket = buat_paket()
    assert paket.modul_dalil == "newmotion.paket_genre.kisah_islami.dalil"


def test_dataset_hadis_mempertahankan_nomor_sunnah_com_dan_tiga_bahasa():
    edisi = {
        "ara": {"hadiths": [{"hadithnumber": 1, "arabicnumber": "2934.02", "text": "نص عربي"}]},
        "ind": {"hadiths": [{"hadithnumber": 1, "text": "Teks Indonesia"}]},
        "eng": {"hadiths": [{"hadithnumber": 1, "text": "English text", "grades": [{"name": "Al-Albani", "grade": "Sahih"}]}]},
    }
    hasil = susun("muslim", edisi)
    entri = hasil["hadis"]["2934"][0]
    assert entri["sub"] == "b"
    assert entri["ar"] == "نص عربي"
    assert entri["id"] == "Teks Indonesia"
    assert entri["en"] == "English text"
    assert entri["derajat"][0]["name"] == "Al-Albani"


def test_derajat_bukhari_dan_muslim_dikunci_sahih():
    assert hadis.derajat("bukhari", []) == ("sahih", [])
    assert hadis.derajat("muslim", []) == ("sahih", [])


def test_derajat_kitab_lain_mengutamakan_albani():
    penilaian = [
        {"name": "Al-Albani", "grade": "Hasan"},
        {"name": "Penilai lain", "grade": "Daif"},
    ]
    assert hadis.derajat("abudawud", penilaian) == ("hasan", ["Penilai lain"])


def test_adapter_hadis_menolak_derajat_tidak_diterima(monkeypatch):
    class Palsu:
        kitab = "abudawud"
        nomor = "10"
        sub = ""
        ar = "نص عربي صحيح"
        id = "Teks"
        en = "Text"
        penilaian = [{"name": "Al-Albani", "grade": "Daif"}]
    monkeypatch.setattr(sumber.hadis, "cari", lambda *_: [Palsu()])
    try:
        sumber.ambil_hadis("abudawud", 10)
    except RuntimeError as exc:
        assert "daif" in str(exc)
    else:
        raise AssertionError("hadis daif seharusnya ditolak")


def test_secret_quran_tidak_dicetak(monkeypatch):
    monkeypatch.setenv("QURAN_FOUNDATION_CLIENT_ID", "id-rahasia")
    monkeypatch.setenv("QURAN_FOUNDATION_CLIENT_SECRET", "secret-rahasia")
    monkeypatch.setattr(sumber, "_KLIEN_QURAN", None)
    class KlienPalsu:
        def ayat(self, surah, ayat):
            class A:
                ar = "بِسْمِ اللَّهِ"
                terjemah = "Dengan nama Allah"
                nama_surah = "Al-Fatihah"
                sumber_terjemah = "Kemenag"
                tautan = "https://quran.com/1/1"
            return A()
    monkeypatch.setattr(sumber, "QuranBertingkat", lambda: KlienPalsu())
    hasil = sumber.ambil_ayat(1, 1)
    assert hasil["teks_arab"] == "بِسْمِ اللَّهِ"
    assert "secret-rahasia" not in repr(hasil)
    monkeypatch.setattr(sumber, "_KLIEN_QURAN", None)
