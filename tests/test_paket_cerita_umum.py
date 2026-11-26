from newmotion.application.pengarah_inti import arahkan_naskah
from newmotion.domain.genre import ambil
from newmotion.adapter_visual_tokoh import terapkan_rencana_visual_tokoh


def _naskah():
    return {
        "genre": "cerita_umum", "konteks_konten": "umum",
        "judul": "Penolong di jalan",
        "tokoh": [
            {"id": "penolong", "nama": "Penolong", "kategori": "tokoh_umum"},
            {"id": "pengendara", "nama": "Pengendara", "kategori": "tokoh_umum"},
        ],
        "adegan": [{
            "id": "beat-001", "nama": "Motor tergelincir",
            "teks": "Pengendara tergelincir dan penolong berjalan mendekat.",
            "peran": ["Penolong", "Pengendara"],
            "tokoh_ids": ["penolong", "pengendara"],
            "peristiwa": [
                {"id": "e1", "aktor": "Pengendara", "aksi": "tergelincir", "sasaran": "motor"},
                {"id": "e2", "aktor": "Penolong", "aksi": "berjalan_menolong", "sasaran": "Pengendara"},
            ],
        }],
    }


def test_paket_cerita_umum_membuat_lintasan_penolong_dan_menautkan_sasaran():
    spek, nama, jumlah = arahkan_naskah(_naskah())
    assert nama == "cerita_umum"
    assert jumlah == 1
    assert spek["rencana_visual_tokoh"]["status"] == "siap_diterjemahkan"
    assert spek["_rencana_visual_tokoh_diterapkan"] is True
    assert len(spek["cerita"]["shot"][0]["boneka"]) == 2
    assert any(x["jenis"] == "motor" for x in spek["cerita"]["shot"][0]["benda"])
    arahan = spek["rencana_visual_tokoh"]["shot"][0]["tokoh"][0]
    assert arahan["tokoh_id"] == "penolong"
    assert arahan["aksi"] == "jalan"
    assert arahan["sasaran_tokoh_id"] == "pengendara"
    assert arahan["x"][0][1] != arahan["x"][-1][1]
    # Penolong tiba di sisi posisi akhir pengendara setelah tergelincir,
    # bukan berhenti di posisi awal pengendara sebelum jatuh.
    arahan_shot = spek["rencana_visual_tokoh"]["shot"][0]["tokoh"]
    penolong = next(x for x in arahan_shot if x["tokoh_id"] == "penolong")
    pengendara = next(x for x in arahan_shot if x["tokoh_id"] == "pengendara")
    assert pengendara["x"][-1][1] == 650
    assert penolong["x"][0][1] == 100
    assert penolong["x"][-1][1] == 430
    assert penolong["x"][-1][1] - penolong["x"][0][1] >= 100
    assert penolong["y"][-1][1] == 1620
    assert pengendara["y"][-1][1] == 1700
    assert pengendara["x"][-1][1] - penolong["x"][-1][1] >= 200
    assert pengendara["y"][-1][1] - penolong["y"][-1][1] >= 80


def test_posisi_penolong_tetap_mengacu_posisi_akhir_meski_urutan_peristiwa_berbeda():
    naskah = _naskah()
    naskah["adegan"][0]["peristiwa"].reverse()
    spek, _, _ = arahkan_naskah(naskah)
    arahan = {
        item["tokoh_id"]: item
        for item in spek["rencana_visual_tokoh"]["shot"][0]["tokoh"]
    }
    assert arahan["pengendara"]["x"][-1][1] == 650
    assert arahan["penolong"]["x"][-1][1] == 430
    assert arahan["penolong"]["y"][-1][1] == 1620


def test_paket_cerita_umum_tidak_mengambil_alih_kebijakan_kisah_islami():
    assert ambil("cerita_umum").pengarah_tokoh_visual is not None
    paket_islami = ambil("kisah_islami")
    assert paket_islami.pengarah_tokoh_visual is None


def test_adapter_meneruskan_motor_jadwal_tergelincir_dan_aksi_menolong():
    spek, _, _ = arahkan_naskah(_naskah())
    # JSON sudah lengkap saat keluar dari sutradara; pemanggilan kedua aman.
    assert terapkan_rencana_visual_tokoh(spek) == []
    shot = spek["cerita"]["shot"][0]
    motor = next(item for item in shot["benda"] if item["jenis"] == "motor")
    assert motor["id"] == "motor-beat-001"
    penolong = next(item for item in shot["boneka"] if item["aktor_id"] == "penolong")
    pengendara = next(item for item in shot["boneka"] if item["aktor_id"] == "pengendara")
    assert penolong["jalan"] == 1.0
    assert penolong["sasaran_id"] == 1
    assert penolong["karakter"]["gerak"] == [[0, "jalan"], [2.5, "menolong"]]
    assert pengendara["kendaraan_id"] == motor["id"]
    assert motor["x"][0][1] == pengendara["x"][0][1]
    assert motor["miring"][-1][1] == 28
    assert pengendara["lepas_kendaraan_at"] == 0.9
    assert pengendara["karakter"]["gerak"] == [[0, "mengendarai_motor"], [0.65, "tergelincir"]]


