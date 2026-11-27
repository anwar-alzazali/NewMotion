import copy
import json
from pathlib import Path

from newmotion.application import pemeriksa_naskah as P


DATA = json.loads((Path(__file__).parent / "data" / "naskah_firaun_pemeriksa.json").read_text(encoding="utf-8"))


def test_pemeriksa_mendeteksi_detail_tanpa_dalil_dan_hook_lemah(monkeypatch):
    from newmotion.infrastructure import llm

    jawaban = {
        "temuan": [
            {"beat": 1, "kategori": "hook_lemah", "tingkat": "berat",
             "bukti": "Pernahkah kamu membayangkan", "alasan": "Hook generik dan tidak menjanjikan detik terakhir Firaun.",
             "saran": "Mulai dari pengakuan Firaun ketika tenggelam."},
            {"beat": 2, "kategori": "detail_tanpa_dalil", "tingkat": "berat",
             "bukti": "Laut Merah; bersenjata lengkap; berteriak; binasa",
             "alasan": "Teks dalil yang disertakan tidak menyebut rincian tersebut.",
             "saran": "Hapus rincian yang tidak didukung dan gunakan peristiwa yang eksplisit."},
            {"beat": 3, "kategori": "fakta_kuat_terlewat", "tingkat": "sedang",
             "bukti": "QS Yunus 92", "alasan": "Jasad Firaun dijadikan tanda bagi manusia.",
             "saran": "Pertimbangkan fakta ini untuk penutup."}
        ],
        "usulan_dalil": []
    }
    metadata = llm.Jawaban("{}", "claude-sonnet-5-5", "anthropic", data=jawaban,
                           token_masuk=12, token_keluar=8, biaya_usd=0.001)
    panggilan = []
    def palsu(tahap, sistem, isi, **kwargs):
        panggilan.append((tahap, sistem, isi))
        assert "terjemah_resmi" in isi
        assert "Jangan membuat teks ayat/hadis" in sistem
        return metadata
    hasil, meta = P.periksa(DATA, panggil=palsu)
    assert len(panggilan) == 1
    assert {x["kategori"] for x in hasil["temuan"]} >= {"detail_tanpa_dalil", "hook_lemah"}
    assert meta.model == "claude-sonnet-5-5"


def test_validasi_menolak_kategori_dan_rujukan_usulan_tidak_sah():
    hasil = {"temuan": [{"beat": 1, "kategori": "fakta_buatan", "tingkat": "berat",
                         "bukti": "x", "alasan": "x", "saran": "x"}], "usulan_dalil": []}
    assert any("kategori tidak dikenal" in x for x in P.validasi_hasil(hasil, DATA))
    hasil["temuan"] = []
    hasil["usulan_dalil"] = [{"id": "palsu", "jenis": "hadis", "kitab": "x", "nomor": "1", "alasan": "x"}]
    assert any("hanya rujukan Quran" in x for x in P.validasi_hasil(hasil, DATA))


