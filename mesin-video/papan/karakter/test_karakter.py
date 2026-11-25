"""Uji asap renderer karakter NewMotion."""
import math
import pytest
from karakter import orang


def test_renderer_menghasilkan_svg_tokoh():
    svg = orang(540, 1700, s=1.0)
    assert svg.startswith('<g transform="translate(')
    assert svg.endswith("</g>")
    assert "stroke=" in svg or "fill=" in svg


def test_renderer_mendukung_wanita_dan_ekspresi_mikro():
    svg = orang(540, 1700, jenis="wanita", wajah="heran", usia="dewasa",
                detail_wajah={"lirikan": 0.4, "kelopak": -0.2})
    assert "translate(540.0,1700.0)" in svg
    assert "kerudung" in svg or "#5a3a5e" in svg


def test_renderer_mendukung_pose_dan_jadwal_gerak():
    svg = orang(540, 1700, gerak=[[0, "berdiri"], [1, "tunjuk"]], t=1.2)
    assert svg.count("<g") >= 1



def test_integrasi_karakter_menghasilkan_rangka_dari_gerak_python():
    from karakter.integrasi import integrasikan_spec

    spesifikasi = {
        "durasi": 1.0,
        "cerita": {"shot": [{"at": 0, "boneka": [{
            "x": 400, "y": 1400, "s": 0.7,
            "karakter": {
                "jenis": "pria", "mode": "pakaian", "kepala": "imamah",
                "warna_kulit": "#a86a45", "warna_baju": "#477b83",
                "warna_aksen": "#d6c08e", "jenis_pakaian": "koko",
                "gerak": "gali", "alat": "beliung", "janggut": "pendek",
            },
        }]}]},
    }
    integrasikan_spec(spesifikasi)
    tokoh = spesifikasi["cerita"]["shot"][0]["boneka"][0]
    assert tokoh["_gabungan"] is True
    assert tokoh["gaya"] == "umum"
    assert tokoh["penutup_kepala"] == "imamah"
    assert tokoh["pakaian"]["warna"] == "#477b83"
    assert tokoh["aksi"] == "gali"
    assert tokoh["pose"][0][1]["pegang"] == "beliung"
    assert len(tokoh["pose"]) >= 15
    assert tokoh["pose"][0][1]["ra"] != tokoh["pose"][3][1]["ra"]


def test_integrasi_karakter_menolak_gerak_tidak_dikenal():
    import pytest
    from karakter.integrasi import integrasikan_tokoh

    with pytest.raises(ValueError, match="tidak dikenal"):
        integrasikan_tokoh({}, {"gerak": "terbang"}, 1.0)

def test_ik_gerak_gali_sesuai_panjang_lengan_renderer():
    from karakter.gerak import ik, LENGAN_A, LENGAN_B

    assert (LENGAN_A, LENGAN_B) == (85, 80)
    for target in [(-18, -105), (18, -62), (-10, 38), (22, 82)]:
        a1, a2 = ik(*target)
        x = math.sin(math.radians(a1)) * 85 + math.sin(math.radians(a2)) * 80
        y = math.cos(math.radians(a1)) * 85 + math.cos(math.radians(a2)) * 80
        assert x == pytest.approx(target[0], abs=1e-6)
        assert y == pytest.approx(target[1], abs=1e-6)


def test_gali_memiliki_pose_angkat_dan_bentur_dengan_dua_tangan():
    from karakter.gerak import gali

    angkat, bentur = gali(0.0), gali(0.60)
    assert angkat["la_ka"] != bentur["la_ka"]
    assert angkat["la_ki"] != bentur["la_ki"]
    assert bentur["naik"] > angkat["naik"]
