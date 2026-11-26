"""Pengarahan subjek naratif ke benda renderer yang benar-benar tampak.

Aturan bersifat leksikal-semantik umum: mengenali entitas dan keadaan yang disebut
pada segmen, lalu menerjemahkannya ke katalog renderer yang sudah tersedia.
Tidak membaca atau mengimpor leksikon alat ukur dan tidak bergantung pada judul cerita.
"""
from __future__ import annotations

import hashlib
import re
from collections.abc import Mapping


# Alias bahasa -> jenis renderer yang sudah tersedia di mesin-video/papan/cerita.js.
# Urutan lebih spesifik diletakkan lebih dahulu agar "kapal Nabi Nuh" tetap satu bahtera.
POLA_SUBJEK = (
    (re.compile(r"\\b(kapal|bahtera|perahu)\\b", re.I), "bahtera"),
    (re.compile(r"\\b(penggali|para penggali|orang yang menggali)\\b", re.I), "penggali"),
    (re.compile(r"\\b(pemimpin|raja|panglima)\\b", re.I), "pemimpin"),
    (re.compile(r"\\b(dinding|tembok|benteng)\\b", re.I), "pagar"),
    (re.compile(r"\\b(lubang|terowongan)\\b", re.I), "ngarai"),
    (re.compile(r"\\b(ombak|gelombang)\\b", re.I), "ombak"),
    (re.compile(r"\\b(arus|aliran air)\\b", re.I), "arus"),
    (re.compile(r"\\b(hewan|binatang|ternak)\\b", re.I), "hewan"),
    (re.compile(r"\\b(unta)\\b", re.I), "unta"),
    (re.compile(r"\\b(gerbang|pintu gerbang)\\b", re.I), "gerbang"),
    (re.compile(r"\\b(istana|keraton)\\b", re.I), "istana"),
    (re.compile(r"\\b(rumah|pondok)\\b", re.I), "rumah"),
)

POLA_PERUBAHAN = {
    "air": re.compile(r"\\b(berlayar|melaju|bergerak|mengapung)\\b", re.I),
    "gelombang": re.compile(r"\\b(menghempas|menggulung|menerjang|membesar)\\b", re.I),
    "retak": re.compile(r"\\b(retak|retakan|pecah)\\b", re.I),
    "lubang": re.compile(r"\\b(lubang|terkikis|terbuka|membesar)\\b", re.I),
    "jebol": re.compile(r"\\b(jebol|runtuh|roboh|hancur)\\b", re.I),
    "gali": re.compile(r"\\b(menggali|menggerogoti|mengikis)\\b", re.I),
    "jatuh": re.compile(r"\\b(jatuh|terjun|tergelincir|tenggelam)\\b", re.I),
}

KATA_KUNCI_LAYAR = (
    re.compile(r"\\b(\\d+(?:[.,]\\d+)?\\s*(?:tahun|bulan|hari|malam|meter|kilometer|orang|tahun))\\b", re.I),
    re.compile(r"\\b(jebol|terbelah|kiamat|banjir besar|hari kebangkitan)\\b", re.I),
)


def _seed(teks: str) -> int:
    return int(hashlib.sha1(teks.casefold().encode("utf-8")).hexdigest()[:8], 16)


def _jenis_disebut(teks: str) -> list[str]:
    jenis = []
    for pola, nama in POLA_SUBJEK:
        if pola.search(teks) and nama not in jenis:
            jenis.append(nama)
    return jenis


def _properti_benda(jenis: str, teks: str, indeks: int, durasi: float, seed: int) -> dict:
    """Susun posisi dan gerak sederhana yang mengikuti aksi dalam teks segmen."""
    x_sisi = 330 if seed % 2 else 750
    dasar = {"jenis": jenis, "x": x_sisi, "y": 1320, "s": 0.82}
    if jenis == "bahtera":
        dasar.update({
            "x": [[0, x_sisi - 90], [max(0.5, durasi * 0.85), x_sisi + 90]],
            "y": [[0, 1300], [max(0.5, durasi * 0.85), 1270]],
            "s": 0.82, "goyang": 1.0, "cahaya": 0.35,
        })
        if re.search(r"\\b(ombak|gelombang|badai|banjir)\\b", teks, re.I):
            dasar["goyang"] = 2.2
    elif jenis == "ombak":
        dasar.update({"x": 540, "y": [[0, 1480], [max(0.5, durasi * 0.8), 1220]],
                      "s": 1.0, "tinggi": 520, "depan": True, "seed": seed % 997})
    elif jenis == "arus":
        dasar.update({"x": 540, "y": 1460, "s": 0.9, "n": 14, "maju": 1.0})
    elif jenis == "pagar":
        dasar.update({"x": 540, "y": 1320, "s": 1.05, "w": 1.4, "belakang": True})
        if POLA_PERUBAHAN["retak"].search(teks):
            dasar["retak"] = 1
        if POLA_PERUBAHAN["lubang"].search(teks):
            dasar["buka"] = 0.48
        if POLA_PERUBAHAN["jebol"].search(teks):
            dasar["buka"] = 1
    elif jenis == "ngarai":
        dasar.update({"x": 540, "y": 1320, "s": 0.95, "belakang": True})
    elif jenis == "penggali":
        dasar.update({"x": x_sisi, "y": 1420, "s": 0.82, "gali": True})
    elif jenis == "pemimpin":
        dasar.update({"x": x_sisi, "y": 1350, "s": 0.92, "belakang": True})
    elif jenis in {"hewan", "unta"}:
        dasar.update({"x": [[0, x_sisi - 100], [max(0.5, durasi * 0.8), x_sisi + 100]],
                      "y": 1390, "s": 0.82})
    elif jenis in {"gerbang", "istana"}:
        dasar.update({"x": 540, "y": 1270, "s": 0.9, "belakang": True})
    return dasar


def arahkan_subjek(teks: str, durasi: float, indeks: int = 0) -> dict:
    """Kembalikan benda, teks layar, dan penanda klimaks untuk satu segmen narasi."""
    if not isinstance(teks, str) or not teks.strip():
        return {"benda": [], "teks": [], "klimaks": False}
    seed = _seed(f"{indeks}|{teks}")
    benda = [
        _properti_benda(jenis, teks, indeks, max(0.5, float(durasi or 0.5)), seed + n * 31)
        for n, jenis in enumerate(_jenis_disebut(teks))
    ]
    teks_layar = []
    for pola in KATA_KUNCI_LAYAR:
        cocok = pola.search(teks)
        if cocok:
            label = cocok.group(1).strip()
            if label.casefold() not in {x["teks"].casefold() for x in teks_layar}:
                teks_layar.append({"at": 0.15, "teks": label.upper(), "y": 340, "ukuran": 62})
    klimaks = bool(POLA_PERUBAHAN["jebol"].search(teks) or
                   re.search(r"\\b(terbelah|meledak|tenggelam|jatuh|ditelan)\\b", teks, re.I))
    return {"benda": benda, "teks": teks_layar, "klimaks": klimaks}
