"""Uji pemeriksaan penataan panggung NewMotion."""
from pathlib import Path

import pytest

from newmotion.penataan_panggung import periksa_penataan_panggung, rencanakan_penataan_panggung, wajib_lolos_penataan_panggung


def test_jalan_di_tempat_ditolak():
    cerita = {"shot": [{"boneka": [{"id": 1, "x": 100, "y": 200, "jalan": 1}]}]}
    temuan = periksa_penataan_panggung(cerita)
    assert any(x["kode"] == "jalan_tanpa_lintasan" and x["tingkat"] == "gagal" for x in temuan)
    with pytest.raises(ValueError, match="Penataan panggung tidak valid"):
        wajib_lolos_penataan_panggung(cerita)


def test_lintasan_perpindahan_lolos():
    cerita = {"shot": [{"boneka": [{
        "id": 1, "x": 300, "y": 200, "gerak": "jalan",
        "lintasan": [{"x": 100, "y": 200}, {"x": 300, "y": 200}],
    }]}]}
    assert not [x for x in periksa_penataan_panggung(cerita) if x["tingkat"] == "gagal"]


def test_interaksi_mendeteksi_sasaran_tidak_ada():
    cerita = {"shot": [{"boneka": [{"id": 1, "aksi": "menolong", "sasaran_id": 9}]}]}
    assert any(x["kode"] == "sasaran_tidak_ditemukan" for x in periksa_penataan_panggung(cerita))


def test_interaksi_memeriksa_jarak():
    cerita = {"shot": [{"boneka": [
        {"id": 1, "x": 100, "y": 200, "aksi": "menolong", "sasaran_id": 2},
        {"id": 2, "x": 700, "y": 200},
    ]}]}
    assert any(x["kode"] == "sasaran_terlalu_jauh" for x in periksa_penataan_panggung(cerita))


def test_kontinuitas_mendeteksi_loncatan_posisi():
    cerita = {"shot": [
        {"boneka": [{"id": 1, "x": 100, "y": 200}]},
        {"boneka": [{"id": 1, "x": 600, "y": 200}]},
    ]}
    assert any(x["kode"] == "loncatan_posisi" for x in periksa_penataan_panggung(cerita))


def test_tumpang_tindih_hanya_peringatan():
    cerita = {"shot": [{"boneka": [
        {"id": 1, "x": 100, "y": 200}, {"id": 2, "x": 120, "y": 210},
    ]}]}
    assert any(x["kode"] == "tokoh_bertumpuk" and x["tingkat"] == "peringatan"
               for x in periksa_penataan_panggung(cerita))


def test_di_tempat_memerlukan_alasan():
    cerita = {"shot": [{"boneka": [{"id": 1, "jalan": 1, "di_tempat": True}]}]}
    assert any(x["kode"] == "alasan_di_tempat_kosong" for x in periksa_penataan_panggung(cerita))


def test_keyframe_x_renderer_dianggap_perpindahan():
    cerita = {"shot": [{"boneka": [{
        "id": 1, "x": [[0, 100], [4, 360]], "y": 200, "jalan": 1,
    }]}]}
    temuan = periksa_penataan_panggung(cerita)
    assert not any(x["kode"] == "jalan_tanpa_lintasan" for x in temuan)


def test_keyframe_xy_renderer_dianggap_perpindahan():
    cerita = {"shot": [{"boneka": [{
        "id": 1, "x": [[0, 100], [2, 240], [4, 420]],
        "y": [[0, 200], [4, 260]], "gerak": "jalan",
    }]}]}
    temuan = periksa_penataan_panggung(cerita)
    assert not any(x["kode"] == "jalan_tanpa_lintasan" for x in temuan)


def test_posisi_tetap_tetap_ditolak_meski_gerak_kaki_aktif():
    cerita = {"shot": [{"boneka": [{
        "id": 1, "x": [[0, 100], [4, 100]], "y": 200, "jalan": 1,
    }]}]}
    temuan = periksa_penataan_panggung(cerita)
    assert any(x["kode"] == "jalan_tanpa_lintasan" and x["tingkat"] == "gagal"
               for x in temuan)


