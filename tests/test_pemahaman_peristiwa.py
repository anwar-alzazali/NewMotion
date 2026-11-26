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

    assert hasil["status"] == "siap"
    assert "sasaran_benda_id" not in hasil["peristiwa"][0]


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
    motor = next(
        item for item in spek["cerita"]["shot"][0]["benda"]
        if item["id"] == "motor-01"
    )

    assert genre == "cerita_umum"
    assert event["sasaran_benda_id"] == "motor-01"
    assert motor["jenis"] == "motor"
    assert motor["x"] == 520
