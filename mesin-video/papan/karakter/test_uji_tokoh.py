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
    temuan = U.periksa_loncatan([[a], [a], [b]], {0: ("lompat", "depan")})
    assert temuan and temuan[0]["kode"] == "A5_LONCATAN"


def test_gerak_cepat_yang_mulus_bukan_loncatan():
    frame = []
    for i in range(4):  # tangan bergerak 60 px/frame dengan kecepatan tetap
        c = _catat()
        c["sendi"]["lengan"][1][2] = [62 + 60 * i, -195]
        frame.append([c])
    assert U.periksa_loncatan(frame, {0: ("lompat", "depan")}) == []


def test_pemendekan_saat_aksi_dari_depan_boleh_tapi_tidak_dari_samping():
    c = _catat()
    c["sendi"]["kaki"][0][1] = [-26, -106]  # paha 94 px (kaki mengayun ke arah kamera)
    kode = lambda pose, sudut: {x["kode"] for x in U.periksa([c], {0: (pose, sudut)}, ACUAN)}  # noqa: E731
    assert "A1_PANJANG_TULANG" not in kode("jalan", "depan")
    assert "A1_PANJANG_TULANG" in kode("jalan", "samping")
    assert "A1_PANJANG_TULANG" in kode("berdiri", "depan")
def test_lima_sudut_benar_dikenali_alat_ukur():
    kasus = [
        (_catat(sudut="samping", profil="samping", badan_samping=True, telinga=1), ("berdiri", "samping")),
        (_catat(sudut="samping_kiri", profil="samping_kiri", badan_samping=True, telinga=1), ("berdiri", "samping_kiri")),
        (_catat(sudut="tiga_perempat", badan_tiga_perempat=True, kepala_tiga_perempat=True, telinga=2), ("berdiri", "tiga_perempat")),
        (_catat(sudut="belakang", belakang=True, badan_belakang=True, telinga=2), ("berdiri", "belakang")),
    ]
    for catatan, label in kasus:
        assert U.periksa([catatan], {0: label}, ACUAN) == []


def test_tiga_perempat_tidak_boleh_hanya_memutar_kepala():
    c = _catat(kepala_tiga_perempat=True, badan_tiga_perempat=False)
    kode = {x["kode"] for x in U.periksa([c], {0: ("berdiri", "tiga_perempat")}, ACUAN)}
    assert "A3_ARAH_TIDAK_SEARAH" in kode


def test_samping_kiri_tidak_boleh_dilabeli_profil_kanan():
    c = _catat(profil="kanan", badan_samping=True, telinga=1)
    kode = {x["kode"] for x in U.periksa([c], {0: ("berdiri", "samping_kiri")}, ACUAN)}
    assert "A3_SUDUT_TIDAK_DIDUKUNG" in kode



def test_integrasi_meneruskan_lima_sudut_ke_renderer():
    from karakter.integrasi import integrasikan_tokoh

    for arah in ("depan", "tiga_perempat", "samping", "samping_kiri", "belakang"):
        boneka = {}
        integrasikan_tokoh(boneka, {"arah": arah}, 2.0)
        assert boneka["sudut"] == arah
        assert boneka["belakang"] is (arah == "belakang")


def test_sahabat_tetap_bertubuh_dengan_wajah_cahaya():
    from karakter.integrasi import integrasikan_tokoh

    boneka = {}
    integrasikan_tokoh(boneka, {"mode": "wajah_cahaya", "arah": "samping_kiri"}, 2.0)
    assert boneka["gaya"] == "umum"
    assert boneka["wajah_cahaya"] is True
    assert boneka["sudut"] == "samping_kiri"

