"""Pengarah papan deterministik untuk cerita umum.

Modul ini menyusun shot renderer dari beat dan peristiwa eksplisit. Ia tidak
menciptakan benda atau kondisi lingkungan yang tidak disebutkan naskah.
"""
from __future__ import annotations


AKSI_GERAK = {"jalan", "berjalan", "berjalan_menolong", "mendekati", "lari", "berlari"}
AKSI_JATUH = {"tergelincir", "jatuh", "terjatuh"}
AKSI_INTERAKSI = {"menolong", "memukul", "menyerang", "menarik", "mendorong"}


def _id_peristiwa(adegan_item: dict, indeks: int) -> list[str]:
    """Pertahankan ID peristiwa sumber atau bentuk ID deterministik yang sama dengan inti."""
    hasil = []
    for nomor, peristiwa in enumerate(adegan_item.get("peristiwa") or [], start=1):
        if not isinstance(peristiwa, dict):
            continue
        identitas = peristiwa.get("id") or f"{adegan_item.get('id') or f'beat-{indeks + 1:03d}'}-peristiwa-{nomor:03d}"
        hasil.append(identitas)
    return hasil


def _profil_shot(adegan_item: dict, indeks: int) -> dict:
    """Tentukan fokus dan intensitas kamera hanya dari data eksplisit beat/peristiwa."""
    peristiwa = [
        item for item in (adegan_item.get("peristiwa") or [])
        if isinstance(item, dict)
    ]
    aksi = [
        str(item.get("aksi") or "").strip().casefold().replace(" ", "_")
        for item in peristiwa
    ]
    aktor = [
        item.get("aktor_id") for item in peristiwa
        if isinstance(item.get("aktor_id"), str)
    ]
    tokoh_beat = [
        item for item in adegan_item.get("tokoh_ids", [])
        if isinstance(item, str)
    ]
    fokus = list(dict.fromkeys(aktor or tokoh_beat))

    if any(item in AKSI_JATUH for item in aksi):
        tujuan, skala, zoom = "menampilkan_perubahan_aksi", "aksi", [1.06, 1.16]
    elif any(item in AKSI_INTERAKSI for item in aksi):
        tujuan, skala, zoom = "menampilkan_interaksi", "menengah", [1.04, 1.12]
    elif any(item in AKSI_GERAK for item in aksi):
        tujuan, skala, zoom = "memperlihatkan_perpindahan", "lebar", [1.0, 1.06]
    elif peristiwa:
        tujuan, skala, zoom = "memperlihatkan_peristiwa", "menengah", [1.0, 1.04]
    else:
        tujuan, skala, zoom = "memperkenalkan_beat", "lebar", [1.0, 1.04]

    return {
        "id": f"shot-beat-{indeks + 1:03d}",
        "tujuan": tujuan,
        "fokus_tokoh_ids": fokus,
        "peristiwa_ids": _id_peristiwa(adegan_item, indeks),
        "komposisi": {"skala": skala, "pusat": "tengah"},
        "dasar_keputusan": "aksi_dan_tokoh_eksplisit" if peristiwa or tokoh_beat else "beat_sumber",
        "zoom": zoom,
    }


def arahkan(naskah: dict) -> dict:
    """Hasilkan satu shot awal per beat; segmentasi lanjutan harus berbasis subperistiwa."""
    adegan = naskah.get("adegan") or []
    shot = []
    waktu = 0.0
    for indeks, adegan_item in enumerate(adegan):
        teks = adegan_item.get("teks", "")
        durasi = max(3.0, min(12.0, len(teks) / 16.0))
        profil = _profil_shot(adegan_item, indeks)
        shot.append({
            "at": round(waktu, 2),
            "_adegan": indeks,
            "horizon": 1100,
            "langit": 0.18,
            "kamera": {"x": 540, "y": 1050, "z": profil["zoom"]},
            "pengarahan": {k: v for k, v in profil.items() if k != "zoom"},
            "benda": [],
            "boneka": [],
        })
        waktu += durasi
    return {"latar": "gelap", "musik": "santai", "cerita": {"shot": shot}}
