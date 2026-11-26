"""Pemanggil LLM bersama: model per tahap, cadangan otomatis, gambar, mode JSON, dan biaya.

Contoh:
    from newmotion.infrastructure.llm import panggil
    j = panggil("sutradara", SKILL, isi, json=True, validasi=validasi_rencana)
    j.data, j.model, j.biaya_usd

Urutan model per tahap diambil dari config/model.toml (atau NEWMOTION_MODEL_<TAHAP>).
Bila panggilan gagal (jaringan, batas, kunci tidak ada), JSON tidak terbaca, atau
`validasi` mengembalikan galat, model berikutnya dicoba dengan pesan yang sama ditambah
daftar galat sebelumnya, sehingga model cadangan tahu apa yang harus dihindari.
"""
from __future__ import annotations

import base64
import json
import os
import re
import time
import tomllib
import urllib.error
import urllib.request
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

AKAR = Path(__file__).resolve().parents[2]
BERKAS_MODEL = AKAR / "config" / "model.toml"
GEMINI_API = "https://generativelanguage.googleapis.com/v1beta"


class GalatLLM(RuntimeError):
    """Semua model dalam rantai gagal; `riwayat` berisi alasan tiap percobaan."""

    def __init__(self, tahap: str, riwayat: list[str]):
        self.riwayat = riwayat
        super().__init__(f"LLM tahap {tahap!r} gagal: " + " | ".join(riwayat))


@dataclass
class Jawaban:
    teks: str
    model: str
    penyedia: str
    token_masuk: int = 0
    token_keluar: int = 0
    biaya_usd: float = 0.0
    data: Any = None
    percobaan: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Gambar:
    data: bytes
    jenis: str = "image/png"

    @classmethod
    def dari_berkas(cls, jalur: str | Path) -> "Gambar":
        p = Path(jalur)
        jenis = "image/jpeg" if p.suffix.lower() in (".jpg", ".jpeg") else "image/png"
        return cls(p.read_bytes(), jenis)


def _muat_konfigurasi(berkas: Path = BERKAS_MODEL) -> dict:
    if not berkas.is_file():
        return {}
    with berkas.open("rb") as f:
        return tomllib.load(f)


def rantai_model(tahap: str, konfigurasi: dict | None = None) -> list[str]:
    timpa = os.environ.get(f"NEWMOTION_MODEL_{tahap.upper()}")
    if timpa:
        return [m.strip() for m in timpa.split(",") if m.strip()]
    k = konfigurasi if konfigurasi is not None else _muat_konfigurasi()
    model = (k.get("tahap", {}).get(tahap) or {}).get("model")
    if not model:
        raise ValueError(f"tahap {tahap!r} belum diatur di config/model.toml")
    return list(model)


def biaya(model: str, masuk: int, keluar: int, konfigurasi: dict | None = None) -> float:
    k = konfigurasi if konfigurasi is not None else _muat_konfigurasi()
    harga = k.get("harga", {})
    hm, hk = harga.get(model) or harga.get("gemini" if model.startswith("gemini") else model) or (0.0, 0.0)
    return round((masuk * hm + keluar * hk) / 1e6, 6)


def baca_json(teks: str) -> Any:
    """Ambil JSON dari jawaban (boleh terbungkus ``` atau ada teks di luar)."""
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", teks.strip())
    for buka, tutup in (("{", "}"), ("[", "]")):
        if buka in t and tutup in t:
            awal, akhir = t.index(buka), t.rindex(tutup)
            if awal < akhir:
                try:
                    return json.loads(t[awal:akhir + 1])
                except json.JSONDecodeError:
                    continue
    return json.loads(t)


# ---------------- transport (bisa diganti di uji) ----------------
def _http(url: str, badan: dict | None, kepala: dict, batas_waktu: int) -> dict:
    data = json.dumps(badan).encode() if badan is not None else None
    req = urllib.request.Request(url, data=data, method="POST" if data else "GET",
                                 headers={"content-type": "application/json", **kepala})
    try:
        with urllib.request.urlopen(req, timeout=batas_waktu) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code}: {e.read().decode(errors='replace')[:200]}") from None
    except (TimeoutError, urllib.error.URLError) as e:
        raise RuntimeError(f"jaringan: {str(e)[:120]}") from None


def _claude(model: str, sistem: str, pesan: str, gambar: Sequence[Gambar], maks: int, json_mode: bool,
            http=_http) -> tuple[str, int, int]:
    kunci = os.environ.get("ANTHROPIC_API_KEY")
    if not kunci:
        raise RuntimeError("ANTHROPIC_API_KEY tidak tersedia")
    isi: list[dict] = [{"type": "image", "source": {"type": "base64", "media_type": g.jenis,
                                                    "data": base64.b64encode(g.data).decode()}} for g in gambar]
    isi.append({"type": "text", "text": pesan + ("\n\nKeluarkan HANYA JSON valid." if json_mode else "")})
    badan = {"model": model, "max_tokens": maks,
             # skill panjang dan sama antar-putaran: di-cache agar putaran berikutnya murah
             "system": [{"type": "text", "text": sistem, "cache_control": {"type": "ephemeral"}}],
             "messages": [{"role": "user", "content": isi}]}
    j = http("https://api.anthropic.com/v1/messages", badan,
             {"x-api-key": kunci, "anthropic-version": "2023-06-01"}, 300)
    teks = "".join(c.get("text", "") for c in j.get("content", []))
    u = j.get("usage") or {}
    masuk = u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0) + u.get("cache_read_input_tokens", 0)
    return teks, masuk, u.get("output_tokens", 0)


