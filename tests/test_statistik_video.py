import json

import pytest

from newmotion.application import statistik_video as S


def _video(folder, nama, *, hook, beat=8, klimaks=False, tayang=None, platform="tiktok", hari=7):
    d = folder / nama
    d.mkdir(parents=True)
    (d / "status.json").write_text(json.dumps({"judul": nama, "genre": "kisah_islami"}), encoding="utf-8")
    beats = [{"narasi": hook if i == 0 else "lanjut cerita.", "peran": ["Firaun"] if i == 1 else []} for i in range(beat)]
    (d / "naskah.json").write_text(json.dumps({"beat": beats, "dalil": [{}]}), encoding="utf-8")
    (d / "rencana.json").write_text(json.dumps({"beat": [{"beat": 1, "klimaks": klimaks, "suara": {"efek": [{"nama": "braam"}]}}]}), encoding="utf-8")
    if tayang is not None:
        S.catat_hasil(d, {"platform": platform, "hari": hari, "tayang": tayang, "suka": tayang // 10, "komentar": 5, "bagikan": 2}, waktu="w")
    return d


def test_jenis_hook():
    assert S.jenis_hook("Apakah kamu siap?") == "pertanyaan"
    assert S.jenis_hook("Kamu akan dibangkitkan tanpa alas kaki.") == "menyapa_kamu"
    assert S.jenis_hook("3 detik terakhir Firaun.") == "angka"
    assert S.jenis_hook("Jangan tunda tobatmu.") == "peringatan"
    assert S.jenis_hook("Laut terbelah dua.") == "pernyataan"


def test_ciri_dari_berkas_antrean(tmp_path):
    d = _video(tmp_path, "v1", hook="Kamu akan tenggelam? Firaun juga.", klimaks=True)
    c = S.simpan_ciri(d)
    assert c["jenis_hook"] == "pertanyaan" and c["jumlah_beat"] == 8 and c["ada_klimaks"] and c["tokoh"] == ["Firaun"]
    assert c["jumlah_efek"] == 1 and json.loads((d / "ciri.json").read_text())["id"] == "v1"


def test_catat_hasil_menimpa_platform_hari_yang_sama(tmp_path):
    d = tmp_path / "v"
    d.mkdir()
    S.catat_hasil(d, {"platform": "tiktok", "hari": 1, "tayang": 10}, waktu="a")
    S.catat_hasil(d, {"platform": "facebook", "hari": 1, "tayang": 7}, waktu="b")
    isi = S.catat_hasil(d, {"platform": "tiktok", "hari": 1, "tayang": 99}, waktu="c")
    assert [(c["platform"], c["tayang"]) for c in isi["catatan"]] == [("facebook", 7), ("tiktok", 99)]
    with pytest.raises(ValueError):
        S.catat_hasil(d, {"platform": "ig", "hari": 1, "tayang": 1}, waktu="d")


def test_nilai_pakai_hari_7_bila_ada():
    s = {"catatan": [{"platform": "tiktok", "hari": 1, "tayang": 100, "suka": 10, "komentar": 0, "bagikan": 0},
                     {"platform": "tiktok", "hari": 7, "tayang": 400, "suka": 40, "komentar": 0, "bagikan": 4}]}
    v = S.nilai(s, "tiktok")
    assert v["hari"] == 7 and v["tayang"] == 400 and v["interaksi"] == pytest.approx(11.0)
    assert S.nilai(s, "facebook") is None


def test_analisis_memperingatkan_data_kurang(tmp_path):
    for i in range(4):
        _video(tmp_path, f"a{i}", hook="Apakah kamu siap?", tayang=1000 + i)
    teks = S.analisis(tmp_path)
    assert "BELUM bisa dipercaya" in teks and "tiktok: 4 video" in teks and "facebook: 0 video" in teks


def test_analisis_mengusulkan_dengan_kekuatan_bukti(tmp_path):
    for i in range(12):
        _video(tmp_path, f"p{i}", hook="Apakah kamu siap?", tayang=5000 + i)
        _video(tmp_path, f"n{i}", hook="Laut terbelah dua.", tayang=1000 + i)
    teks = S.analisis(tmp_path)
    assert "BELUM" not in teks
    assert "jenis hook = pertanyaan unggul" in teks and "n 12 vs 12" in teks and "bukti cukup" in teks


def test_analisis_tanpa_data(tmp_path):
    assert "Belum ada hasil tercatat" in S.analisis(tmp_path)
