"""Uji logika lapis A alat uji tokoh tanpa browser (data catatan sintetis)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import uji_tokoh as U  # noqa: E402

ACUAN = {"paha": 100.0, "betis": 100.0, "lengan_atas": 85.0, "lengan_bawah": 80.0}


def _catat(**lain):
    dasar = {"id": 0, "t": 1.5, "rig": True, "profil": None, "belakang": False, "badan_samping": False,
             "guling": 0, "telinga": 2,
             "sendi": {"kaki": [[[-26, -200], [-26, -100], [-26, 0]], [[26, -200], [26, -100], [26, 0]]],
                       "lengan": [[[-62, -360], [-62, -275], [-62, -195]], [[62, -360], [62, -275], [62, -195]]]}}
    dasar.update(lain)
    return dasar


def test_daftar_pose_dibaca_dari_cerita_js():
    pose = U.daftar_pose((U.PAPAN / "cerita.js").read_text(encoding="utf-8"))
    assert "berdiri" in pose and "duduk" in pose and len(pose) == len(set(pose))


def test_boneka_depan_benar_tidak_ada_temuan():
    assert U.periksa([_catat()], {0: ("berdiri", "depan")}, ACUAN) == []


def test_kepala_samping_badan_depan_dan_tanpa_telinga_terdeteksi():
    kode = {x["kode"] for x in U.periksa([_catat(profil="kanan", telinga=0)], {0: ("berdiri", "samping")}, ACUAN)}
    assert {"A3_ARAH_TIDAK_SEARAH", "A4_BAGIAN_SUDUT"} <= kode


def test_kaki_tenggelam_dan_tulang_memanjang_terdeteksi():
    c = _catat()
    c["sendi"]["kaki"][0][2] = [-26, 70]
    kode = {x["kode"] for x in U.periksa([c], {0: ("berdiri", "depan")}, ACUAN)}
    assert {"A1_PANJANG_TULANG", "A2_KAKI_MENAPAK"} <= kode


def test_pose_duduk_tidak_dituntut_menapak():
    c = _catat()
    c["sendi"]["kaki"][0][2] = [-26, -60]
    c["sendi"]["kaki"][1][2] = [26, -60]
    assert not [x for x in U.periksa([c], {0: ("duduk", "depan")}, {}) if x["kode"] == "A2_KAKI_MENAPAK"]


def test_loncatan_antar_frame_terdeteksi():
    a, b = _catat(), _catat()
    b["sendi"]["lengan"][1][2] = [300, -195]
    temuan = U.periksa_loncatan([[a], [b]], {0: ("lompat", "depan")})
    assert temuan and temuan[0]["kode"] == "A5_LONCATAN"