def test_adegan_motor_jembatan_memenuhi_kontrak_penataan_panggung():
    import json
    from pathlib import Path

    spec = json.loads(
        (Path(__file__).parent / "data" / "adegan_uji_visual.json").read_text(encoding="utf-8")
    )
    cerita = spec["cerita"]
    assert cerita.get("pemeriksaan_penataan_panggung") is True
    gagal = [item for item in periksa_penataan_panggung(cerita) if item["tingkat"] == "gagal"]
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
    temuan = periksa_penataan_panggung(cerita)
    assert any(x["kode"] == "jalan_tanpa_lintasan" and x["tingkat"] == "gagal"
               for x in temuan)

def test_kontinuitas_memeriksa_awal_lintasan_shot_berikutnya():
    cerita = {"shot": [
        {"boneka": [{"id": 1, "x": [[0, 100], [4, 200]], "y": 200}]},
        {"boneka": [{"id": 1, "x": [[0, 650], [4, 700]], "y": 200}]},
    ]}
    temuan = periksa_penataan_panggung(cerita)
    assert any(
        x["kode"] == "loncatan_posisi" and x["shot"] == 1 and x["tokoh"] == "1"
        for x in temuan
    )


def test_kontinuitas_lolos_bila_awal_shot_menyambung_akhir_sebelumnya():
    cerita = {"shot": [
        {"boneka": [{"id": 1, "x": [[0, 100], [4, 200]], "y": 200}]},
        {"boneka": [{"id": 1, "x": [[0, 200], [4, 280]], "y": 200}]},
    ]}
    temuan = periksa_penataan_panggung(cerita)
    assert not any(x["kode"] == "loncatan_posisi" for x in temuan)


def test_renderer_mendukung_pengendara_terikat_dan_lepas_saat_jatuh():
    from pathlib import Path

    sumber = (Path(__file__).parents[1] / "mesin-video" / "papan" / "cerita.js").read_text(encoding="utf-8")
    assert "b.kendaraan_id" in sumber
    assert "b.lepas_kendaraan_at" in sumber
    assert "mengendarai_motor:" in sumber


def test_pengendara_menghadap_samping_dan_memegang_setang():
    akar = Path(__file__).resolve().parents[1]
    cerita = __import__("json").loads((akar / "tests/data/adegan_uji_visual.json").read_text())["cerita"]
    sumber = (akar / "mesin-video/papan/cerita.js").read_text()
    for indeks in (0, 1, 2):
        pengendara = next(b for b in cerita["shot"][indeks]["boneka"] if b["id"] == 1)
        assert pengendara["profil"] == "kanan"
    assert 'b.profil === "kanan"' in sumber
    assert "profilMotor: (b.profil ===" in sumber
    assert "const H = o.profilMotor ? [218, -284 + nafas + (sg < 0 ? -7 : 0)]" in sumber
    assert 'M -30 ${-396 + nafas} Q 22 ${-420 + nafas}' in sumber
    assert 'points="-4 ${hy0} -82 ${hy0 + 72} -142 ${hy0 + 108}"' in sumber
    assert 'M -4 ${-414 + nafas} L 34 ${-414 + nafas}' in sumber
    assert 'S = o.profilMotor ? [34 + (sg < 0 ? -8 : 8)' in sumber



def test_perencanaan_panggung_menempatkan_pelaku_di_sisi_visual():
    cerita = {"shot": [{
        "benda": [{"id": "dinding_1", "x": 500, "y": 900}],
        "boneka": [{"id": 1}, {"id": 2}, {"id": 3}],
        "penataan_panggung": {"otomatis": True, "visual_id": "dinding_1", "pelaku": [1, 2],
                     "sisi_pelaku": 1, "jarak_pelaku": 60, "jarak_lawan": 240}
    }]}
    hasil = rencanakan_penataan_panggung(cerita)
    assert hasil[0]["status"] == "diterapkan"
    assert cerita["shot"][0]["boneka"][0]["x"] == 560
    assert cerita["shot"][0]["boneka"][1]["x"] == 560
    assert cerita["shot"][0]["boneka"][2]["x"] == 260
    assert all(x["y"] == 900 for x in cerita["shot"][0]["boneka"])


def test_perencanaan_panggung_menghormati_posisi_manual():
    cerita = {"shot": [{
        "benda": [{"id": "objek", "x": 500, "y": 900}],
        "boneka": [{"id": 1, "x": 123, "y": 456}],
        "penataan_panggung": {"otomatis": True, "visual_id": "objek", "pelaku": [1]}
    }]}
    rencanakan_penataan_panggung(cerita)
    assert cerita["shot"][0]["boneka"][0]["x"] == 123
    assert cerita["shot"][0]["boneka"][0]["y"] == 456


