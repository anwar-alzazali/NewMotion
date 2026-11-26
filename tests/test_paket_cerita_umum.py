from newmotion.application.pengarah_inti import arahkan_naskah
from newmotion.domain.genre import ambil


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


def test_paket_cerita_umum_tidak_mengambil_alih_kebijakan_kisah_islami():
    assert ambil("cerita_umum").pengarah_tokoh_visual is not None
    paket_islami = ambil("kisah_islami")
    assert paket_islami.pengarah_tokoh_visual is None
