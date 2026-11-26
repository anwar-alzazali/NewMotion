"""Uji generalisasi spek JSON pada cerita umum yang berbeda.

Tes ini mengukur perilaku lintas kategori aksi, bukan mengunci koordinat satu
adegan tertentu. Renderer/video tidak dijalankan.
"""
import json

import pytest

from newmotion.application.pengarah_inti import arahkan_naskah


def _naskah(judul, teks, peristiwa, tokoh=None):
    return {
        "genre": "cerita_umum",
        "konteks_konten": "umum",
        "judul": judul,
        "tokoh": tokoh or [
            {"id": "aktor-a", "nama": "Aktor A", "kategori": "tokoh_umum"},
            {"id": "aktor-b", "nama": "Aktor B", "kategori": "tokoh_umum"},
        ],
        "adegan": [{
            "id": "beat-001",
            "nama": judul,
            "teks": teks,
            "tokoh_ids": ["aktor-a", "aktor-b"],
            "peristiwa": peristiwa,
        }],
    }


KASUS = [
    pytest.param(
        _naskah(
            "Pelari mendekati pejalan",
            "Aktor A berlari mendekati Aktor B.",
            [{
                "id": "lari-01", "aktor": "Aktor A", "aksi": "berlari",
                "sasaran": "Aktor B", "sasaran_tokoh_id": "aktor-b",
                "bukti_teks": "Aktor A berlari mendekati Aktor B",
            }],
        ),
        "lari-01", "siap_diterjemahkan", "lokomosi",
        id="lokomosi-berlari",
    ),
    pytest.param(
        _naskah(
            "Penolong membantu korban",
            "Aktor A menolong Aktor B.",
            [{
                "id": "tolong-01", "aktor": "Aktor A", "aksi": "menolong",
                "sasaran": "Aktor B", "sasaran_tokoh_id": "aktor-b",
                "bukti_teks": "Aktor A menolong Aktor B",
            }],
        ),
        "tolong-01", "siap_diterjemahkan", "interaksi",
        id="interaksi-menolong",
    ),
    pytest.param(
        _naskah(
            "Penjaga menunggu",
            "Aktor B menunggu di tempat.",
            [{
                "id": "diam-01", "aktor": "Aktor B", "aksi": "menunggu",
                "bukti_teks": "Aktor B menunggu di tempat",
            }],
        ),
        "diam-01", "siap_diterjemahkan", "aksi_statis",
        id="aksi-statis-menunggu",
    ),
    pytest.param(
        _naskah(
            "Pengendara menaiki motor",
            "Aktor A mengendarai motor.",
            [{
                "id": "motor-01", "aktor": "Aktor A", "aksi": "mengendarai_motor",
                "sasaran": "motor", "bukti_teks": "Aktor A mengendarai motor",
            }],
        ),
        "motor-01", "siap_diterjemahkan", "kendaraan",
        id="kendaraan-eksplisit",
    ),
    pytest.param(
        _naskah(
            "Pengamat memperhatikan keadaan",
            "Aktor A mengamati keadaan sekitar.",
            [{
                "id": "amati-01", "aktor": "Aktor A", "aksi": "mengamati",
                "sasaran": "keadaan sekitar",
                "bukti_teks": "Aktor A mengamati keadaan sekitar",
            }],
        ),
        "amati-01", "tidak_ada_aksi_visual_eksplisit", "belum_didukung",
        id="aksi-belum-didukung",
    ),
]