def test_paket_cerita_umum_lolos_integrasi_html_tanpa_render():
    import sys
    from pathlib import Path

    akar = Path(__file__).parents[1]
    jalur_mesin = str(akar / "mesin-video")
    if jalur_mesin not in sys.path:
        sys.path.insert(0, jalur_mesin)
    import papan_buat

    spek, _, _ = arahkan_naskah(_naskah())
    papan_buat.jaga_spek(spek)
    html = papan_buat.buat_html(spek, dasar=str(akar), sudah_dijaga=True)

    assert 'motor-beat-001' in html
    assert 'mengendarai_motor' in html
    assert 'tergelincir' in html
    assert 'menolong' in html
    assert '"sasaran_id": 1' in html



def test_posisi_dan_keadaan_tokoh_berlanjut_ke_shot_berikutnya():
    naskah = _naskah()
    naskah["adegan"].append({
        "id": "beat-002", "nama": "Penolong membantu",
        "teks": "Penolong mulai menolong pengendara yang sudah terjatuh.",
        "peran": ["Penolong", "Pengendara"],
        "tokoh_ids": ["penolong", "pengendara"],
        "peristiwa": [
            {"id": "e3", "aktor": "Penolong", "aksi": "menolong", "sasaran": "Pengendara"},
            {"id": "e4", "aktor": "Pengendara", "aksi": "menunggu"},
        ],
    })

    spek, _, jumlah = arahkan_naskah(naskah)
    assert jumlah == 2
    rencana = spek["rencana_visual_tokoh"]["shot"]
    shot_pertama = {x["tokoh_id"]: x for x in rencana[0]["tokoh"]}
    shot_kedua = {x["tokoh_id"]: x for x in rencana[1]["tokoh"]}

    # Penolong tetap di titik kedatangannya; ia tidak berjalan ulang dari tepi layar.
    assert shot_kedua["penolong"]["x"] == shot_pertama["penolong"]["x"][-1][1]
    assert shot_kedua["penolong"]["aksi"] == "menolong"
    assert shot_kedua["penolong"]["pose"] == [[0, "menolong"]]

    # Pengendara tetap di titik akhir tergelincir dan mempertahankan keadaan jatuh.
    assert shot_kedua["pengendara"]["x"] == shot_pertama["pengendara"]["x"][-1][1]
    assert shot_kedua["pengendara"]["y"] == shot_pertama["pengendara"]["y"][-1][1]
    assert shot_kedua["pengendara"]["pose"] == [[0, "tergelincir"]]

    assert terapkan_rencana_visual_tokoh(spek) == []
    hasil_pertama = {x["aktor_id"]: x for x in spek["cerita"]["shot"][0]["boneka"]}
    hasil_kedua = {x["aktor_id"]: x for x in spek["cerita"]["shot"][1]["boneka"]}
    assert hasil_kedua["penolong"]["x"] == hasil_pertama["penolong"]["x"][-1][1]
    assert hasil_kedua["pengendara"]["x"] == hasil_pertama["pengendara"]["x"][-1][1]
    assert hasil_kedua["pengendara"]["y"] == hasil_pertama["pengendara"]["y"][-1][1]
    motor_pertama = next(x for x in spek["cerita"]["shot"][0]["benda"] if x["jenis"] == "motor")
    motor_kedua = next(x for x in spek["cerita"]["shot"][1]["benda"] if x["jenis"] == "motor")
    assert motor_kedua["id"] == motor_pertama["id"]
    assert motor_kedua["x"] == motor_pertama["x"][-1][1]
    assert motor_kedua["y"] == motor_pertama["y"][-1][1]
    assert motor_kedua["miring"] == motor_pertama["miring"][-1][1] == 28


def test_peristiwa_mendapat_id_stabil_dan_tertaut_ke_beat_sumber():
    spek, _, _ = arahkan_naskah(_naskah())
    peristiwa = spek["rencana_cerita"]["adegan"][0]["peristiwa"]
    assert [x["id"] for x in peristiwa] == ["e1", "e2"]
    assert all(x["beat_id"] == "beat-001" for x in peristiwa)
    assert {
        x["id"] for x in spek["rencana_blocking"]["peristiwa"]
    } == {"e1", "e2"}


