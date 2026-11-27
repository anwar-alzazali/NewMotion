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


def _tts_palsu(teks, keluaran, suara=None):
    import re
    import subprocess
    kata = [w for w in re.sub(r"\[[^\]]*\]", " ", teks).split() if re.search(r"\w", w)]
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", f"sine=d={len(kata) * 0.4 + 0.5}",
                    "-c:a", "libmp3lame", str(keluaran)], check=True)
    hasil = [{"teks": w, "t0": round(i * 0.4, 2), "t1": round(i * 0.4 + 0.3, 2)} for i, w in enumerate(kata)]
    keluaran.with_suffix(".waktu.json").write_text(json.dumps({"kata": hasil}), encoding="utf-8")
    _tts_palsu.panggil += 1
    return hasil


def test_narasi_dari_json_mengisi_waktu_shot_dan_dipakai_ulang(tmp_path):
    d = tmp_path / "antrean" / "uji-narasi"
    d.mkdir(parents=True)
    f = d / "papan_manual.json"
    spek = {"cerita": {"shot": [
        {"narasi": "Kamu akan dibangkitkan tanpa alas kaki", "intonasi": "berat", "teks": [{"at": "@dibangkitkan", "teks": "X"}]},
        {"durasi": 2.0},
        {"narasi": "Lalu semua manusia berkumpul", "jeda": 0.8},
        {"narasi": "Dan matahari didekatkan"}]}}
    f.write_text(json.dumps(spek), encoding="utf-8")
    _tts_palsu.panggil = 0
    p, ada = J.siapkan(f, tts_fn=_tts_palsu)
    try:
        hasil = json.loads(p.read_text(encoding="utf-8"))
        at = [s["at"] for s in hasil["cerita"]["shot"]]
        assert ada and at[0] == 0 and at[1] < at[2] < at[3]
        assert at[2] - at[1] >= 2.0  # layar tenang 2 detik sebelum shot 3
        assert not any(k in s for s in hasil["cerita"]["shot"] for k in ("narasi", "intonasi", "jeda", "durasi"))
        assert (d / "audio" / "narasi.mp3").is_file() and hasil["suara"].endswith("narasi.mp3")
        J.siapkan(f, tts_fn=_tts_palsu)
        assert _tts_palsu.panggil == 1  # teks sama: kredit tidak terpakai lagi
    finally:
        p.unlink()


def test_narasi_arab_dan_shot_diam_tanpa_durasi_ditolak():
    with pytest.raises(ValueError, match="Arab"):
        J.susun_teks_narasi({"cerita": {"shot": [{"narasi": "Allah berfirman بِسْمِ"}]}})
    with pytest.raises(ValueError, match="durasi"):
        J.susun_teks_narasi({"cerita": {"shot": [{"narasi": "Satu dua"}, {}]}})
