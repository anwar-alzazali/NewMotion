"""Uji pengurai peristiwa dari narasi, bukan dari fixture peristiwa siap pakai."""
import json

from newmotion.application.pratinjau_visual import naskah_untuk_pengarah
from newmotion.paket_genre.cerita_umum.pemahaman_peristiwa import uraikan_peristiwa


def test_aksi_aktif_menghasilkan_aktor_sasaran_dan_bukti():
    hasil = uraikan_peristiwa(
        "Penolong menolong Pengendara.",
        ["Penolong", "Pengendara"],
    )

    assert hasil["status"] == "siap"
    assert hasil["peristiwa"] == [{
        "id": "peristiwa-001",
        "aktor": "Penolong",
        "aksi": "menolong",
        "bukti_teks": "Penolong menolong Pengendara.",
        "hubungan_temporal": "tidak_dinyatakan",
        "sasaran": "Pengendara",
        "urutan": 1,
    }]


def test_kalimat_pasif_mengambil_pelaku_dari_frasa_oleh():
    hasil = uraikan_peristiwa(
        "Pengendara ditolong oleh Penolong.",
        ["Penolong", "Pengendara"],
    )

    assert len(hasil["peristiwa"]) == 1
    assert hasil["peristiwa"][0]["aktor"] == "Penolong"
    assert hasil["peristiwa"][0]["sasaran"] == "Pengendara"


def test_aksi_berurutan_mewarisi_subjek_yang_dihilangkan():
    hasil = uraikan_peristiwa(
        "Penolong berjalan lalu menolong Pengendara.",
        ["Penolong", "Pengendara"],
    )

    assert [item["aksi"] for item in hasil["peristiwa"]] == ["berjalan", "menolong"]
    assert [item["aktor"] for item in hasil["peristiwa"]] == ["Penolong", "Penolong"]
    assert hasil["peristiwa"][1]["hubungan_temporal"] == "setelah"


def test_aksi_simultan_mempertahankan_aktor_masing_masing():
    hasil = uraikan_peristiwa(
        "Penolong berjalan dan Pengendara menunggu.",
        ["Penolong", "Pengendara"],
    )

    assert [item["aktor"] for item in hasil["peristiwa"]] == ["Penolong", "Pengendara"]
    assert all(item["hubungan_temporal"] == "simultan" for item in hasil["peristiwa"])


def test_negasi_tidak_diubah_menjadi_aksi_visual():
    hasil = uraikan_peristiwa(
        "Penolong tidak menolong Pengendara.",
        ["Penolong", "Pengendara"],
    )

    assert hasil["peristiwa"] == []
    assert hasil["status"] == "perlu_pemeriksaan"
    assert hasil["diagnostik"][0]["kode"] == "klausa_negatif_tidak_dijadikan_aksi"


def test_kalimat_pasif_tanpa_pelaku_ditandai_tidak_ditebak():
    hasil = uraikan_peristiwa(
        "Pengendara ditolong.",
        ["Penolong", "Pengendara"],
    )

    assert hasil["peristiwa"] == []
    assert hasil["diagnostik"][0]["kode"] == "kalimat_pasif_tanpa_pelaku_eksplisit"


def test_integrasi_menghasilkan_peristiwa_dari_beat_tanpa_field_peristiwa():
    naskah = {
        "judul": "Pertolongan",
        "genre": "cerita_umum",
        "konteks_konten": "umum",
        "dalil": [],
        "beat": [{
            "id": "beat-pertolongan",
            "narasi": "Penolong berjalan lalu menolong Pengendara.",
            "peran": ["Penolong", "Pengendara"],
        }],
    }

    sumber = naskah_untuk_pengarah(naskah)

    adegan = sumber["adegan"][0]
    assert [item["aksi"] for item in adegan["peristiwa"]] == ["berjalan", "menolong"]
    assert adegan["peristiwa"][1]["aktor"] == "Penolong"
    assert adegan["diagnostik_pemahaman"]["status"] == "siap"
    assert "peristiwa" not in naskah["beat"][0]


