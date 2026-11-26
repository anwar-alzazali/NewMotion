"""Putaran periksa visual: lembar frame, validasi temuan, dan revisi rencana (LLM palsu)."""
import copy
import json
from pathlib import Path

import pytest

from newmotion.application.lembar_periksa import waktu_frame
from newmotion.application.pengarah_inti import arahkan_naskah
from newmotion.paket_genre.kisah_islami import periksa_visual as P
from newmotion.paket_genre.kisah_islami.rencana_sutradara import terapkan_rencana

DATA = Path(__file__).parent / "data"
NASKAH = json.loads((DATA / "tolok_ukur" / "yajuj1.json").read_text(encoding="utf-8"))
RENCANA = json.loads((DATA / "rencana" / "yajuj1.json").read_text(encoding="utf-8"))


def _spek(rencana=RENCANA):
    return arahkan_naskah(terapkan_rencana(dict(NASKAH), rencana))[0]


def test_waktu_frame_satu_per_shot_di_dalam_shot():
    spek = _spek()
    shots = spek["cerita"]["shot"]
    w = waktu_frame(spek)
    assert len(w) == len(shots) and w[0][0] == 1
    batas = [s["at"] for s in shots[1:]] + [spek["durasi"]]
    for (_, t), s, b in zip(w, shots, batas):
        assert s["at"] <= t < b


def test_validasi_temuan():
    assert P.validasi_temuan({"lulus": True, "temuan": []}, 11) == []
    galat = P.validasi_temuan({"temuan": [{"beat": 12, "berat": "parah", "masalah": ""}]}, 11)
    assert len(galat) == 3
    assert P.validasi_temuan([], 11)


def test_pesan_periksa_memuat_narasi_dan_rencana_tiap_beat():
    p = P.pesan_periksa(NASKAH, RENCANA)
    assert p.count("narasi:") == len(NASKAH["adegan"]) and "DIGALI" in p


def _palsu(jawaban):
    """http palsu: mengeluarkan jawaban berurutan, mencatat badan permintaan."""
    catat = []

    def http(url, badan, kepala, batas):
        catat.append(badan)
        return {"content": [{"type": "text", "text": jawaban[len(catat) - 1]}],
                "usage": {"input_tokens": 1000, "output_tokens": 200}}
    return http, catat


ADA_CHROMIUM = any(Path(p).exists() for p in ("/opt/pw-browsers", Path.home() / ".cache" / "ms-playwright"))


@pytest.mark.skipif(not ADA_CHROMIUM, reason="butuh chromium playwright")
def test_berputar_revisi_sampai_lulus(tmp_path, monkeypatch):
    pytest.importorskip("playwright")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "palsu")
    monkeypatch.setenv("NEWMOTION_MODEL_PERIKSA_VISUAL", "claude-sonnet-5-5")
    monkeypatch.setenv("NEWMOTION_MODEL_SUTRADARA", "claude-sonnet-5-5")
    baru = copy.deepcopy(RENCANA)
    baru["beat"][4]["teks_layar"] = "UTUH LAGI"
    temuan = {"lulus": False, "temuan": [{"beat": 5, "berat": "berat", "masalah": "lubang masih terlihat",
                                          "saran": "lubang 0"}], "catatan": "-"}
    http, catat = _palsu([json.dumps(temuan), json.dumps(baru), json.dumps({"lulus": True, "temuan": []})])
    rencana, _, log = P.berputar(NASKAH, RENCANA, tmp_path, putaran=2, http=http)
    assert len(catat) == 3 and rencana["beat"][4]["teks_layar"] == "UTUH LAGI"
    assert [e["putaran"] for e in log] == [0, 1] and log[0]["revisi"] == "claude-sonnet-5-5"
    assert catat[0]["messages"][0]["content"][0]["type"] == "image"       # lembar dikirim sebagai gambar
    assert "lubang masih terlihat" in catat[1]["messages"][0]["content"][-1]["text"]  # temuan masuk revisi
    assert all(Path(p).exists() for p in log[-1]["lembar"])