def test_id_peristiwa_ganda_ditolak_agar_tidak_menimpa_pemetaan():
    import pytest
    from newmotion.application.pengarah_inti import GalatPengarahan

    naskah = _naskah()
    naskah["adegan"].append({
        "id": "beat-002", "teks": "Penolong menunggu.",
        "tokoh_ids": ["penolong"],
        "peristiwa": [{"id": "e1", "aktor": "Penolong", "aksi": "menunggu"}],
    })
    with pytest.raises(GalatPengarahan, match="digunakan lebih dari sekali"):
        arahkan_naskah(naskah)


def test_id_peristiwa_tidak_diberikan_dibuat_deterministik():
    naskah = _naskah()
    naskah["adegan"][0]["peristiwa"][0].pop("id")
    spek, _, _ = arahkan_naskah(naskah)
    peristiwa = spek["rencana_cerita"]["adegan"][0]["peristiwa"][0]
    assert peristiwa["id"] == "beat-001-peristiwa-001"
    assert peristiwa["beat_id"] == "beat-001"


def test_referensi_aktor_dan_sasaran_tokoh_di_luar_roster_didiagnosis():
    naskah = _naskah()
    naskah["adegan"][0]["peristiwa"][0]["aktor_id"] = "tokoh-hilang"
    naskah["adegan"][0]["peristiwa"][1]["sasaran_tokoh_id"] = "tokoh-hilang"
    spek, _, _ = arahkan_naskah(naskah)
    kode = {x["kode"] for x in spek["rencana_cerita"]["diagnostik"]}
    assert "aktor_id_tidak_terdaftar" in kode
    assert "sasaran_tokoh_id_tidak_terdaftar" in kode


def test_bukti_teks_peristiwa_diperiksa_tanpa_memaksa_migrasi_fixture_lama():
    naskah = _naskah()
    naskah["adegan"][0]["peristiwa"][0]["bukti_teks"] = "Pengendara tergelincir"
    naskah["adegan"][0]["peristiwa"][1]["bukti_teks"] = "penolong terbang"
    spek, _, _ = arahkan_naskah(naskah)
    temuan = spek["rencana_cerita"]["diagnostik"]
    assert any(x["kode"] == "bukti_teks_tidak_ditemukan_di_beat" for x in temuan)
    assert not any(
        x.get("peristiwa_id") == "e1" and x["kode"] == "bukti_teks_belum_dicantumkan"
        for x in temuan
    )


def test_transisi_keadaan_dicatat_dari_peristiwa_dan_dibawa_ke_keadaan_akhir():
    naskah = _naskah()
    naskah["adegan"][0]["peristiwa"][0]["perubahan_keadaan"] = {
        "entitas_id": "pengendara", "dari": "mengendarai", "menjadi": "terjatuh",
    }
    naskah["adegan"].append({
        "id": "beat-002", "teks": "Penolong membantu pengendara yang terjatuh.",
        "tokoh_ids": ["penolong", "pengendara"],
        "peristiwa": [{
            "id": "e3", "aktor": "Penolong", "aksi": "menolong",
            "sasaran": "Pengendara",
            "perubahan_keadaan": {
                "entitas_id": "pengendara", "dari": "terjatuh", "menjadi": "ditolong",
            },
        }],
    })
    spek, _, _ = arahkan_naskah(naskah)
    blocking = spek["rencana_blocking"]
    assert [x["peristiwa_id"] for x in blocking["transisi_keadaan"]] == ["e1", "e3"]
    assert blocking["keadaan_akhir"] == {"pengendara": "ditolong"}
    assert blocking["transisi_keadaan"][1]["dari"] == "terjatuh"


def test_transisi_keadaan_yang_tidak_sambung_diberi_diagnostik():
    naskah = _naskah()
    naskah["adegan"][0]["peristiwa"][0]["perubahan_keadaan"] = {
        "entitas_id": "pengendara", "dari": "mengendarai", "menjadi": "terjatuh",
    }
    naskah["adegan"].append({
        "id": "beat-002", "teks": "Pengendara ditolong.",
        "tokoh_ids": ["pengendara"],
        "peristiwa": [{
            "id": "e3", "aktor": "Pengendara", "aksi": "menunggu",
            "perubahan_keadaan": {
                "entitas_id": "pengendara", "dari": "berdiri", "menjadi": "ditolong",
            },
        }],
    })
    spek, _, _ = arahkan_naskah(naskah)
    assert any(
        x["kode"] == "asal_transisi_tidak_cocok_dengan_keadaan_terakhir"
        and x["peristiwa_id"] == "e3"
        for x in spek["rencana_blocking"]["diagnostik"]
    )


