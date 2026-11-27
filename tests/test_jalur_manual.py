import json

import pytest

from newmotion.application import jalur_manual as J


def test_jalur_spek_hanya_tempat_papan():
    assert J.jalur_spek("mesin-video/papan/kisah/mahsyar1.json").is_file()
    for buruk in ["../etc/passwd.json", "/tmp/x.json", "mesin-video/papan/../../x.json", "bot/worker.json"]:
        with pytest.raises((ValueError, FileNotFoundError)):
            J.jalur_spek(buruk)


def test_mahsyar1_disiapkan_dengan_narasi():
    p, ada = J.siapkan(J.jalur_spek("mesin-video/papan/kisah/mahsyar1.json"))
    assert ada and p.name == "mahsyar1.json"


def test_papan_kiriman_disalin_ke_folder_kisah(tmp_path):
    d = tmp_path / "antrean" / "uji-manual"
    d.mkdir(parents=True)
    f = d / "papan_manual.json"
    f.write_text(json.dumps({"cerita": {"shot": [{"at": 0}]}, "latar": "gelap"}), encoding="utf-8")
    p, ada = J.siapkan(f)
    try:
        assert not ada and p.parent == J.DASAR_KISAH
    finally:
        p.unlink()


def test_papan_kosong_atau_rusak_ditolak(tmp_path):
    f = tmp_path / "x.json"
    f.write_text("{rusak", encoding="utf-8")
    with pytest.raises(ValueError, match="JSON tidak terbaca"):
        J.baca_spek(f)
    f.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="kosong"):
        J.baca_spek(f)


def test_suara_yang_dirujuk_harus_ada(tmp_path):
    d = tmp_path / "antrean" / "uji-suara"
    d.mkdir(parents=True)
    f = d / "papan_manual.json"
    f.write_text(json.dumps({"cerita": {"shot": [{"at": 0}]}, "suara": "../../audio_manual/tidak_ada.mp3"}), encoding="utf-8")
    with pytest.raises(FileNotFoundError):
        J.siapkan(f)
