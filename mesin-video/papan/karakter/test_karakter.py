"""Uji asap renderer karakter NewMotion."""
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
