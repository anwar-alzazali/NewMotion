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
