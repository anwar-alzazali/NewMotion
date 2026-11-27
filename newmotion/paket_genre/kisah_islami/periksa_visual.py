"""Putaran periksa visual: lembar frame -> pemeriksa vision -> sutradara merevisi rencana.

Berhenti bila pemeriksa meluluskan (tanpa temuan berat) atau putaran habis. Revisi tetap
melewati validator lengkap (katalog, bukti, adab); bila revisi gagal, rencana lama dipakai.
"""
from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from newmotion.application.lembar_periksa import buat_lembar
from newmotion.application.pengarah_inti import arahkan_naskah

from .rencana_sutradara import terapkan_rencana
from .sutradara_llm import _narasi, pesan_sutradara, skill_sutradara, validasi_lengkap

SKILL = Path(__file__).resolve().parent / "skill" / "periksa_visual.md"


def validasi_temuan(data: Any, jumlah_beat: int) -> list[str]:
    if not isinstance(data, dict) or not isinstance(data.get("temuan"), list):
        return ['keluaran harus objek {"lulus", "temuan": [...], "catatan"}']
    galat = []
    for i, t in enumerate(data["temuan"]):
        if not isinstance(t, dict):
            galat.append(f"temuan {i} bukan objek")
            continue
        if not isinstance(t.get("beat"), int) or not 1 <= t["beat"] <= jumlah_beat:
            galat.append(f"temuan {i}: beat harus 1..{jumlah_beat}")
        if t.get("berat") not in ("berat", "ringan"):
            galat.append(f"temuan {i}: berat harus 'berat' atau 'ringan'")
        if not str(t.get("masalah", "")).strip():
            galat.append(f"temuan {i}: masalah kosong")
    return galat


def ada_berat(temuan: Mapping) -> bool:
    return any(t.get("berat") == "berat" for t in temuan.get("temuan", []))


def pesan_periksa(naskah: Mapping, rencana: Mapping) -> str:
    beat = {b.get("beat"): b for b in rencana.get("beat", [])}
    baris = [f"Judul: {naskah.get('judul', '-')}", f"Objek inti: {rencana.get('objek_inti', '-')}", ""]
    for i, teks in enumerate(_narasi(naskah), 1):
        b = beat.get(i, {})
        ringkas = {k: b.get(k) for k in ("subjek", "kamu", "kamera", "teks_layar", "klimaks") if k in b}
        baris += [f"BEAT {i} narasi: {teks}", f"BEAT {i} rencana: {json.dumps(ringkas, ensure_ascii=False)}"]
    baris += ["", "Periksa frame pada gambar. Keluarkan JSON sesuai format."]
    return "\n".join(baris)


def periksa(spek: Mapping, naskah: Mapping, rencana: Mapping, folder: str | Path, *, http=None):
    from newmotion.infrastructure import llm

    lembar = buat_lembar(spek, folder)
    n = len(_narasi(naskah))
    opsi = {"http": http} if http else {}
    j = llm.panggil("periksa_visual", SKILL.read_text(encoding="utf-8"), pesan_periksa(naskah, rencana),
                    gambar=[llm.Gambar.dari_berkas(p) for p in lembar], json=True, maks_token=4000,
                    validasi=lambda d: validasi_temuan(d, n), **opsi)
    return j, lembar


def pesan_revisi(naskah: Mapping, rencana: Mapping, temuan: Mapping) -> str:
    return (pesan_sutradara(naskah)
            + "\n\nRencana sebelumnya:\n" + json.dumps(rencana, ensure_ascii=False)
            + "\n\nTemuan pemeriksa visual pada frame hasil rencana itu:\n"
            + json.dumps(temuan.get("temuan", []), ensure_ascii=False)
            + "\n\nTulis ulang rencana LENGKAP untuk semua beat. Perbaiki semua temuan berat; temuan ringan "
              "bila tidak merusak bagian lain. Beat tanpa temuan boleh tetap sama.")


def revisi(naskah: Mapping, rencana: Mapping, temuan: Mapping, *, http=None):
    from newmotion.infrastructure import llm

    opsi = {"http": http} if http else {}
    return llm.panggil("sutradara", skill_sutradara(), pesan_revisi(naskah, rencana, temuan), json=True,
                       maks_token=12000, validasi=lambda r: validasi_lengkap(r, naskah), **opsi)


def berputar(naskah: Mapping, rencana: Mapping, folder: str | Path, *, putaran: int = 2, http=None):
    """Periksa -> revisi sampai lulus atau `putaran` revisi habis. Mengembalikan (rencana, spek, log)."""
    from newmotion.infrastructure.llm import GalatLLM

    folder = Path(folder)
    log: list[dict[str, Any]] = []
    for k in range(putaran + 1):
        spek, _, _ = arahkan_naskah(terapkan_rencana(dict(naskah), rencana))
        try:
            j, lembar = periksa(spek, naskah, rencana, folder / f"putaran_{k}", http=http)
        except GalatLLM as e:
            log.append({"putaran": k, "periksa": "gagal", "galat": str(e)[:300]})
            break
        from newmotion.application.kebutuhan_renderer import catat, dari_temuan

        if http is None:  # uji vision memakai HTTP palsu dan tidak menyentuh data produksi
            catat(dari_temuan(j.data), sumber="pemeriksa", kisah=naskah.get("judul", "tanpa judul"))
        entri = {"putaran": k, "model_periksa": j.model, "biaya_usd": j.biaya_usd, "temuan": j.data,
                 "lembar": [str(p) for p in lembar]}
        log.append(entri)
        if not ada_berat(j.data) or k == putaran:
            break
        try:
            r = revisi(naskah, rencana, j.data, http=http)
        except GalatLLM as e:
            entri["revisi"] = f"gagal: {str(e)[:300]}"
            break
        entri.update(revisi=r.model, biaya_revisi_usd=r.biaya_usd)
        rencana = r.data
    spek, _, _ = arahkan_naskah(terapkan_rencana(dict(naskah), rencana))
    return rencana, spek, log