def test_perubahan_keadaan_tidak_lengkap_tidak_ditebak():
    naskah = _naskah()
    naskah["adegan"][0]["peristiwa"][0]["perubahan_keadaan"] = {
        "entitas_id": "pengendara",
    }
    spek, _, _ = arahkan_naskah(naskah)
    assert spek["rencana_blocking"]["transisi_keadaan"] == []
    assert any(
        x["kode"] == "transisi_keadaan_belum_lengkap"
        for x in spek["rencana_blocking"]["diagnostik"]
    )

def test_pengarah_menetapkan_tujuan_shot_dan_zoom_dari_peristiwa_eksplisit():
    naskah = _naskah()
    naskah["adegan"].append({
        "id": "beat-002",
        "teks": "Penolong menolong pengendara.",
        "tokoh_ids": ["penolong", "pengendara"],
        "peristiwa": [{
            "id": "e3", "aktor": "Penolong", "aksi": "menolong",
            "sasaran": "Pengendara",
        }],
    })
    spek, _, _ = arahkan_naskah(naskah)
    pertama, kedua = spek["cerita"]["shot"]

    assert pertama["pengarahan"]["tujuan"] == "menampilkan_perubahan_aksi"
    assert pertama["pengarahan"]["peristiwa_ids"] == ["e1", "e2"]
    assert pertama["pengarahan"]["fokus_tokoh_ids"] == ["penolong", "pengendara"]
    urutan = pertama["pengarahan"]["urutan_peristiwa"]
    assert [item["peristiwa_id"] for item in urutan] == ["e1", "e2"]
    assert [item["urutan"] for item in urutan] == [1, 2]
    assert urutan[0]["aktor_id"] == "pengendara"
    assert urutan[0]["aksi"] == "tergelincir"
    assert urutan[0]["sasaran"] == "motor"
    assert urutan[1]["sasaran_tokoh_id"] == "pengendara"
    assert pertama["kamera"]["z"] == [1.06, 1.16]

    assert kedua["pengarahan"]["tujuan"] == "menampilkan_interaksi"
    assert kedua["pengarahan"]["peristiwa_ids"] == ["e3"]
    assert kedua["kamera"]["z"] == [1.04, 1.12]
    # Benda hanya dibuat pada shot yang memiliki peristiwa eksplisit terkait motor.
    assert [x["jenis"] for x in pertama["benda"]] == ["motor"]
    assert kedua["benda"] == []



def test_segmentasi_hanya_memisahkan_aksi_dengan_relasi_temporal_eksplisit():
    naskah = _naskah()
    spek, _, _ = arahkan_naskah(naskah)
    pengarahan = spek["cerita"]["shot"][0]["pengarahan"]
    assert len(pengarahan["tahapan_peristiwa"]) == 1
    assert pengarahan["tahapan_peristiwa"][0]["peristiwa_ids"] == ["e1", "e2"]
    assert pengarahan["status_segmentasi"] == "rencana_semantik_belum_memecah_shot_renderer"

    naskah["adegan"][0]["peristiwa"][1]["setelah_peristiwa_id"] = "e1"
    spek_berurutan, _, _ = arahkan_naskah(naskah)
    tahapan = spek_berurutan["cerita"]["shot"][0]["pengarahan"]["tahapan_peristiwa"]
    assert len(tahapan) == 2
    assert tahapan[0]["peristiwa_ids"] == ["e1"]
    assert tahapan[1]["peristiwa_ids"] == ["e2"]
    assert tahapan[1]["dasar_pemisahan"] == "relasi_temporal_eksplisit"
    assert tahapan[1]["bergantung_pada_peristiwa_id"] == "e1"


def test_transisi_keadaan_berantai_membentuk_tahap_aksi_berbeda():
    naskah = _naskah()
    naskah["adegan"][0]["peristiwa"][0]["perubahan_keadaan"] = {
        "entitas_id": "pengendara", "dari": "mengendarai", "menjadi": "terjatuh",
    }
    naskah["adegan"][0]["peristiwa"][1]["perubahan_keadaan"] = {
        "entitas_id": "pengendara", "dari": "terjatuh", "menjadi": "ditolong",
    }
    spek, _, _ = arahkan_naskah(naskah)
    tahapan = spek["cerita"]["shot"][0]["pengarahan"]["tahapan_peristiwa"]
    assert len(tahapan) == 2
    assert tahapan[1]["dasar_pemisahan"] == "transisi_keadaan_berurutan"

