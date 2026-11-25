"""Uji antrean naskah Telegram yang sudah dipindahkan ke NewMotion."""
# Tes ini berjalan tanpa secret dan tanpa memanggil layanan eksternal.
import json
from pathlib import Path

from newmotion.application import antrean_naskah as A


NASKAH = {
    "judul": "Uji antrean",
    "inti": "Cerita uji.",
    "dalil": [],
    "beat": [{
        "narasi": "Tokoh memulai perjalanan.",
        "dalil": [],
        "kata_kunci": ["perjalanan"],
        "peran": ["tokoh utama"],
    }],
}


def test_kartu_status_sama_dengan_fixture_worker():
    fixture = json.loads((Path(__file__).parent / "data" / "kartu_status.json").read_text(encoding="utf-8"))
    assert A.kartu(fixture["status"]) == fixture["teks"]


def test_validasi_menolak_huruf_arab_di_narasi_dan_rujukan_hilang():
    rusak = json.loads(json.dumps(NASKAH))
    rusak["beat"][0]["narasi"] = "Allah berfirman قَالَ"
    rusak["beat"][0]["dalil"] = ["rujukan-tidak-ada"]
    pesan = " | ".join(A.validasi(rusak))
    assert "huruf Arab" in pesan
    assert "rujukan-tidak-ada" in pesan


def test_narasi_tempelan_tidak_boleh_diubah_ai():
    asal = "Kalimat pertama.\n\nKalimat kedua."
    hasil = json.loads(json.dumps(NASKAH))
    hasil["beat"][0]["narasi"] = "Kalimat pertama."
    assert A.narasi_utuh(hasil, asal) == []
    hasil["beat"][0]["narasi"] = "Narasi hasil karangan AI."
    assert A.narasi_utuh(hasil, asal)


def test_model_gemini_memilih_flash_stabil_dan_cadangan():
    nama = ["gemini-2.5-flash", "gemini-3.0-flash", "gemini-3.0-flash-lite", "gemini-3.1-flash-preview"]
    assert A.pilih_model_gemini(nama) == "gemini-3.0-flash"
    assert A.urutan_model_gemini(nama) == ["gemini-3.0-flash", "gemini-2.5-flash", "gemini-3.0-flash-lite"]


def test_proses_antrean_menggunakan_verifikasi_paket_kisah_islami(tmp_path, monkeypatch):
    folder = tmp_path / "antrean"
    antrean = folder / "uji-bot"
    antrean.mkdir(parents=True)
    (antrean / "status.json").write_text(json.dumps(A.status_baru("uji-bot", "Uji bot", "ide")), encoding="utf-8")
    (antrean / "masukan.txt").write_text("Ide cerita uji", encoding="utf-8")

    def verifikasi(naskah, *, quran=None):
        hasil = json.loads(json.dumps(naskah))
        return hasil, ["tanpa dalil untuk uji"]

    monkeypatch.setattr("newmotion.paket_genre.kisah_islami.dalil.verifikasi.verifikasi", verifikasi)
    st = A.proses(
        "uji-bot", "ide", folder=folder,
        tanya=lambda *args, **kwargs: (json.dumps(NASKAH), 12),
        kirim_tg=False,
    )
    assert st["tahap"]["diterima"] == "selesai"
    assert st["tahap"]["dalil"] == "selesai"
    assert st["tahap"]["tinjau"] == "jalan"
    tersimpan = json.loads((antrean / "naskah.json").read_text(encoding="utf-8"))
    assert tersimpan["judul"] == "Uji antrean"


def test_status_baru_menyimpan_genre_dan_konteks_eksplisit():
    status = A.status_baru(
        "uji-metadata", "Uji metadata", "ide",
        genre="kisah_islami", konteks_konten="islami",
    )
    assert status["genre"] == "kisah_islami"
    assert status["konteks_konten"] == "islami"


def test_status_baru_mempertahankan_default_kompatibilitas_lama():
    status = A.status_baru("uji-lama", "Uji lama", "ide")
    assert status["genre"] == "kisah_islami"
    assert status["konteks_konten"] == "islami"


def test_kebijakan_naskah_menolak_genre_yang_paketnya_belum_tersedia():
    status = A.status_baru(
        "uji-komedi", "Uji komedi", "ide",
        genre="komedi", konteks_konten="umum",
    )
    try:
        A.kebijakan_naskah(status)
    except ValueError as galat:
        assert "belum tersedia" in str(galat)
    else:
        raise AssertionError("Genre tanpa paket tidak boleh diproses")


def test_kebijakan_naskah_mempertahankan_pagar_islami_dari_metadata_status():
    status = A.status_baru("uji-islami", "Uji Islami", "ide")
    hasil = A.kebijakan_naskah(status, {"judul": "Uji", "beat": []})
    assert hasil["genre"] == "kisah_islami"
    assert hasil["konteks_konten"] == "islami"
    assert hasil["kebijakan"]["aktifkan_kebijakan_islami"] is True


def test_proses_menyimpan_metadata_kebijakan_ke_naskah(tmp_path):
    folder = tmp_path / "antrean"
    antrean = folder / "uji-metadata-hasil"
    antrean.mkdir(parents=True)
    status = A.status_baru("uji-metadata-hasil", "Uji metadata", "ide")
    (antrean / "status.json").write_text(json.dumps(status), encoding="utf-8")
    (antrean / "masukan.txt").write_text("Ide cerita uji", encoding="utf-8")

    def verifikasi(naskah, *, quran=None):
        hasil = json.loads(json.dumps(naskah))
        return hasil, ["uji"]

    monkeypatch = __import__("pytest").MonkeyPatch()
    monkeypatch.setattr("newmotion.paket_genre.kisah_islami.dalil.verifikasi.verifikasi", verifikasi)
    try:
        hasil = A.proses(
            "uji-metadata-hasil", "ide", folder=folder,
            tanya=lambda *args, **kwargs: (json.dumps(NASKAH), 5),
            kirim_tg=False,
        )
    finally:
        monkeypatch.undo()
    tersimpan = json.loads((antrean / "naskah.json").read_text(encoding="utf-8"))
    assert hasil["tahap"]["diterima"] == "selesai"
    assert tersimpan["genre"] == "kisah_islami"
    assert tersimpan["konteks_konten"] == "islami"
