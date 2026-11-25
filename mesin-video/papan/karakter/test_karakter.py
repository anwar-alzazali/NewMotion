"""Uji kontrak semantik karakter Python -> renderer JavaScript."""
import pytest

from karakter.gerak import GERAK_BERULANG, SEMUA, jadwal_gerak
from karakter.integrasi import integrasikan_spec, integrasikan_tokoh


def test_kamus_aksi_hanya_menyediakan_nama_semantik():
    assert {"jalan", "lari", "gali", "palu"} <= GERAK_BERULANG
    assert "berdiri" in SEMUA


def test_jadwal_gerak_dinormalisasi_tanpa_pose_numeric():
    assert jadwal_gerak([[2, "tunjuk"], [0, "jalan"]]) == [
        [0.0, "jalan"], [2.0, "tunjuk"]
    ]


def test_jadwal_gerak_menolak_nama_tidak_dikenal():
    with pytest.raises(ValueError, match="tidak dikenal"):
        jadwal_gerak("terbang")


def test_jadwal_gerak_menolak_waktu_negatif():
    with pytest.raises(ValueError, match="negatif"):
        jadwal_gerak([[-1, "jalan"]])


def test_integrasi_hanya_mengirim_nama_aksi_ke_js():
    tokoh = {}
    integrasikan_tokoh(tokoh, {
        "jenis": "pria", "mode": "pakaian", "kepala": "imamah",
        "warna_kulit": "#a86a45", "warna_baju": "#477b83",
        "warna_aksen": "#d6c08e", "jenis_pakaian": "koko",
        "gerak": "gali", "alat": "beliung", "janggut": "pendek",
    }, 1.0)
    assert tokoh["pose"] == [[0.0, "gali"]]
    assert tokoh["_gabungan"] is True
    assert tokoh["gaya"] == "umum"
    assert tokoh["penutup_kepala"] == "imamah"
    assert tokoh["pakaian"]["warna"] == "#477b83"
    assert tokoh["aksi"] == "gali"
    assert tokoh["belakang"] is True
    # Kontrak tidak boleh memuat sudut sendi, hasil IK, atau sampel per-frame.
    assert not any(k in tokoh for k in ("ra", "la", "rk", "lk", "pose_keyframes"))
    assert len(tokoh["pose"]) == 1


def test_offset_fase_gali_hanya_metadata_semantik():
    kiri = integrasikan_tokoh({"npc": 101}, {"gerak": "gali"}, 1.0)
    kanan = integrasikan_tokoh({"npc": 102}, {"gerak": "gali"}, 1.0)
    assert kiri["_gerak_offset"] == pytest.approx((101 * 0.381) % 1.15)
    assert kanan["_gerak_offset"] == pytest.approx((102 * 0.381) % 1.15)
    assert kiri["pose"] == kanan["pose"] == [[0.0, "gali"]]


def test_integrasi_spec_mengabaikan_karakter_yang_sudah_diserialisasi():
    spec = {"durasi": 2, "cerita": {"shot": [{"at": 0, "boneka": [
        {"_gabungan": True, "pose": [[0, "berdiri"]], "karakter": {"gerak": "terbang"}}
    ]}]}}
    assert integrasikan_spec(spec) is spec


def test_tampilan_karakter_hanya_mengubah_atribut_yang_diberikan():
    tokoh = {"gaya": "umum", "rambut": "pendek", "pakaian": {"jenis": "kaus", "warna": "#123456"}}
    hasil = integrasikan_tokoh(tokoh, {"gerak": "jalan"}, 2.0)
    assert hasil["pakaian"] == {"jenis": "kaus", "warna": "#123456"}
    assert hasil["rambut"] == "pendek"
    assert hasil["pose"] == [[0.0, "jalan"]]


def test_jadwal_gerak_menolak_waktu_tidak_terbatas():
    with pytest.raises(ValueError, match="terbatas"):
        jadwal_gerak([[float("inf"), "jalan"]])


def test_integrasi_spec_mengirim_semua_aksi_uji_ke_renderer_tunggal():
    import json
    from pathlib import Path

    akar = Path(__file__).resolve().parents[3]
    spec = json.loads((akar / "tests/data/adegan_uji_visual.json").read_text(encoding="utf-8"))
    integrasikan_spec(spec)

    semua = [b for shot in spec["cerita"]["shot"] for b in shot.get("boneka", [])]
    assert semua and all(b.get("_gabungan") is True for b in semua)
    assert all(isinstance(langkah[1], str) for b in semua for langkah in b["pose"])
    assert spec["cerita"]["shot"][2]["boneka"][0]["pose"] == [
        [0.0, "mengendarai_motor"], [2.4, "tergelincir"], [3.4, "rebahan"]
    ]
    assert spec["cerita"]["shot"][3]["boneka"][1]["pose"] == [
        [0.0, "jalan"], [3.8, "menolong"]
    ]
    assert spec["cerita"]["shot"][4]["boneka"][0]["pose"][-1] == [3.8, "bangkit"]
    assert spec["cerita"]["shot"][0]["boneka"][0]["pakaian"]["warna"] == "#3f7890"