_MODEL_GEMINI: list[str] = []


def _pilih_gemini(kunci: str, http=_http) -> str:
    if os.environ.get("GEMINI_MODEL"):
        return os.environ["GEMINI_MODEL"]
    if not _MODEL_GEMINI:
        daftar = http(f"{GEMINI_API}/models?pageSize=200", None, {"x-goog-api-key": kunci}, 60).get("models", [])
        flash = []
        for m in daftar:
            nama = str(m.get("name", "")).split("/")[-1]
            cocok = re.fullmatch(r"gemini-(\d+(?:\.\d+)?)-flash", nama)
            if cocok and "generateContent" in m.get("supportedGenerationMethods", []):
                flash.append((float(cocok.group(1)), nama))
        if not flash:
            raise RuntimeError("tidak ada model Gemini Flash untuk kunci ini")
        _MODEL_GEMINI.append(max(flash)[1])
    return _MODEL_GEMINI[0]


def _gemini(model: str, sistem: str, pesan: str, gambar: Sequence[Gambar], maks: int, json_mode: bool,
            http=_http) -> tuple[str, int, int, str]:
    kunci = (os.environ.get("GEMINI_API_KEY") or "").strip()
    if not kunci:
        raise RuntimeError("GEMINI_API_KEY tidak tersedia")
    nama = _pilih_gemini(kunci, http) if model == "gemini" else model
    bagian = [{"inline_data": {"mime_type": g.jenis, "data": base64.b64encode(g.data).decode()}} for g in gambar]
    bagian.append({"text": pesan})
    konfig: dict = {"maxOutputTokens": maks, "temperature": 0.6}
    if json_mode:
        konfig["responseMimeType"] = "application/json"
    badan = {"systemInstruction": {"parts": [{"text": sistem}]},
             "contents": [{"role": "user", "parts": bagian}], "generationConfig": konfig}
    galat = None
    for jeda in (0, 10, 30):  # server Gemini gratis sering penuh sesaat (503) atau kena batas (429)
        time.sleep(jeda)
        try:
            j = http(f"{GEMINI_API}/models/{nama}:generateContent", badan, {"x-goog-api-key": kunci}, 300)
            break
        except RuntimeError as e:
            galat = e
            if not re.search(r"HTTP (429|500|503)", str(e)):
                raise
    else:
        raise galat
    kandidat = (j.get("candidates") or [{}])[0]
    teks = "".join(p.get("text", "") for p in (kandidat.get("content") or {}).get("parts", []))
    if not teks.strip():
        raise RuntimeError(f"Gemini tanpa jawaban ({kandidat.get('finishReason', '?')})")
    u = j.get("usageMetadata") or {}
    return teks, u.get("promptTokenCount", 0), u.get("candidatesTokenCount", 0), nama


def panggil(tahap: str, sistem: str, pesan: str, *, gambar: Sequence[Gambar] = (), json: bool = False,
            maks_token: int = 8000, validasi: Callable[[Any], list[str]] | None = None,
            http=_http, konfigurasi: dict | None = None) -> Jawaban:
    """Panggil rantai model tahap ini sampai ada jawaban yang terbaca dan lolos validasi."""
    k = konfigurasi if konfigurasi is not None else _muat_konfigurasi()
    riwayat: list[str] = []
    galat_sebelumnya: list[str] = []
    for model in rantai_model(tahap, k):
        isi = pesan
        if galat_sebelumnya:
            isi += ("\n\nPercobaan sebelumnya ditolak validator karena:\n- " + "\n- ".join(galat_sebelumnya[:20])
                    + "\nHindari kesalahan itu.")
        mulai = time.monotonic()
        try:
            if model.startswith("claude"):
                teks, masuk, keluar = _claude(model, sistem, isi, gambar, maks_token, json, http)
                nama, penyedia = model, "anthropic"
            elif model.startswith("gemini"):
                teks, masuk, keluar, nama = _gemini(model, sistem, isi, gambar, maks_token, json, http)
                penyedia = "google"
            else:
                raise RuntimeError(f"penyedia model {model!r} tidak dikenal")
        except RuntimeError as e:
            riwayat.append(f"{model}: {e}")
            continue
        j = Jawaban(teks, nama, penyedia, masuk, keluar, biaya(model, masuk, keluar, k), percobaan=list(riwayat))
        if json:
            try:
                j.data = baca_json(teks)
            except (json_mod.JSONDecodeError, ValueError) as e:
                riwayat.append(f"{nama}: JSON tidak terbaca ({str(e)[:80]})")
                galat_sebelumnya = ["keluaran bukan JSON valid"]
                continue
        if validasi is not None:
            galat = validasi(j.data if json else teks)
            if galat:
                riwayat.append(f"{nama}: ditolak validator ({len(galat)} galat)")
                galat_sebelumnya = galat
                continue
        j.percobaan = riwayat + [f"{nama}: diterima ({time.monotonic() - mulai:.1f} dtk)"]
        return j
    raise GalatLLM(tahap, riwayat)


json_mod = json  # `json` dibayangi parameter panggil(json=...)
