"""Jembatan kontrak karakter Python ke rangka SVG renderer cerita.js."""
from __future__ import annotations

import math

from . import gerak as G
from .tokoh import orang


WAJAH_JS = {
    "datar": "netral", "senyum": "senang", "tertawa": "tawa", "ejek": "sinis",
    "cemberut": "kesal", "sedih": "sedih", "marah": "marah", "takut": "takut",
    "kaget": "kaget", "pejam": "lelah", "kepergok_panik": "takut",
    "jijik_ilfil": "kesal", "sinis": "sinis", "curiga": "ragu", "heran": "bingung",
}
RAMBUT_JS = {"pendek": "pendek", "ikal": "keriting", "panjang": "belah", "botak": "botak"}
KEPALA_VALID = {"imamah", "kain", "kopiah", "kerudung", "tanpa"}
PAKAIAN_VALID = {"kaus", "koko", "gamis", "kemeja", "jaket", "daster", "hoodie", "blazer"}


def _jadwal_gerak(gerak):
    if isinstance(gerak, str):
        jadwal = [(0.0, gerak)]
    elif isinstance(gerak, list) and gerak:
        jadwal = sorted((float(waktu), str(nama)) for waktu, nama in gerak)
    else:
        raise ValueError("karakter.gerak harus berupa nama gerak atau jadwal [[detik, nama], ...]")
    if jadwal[0][0] < 0:
        raise ValueError("waktu gerak tidak boleh negatif")
    for _, nama in jadwal:
        if nama not in G.SEMUA:
            raise ValueError(f"gerak karakter tidak dikenal: {nama}")
    return jadwal


def _pose_renderer(nilai, alat):
    pose = {
        "turun": float(nilai["naik"]), "badan": float(nilai["tubuh"]),
        "kepala": float(nilai["kepala"]), "geser": float(nilai["geser"]),
        "toleh": float(nilai["toleh"]), "angguk": float(nilai["angguk"]),
        "ra": [float(nilai["la_ka"]), float(nilai["sa_ka"])],
        "la": [float(nilai["la_ki"]), float(nilai["sa_ki"])],
        "rk": [float(nilai["pa_ka"]), float(nilai["ba_ka"])],
        "lk": [float(nilai["pa_ki"]), float(nilai["ba_ki"])],
        "pp_ka": float(nilai["pf_ka"]), "pp_ki": float(nilai["pf_ki"]),
        "pk_ka": 1.0, "pk_ki": 1.0,
    }
    if nilai.get("bangku", 0) > 0.5:
        pose["turun"] = max(pose["turun"], 70.0)
        pose["pp_ka"] = min(pose["pp_ka"], 0.3)
        pose["pp_ki"] = min(pose["pp_ki"], 0.3)
    if alat:
        pose["pegang"] = alat
    return pose


def _wajah(nilai):
    if isinstance(nilai, list) and nilai and isinstance(nilai[0], (list, tuple)):
        return [[waktu, WAJAH_JS.get(nama, nama)] for waktu, nama in nilai]
    return WAJAH_JS.get(nilai, nilai)


def _terapkan_tampilan(boneka, karakter):
    jenis = karakter.get("jenis", "pria")
    if jenis not in {"pria", "wanita"}:
        raise ValueError("karakter.jenis harus pria atau wanita")
    mode = karakter.get("mode", "pakaian")
    if mode not in {"pakaian", "siluet"}:
        raise ValueError("karakter.mode harus pakaian atau siluet")
    kepala = karakter.get("kepala", "kerudung" if jenis == "wanita" else "imamah")
    if kepala not in KEPALA_VALID:
        raise ValueError(f"karakter.kepala tidak dikenal: {kepala}")
    boneka["gaya"] = "siluet" if mode == "siluet" else "umum"
    boneka["hidup"] = bool(karakter.get("hidup", True))
    boneka["rambut"] = "kerudung" if jenis == "wanita" or kepala == "kerudung" else RAMBUT_JS.get(karakter.get("model_rambut", "pendek"), "pendek")
    boneka["penutup_kepala"] = kepala
    boneka["warna_penutup"] = karakter.get("warna_penutup", karakter.get("warna_aksen", "#e8dcc4"))
    if karakter.get("warna_kulit"):
        boneka["kulit"] = karakter["warna_kulit"]
    if karakter.get("warna_rambut"):
        boneka["warna_rambut"] = karakter["warna_rambut"]
    if jenis == "wanita":
        boneka["kerudung"] = karakter.get("warna_penutup", karakter.get("warna_baju", "#5a3a5e"))
    pakaian = dict(boneka.get("pakaian") or {})
    pakaian["jenis"] = karakter.get("jenis_pakaian", "gamis" if jenis == "wanita" else "koko")
    if pakaian["jenis"] not in PAKAIAN_VALID:
        raise ValueError(f"jenis pakaian tidak dikenal: {pakaian['jenis']}")
    for sumber, tujuan in (("warna_baju", "warna"), ("warna_aksen", "aksen"),
                           ("warna_bawah", "bawah_warna"), ("bawah", "bawah")):
        if karakter.get(sumber) is not None:
            pakaian[tujuan] = karakter[sumber]
    pakaian.setdefault("bawah", "gamis" if jenis == "wanita" else "celana")
    boneka["pakaian"] = pakaian
    janggut = karakter.get("janggut", "pendek" if jenis == "pria" else "tanpa")
    if janggut == "tanpa" or jenis == "wanita":
        boneka["janggut"] = False
        boneka["janggut_model"] = "tanpa"
    elif janggut in {"tipis", "pendek", "panjang"}:
        boneka["janggut"] = karakter.get("warna_janggut", True)
        boneka["janggut_model"] = janggut
    else:
        raise ValueError("karakter.janggut harus tanpa, tipis, pendek, atau panjang")
    usia = karakter.get("usia", "dewasa")
    if usia not in {"anak", "dewasa", "lansia"}:
        raise ValueError("karakter.usia harus anak, dewasa, atau lansia")
    boneka["skala_usia"] = {"anak": 0.78, "dewasa": 1.0, "lansia": 1.04}[usia]
    if karakter.get("wajah") is not None:
        boneka["wajah"] = _wajah(karakter["wajah"])
    arah = karakter.get("arah")
    if arah == "belakang":
        boneka["belakang"] = True
    elif arah == "depan":
        boneka["belakang"] = False
    elif arah not in (None, "samping", "tiga_perempat"):
        raise ValueError("karakter.arah tidak dikenal")


