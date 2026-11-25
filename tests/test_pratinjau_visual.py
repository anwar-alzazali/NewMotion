from newmotion.application.pratinjau_visual import naskah_untuk_pengarah


def test_beat_diubah_menjadi_adegan_tanpa_mengubah_narasi():
    naskah = {
        "judul": "Cerita",
        "dalil": [],
        "beat": [
            {"narasi": "Tokoh berjalan menuju jembatan.", "kata_kunci": ["jembatan"]},
            {"narasi": "Ia menolong pengendara yang tergelincir.", "kata_kunci": ["menolong"]},
        ],
    }
    hasil = naskah_untuk_pengarah(naskah)
    assert hasil["genre"] == "kisah_islami"
    assert hasil["konteks_konten"] == "islami"
    assert [a["teks"] for a in hasil["adegan"]] == [b["narasi"] for b in naskah["beat"]]
    assert hasil["adegan"][1]["nama"] == "adegan_2"


def test_hanya_dalil_quran_terverifikasi_dan_dipakai_beat_dimasukkan():
    naskah = {
        "judul": "Hud",
        "dalil": [
            {"id": "hud50", "jenis": "quran", "surah": 11, "ayat": "50", "status": "terverifikasi"},
            {"id": "bukhari1", "jenis": "hadis", "kitab": "bukhari", "nomor": "1", "status": "terverifikasi"},
            {"id": "hud51", "jenis": "quran", "surah": 11, "ayat": "51", "status": "gagal"},
        ],
        "beat": [{"narasi": "Nabi Hud menyeru kaumnya.", "dalil": ["hud50", "bukhari1", "hud51"]}],
    }
    hasil = naskah_untuk_pengarah(naskah)
    assert hasil["dalil_dipakai"] == [{"surah": 11, "ayat": "50", "di_adegan": "adegan_1"}]


def test_pratinjau_menolak_naskah_tanpa_beat():
    import pytest
    with pytest.raises(ValueError, match="tidak memiliki beat"):
        naskah_untuk_pengarah({"judul": "Kosong", "beat": []})


def test_pratinjau_diblokir_jika_naskah_belum_disetujui(tmp_path):
    import json
    import pytest
    from newmotion.application.pratinjau_visual import buat_pratinjau

    antrean = tmp_path / "cerita"
    antrean.mkdir()
    (antrean / "naskah.json").write_text(json.dumps({"judul": "Cerita", "beat": []}), encoding="utf-8")
    (antrean / "status.json").write_text(json.dumps({"tahap": {"tinjau": "jalan"}}), encoding="utf-8")
    with pytest.raises(ValueError, match="hanya boleh dibuat setelah naskah disetujui"):
        buat_pratinjau("cerita", folder=tmp_path)


def test_pratinjau_tidak_dirender_ulang_saat_sedang_ditinjau(tmp_path):
    import json
    import pytest
    from newmotion.application.pratinjau_visual import buat_pratinjau

    antrean = tmp_path / "cerita"
    antrean.mkdir()
    (antrean / "naskah.json").write_text(json.dumps({"judul": "Cerita", "beat": []}), encoding="utf-8")
    (antrean / "status.json").write_text(
        json.dumps({"tahap": {"tinjau": "selesai", "tinjau_visual": "jalan"}}), encoding="utf-8"
    )
    with pytest.raises(ValueError, match="sudah dibuat"):
        buat_pratinjau("cerita", folder=tmp_path)
