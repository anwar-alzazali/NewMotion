"""Pengarah papan deterministik untuk cerita umum.

Modul ini menyusun shot renderer dari beat dan peristiwa eksplisit. Ia tidak
menciptakan benda atau kondisi lingkungan yang tidak disebutkan naskah.
"""
from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy


AKSI_GERAK = {"jalan", "berjalan", "berjalan_menolong", "mendekati", "lari", "berlari"}
AKSI_JATUH = {"tergelincir", "jatuh", "terjatuh"}
AKSI_INTERAKSI = {"menolong", "memukul", "menyerang", "menarik", "mendorong"}

# Daftar ini diselaraskan dengan PALET dan fungsi ruang pada papan/cerita.js.
PALET_RENDERER = {
    "siang", "gurun", "kota", "senja", "malam", "gua",
    "pagi", "sore", "subuh", "mendung", "neraka", "gelap_malam",
}
RUANG_RENDERER = {
    "tamu", "dapur", "kampung", "kamar", "kantor", "rumah_sakit",
    "mobil", "studio", "penjara", "istana", "teras",
}
KUNCI_KAMERA_RENDERER = {"x", "y", "z", "hentak", "guncang"}
KUNCI_LINGKUNGAN_RENDERER = {
    "ruang", "palet", "langit", "malam", "horizon", "matahari",
    "debu", "hujan", "panas", "naungan", "kerumunan", "retak", "resap",
}


def _id_peristiwa(adegan_item: dict, indeks: int) -> list[str]:
    """Pertahankan ID peristiwa sumber atau bentuk ID deterministik yang sama dengan inti."""
    hasil = []
    for nomor, peristiwa in enumerate(adegan_item.get("peristiwa") or [], start=1):
        if not isinstance(peristiwa, dict):
            continue
        identitas = peristiwa.get("id") or f"{adegan_item.get('id') or f'beat-{indeks + 1:03d}'}-peristiwa-{nomor:03d}"
        hasil.append(identitas)
    return hasil


def _gabungkan_metadata(naskah: Mapping, adegan_item: Mapping, kunci: str) -> tuple[dict, str]:
    """Gabungkan metadata global dan per-beat; nilai per-beat menjadi prioritas."""
    global_item = naskah.get(kunci, {})
    lokal_item = adegan_item.get(kunci, {})
    if not isinstance(global_item, Mapping) or not isinstance(lokal_item, Mapping):
        raise ValueError(f"Metadata {kunci!r} harus berupa objek")
    hasil = deepcopy(dict(global_item))
    hasil.update(deepcopy(dict(lokal_item)))
    sumber = (
        "metadata_adegan_eksplisit" if lokal_item
        else "metadata_naskah_eksplisit" if global_item
        else "belum_dinyatakan"
    )
    return hasil, sumber


def _kamera_renderer(naskah: Mapping, adegan_item: Mapping, zoom: list, kategori: str) -> tuple[dict, str]:
    """Bentuk kamera dasar dari tujuan shot; metadata eksplisit boleh mengoreksinya."""
    posisi_y = {
        "aksi_jatuh": 1150,
        "interaksi": 1050,
        "lokomosi": 960,
        "peristiwa": 960,
    }[kategori]
    hasil = {"x": 540, "y": posisi_y, "z": deepcopy(zoom)}
    eksplisit, sumber = _gabungkan_metadata(naskah, adegan_item, "kamera")
    tidak_dikenal = set(eksplisit) - KUNCI_KAMERA_RENDERER
    if tidak_dikenal:
        raise ValueError(
            "Kunci kamera tidak didukung renderer: " + ", ".join(sorted(tidak_dikenal))
        )
    hasil.update(eksplisit)
    for kunci in ("x", "y", "z"):
        nilai = hasil.get(kunci)
        if not isinstance(nilai, (int, float, list)):
            raise ValueError(f"Nilai kamera.{kunci} harus angka atau keyframe")
    for kunci in ("hentak", "guncang"):
        nilai = hasil.get(kunci, [])
        if not isinstance(nilai, list):
            raise ValueError(f"kamera.{kunci} harus berupa daftar keyframe")
    return hasil, sumber