def integrasikan_tokoh(boneka, karakter, durasi, fps=15):
    """Terjemahkan satu deskripsi karakter Python menjadi keyframe rangka JS."""
    if not isinstance(karakter, dict):
        raise ValueError("setiap karakter gabungan harus berupa objek")
    _terapkan_tampilan(boneka, karakter)
    gerak = karakter.get("gerak", "berdiri")
    jadwal = _jadwal_gerak(gerak)
    nama_gerak = {nama for _, nama in jadwal}
    alat = karakter.get("alat")
    if alat is None:
        alat = "beliung" if "gali" in nama_gerak else ("palu" if "palu" in nama_gerak else None)
    if alat not in (None, "beliung", "palu"):
        raise ValueError("karakter.alat harus beliung atau palu")
    # Validasi parameter melalui renderer SVG Python: kontrak visual dan gerak harus sah di kedua jalur.
    orang(0, 0, s=0.01, gerak=gerak, mode=karakter.get("mode", "pakaian"),
          kepala=karakter.get("kepala"), jenis=karakter.get("jenis", "pria"),
          wajah=karakter.get("wajah", "datar"), alat=alat, usia=karakter.get("usia", "dewasa"),
          warna_kulit=karakter.get("warna_kulit"), warna_baju=karakter.get("warna_baju"),
          warna_aksen=karakter.get("warna_aksen"), model_rambut=karakter.get("model_rambut", "pendek"),
          janggut=karakter.get("janggut", "pendek" if karakter.get("jenis", "pria") == "pria" else "tanpa"),
          warna_janggut=karakter.get("warna_janggut"))
    lama = max(0.0, float(durasi))
    if lama > 120:
        raise ValueError("durasi gerak satu shot melebihi batas 120 detik")
    jumlah = max(1, int(math.ceil(lama * fps)))
    waktu = sorted(set(round(min(i / fps, lama), 4) for i in range(jumlah + 1)))
    # Sebarkan fase gali antartokoh, tetapi gunakan offset yang sama untuk pose dan efek benturan.
    identitas = boneka.get("npc", boneka.get("id", 0)) or 0
    offset = (int(identitas) * 0.381) % 1.15 if "gali" in nama_gerak else 0.0
    boneka["pose"] = [[t, _pose_renderer(G.pada(gerak, t + offset), alat)] for t in waktu]
    boneka["_gabungan"] = True
    if "gali" in nama_gerak:
        boneka["_gerak_offset"] = offset
        boneka["aksi"] = "gali"
    elif "palu" in nama_gerak:
        boneka["aksi"] = "palu"
    return boneka


def integrasikan_spec(spec, fps=15):
    """Integrasikan semua boneka beratribut 'karakter' pada SPEC.cerita."""
    cerita = spec.get("cerita") or {}
    tembakan = cerita.get("shot") or []
    total = float(spec.get("durasi") or (float(tembakan[-1].get("at", 0)) + 5 if tembakan else 5))
    for indeks, shot in enumerate(tembakan):
        awal = float(shot.get("at", 0))
        akhir = float(tembakan[indeks + 1].get("at", total)) if indeks + 1 < len(tembakan) else total
        durasi = max(0.0, min(total, akhir) - awal)
        for boneka in shot.get("boneka") or []:
            karakter = boneka.get("karakter")
            if karakter is not None and not boneka.get("_gabungan"):
                integrasikan_tokoh(boneka, karakter, durasi, fps=fps)
    return spec