@pytest.mark.parametrize("naskah,event_id,status_visual,kategori", KASUS)
def test_spek_json_lintas_kategori_tetap_tertelusur(
    naskah, event_id, status_visual, kategori
):
    spek, genre, jumlah_shot = arahkan_naskah(naskah)

    # Seluruh keluaran harus berupa JSON valid, bukan hanya objek Python yang kebetulan terbentuk.
    hasil_serial = json.loads(json.dumps(spek, ensure_ascii=False))
    assert genre == "cerita_umum"
    assert jumlah_shot >= 1
    assert hasil_serial["genre"] == "cerita_umum"

    beat = hasil_serial["rencana_cerita"]["adegan"][0]
    event = beat["peristiwa"][0]
    assert event["id"] == event_id
    assert event["beat_id"] == beat["id"]
    assert event["aktor_id"] in {item["id"] for item in hasil_serial["rencana_cerita"]["tokoh"]}

    event_blocking = {
        item["id"] for item in hasil_serial["rencana_blocking"]["peristiwa"]
    }
    assert event_id in event_blocking

    shot = hasil_serial["cerita"]["shot"]
    assert all(item.get("pengarahan", {}).get("peristiwa_ids") for item in shot)
    assert hasil_serial["rencana_visual_tokoh"]["status"] == status_visual

    if kategori == "lokomosi":
        boneka = shot[0]["boneka"]
        pelari = next(item for item in boneka if item["aktor_id"] == "aktor-a")
        assert pelari["jalan"] == 1.35
        assert pelari["x"][0][1] != pelari["x"][-1][1]
    elif kategori == "interaksi":
        penolong = next(
            item for item in shot[0]["boneka"] if item["aktor_id"] == "aktor-a"
        )
        assert penolong["karakter"]["gerak"] == [[0, "menolong"]]
        assert penolong["sasaran_id"] is not None
    elif kategori == "aksi_statis":
        penjaga = next(
            item for item in shot[0]["boneka"] if item["aktor_id"] == "aktor-b"
        )
        assert penjaga["aksi_cerita"] == "menunggu"
    elif kategori == "kendaraan":
        motor = next(item for item in shot[0]["benda"] if item["jenis"] == "motor")
        pengendara = next(
            item for item in shot[0]["boneka"] if item["aktor_id"] == "aktor-a"
        )
        assert pengendara["kendaraan_id"] == motor["id"]
    elif kategori == "belum_didukung":
        kode = {
            item["kode"]
            for item in hasil_serial["rencana_visual_tokoh"]["diagnostik"]
        }
        assert "aksi_visual_belum_didukung" in kode
        # Ketidakmampuan harus tampak sebagai diagnostik, bukan visual rekaan.
        assert all(not item["boneka"] for item in shot)


def test_id_dan_urutan_peristiwa_stabil_pada_pengulangan_input():
    naskah = _naskah(
        "Dua aksi berurutan",
        "Aktor A berlari mendekati Aktor B lalu menolongnya.",
        [
            {
                "id": "event-01", "aktor": "Aktor A", "aksi": "berlari",
                "sasaran": "Aktor B", "sasaran_tokoh_id": "aktor-b",
                "bukti_teks": "Aktor A berlari mendekati Aktor B",
                "setelah_peristiwa_id": None,
            },
            {
                "id": "event-02", "aktor": "Aktor A", "aksi": "menolong",
                "sasaran": "Aktor B", "sasaran_tokoh_id": "aktor-b",
                "bukti_teks": "menolongnya",
                "setelah_peristiwa_id": "event-01",
            },
        ],
    )
    pertama, _, _ = arahkan_naskah(naskah)
    kedua, _, _ = arahkan_naskah(naskah)

    def sid(spek):
        return [
            (
                shot["pengarahan"].get("peristiwa_ids"),
                shot["pengarahan"].get("tahap_id"),
                shot["at"],
            )
            for shot in spek["cerita"]["shot"]
        ]

    assert sid(pertama) == sid(kedua)
    assert [item["id"] for item in pertama["rencana_blocking"]["peristiwa"]] == [
        "event-01", "event-02"
    ]
    assert len(pertama["cerita"]["shot"]) == 2
    assert pertama["cerita"]["shot"][1]["at"] > pertama["cerita"]["shot"][0]["at"]


def test_objek_tidak_diciptakan_jika_naskah_tidak_menyatakannya():
    naskah = _naskah(
        "Percakapan dua orang",
        "Aktor A menolong Aktor B.",
        [{
            "id": "tolong-02", "aktor": "Aktor A", "aksi": "menolong",
            "sasaran": "Aktor B", "sasaran_tokoh_id": "aktor-b",
            "bukti_teks": "Aktor A menolong Aktor B",
        }],
    )
    spek, _, _ = arahkan_naskah(naskah)
    assert all(not shot["benda"] for shot in spek["cerita"]["shot"])