def test_perencanaan_panggung_dapat_mengganti_posisi_manual_dengan_paksa():
    cerita = {"shot": [{
        "benda": [{"id": "objek", "x": 500, "y": 900}],
        "boneka": [{"id": 1, "x": 123, "y": 456}],
        "penataan_panggung": {"otomatis": True, "visual_id": "objek", "pelaku": [1], "paksa": True}
    }]}
    rencanakan_penataan_panggung(cerita)
    assert cerita["shot"][0]["boneka"][0]["x"] == 570
    assert cerita["shot"][0]["boneka"][0]["y"] == 900


def test_periksa_penataan_panggung_mendeteksi_perubahan_arah_tanpa_putar_balik():
    cerita = {"shot": [
        {"boneka": [{"id": 1, "x": [[0, 100], [4, 300]], "y": 200, "gerak": "jalan"}]},
        {"boneka": [{"id": 1, "x": [[0, 300], [4, 100]], "y": 200, "gerak": "jalan"}]},
    ]}
    temuan = periksa_penataan_panggung(cerita)
    assert any(x["kode"] == "arah_lintasan_berubah" and x["shot"] == 1 for x in temuan)


def test_papan_buat_mengintegrasikan_penataan_panggung_otomatis():
    sumber = (Path(__file__).parents[1] / "mesin-video" / "papan_buat.py").read_text(encoding="utf-8")
    assert "rencanakan_penataan_panggung(cerita)" in sumber
    assert 'if cerita.get("penataan_panggung_otomatis")' in sumber

def test_rencana_blocking_mengaitkan_peristiwa_ke_shot_tanpa_mengarang_gerak():
    from newmotion.penataan_panggung import susun_rencana_blocking

    rencana = {
        "adegan": [{
            "id": "beat-001",
            "peristiwa": [{
                "id": "peristiwa-1",
                "aktor_id": "tokoh-penolong",
                "aksi": "menghampiri",
                "sasaran": "Pengendara",
                "sasaran_tokoh_id": "tokoh-pengendara",
                "tujuan": "menolong",
            }],
        }]
    }
    cerita = {"shot": [
        {"_beat_id": "beat-001", "boneka": [], "benda": []},
        {"_beat_id": "beat-001", "boneka": [], "benda": []},
    ]}

    hasil = susun_rencana_blocking(rencana, cerita)

    assert hasil["tahap"] == "kontrak_semantik"
    assert hasil["peristiwa"][0]["aktor_id"] == "tokoh-penolong"
    assert hasil["peristiwa"][0]["sasaran_tokoh_id"] == "tokoh-pengendara"
    assert [s["peristiwa_ids"] for s in hasil["shot"]] == [
        ["peristiwa-1"], ["peristiwa-1"]
    ]
    assert hasil["diagnostik"] == []
    # Fungsi hanya membuat kontrak; spesifikasi geometri renderer tidak disentuh.
    assert cerita["shot"][0]["boneka"] == []
    assert "lintasan" not in hasil["peristiwa"][0]


def test_rencana_blocking_tidak_mengarang_identitas_aktor_atau_aksi():
    from newmotion.penataan_panggung import susun_rencana_blocking

    hasil = susun_rencana_blocking(
        {"adegan": [{
            "id": "beat-002",
            "peristiwa": [{"id": "peristiwa-2", "aktor": "Orang asing"}],
        }]},
        {"shot": [{"_beat_id": "beat-002"}]},
    )

    assert hasil["peristiwa"][0]["status"] == "perlu_pelengkapan_semantik"
    assert hasil["peristiwa"][0]["aktor_id"] is None
    assert hasil["diagnostik"][0]["kode"] == "peristiwa_belum_lengkap_untuk_blocking"


def test_rencana_blocking_mencatat_peristiwa_tanpa_shot_tertaut():
    from newmotion.penataan_panggung import susun_rencana_blocking

    hasil = susun_rencana_blocking(
        {"adegan": [{
            "id": "beat-003",
            "peristiwa": [{"id": "peristiwa-3", "aktor_id": "tokoh-a", "aksi": "berjalan"}],
        }]},
        {"shot": []},
    )

    assert any(
        item["kode"] == "beat_peristiwa_tidak_memiliki_shot"
        for item in hasil["diagnostik"]
    )