def test_pengurai_tidak_diterapkan_ke_kisah_islami():
    naskah = {
        "judul": "Cerita Islami",
        "dalil": [],
        "beat": [{
            "narasi": "Penolong menolong Pengendara.",
            "peran": ["Penolong", "Pengendara"],
        }],
    }

    sumber = naskah_untuk_pengarah(naskah)

    assert sumber["genre"] == "kisah_islami"
    assert "peristiwa" not in sumber["adegan"][0]
    assert "diagnostik_pemahaman" not in sumber["adegan"][0]


def test_keluaran_pengurai_dapat_diserialisasi_json_dan_deterministik():
    teks = "Penolong berjalan lalu menolong Pengendara."
    pertama = uraikan_peristiwa(teks, ["Penolong", "Pengendara"])
    kedua = uraikan_peristiwa(teks, ["Penolong", "Pengendara"])

    assert pertama == kedua
    assert json.loads(json.dumps(pertama, ensure_ascii=False)) == pertama

def test_sutradara_menghasilkan_spek_json_dari_narasi_biasa():
    from newmotion.application.pengarah_inti import arahkan_naskah

    naskah = {
        "judul": "Pertolongan di jalan",
        "genre": "cerita_umum",
        "konteks_konten": "umum",
        "dalil": [],
        "beat": [{
            "id": "jalan-01",
            "narasi": "Penolong berjalan lalu menolong Pengendara.",
            "peran": ["Penolong", "Pengendara"],
        }],
    }
    sumber = naskah_untuk_pengarah(naskah)
    spek, genre, jumlah_shot = arahkan_naskah(
        sumber, genre_pilihan="cerita_umum"
    )
    hasil = json.loads(json.dumps(spek, ensure_ascii=False))
    peristiwa = hasil["rencana_cerita"]["adegan"][0]["peristiwa"]

    assert genre == "cerita_umum"
    # Dua peristiwa berurutan harus menjadi dua tahap/shot renderer.
    assert jumlah_shot == 2
    assert [item["aksi"] for item in peristiwa] == ["berjalan", "menolong"]
    assert peristiwa[0]["aktor_id"] == peristiwa[1]["aktor_id"]
    assert peristiwa[1]["sasaran_tokoh_id"] is not None
    assert all(item["bukti_teks"] in naskah["beat"][0]["narasi"] for item in peristiwa)
    assert [
        id_peristiwa
        for shot in hasil["cerita"]["shot"]
        for id_peristiwa in shot["pengarahan"]["peristiwa_ids"]
    ] == [item["id"] for item in peristiwa]
    assert hasil["rencana_cerita"]["adegan"][0]["diagnostik_pemahaman"]["status"] == "siap"


def test_aksi_simultan_dapat_mewarisi_subjek_yang_dihilangkan():
    hasil = uraikan_peristiwa(
        "Penolong berjalan dan menolong Pengendara.",
        ["Penolong", "Pengendara"],
    )

    assert [item["aksi"] for item in hasil["peristiwa"]] == ["berjalan", "menolong"]
    assert [item["aktor"] for item in hasil["peristiwa"]] == ["Penolong", "Penolong"]
    assert all(item["hubungan_temporal"] == "simultan" for item in hasil["peristiwa"])
    assert hasil["status"] == "siap"


def test_sasaran_benda_dipetakan_hanya_dari_roster_eksplisit():
    benda = [{
        "id": "motor-01",
        "nama": "motor",
        "jenis_renderer": "motor",
        "posisi": {"x": 520, "y": 1500, "s": 0.8},
    }]
    hasil = uraikan_peristiwa("Pengendara menaiki motor.", ["Pengendara"], benda)

    assert hasil["status"] == "siap"
    assert hasil["peristiwa"][0]["aktor"] == "Pengendara"
    assert hasil["peristiwa"][0]["aksi"] == "menaiki"
    assert hasil["peristiwa"][0]["sasaran_benda_id"] == "motor-01"


