"""Pengarah papan minimal dan deterministik untuk cerita umum."""
from __future__ import annotations


def arahkan(naskah: dict) -> dict:
    adegan = naskah.get("adegan") or []
    shot = []
    waktu = 0.0
    for indeks, adegan_item in enumerate(adegan):
        teks = adegan_item.get("teks", "")
        durasi = max(3.0, min(12.0, len(teks) / 16.0))
        shot.append({
            "at": round(waktu, 2),
            "_adegan": indeks,
            "horizon": 1100,
            "langit": 0.18,
            "kamera": {"x": 540, "y": 1050, "z": [1.0, 1.04]},
            "benda": [],
            "boneka": [],
        })
        waktu += durasi
    return {"latar": "gelap", "musik": "santai", "cerita": {"shot": shot}}
