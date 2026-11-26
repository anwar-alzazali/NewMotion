"""Pengarahan subjek naratif ke benda renderer yang benar-benar tampak.

Pemetaan memakai konteks kalimat dan hanya memilih bentuk yang sesuai. Jika katalog
renderer tidak memiliki bentuk yang tepat, pengarah memilih tidak menggambar.
Aturan deterministik, tanpa LLM, tanpa leksikon alat ukur, dan tanpa judul cerita.
"""
from __future__ import annotations

import hashlib
import re


POLA_KAPAL = re.compile(r"\b(kapal|bahtera|perahu)\b", re.I)
POLA_OMBAK = re.compile(r"\b(ombak|gelombang)\b", re.I)
POLA_GERAK_KELOMPOK = re.compile(
    r"\b(berlari|berlarian|menyerbu|berbondong-bondong|berdatangan|bergerak serentak)\b",
    re.I,
)
POLA_DINDING = re.compile(r"\b(dinding|tembok|benteng|lubang|terowongan)\b", re.I)
POLA_ZULKARNAIN = re.compile(r"\b(zulkarnain|zulqarnain)\b", re.I)
POLA_YAJUJ = re.compile(r"\b(ya['’]?juj|ma['’]?juj)\b", re.I)
POLA_MATERIAL_DINDING = re.compile(r"\b(besi|tembaga)\b", re.I)
POLA_DUA_GUNUNG = re.compile(r"\b(dua gunung|celah dua gunung)\b", re.I)
POLA_KUBUR = re.compile(r"\b(kubur|makam|pemakaman|jenazah)\b", re.I)
POLA_PEMIMPIN_SAKRAL = re.compile(
    r"\b(rasulullah|rasul|nabi(?:\s+\w+)?|malaikat(?:\s+\w+)?|jibril|mikail|israfil|"
    r"abu bakar|umar|utsman|usman|ali bin abi thalib)\b.{0,45}"
    r"\b(pemimpin|pemuka|raja|panglima)\b|"
    r"\b(pemimpin|pemuka|raja|panglima)\b.{0,45}"
    r"\b(rasulullah|rasul|nabi(?:\s+\w+)?|malaikat(?:\s+\w+)?|jibril|mikail|israfil|"
    r"abu bakar|umar|utsman|usman|ali bin abi thalib)\b",
    re.I,
)
POLA_PENGGALI_SAKRAL = re.compile(
    r"\b(rasulullah|rasul|nabi(?:\s+\w+)?|malaikat(?:\s+\w+)?|jibril|mikail|israfil|"
    r"sahabat|abu bakar|umar|utsman|usman|ali bin abi thalib)\b.{0,35}"
    r"\b(penggali|menggali|digali|menggerogoti|mengikis)\b|"
    r"\b(penggali|menggali|digali|menggerogoti|mengikis)\b.{0,35}"
    r"\b(rasulullah|rasul|nabi(?:\s+\w+)?|malaikat(?:\s+\w+)?|jibril|mikail|israfil|"
    r"sahabat|abu bakar|umar|utsman|usman|ali bin abi thalib)\b",
    re.I,
)
POLA_GALI = re.compile(r"\b(penggali|menggali|digali|menggerogoti|mengikis)\b", re.I)
POLA_PEMIMPIN = re.compile(r"\b(pemimpin|pemuka|raja|panglima)\b", re.I)
POLA_SAHABAT = re.compile(
    r"\b(sahabat|abu bakar|umar|utsman|usman|ali bin abi thalib)\b", re.I
)
POLA_KAABAH = re.compile(
    r"\b(ka['’]?bah|baitullah|rumah allah|rumah tuhan)\b", re.I
)
POLA_MATA_AIR = re.compile(r"\b(mata air|mata-mata air)\b", re.I)
POLA_AIR_MATA = re.compile(r"\b(air mata|air matanya|menangis|tangis)\b", re.I)

# Objek manusia renderer harus memiliki konteks pelaku yang jelas. "Arus" di cerita.js
# adalah kerumunan berlari, bukan air; air generik tidak dipetakan ke jenis ini.
POLA_KERUMUNAN = re.compile(
    r"\b(kaum\w*|orang-orang|manusia|golongan|umat|kerumunan|massa)\b", re.I
)
POLA_HEWAN = re.compile(r"\b(hewan|binatang|ternak)\b", re.I)
POLA_GUNUNG = re.compile(r"\b(gunung|bukit)\b", re.I)
POLA_GERBANG = re.compile(r"\b(gerbang|pintu gerbang)\b", re.I)
POLA_ISTANA = re.compile(r"\b(istana|keraton)\b", re.I)
POLA_RUMAH = re.compile(r"\b(rumah|pondok)\b", re.I)

