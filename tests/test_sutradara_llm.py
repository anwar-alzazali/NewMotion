"""Rencana sutradara (LLM) -> validator -> papan: format, adab, katalog, dan integrasi pengarah."""
import copy
import json
from pathlib import Path

import pytest

from newmotion.application.katalog_renderer import katalog, katalog_subjek
from newmotion.application.pengarah_inti import arahkan_naskah
from newmotion.paket_genre.kisah_islami import sutradara_llm as S
from newmotion.paket_genre.kisah_islami.rencana_sutradara import terapkan_rencana, validasi_rencana

DATA = Path(__file__).parent / "data"
NASKAH = json.loads((DATA / "tolok_ukur" / "yajuj1.json").read_text(encoding="utf-8"))
RENCANA = json.loads((DATA / "rencana" / "yajuj1.json").read_text(encoding="utf-8"))
NARASI = [a["teks"] for a in NASKAH["adegan"]]


def _shots(rencana=RENCANA, naskah=NASKAH):
    spek, _, _ = arahkan_naskah(terapkan_rencana(naskah, rencana))
    return spek["cerita"]["shot"]


def test_katalog_dibaca_dari_renderer():
    k = katalog()
    assert {"ngarai", "penggali", "bahtera", "arus"} <= set(k)
    assert {"lubang", "jebol"} <= set(k["ngarai"]["parameter"])
    assert "kartu_dalil" in k and "kartu_dalil" not in katalog_subjek()


def test_skill_memuat_katalog_dan_tanpa_contoh_tolok_ukur():
    skill = S.skill_sutradara()
    assert "{KATALOG}" not in skill and "- ngarai:" in skill
    contoh = skill[skill.index("## Contoh"):]
    for nama in ("Ya'juj", "Nuh", "Mahsyar", "Dabbah", "kubur"):
        assert nama.lower() not in contoh.lower()  # contoh tidak boleh membocorkan cerita uji


def test_rencana_contoh_lolos_validator_lengkap():
    assert S.validasi_lengkap(RENCANA, NASKAH) == []


def test_rencana_diterjemahkan_ke_papan():
    shots = _shots()
    jebol = [b for s in shots for b in s["benda"] if b["jenis"] == "ngarai" and b.get("jebol")]
    assert jebol and jebol[0]["jebol"][-1][1] == 1.0          # [awal, akhir] -> kunci waktu
    pertama = shots[0]
    assert pertama["boneka"] == []                              # kamu: tidak
    assert any(t["teks"] == "DIGALI\nSETIAP HARI" for t in pertama["teks"])
    gali = next(b for b in pertama["benda"] if b["jenis"] == "penggali")
    dinding = next(b for b in pertama["benda"] if b["jenis"] == "ngarai")
    assert gali["y"] < dinding["y"]                              # di lubang dinding, bukan di tanah
    assert "_di_lubang" not in gali
    assert any("guncang" in s["kamera"] for s in shots)


def test_validator_menolak_kesalahan_umum():
    r = copy.deepcopy(RENCANA)
    r["beat"][0]["subjek"].append({"jenis": "naga", "tempat": "tengah"})
    r["beat"][1]["bukti"] = "kalimat karangan yang tidak ada di narasi"
    r["beat"][2]["subjek"][0]["keadaan"] = {"terbang": 1}
    r["beat"][3]["kamu"] = "pahlawan"
    r["beat"].pop()
    galat = "\n".join(validasi_rencana(r, NARASI))
    for kata in ("naga", "bukti", "terbang", "kamu harus", "tepat satu entri"):
        assert kata in galat


def test_validator_menolak_sosok_manusia_untuk_rasulullah():
    naskah = {"judul": "uji", "genre": "kisah_islami", "konteks_konten": "islami",
              "adegan": [{"nama": "a1", "teks": "Rasulullah, pemimpin umat ini, berdiri di atas bukit."}]}
    r = {"objek_inti": None, "beat": [{"beat": 1, "bukti": "Rasulullah, pemimpin umat ini", "kamu": "tidak",
                                       "subjek": [{"jenis": "pemimpin", "tempat": "tengah"}],
                                       "kamera": {"bidikan": "lebar", "aksen": None}, "teks_layar": None, "klimaks": False}]}
    assert any(g.startswith("adab:") for g in S.validasi_lengkap(r, naskah))


def test_llm_tiruan_dipakai_lewat_rantai_model(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "uji")
    monkeypatch.setenv("NEWMOTION_MODEL_SUTRADARA", "claude-sonnet-5-5")
    terkirim = {}

    def http(url, badan, kepala, batas):
        terkirim["badan"] = badan
        return {"content": [{"type": "text", "text": json.dumps(RENCANA)}],
                "usage": {"input_tokens": 9000, "output_tokens": 4000}}

    j = S.buat_rencana(NASKAH, http=http)
    assert j.data == RENCANA and j.biaya_usd == pytest.approx((9000 * 2 + 4000 * 10) / 1e6)
    assert "1. Ada satu dinding" in terkirim["badan"]["messages"][0]["content"][-1]["text"]


def test_tanpa_rencana_pengarah_aturan_tidak_berubah():
    tanpa, _, _ = arahkan_naskah(NASKAH)
    assert all("rencana" not in a for a in NASKAH["adegan"])
    assert tanpa["cerita"]["shot"][0]["boneka"]  # pengarah aturan tetap menaruh tokoh "kamu"
