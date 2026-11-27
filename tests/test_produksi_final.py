"""Produksi final: narasi per beat (intonasi, jeda), waktu nyata ke pengarah, papan bersuara. TTS palsu."""
import json
import shutil
import subprocess

import pytest

from newmotion.paket_genre.kisah_islami import narasi_final as N

ADA_FFMPEG = shutil.which("ffmpeg") is not None
BEAT = ["Ada satu dinding yang digali setiap hari.", "Esoknya, dinding itu kembali utuh.",
        "Mereka menembusnya, dan keluar."]
RENCANA = {"beat": [
    {"beat": 1, "suara": {"intonasi": "berat"}},
    {"beat": 2, "suara": {"intonasi": "bisik"}, "klimaks": False},
    {"beat": 3, "suara": {"intonasi": "tegang"}, "klimaks": True}]}


def _tts_palsu(teks, keluaran):
    """Kata berurutan 0,3 dtk per kata (tag ikut sebagai token, seperti ElevenLabs) + audio sunyi."""
    kata, t = [], 0.0
    for w in teks.split():
        kata.append({"teks": w, "t0": round(t, 2), "t1": round(t + 0.25, 2)})
        t += 0.3
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", f"sine=f=220:d={t + 0.5}",
                    "-c:a", "libmp3lame", str(keluaran)], check=True)
    keluaran.with_suffix(".waktu.json").write_text(json.dumps({"kata": kata}), encoding="utf-8")
    return kata


def test_teks_tts_memberi_tag_intonasi_per_beat():
    teks, jumlah = N.teks_tts({"adegan": [{"teks": t} for t in BEAT]}, RENCANA)
    assert teks.splitlines()[0].startswith("[serious]") and teks.splitlines()[1].startswith("[whispers]")
    assert jumlah == [7, 5, 4]


def test_jeda_lebih_panjang_di_sekitar_klimaks():
    assert N.jeda_setelah(RENCANA, 0, 3) == N.JEDA_DASAR
    assert N.jeda_setelah(RENCANA, 1, 3) == N.JEDA_SEBELUM_KLIMAKS
    assert N.jeda_setelah(RENCANA, 2, 3) == 0.0


@pytest.mark.skipif(not ADA_FFMPEG, reason="butuh ffmpeg")
def test_buat_narasi_memotong_merakit_dan_memakai_ulang(tmp_path):
    naskah = {"adegan": [{"teks": t} for t in BEAT]}
    w = N.buat_narasi(naskah, RENCANA, tmp_path, tts_fn=_tts_palsu)
    assert (tmp_path / "narasi.mp3").is_file()
    assert w["waktu_adegan"][0] == 0 and w["waktu_adegan"][1] > w["waktu_adegan"][0]
    assert [len(x) for x in w["waktu_kata"]] == [7, 5, 4]
    assert not any(k["teks"].startswith("[") for k in w["kata"])        # token tag dibuang
    jeda = w["waktu_adegan"][2] - w["waktu_kata"][1][-1][0]
    assert jeda >= N.JEDA_SEBELUM_KLIMAKS                                 # jeda sebelum klimaks
    panggil = []
    N.buat_narasi(naskah, RENCANA, tmp_path, tts_fn=lambda *a: panggil.append(a))
    assert panggil == []                                                  # kredit tidak terpakai dua kali


@pytest.mark.skipif(not ADA_FFMPEG, reason="butuh ffmpeg")
def test_papan_final_mengikuti_waktu_narasi(tmp_path):
    from newmotion.application.produksi_final import papan_final

    d = tmp_path / "kisah"
    d.mkdir()
    (d / "naskah.json").write_text(json.dumps({"judul": "Dinding", "dalil": [],
                                                "beat": [{"narasi": t} for t in BEAT]}), encoding="utf-8")
    (d / "status.json").write_text(json.dumps({"tahap": {"tinjau_visual": "selesai", "dalil": "selesai"}}), encoding="utf-8")
    papan = papan_final("kisah", folder=tmp_path, tts_fn=_tts_palsu)
    spek = json.loads(papan.read_text(encoding="utf-8"))
    w = json.loads((d / "audio" / "waktu_adegan.json").read_text(encoding="utf-8"))
    awal = {}
    for sh in spek["cerita"]["shot"]:
        awal.setdefault(sh["_adegan"], sh["at"])
    assert [round(awal[i], 2) for i in range(3)] == [round(x, 2) for x in w["waktu_adegan"]]
    assert spek["suara"] == "audio/narasi.mp3" and "durasi" not in spek


def test_render_final_diblokir_sebelum_visual_disetujui(tmp_path):
    from newmotion.application.produksi_final import papan_final

    d = tmp_path / "kisah"
    d.mkdir()
    (d / "naskah.json").write_text(json.dumps({"judul": "x", "beat": [{"narasi": "a"}]}), encoding="utf-8")
    (d / "status.json").write_text(json.dumps({"tahap": {"tinjau_visual": "jalan", "dalil": "selesai"}}), encoding="utf-8")
    with pytest.raises(ValueError, match="setelah pratinjau visual disetujui"):
        papan_final("kisah", folder=tmp_path, tts_fn=_tts_palsu)