def test_benda_yang_tidak_terdaftar_tidak_ditebak_dari_kata_narasi():
    hasil = uraikan_peristiwa("Pengendara menaiki motor.", ["Pengendara"])

    assert hasil["status"] == "sebagian"
    assert "sasaran_benda_id" not in hasil["peristiwa"][0]
    assert hasil["diagnostik"][0]["kode"] == "sasaran_benda_belum_terpetakan"


def test_sasaran_benda_ambigu_ditandai_tanpa_memilih_salah_satu():
    benda = [
        {"id": "motor-01", "nama": "motor"},
        {"id": "motor-02", "nama": "motor"},
    ]
    hasil = uraikan_peristiwa("Pengendara menaiki motor.", ["Pengendara"], benda)

    assert hasil["peristiwa"] == []
    assert hasil["diagnostik"][0]["kode"] == "sasaran_benda_ambigu"


def test_narasi_biasa_menghasilkan_tautan_benda_dan_objek_renderer():
    from newmotion.application.pengarah_inti import arahkan_naskah

    naskah = {
        "judul": "Pengendara menaiki motor",
        "genre": "cerita_umum",
        "konteks_konten": "umum",
        "dalil": [],
        "benda": [{
            "id": "motor-01",
            "nama": "motor",
            "jenis_renderer": "motor",
            "posisi": {"x": 520, "y": 1500, "s": 0.8},
        }],
        "beat": [{
            "id": "beat-motor",
            "narasi": "Pengendara menaiki motor.",
            "peran": ["Pengendara"],
        }],
    }
    sumber = naskah_untuk_pengarah(naskah)
    spek, genre, _ = arahkan_naskah(sumber, genre_pilihan="cerita_umum")
    event = spek["rencana_cerita"]["adegan"][0]["peristiwa"][0]
    event_blocking = spek["rencana_blocking"]["peristiwa"][0]
    motor = next(
        item for item in spek["cerita"]["shot"][0]["benda"]
        if item["id"] == "motor-01"
    )

    assert genre == "cerita_umum"
    assert event["sasaran_benda_id"] == "motor-01"
    assert event_blocking["sasaran_benda"] == "motor"
    assert event_blocking["sasaran_benda_id"] == "motor-01"
    assert motor["jenis"] == "motor"
    assert motor["x"] == 520
    assert spek["cerita"]["shot"][0]["boneka"][0]["kendaraan_id"] == "motor-01"


def test_benda_tetap_divisualkan_jika_aksi_tokoh_belum_didukung():
    from newmotion.application.pengarah_inti import arahkan_naskah

    naskah = {
        "judul": "Pengendara mengamati motor",
        "genre": "cerita_umum",
        "konteks_konten": "umum",
        "dalil": [],
        "benda": [{
            "id": "motor-01",
            "nama": "motor",
            "jenis_renderer": "motor",
            "posisi": {"x": 520, "y": 1500, "s": 0.8},
        }],
        "beat": [{
            "id": "beat-amati",
            "narasi": "Pengendara mengamati motor.",
            "peran": ["Pengendara"],
        }],
    }
    sumber = naskah_untuk_pengarah(naskah)
    spek, _, _ = arahkan_naskah(sumber, genre_pilihan="cerita_umum")

    assert spek["rencana_visual_tokoh"]["diagnostik"][0]["kode"] == "aksi_visual_belum_didukung"
    assert spek["cerita"]["shot"][0]["benda"][0]["id"] == "motor-01"



def test_parser_menghasilkan_keadaan_akhir_tanpa_mengarang_keadaan_awal():
    hasil = uraikan_peristiwa(
        "Pengendara jatuh lalu berdiri.",
        ["Pengendara"],
    )

    assert [item["aksi"] for item in hasil["peristiwa"]] == ["jatuh", "berdiri"]
    perubahan = [item["perubahan_keadaan"] for item in hasil["peristiwa"]]
    assert perubahan == [
        {"entitas": "Pengendara", "menjadi": "terjatuh"},
        {"entitas": "Pengendara", "menjadi": "berdiri"},
    ]
    assert all("dari" not in item for item in perubahan)


