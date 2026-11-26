"""Pengarah benda renderer dari entitas benda yang sudah diidentifikasi semantik.

Modul ini tidak menebak benda dari kata bebas. Ia hanya menerjemahkan entitas
ber-ID dan jenis renderer eksplisit ke shot yang menautkan entitas tersebut.
"""
from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
import json


# Subset jenis yang diverifikasi pada papan/cerita.js; bukan klaim seluruh katalog renderer.
JENIS_RENDERER_DIDUKUNG = frozenset({
    "gunung", "petir", "ombak", "bahtera", "surya", "kota", "arus",
    "pancar", "hewan", "tebing", "bintang", "bulan", "ngarai", "batu",
    "danau", "jembatan", "jalan", "rumah", "pohon", "laut", "api",
    "gedung", "gua", "unta", "masjid", "menara", "gapura", "saf",
    "rumah_kampung", "warung", "sekolah", "pagar", "rumah_sakit_gedung",
    "pantai", "ikan", "makam", "jendela", "sapu", "pot", "meja",
    "kursi", "sofa", "kasur", "lemari", "tv", "ponsel", "dompet",
    "uang", "amplop", "koin", "kue", "kalender", "mobil_luar",
    "meja_belajar", "meja_kantor", "ranjang_rs", "infus", "lapak",
    "tiang_listrik", "pisang", "kelapa", "mangga", "bambu", "semak",
    "rumput", "sawah", "telaga", "cawan", "retakan", "jurang", "zaqqum",
    "lahar", "cahaya", "kerumunan",
})
KUNCI_PROPERTI_TERLINDUNGI = {
    "id", "jenis", "jenis_renderer", "x", "y", "s", "depan", "belakang",
}


def _posisi_renderer(entitas):
    posisi = entitas.get("posisi")
    if not isinstance(posisi, Mapping):
        return None
    if "x" not in posisi or "y" not in posisi:
        return None
    x, y = posisi["x"], posisi["y"]
    if not isinstance(x, (int, float, list)) or isinstance(x, bool):
        raise ValueError(f"Posisi x benda {entitas.get('id')!r} tidak valid")
    if not isinstance(y, (int, float, list)) or isinstance(y, bool):
        raise ValueError(f"Posisi y benda {entitas.get('id')!r} tidak valid")
    skala = posisi.get("s", 1)
    if not isinstance(skala, (int, float)) or isinstance(skala, bool) or skala <= 0:
        raise ValueError(f"Skala benda {entitas.get('id')!r} harus angka positif")
    return {"x": deepcopy(x), "y": deepcopy(y), "s": skala}


def _benda_renderer(entitas):
    identitas = entitas.get("id")
    jenis = entitas.get("jenis_renderer")
    if not isinstance(jenis, str) or jenis not in JENIS_RENDERER_DIDUKUNG:
        raise ValueError(
            f"Jenis renderer benda {identitas!r} tidak didukung: {jenis!r}"
        )
    posisi = _posisi_renderer(entitas)
    if posisi is None:
        return None
    properti = entitas.get("properti", {})
    if not isinstance(properti, Mapping):
        raise ValueError(f"properti benda {identitas!r} harus berupa objek")
    konflik = set(properti) & KUNCI_PROPERTI_TERLINDUNGI
    if konflik:
        raise ValueError(
            f"properti benda {identitas!r} tidak boleh menimpa: "
            + ", ".join(sorted(conflict for conflict in konflik))
        )
    lapisan = entitas.get("lapisan", {})
    if not isinstance(lapisan, Mapping) or set(lapisan) - {"depan", "belakang"}:
        raise ValueError(f"lapisan benda {identitas!r} hanya menerima depan/belakang")
    if any(type(nilai) is not bool for nilai in lapisan.values()):
        raise ValueError(f"Nilai lapisan benda {identitas!r} harus boolean")
    hasil = {
        "id": identitas,
        "jenis": jenis,
        **posisi,
        **deepcopy(dict(lapisan)),
        **deepcopy(dict(properti)),
    }
    try:
        json.dumps(hasil, ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError) as galat:
        raise ValueError(f"Data benda {identitas!r} bukan JSON yang sah: {galat}") from galat
    return hasil


def arahkan_benda_visual(rencana_cerita, rencana_blocking, cerita):
    """Petakan benda eksplisit ke shot yang memiliki tautan beat/peristiwa."""
    daftar_benda = rencana_cerita.get("benda", [])
    daftar_adegan = rencana_cerita.get("adegan", [])
    benda_by_id = {item["id"]: item for item in daftar_benda if isinstance(item, Mapping)}
    beat_by_id = {item["id"]: item for item in daftar_adegan if isinstance(item, Mapping)}
    hasil_shot = []
    diagnostik = []

    for indeks, shot in enumerate((cerita or {}).get("shot", [])):
        if not isinstance(shot, Mapping):
            continue
        beat_id = shot.get("_beat_id")
        beat = beat_by_id.get(beat_id, {})
        id_terkait = list(beat.get("benda_ids", []))
        pengarahan = shot.get("pengarahan", {})
        peristiwa_shot = set(pengarahan.get("peristiwa_ids", []))
        for peristiwa in beat.get("peristiwa", []):
            if (
                isinstance(peristiwa, Mapping)
                and peristiwa.get("id") in peristiwa_shot
                and isinstance(peristiwa.get("sasaran_benda_id"), str)
            ):
                id_terkait.append(peristiwa["sasaran_benda_id"])

        id_terkait = list(dict.fromkeys(id_terkait))
        if not id_terkait:
            continue
        benda_shot = []
        for benda_id in id_terkait:
            entitas = benda_by_id.get(benda_id)
            if entitas is None:
                diagnostik.append({
                    "kode": "benda_tidak_ditemukan",
                    "shot": indeks,
                    "beat_id": beat_id,
                    "benda_id": benda_id,
                })
                continue
            visual = _benda_renderer(entitas)
            if visual is None:
                diagnostik.append({
                    "kode": "benda_perlu_penempatan",
                    "shot": indeks,
                    "beat_id": beat_id,
                    "benda_id": benda_id,
                    "pesan": "Entitas sudah dikenal tetapi belum memiliki posisi x/y renderer.",
                })
                continue
            benda_shot.append(visual)
        if benda_shot:
            hasil_shot.append({
                "indeks": indeks,
                "benda": benda_shot,
                "beat_id": beat_id,
                "peristiwa_ids": [
                    item.get("id") for item in beat.get("peristiwa", [])
                    if isinstance(item, Mapping) and item.get("id") in peristiwa_shot
                ],
            })

    status = "siap" if hasil_shot and not diagnostik else (
        "perlu_pelengkapan" if diagnostik else "tidak_ada_benda_tertaut"
    )
    return {
        "versi": 1,
        "status": status,
        "shot": hasil_shot,
        "diagnostik": diagnostik,
    }
