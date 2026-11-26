"""Uji kontrak entitas benda eksplisit menuju objek renderer."""

import pytest

from newmotion.application.pengarah_inti import GalatPengarahan, arahkan_naskah


def _naskah(benda=None, adegan_tambahan=None):
    adegan = {
        "id": "beat-01",
        "nama": "Tokoh di jembatan",
        "teks": "Aktor A menunggu di dekat jembatan.",
        "tokoh_ids": ["aktor-a"],
        "peristiwa": [{
            "id": "event-01",
            "aktor": "Aktor A",
            "aksi": "menunggu",
            "sasaran": "jembatan",
            "sasaran_benda_id": "jembatan-01",
            "bukti_teks": "Aktor A menunggu di dekat jembatan",
        }],
    }
    if adegan_tambahan:
        adegan_tambahan(adegan)
    return {
        "genre": "cerita_umum",
        "konteks_konten": "umum",
        "judul": "Uji entitas benda",
        "tokoh": [{"id": "aktor-a", "nama": "Aktor A", "kategori": "tokoh_umum"}],
        "benda": benda or [],
        "adegan": [adegan],
    }


def _jembatan(**tambahan):
    benda = {
        "id": "jembatan-01",
        "nama": "Jembatan",
        "jenis_renderer": "jembatan",
        "posisi": {"x": 540, "y": 1480, "s": 1.1},
        "properti": {"cahaya": 0.25},
        "lapisan": {"belakang": True},
    }
    benda.update(tambahan)
    return benda


def test_entitas_benda_dengan_id_dan_jenis_renderer_menjadi_objek_shot():
    spek, _, _ = arahkan_naskah(_naskah([_jembatan()]))
    shot = spek["cerita"]["shot"][0]
    visual = next(item for item in shot["benda"] if item["id"] == "jembatan-01")

    assert visual["jenis"] == "jembatan"
    assert visual["x"] == 540
    assert visual["y"] == 1480
    assert visual["s"] == 1.1
    assert visual["cahaya"] == 0.25
    assert visual["belakang"] is True
    assert spek["rencana_visual_benda"]["status"] == "siap"
    assert spek["rencana_visual_benda"]["shot"][0]["peristiwa_ids"] == ["event-01"]


def test_benda_muncul_hanya_pada_shot_yang_menautkan_peristiwanya():
    def dua_peristiwa(adegan):
        adegan["peristiwa"][0].pop("sasaran_benda_id")
        adegan["peristiwa"].append({
            "id": "event-02",
            "aktor": "Aktor A",
            "aksi": "berlari",
            "sasaran": "jembatan",
            "sasaran_benda_id": "jembatan-01",
            "setelah_peristiwa_id": "event-01",
            "bukti_teks": "berlari ke jembatan",
        })
        adegan["teks"] = "Aktor A menunggu di dekat jembatan lalu berlari ke jembatan."

    spek, _, _ = arahkan_naskah(_naskah([_jembatan()], dua_peristiwa))
    shot = spek["cerita"]["shot"]

    assert len(shot) == 2
    assert not any(x["id"] == "jembatan-01" for x in shot[0]["benda"])
    assert any(x["id"] == "jembatan-01" for x in shot[1]["benda"])


def test_benda_dengan_posisi_keyframe_diteruskan_tanpa_diratakan():
    posisi = {
        "x": [[0, 400], [2.0, 620]],
        "y": [[0, 1500], [2.0, 1450]],
        "s": 0.9,
    }
    spek, _, _ = arahkan_naskah(_naskah([_jembatan(posisi=posisi)]))
    benda = next(x for x in spek["cerita"]["shot"][0]["benda"] if x["id"] == "jembatan-01")

    assert benda["x"] == posisi["x"]
    assert benda["y"] == posisi["y"]
    assert benda["s"] == 0.9


def test_benda_tanpa_posisi_menghasilkan_diagnostik_bukan_posisi_rekaan():
    benda = _jembatan()
    benda.pop("posisi")
    spek, _, _ = arahkan_naskah(_naskah([benda]))

    assert not any(x["id"] == "jembatan-01" for x in spek["cerita"]["shot"][0]["benda"])
    assert spek["rencana_visual_benda"]["status"] == "perlu_pelengkapan"
    assert spek["rencana_visual_benda"]["diagnostik"][0]["kode"] == "benda_perlu_penempatan"


def test_jenis_renderer_yang_tidak_dikenal_ditolak():
    benda = _jembatan(jenis_renderer="jembatan_ajaib")
    with pytest.raises(GalatPengarahan, match="tidak didukung"):
        arahkan_naskah(_naskah([benda]))


def test_properti_tidak_boleh_menimpa_id_atau_posisi_renderer():
    benda = _jembatan(properti={"x": 10})
    with pytest.raises(GalatPengarahan, match="tidak boleh menimpa"):
        arahkan_naskah(_naskah([benda]))


def test_id_benda_ganda_ditolak_di_roster_semantik():
    with pytest.raises(GalatPengarahan, match="ID benda"):
        arahkan_naskah(_naskah([_jembatan(), _jembatan()]))


def test_benda_global_tidak_ditampilkan_tanpa_tautan_ke_beat_atau_peristiwa():
    def hapus_tautan(adegan):
        adegan["peristiwa"][0].pop("sasaran_benda_id")
    spek, _, _ = arahkan_naskah(_naskah([_jembatan()], hapus_tautan))

    assert not any(x["id"] == "jembatan-01" for x in spek["cerita"]["shot"][0]["benda"])
    assert spek["rencana_visual_benda"]["status"] == "tidak_ada_benda_tertaut"


def test_benda_ids_di_beat_mempertahankan_id_yang_sama_di_beberapa_shot():
    def tambah_beat(adegan):
        adegan["benda_ids"] = ["jembatan-01"]
    naskah = _naskah([_jembatan()], tambah_beat)
    naskah["adegan"].append({
        "id": "beat-02",
        "nama": "Masih di jembatan",
        "teks": "Aktor A tetap menunggu di dekat jembatan.",
        "tokoh_ids": ["aktor-a"],
        "benda_ids": ["jembatan-01"],
        "peristiwa": [{
            "id": "event-02",
            "aktor": "Aktor A",
            "aksi": "menunggu",
            "bukti_teks": "Aktor A tetap menunggu di dekat jembatan",
        }],
    })
    spek, _, _ = arahkan_naskah(naskah)

    ids = [
        [x["id"] for x in shot["benda"] if x["jenis"] == "jembatan"]
        for shot in spek["cerita"]["shot"]
    ]
    assert ids == [["jembatan-01"], ["jembatan-01"]]
