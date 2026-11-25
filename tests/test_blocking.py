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


def test_adegan_motor_jembatan_memenuhi_kontrak_blocking():
    import json
    from pathlib import Path

    spec = json.loads(
        (Path(__file__).parent / "data" / "adegan_uji_visual.json").read_text(encoding="utf-8")
    )
    cerita = spec["cerita"]
    assert cerita.get("pemeriksaan_blocking") is True
    gagal = [item for item in periksa_blocking(cerita) if item["tingkat"] == "gagal"]
    assert gagal == [], gagal

    shot_naik = cerita["shot"][0]
    motor_naik = next(b for b in shot_naik["benda"] if b["jenis"] == "motor")
    pengendara = next(b for b in shot_naik["boneka"] if b["id"] == 1)
    assert isinstance(pengendara["x"], list) and isinstance(pengendara["pose"], list)

    shot_jalan = cerita["shot"][1]
    motor_jalan = next(b for b in shot_jalan["benda"] if b["jenis"] == "motor")
    rider_jalan = next(b for b in shot_jalan["boneka"] if b["id"] == 1)
    assert motor_jalan["x"][-1][1] > motor_jalan["x"][0][1]
    assert rider_jalan["kendaraan_id"] == motor_jalan["id"] == "motor_1"
    assert rider_jalan["pose_motor"] == "mengendarai_motor"

    shot_tergelincir = cerita["shot"][2]
    motor_tergelincir = next(b for b in shot_tergelincir["benda"] if b["jenis"] == "motor")
    korban_tergelincir = next(b for b in shot_tergelincir["boneka"] if b["id"] == 1)
    assert korban_tergelincir["kendaraan_id"] == motor_tergelincir["id"]
    assert korban_tergelincir["lepas_kendaraan_at"] == 2.4
    assert motor_tergelincir["miring"][-1][1] <= -60
    assert korban_tergelincir["pose"][-1][1] == "rebahan"

    shot_bantu = cerita["shot"][3]
    penolong = next(b for b in shot_bantu["boneka"] if b["id"] == 2)
    korban = next(b for b in shot_bantu["boneka"] if b["id"] == 1)
    assert penolong.get("aksi") == "menolong"
    assert penolong.get("sasaran_id") == korban["id"]
    assert penolong["pose"][-1][1] == "menolong"
    assert penolong["x"][-1][1] < penolong["x"][0][1]


def test_keyframe_jalan_tanpa_perpindahan_ditolak():
    cerita = {"shot": [{"boneka": [{
        "id": 1, "x": [[0, 100], [4, 100]], "y": 200,
        "jalan": [[0, 0.7], [3, 0.7], [4, 0]],
    }]}]}
    temuan = periksa_blocking(cerita)
    assert any(x["kode"] == "jalan_tanpa_lintasan" and x["tingkat"] == "gagal"
               for x in temuan)

def test_kontinuitas_memeriksa_awal_lintasan_shot_berikutnya():
    cerita = {"shot": [
        {"boneka": [{"id": 1, "x": [[0, 100], [4, 200]], "y": 200}]},
        {"boneka": [{"id": 1, "x": [[0, 650], [4, 700]], "y": 200}]},
    ]}
    temuan = periksa_blocking(cerita)
    assert any(
        x["kode"] == "loncatan_posisi" and x["shot"] == 1 and x["tokoh"] == "1"
        for x in temuan
    )


def test_kontinuitas_lolos_bila_awal_shot_menyambung_akhir_sebelumnya():
    cerita = {"shot": [
        {"boneka": [{"id": 1, "x": [[0, 100], [4, 200]], "y": 200}]},
        {"boneka": [{"id": 1, "x": [[0, 200], [4, 280]], "y": 200}]},
    ]}
    temuan = periksa_blocking(cerita)
    assert not any(x["kode"] == "loncatan_posisi" for x in temuan)


def test_renderer_mendukung_pengendara_terikat_dan_lepas_saat_jatuh():
    from pathlib import Path

    sumber = (Path(__file__).parents[1] / "mesin-video" / "papan" / "cerita.js").read_text(encoding="utf-8")
    assert "b.kendaraan_id" in sumber
    assert "b.lepas_kendaraan_at" in sumber
    assert "mengendarai_motor:" in sumber


def test_pengendara_menghadap_samping_dan_memegang_setang():
    akar = Path(__file__).resolve().parents[1]
    cerita = __import__("json").loads((akar / "tests/data/adegan_uji_visual.json").read_text())
    sumber = (akar / "mesin-video/papan/cerita.js").read_text()
    for indeks in (0, 1, 2):
        pengendara = next(b for b in cerita["shot"][indeks]["boneka"] if b["id"] == 1)
        assert pengendara["profil"] == "kanan"
    assert 'b.profil === "kanan"' in sumber
    assert "profilMotor: b.profil ===" in sumber
    assert "const H = o.profilMotor ? [218, -284 + nafas]" in sumber
