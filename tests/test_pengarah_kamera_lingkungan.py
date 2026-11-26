"""Uji kontrak kamera dan lingkungan yang benar-benar didukung renderer."""

import pytest

from newmotion.application.pengarah_inti import arahkan_naskah


def _naskah(**tambahan):
    naskah = {
        "genre": "cerita_umum",
        "konteks_konten": "umum",
        "judul": "Uji kamera dan lingkungan",
        "tokoh": [{"id": "aktor-a", "nama": "Aktor A", "kategori": "tokoh_umum"}],
        "adegan": [{
            "id": "beat-01",
            "nama": "Aksi",
            "teks": "Aktor A berlari.",
            "tokoh_ids": ["aktor-a"],
            "peristiwa": [{
                "id": "lari-01",
                "aktor": "Aktor A",
                "aksi": "berlari",
                "bukti_teks": "Aktor A berlari",
            }],
        }],
    }
    naskah.update(tambahan)
    return naskah


def test_kamera_keyframe_dan_lingkungan_eksplisit_diteruskan_ke_shot():
    naskah = _naskah()
    naskah["adegan"][0]["kamera"] = {
        "x": [[0, 540], [2.5, 610]],
        "y": 980,
        "z": [[0, 1.0], [2.5, 1.18]],
        "guncang": [[1.2, 32]],
    }
    naskah["adegan"][0]["lingkungan"] = {
        "palet": "senja",
        "langit": 0.2,
        "malam": 0.35,
        "horizon": 1180,
        "debu": 10,
        "hujan": [[0, 0], [2.0, 0.8]],
    }

    spek, _, _ = arahkan_naskah(naskah)
    shot = spek["cerita"]["shot"][0]

    assert shot["kamera"] == naskah["adegan"][0]["kamera"]
    assert shot["palet"] == "senja"
    assert shot["langit"] == 0.2
    assert shot["malam"] == 0.35
    assert shot["horizon"] == 1180
    assert shot["debu"] == 10
    assert shot["hujan"] == [[0, 0], [2.0, 0.8]]
    assert shot["pengarahan"]["dasar_kamera"] == "metadata_adegan_eksplisit"
    assert shot["pengarahan"]["dasar_lingkungan"] == "metadata_adegan_eksplisit"


def test_metadata_global_dapat_dioverride_per_adegan():
    naskah = _naskah(
        kamera={"x": 500, "y": 960, "z": [1.0, 1.1]},
        lingkungan={"palet": "siang", "debu": 5, "horizon": 1000},
    )
    naskah["adegan"][0]["lingkungan"] = {"palet": "mendung", "hujan": 0.5}

    spek, _, _ = arahkan_naskah(naskah)
    shot = spek["cerita"]["shot"][0]

    assert shot["kamera"] == naskah["kamera"]
    assert shot["palet"] == "mendung"
    assert shot["debu"] == 5
    assert shot["horizon"] == 1000
    assert shot["hujan"] == 0.5
    assert shot["pengarahan"]["dasar_kamera"] == "metadata_naskah_eksplisit"
    assert shot["pengarahan"]["dasar_lingkungan"] == "metadata_adegan_eksplisit"


def test_tanpa_konteks_lingkungan_tidak_mengarang_palet_atau_cuaca():
    spek, _, _ = arahkan_naskah(_naskah())
    shot = spek["cerita"]["shot"][0]

    assert "palet" not in shot
    assert "ruang" not in shot
    assert "hujan" not in shot
    assert "kerumunan" not in shot
    assert shot["pengarahan"]["dasar_lingkungan"] == "belum_dinyatakan"


@pytest.mark.parametrize(
    "aksi,y",
    [("berlari", 960), ("menolong", 1050), ("jatuh", 1150)],
)
def test_posisi_vertikal_kamera_didasarkan_pada_tujuan_shot(aksi, y):
    naskah = _naskah()
    naskah["adegan"][0]["peristiwa"][0]["aksi"] = aksi
    naskah["adegan"][0]["teks"] = f"Aktor A {aksi}."
    spek, _, _ = arahkan_naskah(naskah)
    assert spek["cerita"]["shot"][0]["kamera"]["y"] == y


def test_palet_yang_tidak_dikenal_ditolak_sebelum_menjadi_json_renderer():
    naskah = _naskah()
    naskah["adegan"][0]["lingkungan"] = {"palet": "pantai_fantasi"}
    with pytest.raises(ValueError, match="Palet"):
        arahkan_naskah(naskah)


def test_kunci_lingkungan_di_luar_kontrak_renderer_ditolak():
    naskah = _naskah()
    naskah["adegan"][0]["lingkungan"] = {"kabut_ajaib": 1}
    with pytest.raises(ValueError, match="Kunci lingkungan"):
        arahkan_naskah(naskah)
