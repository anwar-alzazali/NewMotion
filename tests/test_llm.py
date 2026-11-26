"""Pemanggil LLM bersama: rantai model, cadangan, validator, JSON, gambar, biaya (tanpa jaringan)."""
import pytest

from newmotion.infrastructure import llm

KONFIG = {"tahap": {"sutradara": {"model": ["claude-sonnet-5-5", "gemini"]}},
          "harga": {"claude-sonnet-5-5": [2.0, 10.0], "gemini": [0.0, 0.0]}}


@pytest.fixture(autouse=True)
def kunci(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "uji")
    monkeypatch.setenv("GEMINI_API_KEY", "uji")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-9-flash")
    monkeypatch.delenv("NEWMOTION_MODEL_SUTRADARA", raising=False)


def _palsu(jawaban_claude=None, jawaban_gemini=None, galat_claude=None):
    panggilan = []

    def http(url, badan, kepala, batas):
        panggilan.append((url, badan))
        if "anthropic" in url:
            if galat_claude:
                raise RuntimeError(galat_claude)
            return {"content": [{"type": "text", "text": jawaban_claude}],
                    "usage": {"input_tokens": 1000, "output_tokens": 500}}
        return {"candidates": [{"content": {"parts": [{"text": jawaban_gemini}]}}],
                "usageMetadata": {"promptTokenCount": 900, "candidatesTokenCount": 400}}
    return http, panggilan


def test_model_utama_dipakai_dan_biaya_dihitung():
    http, panggilan = _palsu('```json\n{"ok": 1}\n```')
    j = llm.panggil("sutradara", "skill", "isi", json=True, http=http, konfigurasi=KONFIG)
    assert j.data == {"ok": 1} and j.model == "claude-sonnet-5-5"
    assert j.biaya_usd == pytest.approx((1000 * 2 + 500 * 10) / 1e6)
    assert len(panggilan) == 1
    assert panggilan[0][1]["system"][0]["cache_control"] == {"type": "ephemeral"}


def test_cadangan_dipakai_saat_utama_gagal():
    http, _ = _palsu(jawaban_gemini='{"ok": 2}', galat_claude="HTTP 529")
    j = llm.panggil("sutradara", "s", "p", json=True, http=http, konfigurasi=KONFIG)
    assert j.model == "gemini-9-flash" and j.data == {"ok": 2} and j.biaya_usd == 0
    assert any("HTTP 529" in x for x in j.percobaan)


def test_ditolak_validator_naik_ke_model_berikutnya_dengan_daftar_galat():
    http, panggilan = _palsu('{"jenis": "naga"}', '{"jenis": "bahtera"}')
    validasi = lambda d: [] if d["jenis"] == "bahtera" else [f"jenis {d['jenis']} tidak ada di katalog"]  # noqa: E731
    j = llm.panggil("sutradara", "s", "p", json=True, validasi=validasi, http=http, konfigurasi=KONFIG)
    assert j.data == {"jenis": "bahtera"}
    assert [p[0].split("/")[2] for p in panggilan] == ["api.anthropic.com"] * 2 + ["generativelanguage.googleapis.com"]
    assert "naga tidak ada di katalog" in panggilan[1][1]["messages"][0]["content"][-1]["text"]  # ulang model sama
    teks_gemini = panggilan[2][1]["contents"][0]["parts"][-1]["text"]
    assert "naga tidak ada di katalog" in teks_gemini


def test_tanpa_ulang_validasi_langsung_ke_cadangan():
    http, panggilan = _palsu('{"jenis": "naga"}', '{"jenis": "bahtera"}')
    validasi = lambda d: [] if d["jenis"] == "bahtera" else ["salah"]
    llm.panggil("sutradara", "s", "p", json=True, validasi=validasi, http=http, konfigurasi=KONFIG, ulang_validasi=0)
    assert len(panggilan) == 2


def test_semua_gagal_memberi_riwayat():
    http, _ = _palsu("bukan json", "juga bukan")
    with pytest.raises(llm.GalatLLM) as e:
        llm.panggil("sutradara", "s", "p", json=True, http=http, konfigurasi=KONFIG)
    assert len(e.value.riwayat) == 4  # tiap model: percobaan + satu ulang


def test_gambar_dikirim_ke_kedua_penyedia():
    http, panggilan = _palsu(galat_claude="x", jawaban_gemini="baik")
    llm.panggil("sutradara", "s", "lihat", gambar=[llm.Gambar(b"\x89PNG", "image/png")], http=http, konfigurasi=KONFIG)
    assert panggilan[0][1]["messages"][0]["content"][0]["type"] == "image"
    assert "inline_data" in panggilan[1][1]["contents"][0]["parts"][0]


def test_rantai_bisa_ditimpa_variabel_lingkungan(monkeypatch):
    monkeypatch.setenv("NEWMOTION_MODEL_SUTRADARA", "gemini")
    assert llm.rantai_model("sutradara", KONFIG) == ["gemini"]


def test_konfigurasi_repo_mengatur_semua_tahap():
    k = llm._muat_konfigurasi()
    for tahap in ("rapikan", "naskah", "sutradara", "periksa_visual", "chat"):
        assert llm.rantai_model(tahap, k)
    for model in {m for t in k["tahap"].values() for m in t["model"]}:
        assert model in k["harga"]


def test_gemini_penuh_dicoba_ulang_dengan_jeda(monkeypatch):
    monkeypatch.setattr(llm.time, "sleep", lambda d: None)
    k = {"tahap": {"sutradara": {"model": ["gemini"]}}, "harga": {"gemini": [0, 0]}}
    hitung = {"n": 0}

    def http(url, badan, kepala, batas):
        hitung["n"] += 1
        if hitung["n"] < 3:
            raise RuntimeError("HTTP 503: high demand")
        return {"candidates": [{"content": {"parts": [{"text": '{"ok": 3}'}]}}], "usageMetadata": {}}
    j = llm.panggil("sutradara", "s", "p", json=True, http=http, konfigurasi=k)
    assert j.data == {"ok": 3} and hitung["n"] == 3