def test_perbaikan_otomatis_satu_putaran_dan_pemeriksaan_ulang(tmp_path, monkeypatch):
    from newmotion.application import antrean_naskah as A
    from newmotion.infrastructure.llm import Jawaban

    naskah = copy.deepcopy(DATA)
    revisi = copy.deepcopy(DATA)
    revisi["beat"][0]["narasi"] = "Saat tenggelam, Firaun mengakui keimanannya."
    revisi["beat"][1]["narasi"] = "Firaun dan tentaranya mengejar Bani Israil, lalu tenggelam."
    revisi["beat"][1]["dalil"] = ["yunus90", "yunus91"]
    revisi["beat"][2]["narasi"] = "Jasad Firaun diselamatkan sebagai tanda bagi manusia."
    revisi["beat"][2]["dalil"] = ["yunus92"]

    antrean = tmp_path / "antrean" / "uji-firaun"
    antrean.mkdir(parents=True)
    (antrean / "status.json").write_text(json.dumps(A.status_baru("uji-firaun", DATA["judul"], "ide")), encoding="utf-8")
    (antrean / "masukan.txt").write_text("Firaun", encoding="utf-8")
    jawaban_ai = Jawaban("{}", "model-uji", "anthropic", data=naskah, token_masuk=2, token_keluar=3)
    jawaban_revisi = Jawaban("{}", "model-uji", "anthropic", data=revisi, token_masuk=4, token_keluar=5)
    panggilan_penulis = []
    def buat(mode, masukan, lama=None, **kwargs):
        panggilan_penulis.append(mode)
        return (copy.deepcopy(naskah), jawaban_ai) if len(panggilan_penulis) == 1 else (copy.deepcopy(revisi), jawaban_revisi)
    monkeypatch.setattr(A, "buat_naskah", buat)

    hasil_periksa = [
        {"temuan": [
            {"beat": 1, "kategori": "hook_lemah", "tingkat": "berat", "bukti": "hook umum", "alasan": "Tidak terkait judul", "saran": "Mulai dari tenggelam."},
            {"beat": 2, "kategori": "detail_tanpa_dalil", "tingkat": "berat", "bukti": "Laut Merah", "alasan": "Tidak ada pada teks dalil", "saran": "Hapus."}
        ], "usulan_dalil": []},
        {"temuan": [], "usulan_dalil": []}
    ]
    def periksa_palsu(_n):
        data = hasil_periksa.pop(0)
        return data, Jawaban("{}", "pemeriksa-uji", "anthropic", data=data, token_masuk=1, token_keluar=1)
    monkeypatch.setattr("newmotion.application.pemeriksa_naskah.periksa", periksa_palsu)

    def verifikasi_palsu(n, *, quran=None):
        hasil = copy.deepcopy(n)
        for d in hasil.get("dalil", []):
            d.update(status="terverifikasi", diverifikasi_oleh="fixture-uji")
        return hasil, ["fixture"]
    monkeypatch.setattr("newmotion.paket_genre.kisah_islami.dalil.verifikasi.verifikasi", verifikasi_palsu)

    status = A.proses("uji-firaun", "ide", folder=tmp_path / "antrean", kirim_tg=False)
    tersimpan = json.loads((antrean / "naskah.json").read_text(encoding="utf-8"))
    assert panggilan_penulis == ["ide", "revisi"]
    assert "Saat tenggelam" in tersimpan["beat"][0]["narasi"]
    assert status["pemeriksaan_naskah"]["temuan"] == []
    assert status["pemeriksaan_naskah_ringkas"] == "tidak ada temuan"
    assert status["pemeriksaan_naskah_ai"]["tahap"] == "periksa_naskah"

def test_usulan_yunus_92_harus_lolos_verifikasi_resmi_sebelum_dipakai():
    from types import SimpleNamespace
    from newmotion.paket_genre.kisah_islami.dalil.verifikasi import verifikasi

    class QuranPalsu:
        def ayat(self, surah, ayat):
            assert (surah, ayat) == (10, 92)
            return SimpleNamespace(
                nama_surah="Yunus", ar="teks arab sumber",
                terjemah="Jasad Firaun diselamatkan sebagai tanda bagi manusia.",
                sumber_terjemah="terjemahan uji", tautan="https://contoh.invalid/10/92",
                kata=[],
            )

    calon = {"dalil": [{
        "id": "yunus92_usulan", "jenis": "quran", "label": "QS Yunus 92",
        "surah": 10, "ayat": "92", "alasan": "Fakta penutup yang kuat",
    }]}
    hasil_tanpa_klien, _ = verifikasi(calon, quran=None)
    assert hasil_tanpa_klien["dalil"][0].get("status") != "terverifikasi"
    hasil, _ = verifikasi(calon, quran=QuranPalsu())
    assert hasil["dalil"][0]["status"] == "terverifikasi"
    assert hasil["dalil"][0]["diverifikasi_oleh"].startswith("sutradara.dalil")
