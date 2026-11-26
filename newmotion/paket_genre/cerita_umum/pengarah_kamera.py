"""Pengarah kamera deterministik berdasarkan lintasan panggung yang sudah diterjemahkan.

Modul ini hanya membaca posisi boneka hasil adapter. Ia tidak membuat lintasan
aktor, tidak mengubah blocking, dan tidak menimpa sumbu kamera yang dinyatakan
secara eksplisit oleh naskah.
"""
from __future__ import annotations

from collections.abc import Mapping


def _lintasan(nilai):
    """Baca angka, rentang [awal, akhir], atau keyframe [[detik, nilai], ...]."""
    if isinstance(nilai, (int, float)) and not isinstance(nilai, bool):
        return []
    if not isinstance(nilai, list) or not nilai:
        return []
    if all(
        isinstance(item, (list, tuple)) and len(item) == 2
        and isinstance(item[0], (int, float))
        and isinstance(item[1], (int, float))
        for item in nilai
    ):
        return [(float(item[0]), float(item[1])) for item in nilai]
    if len(nilai) == 2 and all(
        isinstance(item, (int, float)) and not isinstance(item, bool)
        for item in nilai
    ):
        return [(0.0, float(nilai[0])), (1.0, float(nilai[1]))]
    return []


def _nilai(kunci, waktu, bawaan):
    if not kunci:
        return float(bawaan)
    if waktu <= kunci[0][0]:
        return kunci[0][1]
    for (t0, v0), (t1, v1) in zip(kunci, kunci[1:]):
        if waktu <= t1:
            if t1 == t0:
                return v1
            p = (waktu - t0) / (t1 - t0)
            return v0 + (v1 - v0) * p
    return kunci[-1][1]


def _posisi_tokoh(tokoh, waktu):
    x = tokoh.get("x", 540)
    y = tokoh.get("y", 1510)
    kx, ky = _lintasan(x), _lintasan(y)
    x0 = x if isinstance(x, (int, float)) else (kx[0][1] if kx else 540)
    y0 = y if isinstance(y, (int, float)) else (ky[0][1] if ky else 1510)
    return _nilai(kx, waktu, x0), _nilai(ky, waktu, y0)


def arahkan_kamera(rencana_cerita, rencana_blocking, cerita):
    """Buat keyframe x/y kamera dari pusat kelompok tokoh yang menjadi fokus shot."""
    hasil = []
    daftar_shot = cerita.get("shot", []) if isinstance(cerita, Mapping) else []
    for indeks, shot in enumerate(daftar_shot):
        if not isinstance(shot, dict):
            continue
        pengarahan = shot.get("pengarahan")
        kamera = shot.get("kamera")
        if not isinstance(pengarahan, dict) or not isinstance(kamera, dict):
            continue

        eksplisit = set(pengarahan.get("kunci_kamera_eksplisit", []))
        boneka = shot.get("boneka") or []
        fokus = set(pengarahan.get("fokus_tokoh_ids") or [])
        tokoh = [
            item for item in boneka
            if isinstance(item, Mapping)
            and (not fokus or item.get("aktor_id") in fokus)
        ]
        if not tokoh:
            pengarahan["status_kamera"] = "tanpa_tokoh_fokus"
            continue

        lintasan = {
            id(item): (_lintasan(item.get("x")), _lintasan(item.get("y")))
            for item in tokoh
        }
        waktu = sorted({
            t
            for pasangan in lintasan.values()
            for sumbu in pasangan
            for t, _ in sumbu
        })
        if len(waktu) < 2:
            pengarahan["status_kamera"] = "profil_tetap_tidak_ada_lintasan"
            continue

        key_x, key_y = [], []
        for t in waktu:
            posisi = [_posisi_tokoh(item, t) for item in tokoh]
            # Pusat bounding-box menjaga seluruh kelompok fokus tetap dalam komposisi.
            xs = [p[0] for p in posisi]
            ys = [p[1] for p in posisi]
            pusat_x = max(0.0, min(1080.0, (min(xs) + max(xs)) / 2))
            pusat_y = max(0.0, min(1920.0, (min(ys) + max(ys)) / 2))
            key_x.append([round(t, 3), round(pusat_x, 2)])
            key_y.append([round(t, 3), round(pusat_y, 2)])

        if "x" not in eksplisit:
            kamera["x"] = key_x
        if "y" not in eksplisit:
            kamera["y"] = key_y
        if "x" in eksplisit and "y" in eksplisit:
            status = "kamera_dikunci_naskah"
        elif "x" in eksplisit:
            status = "kamera_y_mengikuti_panggung"
        elif "y" in eksplisit:
            status = "kamera_x_mengikuti_panggung"
        else:
            status = "kamera_mengikuti_panggung"
        pengarahan["status_kamera"] = status
        hasil.append({
            "shot": indeks,
            "aktor_ids": [item.get("aktor_id") for item in tokoh],
            "x": kamera.get("x"),
            "y": kamera.get("y"),
            "status": status,
        })

    return {
        "versi": 1,
        "status": "diterapkan" if hasil else "tidak_ada_lintasan_fokus",
        "shot": hasil,
        "diagnostik": [],
    }