POLA_PERUBAHAN = {
    "retak": re.compile(r"\b(retak|retakan|pecah)\b", re.I),
    "lubang": re.compile(r"\b(lubang|terkikis|terbuka|membesar|hampir tembus|nyaris tembus)\b", re.I),
    "jebol": re.compile(r"\b(jebol|runtuh|roboh|hancur)\b", re.I),
}

KATA_KUNCI_LAYAR = (
    re.compile(r"\b(\d+(?:[.,]\d+)?\s*(?:tahun|bulan|hari|malam|meter|kilometer|orang))\b", re.I),
    re.compile(
        r"\b((?:seratus|seribu|satu|dua|tiga|empat|lima|enam|tujuh|delapan|sembilan|sepuluh|sebelas)"
        r"(?:\s+(?:ratus|puluh|belas|satu|dua|tiga|empat|lima|enam|tujuh|delapan|sembilan)){0,3}"
        r"\s+(?:tahun|bulan|hari|malam|hasta|meter|kilometer|orang|golongan))\b",
        re.I,
    ),
    re.compile(r"\b(jebol|terbelah|kiamat|banjir besar|hari kebangkitan)\b", re.I),
)


def _seed(teks: str) -> int:
    return int(hashlib.sha1(teks.casefold().encode("utf-8")).hexdigest()[:8], 16)


def _kalimat_yang_memuat(teks: str, pola: re.Pattern) -> list[str]:
    return [
        kalimat.strip()
        for kalimat in re.split(r"(?<=[.!?;])\s+|\n+", teks)
        if kalimat.strip() and pola.search(kalimat)
    ]


def _konteks_dinding_zulkarnain(teks: str, konteks: str | None = None) -> bool:
    """Ngarai renderer hanya untuk dinding Zulkarnain yang sudah dikenali konteks cerita."""
    if POLA_KUBUR.search(teks):
        return False
    sumber = f"{teks} {konteks or ''}"
    material = bool(POLA_MATERIAL_DINDING.search(sumber))
    dua_gunung = bool(POLA_DUA_GUNUNG.search(sumber))
    zulkarnain = bool(POLA_ZULKARNAIN.search(sumber))
    yajuj = bool(POLA_YAJUJ.search(sumber))
    return (material and dua_gunung) or (zulkarnain and (material or dua_gunung or yajuj)) or (
        yajuj and (material or dua_gunung)
    )


def _jenis_disebut(teks: str, konteks: str | None = None) -> list[str]:
    jenis: list[str] = []
    tambah = lambda nama: jenis.append(nama) if nama not in jenis else None

    if POLA_KAPAL.search(teks):
        tambah("bahtera")
    if POLA_OMBAK.search(teks):
        tambah("ombak")

    # Konteks diperiksa per kalimat agar "lubang kubur" tidak ikut memakai
    # dinding Zulkarnain hanya karena kalimat lain menyebut dinding besi.
    kalimat_dinding = [
        kalimat for kalimat in re.split(r"(?<=[.!?;])\s+|\n+", teks)
        if kalimat.strip()
    ]
    for kalimat in kalimat_dinding:
        konteks_dinding = _konteks_dinding_zulkarnain(kalimat, konteks)
        if konteks_dinding and (POLA_DINDING.search(kalimat) or POLA_GALI.search(kalimat)):
            tambah("ngarai")
        # Penggali adalah sosok manusia; blokir hanya bila kalimat menghubungkannya
        # langsung dengan tokoh sakral, bukan sekadar menyebut Allah di kalimat yang sama.
        if konteks_dinding and POLA_GALI.search(kalimat) and not POLA_PENGGALI_SAKRAL.search(kalimat):
            tambah("penggali")

    # "Pemimpin" tidak menjadi sosok manusia bila dalam kalimat yang sama merujuk
    # Nabi/Rasul/malaikat/sahabat. Frasa deskriptif tidak boleh mengubah adab visual.
    for kalimat in _kalimat_yang_memuat(teks, POLA_PEMIMPIN):
        if not POLA_PEMIMPIN_SAKRAL.search(kalimat):
            tambah("pemimpin")

    # Kelompok manusia tidak boleh dijadikan siluet sahabat. Untuk kelompok umum,
    # renderer arus/kerumunan hanya dipakai saat subjek plural memang disebut.
    for kalimat in _kalimat_yang_memuat(teks, POLA_KERUMUNAN):
        if not POLA_SAHABAT.search(kalimat):
            tambah("arus" if POLA_GERAK_KELOMPOK.search(kalimat) else "kerumunan")

    for kalimat in _kalimat_yang_memuat(teks, POLA_MATA_AIR):
        if not POLA_AIR_MATA.search(kalimat):
            tambah("pancar")
    if POLA_GUNUNG.search(teks):
        tambah("gunung")
    if POLA_HEWAN.search(teks):
        tambah("hewan")
    if re.search(r"\bunta\b", teks, re.I):
        tambah("unta")
    if POLA_GERBANG.search(teks):
        tambah("gerbang")
    if POLA_ISTANA.search(teks):
        tambah("istana")
    # Renderer rumah adalah rumah umum; tidak ada bentuk Ka'bah dalam katalog.
    if POLA_RUMAH.search(teks) and not POLA_KAABAH.search(teks):
        tambah("rumah")
    return jenis