def _lingkungan_renderer(naskah: Mapping, adegan_item: Mapping) -> tuple[dict, str]:
    """Teruskan hanya konteks lingkungan eksplisit yang dikenali renderer."""
    hasil, sumber = _gabungkan_metadata(naskah, adegan_item, "lingkungan")
    tidak_dikenal = set(hasil) - KUNCI_LINGKUNGAN_RENDERER
    if tidak_dikenal:
        raise ValueError(
            "Kunci lingkungan tidak didukung renderer: " + ", ".join(sorted(tidak_dikenal))
        )
    palet = hasil.get("palet")
    if palet is not None and palet not in PALET_RENDERER:
        raise ValueError(f"Palet {palet!r} tidak dikenal oleh renderer")
    ruang = hasil.get("ruang")
    if ruang is not None:
        jenis_ruang = ruang.get("jenis") if isinstance(ruang, Mapping) else ruang
        if not isinstance(jenis_ruang, str) or jenis_ruang not in RUANG_RENDERER:
            raise ValueError(f"Jenis ruang {jenis_ruang!r} tidak didukung renderer")
    return hasil, sumber


def _profil_shot(adegan_item: dict, indeks: int, naskah: Mapping) -> dict:
    """Tentukan fokus dan intensitas kamera dari peristiwa; lingkungan wajib eksplisit."""
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
    sasaran_tokoh = [
        item.get("sasaran_tokoh_id") for item in peristiwa
        if isinstance(item.get("sasaran_tokoh_id"), str)
    ]
    tokoh_beat = [
        item for item in adegan_item.get("tokoh_ids", [])
        if isinstance(item, str)
    ]
    fokus = list(dict.fromkeys(aktor + sasaran_tokoh + tokoh_beat))

    if any(item in AKSI_JATUH for item in aksi):
        tujuan, skala, zoom, kategori = "menampilkan_perubahan_aksi", "aksi", [1.06, 1.16], "aksi_jatuh"
    elif any(item in AKSI_INTERAKSI for item in aksi):
        tujuan, skala, zoom, kategori = "menampilkan_interaksi", "menengah", [1.04, 1.12], "interaksi"
    elif any(item in AKSI_GERAK for item in aksi):
        tujuan, skala, zoom, kategori = "memperlihatkan_perpindahan", "lebar", [1.0, 1.06], "lokomosi"
    else:
        tujuan, skala, zoom, kategori = (
            ("memperlihatkan_peristiwa", "menengah", [1.0, 1.04], "peristiwa")
            if peristiwa else
            ("memperkenalkan_beat", "lebar", [1.0, 1.04], "peristiwa")
        )

    kamera, sumber_kamera = _kamera_renderer(naskah, adegan_item, zoom, kategori)
    lingkungan, sumber_lingkungan = _lingkungan_renderer(naskah, adegan_item)
    urutan_peristiwa = [
        {
            "urutan": nomor,
            "peristiwa_id": item.get("id") or _id_peristiwa(adegan_item, indeks)[nomor - 1],
            "aktor_id": item.get("aktor_id"),
            "aksi": item.get("aksi"),
            "sasaran": item.get("sasaran"),
            "sasaran_tokoh_id": item.get("sasaran_tokoh_id"),
        }
        for nomor, item in enumerate(peristiwa, start=1)
    ]

    return {
        "id": f"shot-beat-{indeks + 1:03d}",
        "tujuan": tujuan,
        "fokus_tokoh_ids": fokus,
        "peristiwa_ids": _id_peristiwa(adegan_item, indeks),
        "urutan_peristiwa": urutan_peristiwa,
        "komposisi": {"skala": skala, "pusat": "tengah"},
        "dasar_keputusan": "aksi_dan_tokoh_eksplisit" if peristiwa or tokoh_beat else "beat_sumber",
        "dasar_kamera": kategori if sumber_kamera == "belum_dinyatakan" else sumber_kamera,
        "dasar_lingkungan": sumber_lingkungan,
        "kamera": kamera,
        "lingkungan": lingkungan,
    }


def arahkan(naskah: dict) -> dict:
    """Hasilkan satu shot awal per beat; segmentasi lanjutan harus berbasis subperistiwa."""
    adegan = naskah.get("adegan") or []
    shot = []
    waktu = 0.0
    for indeks, adegan_item in enumerate(adegan):
        teks = adegan_item.get("teks", "")
        durasi = max(3.0, min(12.0, len(teks) / 16.0))
        profil = _profil_shot(adegan_item, indeks, naskah)
        kamera = profil.pop("kamera")
        lingkungan = profil.pop("lingkungan")
        butir_shot = {
            "at": round(waktu, 2),
            "durasi": round(durasi, 2),
            "_adegan": indeks,
            "horizon": 1100,
            "langit": 0.18,
            "kamera": kamera,
            "pengarahan": profil,
            "benda": [],
            "boneka": [],
        }
        # Konteks eksplisit per-beat mengalahkan nilai lingkungan bawaan.
        butir_shot.update(lingkungan)
        shot.append(butir_shot)
        waktu += durasi
    return {"latar": "gelap", "musik": "santai", "cerita": {"shot": shot}}
