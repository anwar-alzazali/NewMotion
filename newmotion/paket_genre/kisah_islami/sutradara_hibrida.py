"""Sutradara hibrida untuk produksi: rencana LLM + periksa visual, dengan jatuh ke sutradara aturan.

    spek, info = arahkan_hibrida(naskah_adegan, folder)

Menulis folder/rencana.json (dipakai lagi saat render final, tanpa memanggil LLM) dan
folder/periksa.json. Mode diambil dari NEWMOTION_SUTRADARA atau [produksi] di config/model.toml.
"""
from __future__ import annotations

import json
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from newmotion.application.pengarah_inti import arahkan_naskah

from .rencana_sutradara import terapkan_rencana


def konfigurasi_produksi() -> dict[str, Any]:
    from newmotion.infrastructure.llm import _muat_konfigurasi

    k = dict(_muat_konfigurasi().get("produksi", {}))
    k.setdefault("sutradara", "aturan")
    k.setdefault("periksa_putaran", 0)
    if os.environ.get("NEWMOTION_SUTRADARA"):
        k["sutradara"] = os.environ["NEWMOTION_SUTRADARA"]
    if os.environ.get("NEWMOTION_PERIKSA_PUTARAN", "").isdigit():
        k["periksa_putaran"] = int(os.environ["NEWMOTION_PERIKSA_PUTARAN"])
    return k


def _ada_kunci() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("GEMINI_API_KEY"))


def arahkan_hibrida(naskah: Mapping, folder: str | Path, *, genre: str = "kisah_islami",
                    http=None) -> tuple[dict, dict]:
    """Kembalikan (spek, info). info: mode, model, biaya_usd, periksa, catatan."""
    folder = Path(folder)
    k = konfigurasi_produksi()
    info: dict[str, Any] = {"mode": "aturan", "biaya_usd": 0.0}
    if k["sutradara"] == "llm" and genre == "kisah_islami" and (_ada_kunci() or http):
        from newmotion.infrastructure.llm import GalatLLM

        from .periksa_visual import berputar
        from .sutradara_llm import buat_rencana

        try:
            j = buat_rencana(naskah, http=http)
            rencana = j.data
            from newmotion.application.kebutuhan_renderer import catat, dari_rencana

            if http is None:  # pemanggilan HTTP palsu pada uji tidak boleh menulis antrean produksi
                catat(dari_rencana(rencana), sumber="sutradara", kisah=naskah.get("judul", "tanpa judul"))
            info.update(mode="llm", model=j.model, biaya_usd=j.biaya_usd)
            if int(k["periksa_putaran"]) > 0:
                rencana, _, log = berputar(naskah, rencana, folder / "periksa", putaran=int(k["periksa_putaran"]), http=http)
                info["biaya_usd"] += sum(e.get("biaya_usd", 0) + e.get("biaya_revisi_usd", 0) for e in log)
                info["periksa"] = [{"putaran": e["putaran"], "lulus": (e.get("temuan") or {}).get("lulus"),
                                    "temuan": len((e.get("temuan") or {}).get("temuan", [])), "revisi": e.get("revisi")}
                                   for e in log]
                (folder / "periksa.json").write_text(json.dumps(log, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
            folder.mkdir(parents=True, exist_ok=True)
            (folder / "rencana.json").write_text(json.dumps(rencana, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
            spek, _, _ = arahkan_naskah(terapkan_rencana(dict(naskah), rencana), genre_pilihan=genre)
            info["biaya_usd"] = round(info["biaya_usd"], 4)
            return spek, info
        except (GalatLLM, ValueError, RuntimeError) as e:
            info["catatan"] = f"sutradara LLM gagal, memakai sutradara aturan: {str(e)[:240]}"
    elif k["sutradara"] == "llm":
        info["catatan"] = "kunci LLM tidak tersedia; memakai sutradara aturan"
    spek, _, _ = arahkan_naskah(naskah, genre_pilihan=genre)
    return spek, info


def baca_rencana(folder: str | Path) -> dict | None:
    p = Path(folder) / "rencana.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else None
