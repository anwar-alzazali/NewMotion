from copy import deepcopy

import pytest

from newmotion.adapter_visual_tokoh import (
    GalatAdapterVisualTokoh,
    terapkan_rencana_visual_tokoh,
)


def _spec(rencana, *, boneka=None, benda=None):
    return {
        "rencana_cerita": {
            "tokoh": [
                {"id": "penolong", "nama": "Penolong", "kategori": "tokoh_umum"},
                {"id": "pengendara", "nama": "Pengendara", "kategori": "tokoh_umum"},
            ]
        },
        "rencana_visual_tokoh": rencana,
        "cerita": {
            "shot": [{
                "at": 0,
                "boneka": deepcopy(boneka or []),
                "benda": deepcopy(benda or []),
            }]
        },
    }


def test_adapter_menerjemahkan_gerak_jalan_dan_profil_karakter():
    spec = _spec({
        "status": "siap_diterjemahkan",
        "shot": [{
            "indeks": 0,
            "tokoh": [{
                "tokoh_id": "penolong",
                "aksi": "jalan",
                "x": [[0, 180], [2, 520]],
                "y": 1500,
                "pose": [[0, "berdiri"], [1.8, "menolong"]],
                "karakter": {"jenis": "pria", "warna_kulit": "#c99a72"},
            }],
        }],
        "diagnostik": [],
    })

    hasil = terapkan_rencana_visual_tokoh(spec)
    boneka = spec["cerita"]["shot"][0]["boneka"][0]

    assert hasil[0]["aktor_ids"] == ["penolong"]
    assert boneka["aktor_id"] == "penolong"
    assert boneka["x"] == [[0, 180], [2, 520]]
    assert boneka["jalan"] == 1.0
    assert boneka["pose"] == [[0, "berdiri"], [1.8, "menolong"]]
    assert boneka["karakter"]["warna_kulit"] == "#c99a72"


def test_adapter_menghubungkan_sasaran_tokoh_dan_motor_yang_sudah_ada():
    spec = _spec({
        "status": "siap_diterjemahkan",
        "shot": [{
            "indeks": 0,
            "tokoh": [
                {
                    "tokoh_id": "penolong", "aksi": "jalan",
                    "x": [[0, 800], [2, 500]], "y": 1500,
                    "sasaran_tokoh_id": "pengendara",
                },
                {
                    "tokoh_id": "pengendara",
                    "x": 500, "y": 1500, "kendaraan_id": "motor-1",
                },
            ],
        }],
        "diagnostik": [],
    }, benda=[{"id": "motor-1", "jenis": "motor", "x": [[0, 300], [2, 500]], "y": 1550}])

    terapkan_rencana_visual_tokoh(spec)
    penolong, pengendara = spec["cerita"]["shot"][0]["boneka"]

    assert penolong["sasaran_id"] == 1
    assert pengendara["kendaraan_id"] == "motor-1"


def test_adapter_mempertahankan_boneka_lama_dan_tidak_mengubahnya():
    lama = {"id": "avatar", "x": 540, "y": 1500}
    spec = _spec({
        "status": "siap_diterjemahkan",
        "shot": [{
            "indeks": 0,
            "tokoh": [{"tokoh_id": "penolong", "x": 200, "y": 1500}],
        }],
        "diagnostik": [],
    }, boneka=[lama])

    terapkan_rencana_visual_tokoh(spec)

    assert spec["cerita"]["shot"][0]["boneka"][0] == lama
    assert spec["cerita"]["shot"][0]["boneka"][1]["aktor_id"] == "penolong"


def test_adapter_tidak_melakukan_apapun_bila_paket_tidak_mendukung_visual_tokoh():
    spec = _spec({"status": "belum_didukung_paket", "shot": [], "diagnostik": []})
    sebelum = deepcopy(spec)

    assert terapkan_rencana_visual_tokoh(spec) == []
    assert spec == sebelum


@pytest.mark.parametrize("arahan", [
    {"tokoh_id": "tidak-terdaftar", "x": 100, "y": 1500},
    {"tokoh_id": "penolong", "y": 1500},
    {"tokoh_id": "penolong", "x": 100, "y": 1500, "sasaran_tokoh_id": "hilang"},
])
def test_adapter_menolak_referensi_dan_posisi_yang_tidak_valid(arahan):
    spec = _spec({
        "status": "siap_diterjemahkan",
        "shot": [{"indeks": 0, "tokoh": [arahan]}],
        "diagnostik": [],
    })

    with pytest.raises(GalatAdapterVisualTokoh):
        terapkan_rencana_visual_tokoh(spec)


def test_adapter_menolak_aksi_jalan_tanpa_perpindahan_posisi():
    spec = _spec({
        "status": "siap_diterjemahkan",
        "shot": [{
            "indeks": 0,
            "tokoh": [{
                "tokoh_id": "penolong", "aksi": "jalan",
                "x": [[0, 200], [2, 200]], "y": 1500,
            }],
        }],
        "diagnostik": [],
    })

    with pytest.raises(GalatAdapterVisualTokoh, match="lintasan posisi"):
        terapkan_rencana_visual_tokoh(spec)


def test_adapter_menolak_kendaraan_yang_bukan_motor_di_shot():
    spec = _spec({
        "status": "siap_diterjemahkan",
        "shot": [{
            "indeks": 0,
            "tokoh": [{
                "tokoh_id": "pengendara", "x": 200, "y": 1500,
                "kendaraan_id": "objek-1",
            }],
        }],
        "diagnostik": [],
    }, benda=[{"id": "objek-1", "jenis": "meja"}])

    with pytest.raises(GalatAdapterVisualTokoh, match="bukan benda motor"):
        terapkan_rencana_visual_tokoh(spec)


def test_adapter_renderer_dijalankan_setelah_gerbang_adab():
    from pathlib import Path

    sumber = (
        Path(__file__).parents[1] / "mesin-video" / "papan_buat.py"
    ).read_text(encoding="utf-8")
    posisi_gerbang = sumber.index("jaga_spek(spec)")
    posisi_adapter = sumber.index("terapkan_rencana_visual_tokoh(spec)")
    posisi_integrasi = sumber.index("integrasikan_spec(spec)")
    assert posisi_gerbang < posisi_adapter < posisi_integrasi
