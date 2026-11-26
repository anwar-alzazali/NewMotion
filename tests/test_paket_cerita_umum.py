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
    assert pengendara["x"][-1][1] == 455
    assert penolong["x"][-1][1] == 385
    assert penolong["y"][-1][1] == pengendara["y"][-1][1] == 1620


def test_paket_cerita_umum_tidak_mengambil_alih_kebijakan_kisah_islami():
    assert ambil("cerita_umum").pengarah_tokoh_visual is not None
    paket_islami = ambil("kisah_islami")
    assert paket_islami.pengarah_tokoh_visual is None


def test_adapter_meneruskan_motor_jadwal_tergelincir_dan_aksi_menolong():
    spek, _, _ = arahkan_naskah(_naskah())
    hasil = terapkan_rencana_visual_tokoh(spek)
    assert hasil[0]["jumlah_tokoh_ditambahkan"] == 2
    shot = spek["cerita"]["shot"][0]
    motor = next(item for item in shot["benda"] if item["jenis"] == "motor")
    assert motor["id"] == "motor-beat-001"
    penolong = next(item for item in shot["boneka"] if item["aktor_id"] == "penolong")
    pengendara = next(item for item in shot["boneka"] if item["aktor_id"] == "pengendara")
    assert penolong["jalan"] == 1.0
    assert penolong["sasaran_id"] == 1
    assert penolong["karakter"]["gerak"] == [[0, "jalan"], [2.2, "menolong"]]
    assert pengendara["kendaraan_id"] == motor["id"]
    assert motor["x"][0][1] == pengendara["x"][0][1]
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

    terapkan_rencana_visual_tokoh(spek)
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