def test_tergelincir_tidak_diartikan_otomatis_sebagai_jatuh():
    hasil = uraikan_peristiwa("Pengendara tergelincir.", ["Pengendara"])

    assert hasil["peristiwa"][0]["aksi"] == "tergelincir"
    assert "perubahan_keadaan" not in hasil["peristiwa"][0]


def test_sutradara_menghubungkan_transisi_keadaan_ke_id_tokoh():
    from newmotion.application.pengarah_inti import arahkan_naskah

    naskah = {
        "judul": "Pengendara jatuh lalu berdiri",
        "genre": "cerita_umum",
        "konteks_konten": "umum",
        "dalil": [],
        "beat": [{
            "id": "beat-keadaan",
            "narasi": "Pengendara jatuh lalu berdiri.",
            "peran": ["Pengendara"],
        }],
    }
    sumber = naskah_untuk_pengarah(naskah)
    spek, _, _ = arahkan_naskah(sumber, genre_pilihan="cerita_umum")
    tokoh_id = spek["rencana_cerita"]["tokoh"][0]["id"]
    peristiwa = spek["rencana_cerita"]["adegan"][0]["peristiwa"]
    transisi = spek["rencana_blocking"]["transisi_keadaan"]

    assert [item["perubahan_keadaan"]["entitas_id"] for item in peristiwa] == [
        tokoh_id, tokoh_id
    ]
    assert transisi[0]["dari"] is None
    assert transisi[0]["menjadi"] == "terjatuh"
    assert transisi[1]["dari"] == "terjatuh"
    assert transisi[1]["menjadi"] == "berdiri"
    assert spek["rencana_blocking"]["keadaan_akhir"][tokoh_id] == "berdiri"



def test_transisi_keadaan_benda_hanya_dari_peristiwa_eksplisit():
    from newmotion.application.pengarah_inti import arahkan_naskah

    naskah = {
        "judul": "Motor mulai bergerak",
        "genre": "cerita_umum",
        "konteks_konten": "umum",
        "tokoh": [{"id": "pengendara-01", "nama": "Pengendara"}],
        "benda": [{
            "id": "motor-01",
            "nama": "motor",
            "alias": ["sepeda motor"],
            "jenis_renderer": "motor",
            "posisi": {"x": 520, "y": 1500, "s": 0.8},
        }],
        "adegan": [{
            "id": "beat-motor-bergerak",
            "teks": "Pengendara mengamati motor yang mulai bergerak.",
            "peran": ["Pengendara"],
            "tokoh_ids": ["pengendara-01"],
            "peristiwa": [{
                "id": "motor-bergerak-01",
                "aktor": "Pengendara",
                "aksi": "mengamati",
                "bukti_teks": "Pengendara mengamati motor yang mulai bergerak",
                "perubahan_keadaan": {
                    "entitas": "sepeda motor",
                    "menjadi": "bergerak",
                },
            }],
        }],
    }
    spek, _, _ = arahkan_naskah(naskah, genre_pilihan="cerita_umum")

    perubahan = spek["rencana_cerita"]["adegan"][0]["peristiwa"][0]["perubahan_keadaan"]
    assert perubahan["entitas_id"] == "motor-01"
    assert spek["rencana_blocking"]["transisi_keadaan"][0]["entitas_id"] == "motor-01"
    assert spek["rencana_blocking"]["keadaan_akhir"]["motor-01"] == "bergerak"


