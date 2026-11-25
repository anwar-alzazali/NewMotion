"""Uji pemeriksaan blocking NewMotion."""
import pytest

from newmotion.blocking import periksa_blocking, wajib_lolos_blocking


def test_jalan_di_tempat_ditolak():
    cerita = {"shot": [{"boneka": [{"id": 1, "x": 100, "y": 200, "jalan": 1}]}]}
    temuan = periksa_blocking(cerita)
    assert any(x["kode"] == "jalan_tanpa_lintasan" and x["tingkat"] == "gagal" for x in temuan)
    with pytest.raises(ValueError, match="Blocking tidak valid"):
        wajib_lolos_blocking(cerita)


def test_lintasan_perpindahan_lolos():
    cerita = {"shot": [{"boneka": [{
        "id": 1, "x": 300, "y": 200, "gerak": "jalan",
        "lintasan": [{"x": 100, "y": 200}, {"x": 300, "y": 200}],
    }]}]}
    assert not [x for x in periksa_blocking(cerita) if x["tingkat"] == "gagal"]


def test_interaksi_mendeteksi_sasaran_tidak_ada():
    cerita = {"shot": [{"boneka": [{"id": 1, "aksi": "menolong", "sasaran_id": 9}]}]}
    assert any(x["kode"] == "sasaran_tidak_ditemukan" for x in periksa_blocking(cerita))


def test_interaksi_memeriksa_jarak():
    cerita = {"shot": [{"boneka": [
        {"id": 1, "x": 100, "y": 200, "aksi": "menolong", "sasaran_id": 2},
        {"id": 2, "x": 700, "y": 200},
    ]}]}
    assert any(x["kode"] == "sasaran_terlalu_jauh" for x in periksa_blocking(cerita))


def test_kontinuitas_mendeteksi_loncatan_posisi():
    cerita = {"shot": [
        {"boneka": [{"id": 1, "x": 100, "y": 200}]},
        {"boneka": [{"id": 1, "x": 600, "y": 200}]},
    ]}
    assert any(x["kode"] == "loncatan_posisi" for x in periksa_blocking(cerita))


def test_tumpang_tindih_hanya_peringatan():
    cerita = {"shot": [{"boneka": [
        {"id": 1, "x": 100, "y": 200}, {"id": 2, "x": 120, "y": 210},
    ]}]}
    assert any(x["kode"] == "tokoh_bertumpuk" and x["tingkat"] == "peringatan"
               for x in periksa_blocking(cerita))


def test_di_tempat_memerlukan_alasan():
    cerita = {"shot": [{"boneka": [{"id": 1, "jalan": 1, "di_tempat": True}]}]}
    assert any(x["kode"] == "alasan_di_tempat_kosong" for x in periksa_blocking(cerita))


def test_keyframe_x_renderer_dianggap_perpindahan():
    cerita = {"shot": [{"boneka": [{
        "id": 1, "x": [[0, 100], [4, 360]], "y": 200, "jalan": 1,
    }]}]}
    temuan = periksa_blocking(cerita)
    assert not any(x["kode"] == "jalan_tanpa_lintasan" for x in temuan)


def test_keyframe_xy_renderer_dianggap_perpindahan():
    cerita = {"shot": [{"boneka": [{
        "id": 1, "x": [[0, 100], [2, 240], [4, 420]],
        "y": [[0, 200], [4, 260]], "gerak": "jalan",
    }]}]}
    temuan = periksa_blocking(cerita)
    assert not any(x["kode"] == "jalan_tanpa_lintasan" for x in temuan)


def test_posisi_tetap_tetap_ditolak_meski_gerak_kaki_aktif():
    cerita = {"shot": [{"boneka": [{
        "id": 1, "x": [[0, 100], [4, 100]], "y": 200, "jalan": 1,
    }]}]}
    temuan = periksa_blocking(cerita)
    assert any(x["kode"] == "jalan_tanpa_lintasan" and x["tingkat"] == "gagal"
               for x in temuan)
