"""Sutradara hibrida produksi: rencana LLM disimpan, jatuh ke aturan bila gagal."""
import json
from pathlib import Path

from newmotion.paket_genre.kisah_islami import sutradara_hibrida as H

DATA = Path(__file__).parent / "data"
NASKAH = json.loads((DATA / "tolok_ukur" / "yajuj1.json").read_text(encoding="utf-8"))
RENCANA = json.loads((DATA / "rencana" / "yajuj1.json").read_text(encoding="utf-8"))


def _palsu(jawaban):
    def http(url, badan, kepala, batas):
        return {"content": [{"type": "text", "text": jawaban}], "usage": {"input_tokens": 1000, "output_tokens": 300}}
    return http


def test_mode_llm_menyimpan_rencana_dan_memakainya(tmp_path, monkeypatch):
    monkeypatch.setenv("NEWMOTION_SUTRADARA", "llm")
    monkeypatch.setenv("NEWMOTION_PERIKSA_PUTARAN", "0")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "palsu")
    monkeypatch.setenv("NEWMOTION_MODEL_SUTRADARA", "claude-sonnet-5-5")
    spek, info = H.arahkan_hibrida(NASKAH, tmp_path, http=_palsu(json.dumps(RENCANA)))
    assert info["mode"] == "llm" and info["biaya_usd"] > 0
    assert H.baca_rencana(tmp_path) == RENCANA
    assert spek["rekaman"] and spek["musik"] is False   # suara dari rencana


def test_llm_gagal_tanpa_cadangan_menjadi_galat_jelas(tmp_path, monkeypatch):
    import pytest
    monkeypatch.setenv("NEWMOTION_SUTRADARA", "llm")
    monkeypatch.setenv("NEWMOTION_PERIKSA_PUTARAN", "0")
    monkeypatch.setenv("NEWMOTION_CADANGAN_ATURAN", "0")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "palsu")
    monkeypatch.setenv("NEWMOTION_MODEL_SUTRADARA", "claude-sonnet-5-5")
    with pytest.raises(RuntimeError, match="sutradara LLM gagal"):
        H.arahkan_hibrida(NASKAH, tmp_path, http=_palsu("bukan json"))
    assert (tmp_path / "sutradara_galat.txt").read_text().startswith("LLM tahap")


def test_llm_gagal_jatuh_ke_aturan(tmp_path, monkeypatch):
    monkeypatch.setenv("NEWMOTION_CADANGAN_ATURAN", "1")
    monkeypatch.setenv("NEWMOTION_SUTRADARA", "llm")
    monkeypatch.setenv("NEWMOTION_PERIKSA_PUTARAN", "0")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "palsu")
    monkeypatch.setenv("NEWMOTION_MODEL_SUTRADARA", "claude-sonnet-5-5")
    spek, info = H.arahkan_hibrida(NASKAH, tmp_path, http=_palsu("bukan json"))
    assert info["mode"] == "aturan" and "gagal" in info["catatan"]
    assert spek["cerita"]["shot"] and H.baca_rencana(tmp_path) is None


def test_tanpa_kunci_memakai_aturan(tmp_path, monkeypatch):
    monkeypatch.setenv("NEWMOTION_CADANGAN_ATURAN", "1")
    monkeypatch.setenv("NEWMOTION_SUTRADARA", "llm")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    _, info = H.arahkan_hibrida(NASKAH, tmp_path)
    assert info["mode"] == "aturan" and "kunci" in info["catatan"]