def test_nama_entitas_keadaan_yang_bertabrakan_ditandai_ambigu():
    from newmotion.application.pengarah_inti import arahkan_naskah

    naskah = {
        "judul": "Nama entitas ambigu",
        "genre": "cerita_umum",
        "konteks_konten": "umum",
        "tokoh": [{"id": "motor-tokoh", "nama": "Motor"}],
        "benda": [{
            "id": "motor-benda",
            "nama": "Motor",
            "jenis_renderer": "motor",
            "posisi": {"x": 520, "y": 1500, "s": 0.8},
        }],
        "adegan": [{
            "id": "beat-ambigu",
            "teks": "Motor bergerak.",
            "peran": ["Motor"],
            "tokoh_ids": ["motor-tokoh"],
            "peristiwa": [{
                "id": "event-ambigu",
                "aktor": "Motor",
                "aksi": "mengamati",
                "bukti_teks": "Motor bergerak",
                "perubahan_keadaan": {
                    "entitas": "Motor",
                    "menjadi": "bergerak",
                },
            }],
        }],
    }
    spek, _, _ = arahkan_naskah(naskah, genre_pilihan="cerita_umum")

    kode = {item["kode"] for item in spek["rencana_cerita"]["diagnostik"]}
    assert "entitas_perubahan_keadaan_ambigu" in kode
    assert "entitas_id" not in spek["rencana_cerita"]["adegan"][0]["peristiwa"][0]["perubahan_keadaan"]



def test_tujuan_aksi_dipisahkan_dari_aksi_yang_benar_benar_terjadi():
    hasil = uraikan_peristiwa(
        "Penolong berjalan untuk menolong Pengendara.",
        ["Penolong", "Pengendara"],
    )

    assert hasil["status"] == "siap"
    assert len(hasil["peristiwa"]) == 1
    peristiwa = hasil["peristiwa"][0]
    assert peristiwa["aksi"] == "berjalan"
    assert peristiwa["tujuan"] == {
        "aksi": "menolong",
        "sasaran": "Pengendara",
    }
    assert peristiwa["bukti_teks"] == "Penolong berjalan untuk menolong Pengendara"
    assert "menolong" != peristiwa["aksi"]


def test_tujuan_aksi_belum_dikenali_tidak_dianggap_sasaran_benda():
    benda = [{
        "id": "motor-01",
        "nama": "motor",
        "jenis_renderer": "motor",
    }]
    hasil = uraikan_peristiwa(
        "Penolong berjalan untuk menjaga motor.",
        ["Penolong"],
        benda,
    )
    # "menjaga" belum termasuk kamus aksi; frasa ini tidak boleh ditebak sebagai tujuan.
    assert hasil["peristiwa"][0]["aksi"] == "berjalan"
    assert "tujuan" not in hasil["peristiwa"][0]
    assert "sasaran_benda_id" not in hasil["peristiwa"][0]


def test_tujuan_aksi_diteruskan_ke_rencana_semantik_dan_blocking():
    from newmotion.application.pengarah_inti import arahkan_naskah

    naskah = {
        "judul": "Penolong berjalan untuk menolong Pengendara",
        "genre": "cerita_umum",
        "konteks_konten": "umum",
        "dalil": [],
        "beat": [{
            "id": "beat-tujuan",
            "narasi": "Penolong berjalan untuk menolong Pengendara.",
            "peran": ["Penolong", "Pengendara"],
        }],
    }
    sumber = naskah_untuk_pengarah(naskah)
    spek, _, _ = arahkan_naskah(sumber, genre_pilihan="cerita_umum")

    peristiwa = spek["rencana_cerita"]["adegan"][0]["peristiwa"][0]
    peristiwa_blocking = spek["rencana_blocking"]["peristiwa"][0]
    assert peristiwa["aksi"] == "berjalan"
    assert peristiwa["tujuan"] == {
        "aksi": "menolong",
        "sasaran": "Pengendara",
    }
    assert peristiwa_blocking["tujuan"] == peristiwa["tujuan"]



def test_tujuan_aksi_pada_kalimat_pasif_tetap_mempertahankan_pelaku():
    hasil = uraikan_peristiwa(
        "Pengendara ditolong oleh Penolong untuk berdiri.",
        ["Pengendara", "Penolong"],
    )

    assert hasil["status"] == "siap"
    assert len(hasil["peristiwa"]) == 1
    peristiwa = hasil["peristiwa"][0]
    assert peristiwa["aktor"] == "Penolong"
    assert peristiwa["sasaran"] == "Pengendara"
    assert peristiwa["aksi"] == "menolong"
    assert peristiwa["tujuan"] == {"aksi": "berdiri"}
