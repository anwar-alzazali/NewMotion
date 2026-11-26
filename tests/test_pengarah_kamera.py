"""Uji kamera mengikuti lintasan tokoh setelah adapter visual."""

from copy import deepcopy

from newmotion.application.pengarah_inti import arahkan_naskah


def _naskah(aksi="berlari"):
    teks = "Aktor A berlari mendekati Aktor B." if aksi == "berlari" else "Aktor A menunggu."
    peristiwa = {
        "id": "event-01",
        "aktor": "Aktor A",
        "aksi": aksi,
        "bukti_teks": teks.rstrip("."),
    }
    if aksi == "berlari":
        peristiwa.update({
            "sasaran": "Aktor B",
            "sasaran_tokoh_id": "aktor-b",
            "bukti_teks": "Aktor A berlari mendekati Aktor B",
        })
    return {
        "genre": "cerita_umum",
        "konteks_konten": "umum",
        "judul": "Kamera mengikuti tokoh",
        "tokoh": [
            {"id": "aktor-a", "nama": "Aktor A", "kategori": "tokoh_umum"},
            {"id": "aktor-b", "nama": "Aktor B", "kategori": "tokoh_umum"},
        ],
        "adegan": [{
            "id": "beat-01",
            "nama": "Pergerakan tokoh",
            "teks": teks,
            "tokoh_ids": ["aktor-a", "aktor-b"],
            "peristiwa": [peristiwa],
        }],
    }


def test_kamera_mengikuti_pusat_kelompok_tokoh_yang_bergerak():
    spek, _, _ = arahkan_naskah(_naskah())
    shot = spek["cerita"]["shot"][0]
    kamera = shot["kamera"]

    assert isinstance(kamera["x"], list)
    assert isinstance(kamera["y"], list)
    assert len(kamera["x"]) >= 2
    assert len(kamera["y"]) >= 2
    assert kamera["x"][0][1] != kamera["x"][-1][1]
    assert shot["pengarahan"]["status_kamera"] == "kamera_mengikuti_panggung"
    assert spek["rencana_kamera"]["status"] == "diterapkan"
    assert spek["rencana_kamera"]["shot"][0]["aktor_ids"] == ["aktor-a", "aktor-b"]


def test_sumbu_kamera_eksplisit_tidak_ditimpa_sumbu_lain_boleh_mengikuti():
    naskah = _naskah()
    naskah["adegan"][0]["kamera"] = {"x": 610}
    spek, _, _ = arahkan_naskah(naskah)
    shot = spek["cerita"]["shot"][0]

    assert shot["kamera"]["x"] == 610
    assert isinstance(shot["kamera"]["y"], list)
    assert shot["pengarahan"]["status_kamera"] == "kamera_x_mengikuti_panggung"


def test_kamera_tetap_jika_tidak_ada_lintasan_tokoh():
    spek, _, _ = arahkan_naskah(_naskah("menunggu"))
    shot = spek["cerita"]["shot"][0]

    assert isinstance(shot["kamera"]["x"], (int, float))
    assert isinstance(shot["kamera"]["y"], (int, float))
    assert shot["pengarahan"]["status_kamera"] == "profil_tetap_tidak_ada_lintasan"
    assert spek["rencana_kamera"]["status"] == "tidak_ada_lintasan_fokus"


def test_pengarah_kamera_deterministik_pada_input_yang_sama():
    naskah = _naskah()
    pertama, _, _ = arahkan_naskah(deepcopy(naskah))
    kedua, _, _ = arahkan_naskah(deepcopy(naskah))

    assert pertama["cerita"]["shot"][0]["kamera"] == kedua["cerita"]["shot"][0]["kamera"]
    assert pertama["rencana_kamera"] == kedua["rencana_kamera"]
