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
    "amplop", "api", "arus", "awan", "bahtera", "bambu", "batu", "bawah_laut",
    "bayang_misteri", "belah", "bingkai", "bintang", "buku", "bulan", "cahaya",
    "cawan", "chat", "danau", "dompet", "gapura", "gedung", "gelap", "gerbang",
    "gua", "gunung", "hati", "hewan", "hp", "ikan", "infus", "jalan", "jembatan",
    "jenazah", "jendela", "jurang", "kalender", "kamboja", "kantong",
    "kantor_gedung", "kartu_dalil", "kasur", "kelapa", "kerumunan", "kipas",
    "kitab", "koin", "kompor", "kota", "kue", "kulkas", "kursi", "lahar",
    "lapak", "laut", "lemari", "logo_app", "makam", "mangga", "masjid",
    "masjid_kampung", "massa_api", "meja", "meja_belajar", "meja_kantor",
    "menara", "mik", "mobil_luar", "monitor", "motor", "ngarai", "nur",
    "obat", "ombak", "pagar", "pancar", "pantai", "pemimpin", "penggali",
    "petir", "pisang", "pohon", "ponsel", "pot", "rak_buku", "ranjang_rs",
    "rantai", "rantai_tarik", "retakan", "rincian", "rumah", "rumah_kampung",
    "rumah_sakit_gedung", "rumput", "saf", "sajadah", "sapu", "sawah",
    "sekolah", "semak", "setir", "sofa", "stempel", "surya", "tanda",
    "tebing", "telaga", "tiang_listrik", "timbangan", "toko", "tv", "uang",
    "unta", "warung", "zaqqum",
})
KUNCI_PROPERTI_TERLINDUNGI = {
    "id", "jenis", "jenis_renderer", "x", "y", "s", "depan", "belakang",
}


def _tambah_offset(nilai, offset):
    if isinstance(nilai, (int, float)) and not isinstance(nilai, bool):
        return round(nilai + offset, 3)
    if isinstance(nilai, list) and nilai and all(
        isinstance(titik, (list, tuple)) and len(titik) == 2
        and isinstance(titik[0], (int, float))
        and isinstance(titik[1], (int, float))
        for titik in nilai
    ):
        return [
            [titik[0], round(titik[1] + offset, 3)]
            for titik in nilai
        ]
    raise ValueError("Lintasan posisi relatif harus berupa angka atau keyframe [waktu, nilai]")


def _posisi_renderer(entitas, tokoh_visual_by_id=None):
    posisi = entitas.get("posisi")
    if not isinstance(posisi, Mapping):
        relasi = entitas.get("relasi_posisi")
        if not isinstance(relasi, Mapping):
            return None
        tokoh_id = relasi.get("tokoh_id")
        tokoh = (tokoh_visual_by_id or {}).get(tokoh_id)
        if not isinstance(tokoh, Mapping):
            return None
        hubungan = relasi.get("hubungan")
        if hubungan not in {"di_samping_kiri", "di_samping_kanan", "di_depan", "di_belakang", "mengikuti"}:
            raise ValueError(f"Hubungan posisi benda {entitas.get('id')!r} tidak didukung")
        offset_x = relasi.get("offset_x", {
            "di_samping_kiri": -150,
            "di_samping_kanan": 150,
            "di_depan": 0,
            "di_belakang": 0,
            "mengikuti": 0,
        }[hubungan])
        offset_y = relasi.get("offset_y", {
            "di_samping_kiri": 0,
            "di_samping_kanan": 0,
            "di_depan": 90,
            "di_belakang": -90,
            "mengikuti": 0,
        }[hubungan])
        if any(not isinstance(x, (int, float)) or isinstance(x, bool) for x in (offset_x, offset_y)):
            raise ValueError(f"Offset posisi relatif benda {entitas.get('id')!r} harus angka")
        if "x" not in tokoh or "y" not in tokoh:
            return None
        return {
            "x": _tambah_offset(tokoh["x"], offset_x),
            "y": _tambah_offset(tokoh["y"], offset_y),
            "s": relasi.get("s", 1),
        }
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


def _benda_renderer(entitas, tokoh_visual_by_id=None):
    identitas = entitas.get("id")
    jenis = entitas.get("jenis_renderer")
    if not isinstance(jenis, str) or jenis not in JENIS_RENDERER_DIDUKUNG:
        raise ValueError(
            f"Jenis renderer benda {identitas!r} tidak didukung: {jenis!r}"
        )
    posisi = _posisi_renderer(entitas, tokoh_visual_by_id)
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


def arahkan_benda_visual(rencana_cerita, rencana_blocking, cerita, rencana_visual_tokoh=None):
    """Petakan benda eksplisit ke shot; posisi dapat mengikuti lintasan tokoh."""
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
        visual_tokoh_shot = {}
        if isinstance(rencana_visual_tokoh, list):
            entri_tokoh = next((
                item for item in rencana_visual_tokoh
                if isinstance(item, Mapping) and item.get("indeks") == indeks
            ), {})
            for arahan_tokoh in entri_tokoh.get("tokoh", []):
                if isinstance(arahan_tokoh, Mapping) and isinstance(arahan_tokoh.get("tokoh_id"), str):
                    visual_tokoh_shot[arahan_tokoh["tokoh_id"]] = arahan_tokoh
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
            visual = _benda_renderer(entitas, visual_tokoh_shot)
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