def _properti_benda(jenis: str, teks: str, durasi: float, seed: int) -> dict:
    """Susun posisi dan gerak sederhana yang mengikuti aksi dalam teks segmen."""
    x_sisi = 330 if seed % 2 else 750
    dasar = {"jenis": jenis, "x": x_sisi, "y": 1320, "s": 0.82}
    if jenis == "bahtera":
        dasar.update({
            "x": [[0, x_sisi - 90], [max(0.5, durasi * 0.85), x_sisi + 90]],
            "y": [[0, 1300], [max(0.5, durasi * 0.85), 1270]],
            "s": 0.82, "goyang": 1.0, "cahaya": 0.35,
        })
        if re.search(r"\b(ombak|gelombang|badai|banjir)\b", teks, re.I):
            dasar["goyang"] = 2.2
    elif jenis == "ombak":
        dasar.update({
            "x": 540, "y": [[0, 1480], [max(0.5, durasi * 0.8), 1220]],
            "s": 1.0, "tinggi": 520, "depan": True, "seed": seed % 997,
        })
    elif jenis == "pancar":
        dasar.update({
            "x": 540, "y": 1450, "s": 0.9, "kuat": 0.9, "tinggi": 520,
            "seed": seed % 997,
        })
    elif jenis == "gunung":
        dasar.update({"x": x_sisi, "y": 1320, "s": 0.9, "belakang": True})
    elif jenis == "kerumunan":
        dasar.update({
            "x": x_sisi, "y": 1580, "s": 0.72, "n": 5, "w": 420,
            "seed": seed % 997,
        })
    elif jenis == "ngarai":
        dasar.update({
            "x": 540, "y": 1320, "s": 0.95, "lubang": 0.12, "jebol": 0.0,
            "lx": 0, "ly": -190, "seed": seed % 997, "belakang": True,
        })
        if POLA_PERUBAHAN["retak"].search(teks):
            dasar["lubang"] = 0.24
        if POLA_PERUBAHAN["lubang"].search(teks):
            dasar["lubang"] = 0.62
        if POLA_PERUBAHAN["jebol"].search(teks):
            dasar["lubang"] = 1.0
            dasar["jebol"] = 1.0
    elif jenis == "penggali":
        dasar.update({
            "x": 540, "y": 1420, "s": 0.82, "aktif": 1, "n": 5,
            "seed": seed % 997,
        })
    elif jenis == "pemimpin":
        dasar.update({"x": x_sisi, "y": 1350, "s": 0.92, "angkat": 0.75})
    elif jenis in {"hewan", "unta"}:
        dasar.update({
            "x": [[0, x_sisi - 100], [max(0.5, durasi * 0.8), x_sisi + 100]],
            "y": 1390, "s": 0.82,
        })
    elif jenis in {"gerbang", "istana"}:
        dasar.update({"x": 540, "y": 1270, "s": 0.9, "belakang": True})
    return dasar


def arahkan_subjek(
    teks: str, durasi: float, indeks: int = 0, *, konteks: str | None = None
) -> dict:
    """Kembalikan benda, teks layar, dan penanda klimaks untuk satu segmen narasi."""
    if not isinstance(teks, str) or not teks.strip():
        return {"benda": [], "teks": [], "klimaks": False}
    seed = _seed(f"{indeks}|{teks}")
    benda = [
        _properti_benda(jenis, teks, max(0.5, float(durasi or 0.5)), seed + n * 31)
        for n, jenis in enumerate(_jenis_disebut(teks, konteks))
    ]
    teks_layar = []
    for pola in KATA_KUNCI_LAYAR:
        cocok = pola.search(teks)
        if cocok:
            label = cocok.group(1).strip()
            if label.casefold() not in {x["teks"].casefold() for x in teks_layar}:
                teks_layar.append({"at": 0.15, "teks": label.upper(), "y": 340, "ukuran": 62})
    klimaks = bool(
        POLA_PERUBAHAN["jebol"].search(teks)
        or re.search(r"\b(terbelah|meledak|tenggelam|jatuh|ditelan)\b", teks, re.I)
    )
    return {"benda": benda, "teks": teks_layar, "klimaks": klimaks}
