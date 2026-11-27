"""Uji antrean naskah Telegram yang sudah dipindahkan ke NewMotion."""
# Tes ini berjalan tanpa secret dan tanpa memanggil layanan eksternal.
import json
from pathlib import Path

from newmotion.application import antrean_naskah as A


NASKAH = {
    "judul": "Uji antrean",
    "inti": "Cerita uji.",
    "uji_cerita": {
        "kalimat_inti": "Cerita uji.",
        "fakta_terkuat_detik_0": "Fakta pembuka.",
        "jawaban_hook": "Jawaban video.",
        "momen_emosi_kejutan": "Momen beat satu.",
        "alasan_interaksi": "Pertanyaan relevan.",
        "kalimat_dibuang": [],
    },
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
    assert st["naskah_ai"]["model"] == "uji"
    assert st["naskah_ai"]["penyedia"] == "palsu"
    assert st["naskah_ai"]["token_masuk"] == 12
    assert st["naskah_ai"]["biaya_status"] == "tercatat"
    assert st["token_ai"] == 12


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


def test_status_menandai_biaya_gemini_belum_terverifikasi(tmp_path, monkeypatch):
    from newmotion.infrastructure.llm import Jawaban

    folder = tmp_path / "antrean"
    antrean = folder / "uji-biaya-gemini"
    antrean.mkdir(parents=True)
    status = A.status_baru("uji-biaya-gemini", "Uji biaya", "ide")
    (antrean / "status.json").write_text(json.dumps(status), encoding="utf-8")
    (antrean / "masukan.txt").write_text("Ide cerita", encoding="utf-8")

    def verifikasi(naskah, *, quran=None):
        return json.loads(json.dumps(naskah)), ["uji"]

    monkeypatch.setattr("newmotion.paket_genre.kisah_islami.dalil.verifikasi.verifikasi", verifikasi)
    jawaban = Jawaban("{}", "gemini-3-flash", "google", biaya_usd=0, data=NASKAH)
    monkeypatch.setattr(A, "buat_naskah", lambda *args, **kwargs: (NASKAH, jawaban))

    hasil = A.proses("uji-biaya-gemini", "ide", folder=folder, kirim_tg=False)
    assert hasil["biaya_ai_status"] == "belum_terverifikasi"
    assert hasil["naskah_ai"]["biaya_status"] == "belum_terverifikasi"


def test_proses_menyimpan_metadata_kebijakan_ke_naskah(tmp_path, monkeypatch):
    folder = tmp_path / "antrean"
    antrean = folder / "uji-metadata-hasil"
    antrean.mkdir(parents=True)
    status = A.status_baru("uji-metadata-hasil", "Uji metadata", "ide")
    (antrean / "status.json").write_text(json.dumps(status), encoding="utf-8")
    (antrean / "masukan.txt").write_text("Ide cerita uji", encoding="utf-8")

    def verifikasi(naskah, *, quran=None):
        hasil = json.loads(json.dumps(naskah))
        return hasil, ["uji"]

    monkeypatch.setattr("newmotion.paket_genre.kisah_islami.dalil.verifikasi.verifikasi", verifikasi)
    hasil = A.proses(
        "uji-metadata-hasil", "ide", folder=folder,
        tanya=lambda *args, **kwargs: (json.dumps(NASKAH), 5),
        kirim_tg=False,
    )
    tersimpan = json.loads((antrean / "naskah.json").read_text(encoding="utf-8"))
    assert hasil["tahap"]["diterima"] == "selesai"
    assert tersimpan["genre"] == "kisah_islami"
    assert tersimpan["konteks_konten"] == "islami"



def test_metadata_kosong_tidak_ditutup_dengan_nilai_cadangan():
    status = A.status_baru("uji-kosong", "Uji kosong", "ide")
    status["genre"] = ""
    try:
        A.kebijakan_naskah(status, {"genre": "kisah_islami", "konteks_konten": "islami"})
    except ValueError as galat:
        assert "genre kosong" in str(galat)
    else:
        raise AssertionError("Genre kosong tidak boleh diam-diam memakai metadata cadangan")

    status = A.status_baru("uji-konteks-kosong", "Uji konteks kosong", "ide")
    status["konteks_konten"] = ""
    try:
        A.kebijakan_naskah(status, {"konteks_konten": "islami"})
    except ValueError as galat:
        assert "konteks_konten kosong" in str(galat)
    else:
        raise AssertionError("Konteks kosong tidak boleh diam-diam memakai metadata cadangan")


def test_uji_cerita_memvalidasi_enam_unsur():
    assert A.validasi_uji_cerita(NASKAH) == []
    rusak = json.loads(json.dumps(NASKAH))
    del rusak["uji_cerita"]["jawaban_hook"]
    assert any("jawaban_hook" in x for x in A.validasi_uji_cerita(rusak))


def test_kartu_telegram_memuat_ringkasan_uji_cerita():
    st = A.status_baru("uji", "Uji", "ide")
    st["uji_cerita_ringkas"] = "Inti | fakta detik nol | jawaban hook"
    assert "Uji cerita" in A.kartu(st)


def test_peta_tempel_menolak_nomor_paragraf_nol():
    assert A.validasi_peta_tempel({"beat": [{"paragraf": [0]}]})


def test_peta_tempel_wajib_memetakan_semua_paragraf_tepat_satu_kali():
    lengkap = {"judul": "Judul", "inti": "Inti",
               "beat": [{"paragraf": [1, 2]}, {"paragraf": [3]}]}
    assert A.validasi_peta_tempel(lengkap, jumlah_paragraf=3) == []

    hilang = {"judul": "Judul", "inti": "Inti",
              "beat": [{"paragraf": [1]}, {"paragraf": [3]}]}
    assert any("paragraf belum dipetakan: 2" in x
               for x in A.validasi_peta_tempel(hilang, jumlah_paragraf=3))

    ganda = {"judul": "Judul", "inti": "Inti",
             "beat": [{"paragraf": [1, 2]}, {"paragraf": [2, 3]}]}
    assert any("dipetakan lebih dari sekali" in x
               for x in A.validasi_peta_tempel(ganda, jumlah_paragraf=3))


def test_peta_tempel_menolak_urutan_terbalik_dan_nomor_di_luar_naskah():
    terbalik = {"judul": "Judul", "inti": "Inti",
                "beat": [{"paragraf": [2, 1]}]}
    assert any("urutan paragraf harus menaik" in x
               for x in A.validasi_peta_tempel(terbalik, jumlah_paragraf=2))

    di_luar = {"judul": "Judul", "inti": "Inti",
               "beat": [{"paragraf": [1, 3]}]}
    assert any("paragraf 3 tidak ada" in x
               for x in A.validasi_peta_tempel(di_luar, jumlah_paragraf=2))


def test_peta_tempel_tidak_boleh_menambah_atau_menghilangkan_rujukan():
    dasar = {"judul": "Judul", "inti": "Inti", "dalil": [],
             "beat": [{"paragraf": [1]}]}
    sumber = ["(QS Hud 50)"]
    assert any("tidak boleh menambah" in x
               for x in A.validasi_peta_tempel(dasar, 1, sumber))

    palsu = {"judul": "Judul", "inti": "Inti",
             "dalil": [{"id": "ayat", "label": "QS Al-Baqarah 255"}],
             "beat": [{"paragraf": [1]}]}
    assert any("tidak boleh menambah" in x
               for x in A.validasi_peta_tempel(palsu, 1, sumber))

    benar = {"judul": "Judul", "inti": "Inti",
             "dalil": [{"id": "hud50", "label": "QS HUD 50"}],
             "beat": [{"paragraf": [1]}]}
    assert A.validasi_peta_tempel(benar, 1, sumber) == []



def test_jalur_ide_revisi_dan_tempel_memakai_tahap_llm_yang_tepat(monkeypatch):
    from newmotion.infrastructure import llm

    jawaban = llm.Jawaban(json.dumps(NASKAH), "model-uji", "anthropic", data=NASKAH)
    panggilan = []

    def palsu(tahap, sistem, isi, **kwargs):
        panggilan.append((tahap, sistem, isi, kwargs.get("validasi")))
        return jawaban

    monkeypatch.setattr(llm, "panggil", palsu)
    monkeypatch.setattr(A, "_PATH_SKILL", Path(__file__).parents[1] / "newmotion/paket_genre/kisah_islami/skill/naskah.md")

    A.buat_naskah("ide", "Ide uji")
    lama = json.loads(json.dumps(NASKAH))
    lama["beat"].append({
        "narasi": "Bagian yang tidak diminta berubah.",
        "dalil": [], "kata_kunci": ["tetap"], "peran": [],
    })
    revisi = json.loads(json.dumps(lama))
    revisi["beat"][0]["narasi"] = "Kalimat yang memang diminta diubah."
    jawaban.data = revisi
    hasil_revisi, _ = A.buat_naskah("revisi", "Ubah kalimat pembuka saja", lama)
    assert [x[0] for x in panggilan] == ["naskah", "naskah"]
    assert all(callable(x[3]) for x in panggilan)
    assert "NASKAH SAAT INI" in panggilan[1][2]
    assert "CATATAN PEMILIK" in panggilan[1][2]
    assert "Ubah kalimat pembuka saja" in panggilan[1][2]
    assert "ubah hanya bagian yang diminta pemilik" in panggilan[1][1]
    assert hasil_revisi["beat"][0]["narasi"] == "Kalimat yang memang diminta diubah."
    assert hasil_revisi["beat"][1] == lama["beat"][1]

    hasil_tempel = {
        "judul": "Tempel",
        "inti": "Naskah asli",
        "dalil": [],
        "beat": [{"paragraf": [1], "dalil": [], "kata_kunci": [], "peran": []}],
    }
    jawaban.data = hasil_tempel
    hasil, _ = A.buat_naskah("tempel", "Kalimat pemilik harus utuh.")
    assert panggilan[-1][0] == "rapikan"
    assert hasil["beat"][0]["narasi"] == "Kalimat pemilik harus utuh."
