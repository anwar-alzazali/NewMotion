"""Uji tidak pernah memanggil LLM sungguhan: sutradara produksi dipaksa ke aturan kecuali uji memintanya."""
import pytest


@pytest.fixture(autouse=True)
def _tanpa_llm_sungguhan(monkeypatch):
    monkeypatch.setenv("NEWMOTION_SUTRADARA", "aturan")
