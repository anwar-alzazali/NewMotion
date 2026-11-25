"""Serializer kontrak karakter Python ke renderer JavaScript tunggal."""
from __future__ import annotations

from .gerak import jadwal_gerak

WAJAH_JS = {
    "datar": "netral", "senyum": "senang", "tertawa": "tawa", "ejek": "sinis",
    "cemberut": "kesal", "sedih": "sedih", "marah": "marah", "takut": "takut",
    "kaget": "kaget", "pejam": "lelah", "kepergok_panik": "takut",
    "jijik_ilfil": "kesal", "sinis": "sinis", "curiga": "ragu", "heran": "bingung",
}
RAMBUT_JS = {"pendek": "pendek", "ikal": "keriting", "panjang": "belah", "botak": "botak"}
KEPALA_VALID = {"imamah", "kain", "kopiah", "kerudung", "tanpa"}
PAKAIAN_VALID = {"kaus", "koko", "gamis", "kemeja", "jaket", "daster", "hoodie", "blazer"}


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


def integrasikan_tokoh(boneka, karakter, durasi, fps=None):
    """Serialisasikan deskripsi karakter; tidak membuat pose atau frame di Python."""
    if not isinstance(karakter, dict):
        raise ValueError("setiap karakter gabungan harus berupa objek")
    _terapkan_tampilan(boneka, karakter)
    jadwal = jadwal_gerak(karakter.get("gerak", "berdiri"))
    nama_gerak = {nama for _, nama in jadwal}
    alat = karakter.get("alat")
    if alat is None:
        alat = "beliung" if "gali" in nama_gerak else ("palu" if "palu" in nama_gerak else None)
    if alat not in (None, "beliung", "palu"):
        raise ValueError("karakter.alat harus beliung atau palu")
    lama = max(0.0, float(durasi))
    if lama > 120:
        raise ValueError("durasi gerak satu shot melebihi batas 120 detik")

    # JS menerima nama aksi dan waktu mulai; bukan sudut sendi atau pose per-frame.
    boneka["pose"] = jadwal
    boneka["_gabungan"] = True
    if "gali" in nama_gerak:
        if karakter.get("arah") is None:
            boneka["belakang"] = True
        identitas = boneka.get("npc", boneka.get("id", 0)) or 0
        boneka["_gerak_offset"] = (int(identitas) * 0.381) % 1.15
        boneka["aksi"] = "gali"
    elif "palu" in nama_gerak:
        boneka["aksi"] = "palu"
    return boneka


def integrasikan_spec(spec, fps=None):
    """Serialisasikan semua karakter pada SPEC.cerita ke kontrak renderer JS."""
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
                integrasikan_tokoh(boneka, karakter, durasi)
    return spec
