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



def test_metadata_genre_dan_konteks_dipertahankan_sampai_kontrak_adegan():
    naskah = {
        "judul": "Komedi berlatar kehidupan sahabat",
        "genre": "komedi",
        "konteks_konten": "islami",
        "dalil": [],
        "beat": [{"narasi": "Sahabat Abu Bakar tersenyum.", "kata_kunci": ["percakapan"]}],
    }
    hasil = naskah_untuk_pengarah(naskah)
    assert hasil["genre"] == "komedi"
    assert hasil["konteks_konten"] == "islami"


def test_konteks_umum_tidak_diubah_menjadi_islami():
    naskah = {
        "judul": "Komedi umum",
        "genre": "komedi",
        "konteks_konten": "umum",
        "dalil": [],
        "beat": [{"narasi": "Dua teman terlambat datang.", "kata_kunci": ["teman"]}],
    }
    hasil = naskah_untuk_pengarah(naskah)
    assert hasil["genre"] == "komedi"
    assert hasil["konteks_konten"] == "umum"


def test_konteks_ambigu_diblokir_sebelum_pengarah():
    import pytest
    naskah = {
        "judul": "Komedi",
        "genre": "komedi",
        "dalil": [],
        "beat": [{"narasi": "Dua teman bercanda.", "kata_kunci": ["teman"]}],
    }
    with pytest.raises(ValueError, match="belum cukup jelas"):
        naskah_untuk_pengarah(naskah)


def test_peran_dialog_dan_identitas_beat_diteruskan_ke_pengarah():
    naskah = {
        "judul": "Penolong di jembatan",
        "dalil": [],
        "beat": [
            {
                "id": "awal",
                "narasi": "Seorang pengendara kehilangan keseimbangan.",
                "peran": ["Pengendara", "Penolong"],
                "dialog": [],
            },
            {
                "id": "pertolongan",
                "narasi": "Penolong menghampiri pengendara.",
                "peran": ["Penolong", "Pengendara"],
                "dialog": [
                    {"pembicara": "Penolong", "ucapan": "Pegang tangan saya.", "penjawab": "Pengendara"}
                ],
            },
        ],
    }

    hasil = naskah_untuk_pengarah(naskah)

    awal, pertolongan = hasil["adegan"]
    assert awal["id"] == "awal"
    assert pertolongan["id"] == "pertolongan"
    assert awal["peran"] == ["Pengendara", "Penolong"]
    assert pertolongan["dialog"] == naskah["beat"][1]["dialog"]
    assert awal["tokoh_ids"][1] == pertolongan["tokoh_ids"][0]
    assert awal["tokoh_ids"][0] == pertolongan["tokoh_ids"][1]
    assert {tokoh["nama"] for tokoh in hasil["tokoh"]} == {"Pengendara", "Penolong"}


def test_identitas_tokoh_stabil_meski_penulisan_spasi_dan_huruf_berbeda():
    naskah = {
        "judul": "Identitas",
        "dalil": [],
        "beat": [
            {"narasi": "Tokoh hadir.", "peran": ["  Sahabat   Abu Bakar "]},
            {"narasi": "Tokoh berbicara.", "peran": ["sahabat abu bakar"]},
        ],
    }

    hasil = naskah_untuk_pengarah(naskah)

    assert hasil["adegan"][0]["tokoh_ids"] == hasil["adegan"][1]["tokoh_ids"]
    assert len(hasil["tokoh"]) == 1


def test_data_peristiwa_eksplisit_diteruskan_tanpa_ditebak():
    peristiwa = [{
        "id": "peristiwa-1",
        "aktor": "Penolong",
        "aksi": "menghampiri",
        "sasaran": "Pengendara",
        "tujuan": "menolong",
    }]
    naskah = {
        "judul": "Peristiwa",
        "dalil": [],
        "beat": [{"narasi": "Penolong menghampiri pengendara.", "peristiwa": peristiwa}],
    }

    hasil = naskah_untuk_pengarah(naskah)

    assert hasil["adegan"][0]["peristiwa"] == peristiwa
    assert hasil["adegan"][0]["peran"] == []
    assert hasil["tokoh"] == []


def test_id_beat_duplikat_ditolak():
    import pytest

    naskah = {
        "judul": "ID ganda",
        "dalil": [],
        "beat": [
            {"id": "sama", "narasi": "Adegan pertama."},
            {"id": "sama", "narasi": "Adegan kedua."},
        ],
    }

    with pytest.raises(ValueError, match="digunakan lebih dari sekali"):
        naskah_untuk_pengarah(naskah)


def test_dialog_dengan_bentuk_tidak_valid_ditolak():
    import pytest

    naskah = {
        "judul": "Dialog salah",
        "dalil": [],
        "beat": [{"narasi": "Adegan.", "dialog": "bukan daftar"}],
    }

    with pytest.raises(ValueError, match="Dialog pada beat"):
        naskah_untuk_pengarah(naskah)

def test_metadata_tokoh_eksplisit_dipertahankan_ke_kontrak_semantik():
    naskah = {
        "judul": "Tokoh dengan profil",
        "dalil": [],
        "tokoh": [{
            "id": "pengendara-01",
            "nama": "Pengendara",
            "kategori": "tokoh_umum",
            "deskripsi_visual": "Pria dewasa memakai jaket biru dan helm hitam.",
            "tampil": "tubuh",
        }],
        "beat": [{
            "narasi": "Pengendara melintasi jembatan.",
            "peran": [" pengendara "],
        }],
    }

    hasil = naskah_untuk_pengarah(naskah)

    assert hasil["tokoh"] == [{
        "id": "pengendara-01",
        "nama": "Pengendara",
        "kategori": "tokoh_umum",
        "deskripsi_visual": "Pria dewasa memakai jaket biru dan helm hitam.",
        "tampil": "tubuh",
    }]
    assert hasil["adegan"][0]["tokoh_ids"] == ["pengendara-01"]


def test_tokoh_eksplisit_tanpa_id_mendapat_id_deterministik():
    naskah = {
        "judul": "ID tokoh",
        "dalil": [],
        "tokoh": [{"nama": "Penolong", "deskripsi_visual": "Kemeja hijau."}],
        "beat": [{"narasi": "Penolong datang.", "peran": ["Penolong"]}],
    }

    pertama = naskah_untuk_pengarah(naskah)
    kedua = naskah_untuk_pengarah(naskah)

    assert pertama["tokoh"][0]["id"].startswith("tokoh-")
    assert pertama["tokoh"][0]["id"] == kedua["tokoh"][0]["id"]
    assert pertama["adegan"][0]["tokoh_ids"] == [pertama["tokoh"][0]["id"]]


def test_roster_tokoh_menolak_nama_ambigu():
    import pytest

    naskah = {
        "judul": "Nama ambigu",
        "dalil": [],
        "tokoh": [
            {"id": "a", "nama": "Penolong"},
            {"id": "b", "nama": " penolong "},
        ],
        "beat": [{"narasi": "Penolong datang."}],
    }

    with pytest.raises(ValueError, match="ambigu"):
        naskah_untuk_pengarah(naskah)


def test_roster_tokoh_menolak_id_ganda():
    import pytest

    naskah = {
        "judul": "ID ganda",
        "dalil": [],
        "tokoh": [
            {"id": "sama", "nama": "Penolong"},
            {"id": "sama", "nama": "Pengendara"},
        ],
        "beat": [{"narasi": "Mereka bertemu."}],
    }

    with pytest.raises(ValueError, match="digunakan lebih dari sekali"):
        naskah_untuk_pengarah(naskah)

