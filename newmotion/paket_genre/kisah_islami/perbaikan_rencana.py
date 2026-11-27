"""Perbaikan pasti (tanpa LLM) untuk rencana sutradara sebelum divalidasi.

Kegagalan LLM yang paling sering bukan salah makna, tetapi salah format kecil: bukti tidak persis, parameter
benda yang tidak ada, nilai di luar pilihan, figuran di beat yang menyebut nabi, kartu dalil berlebih.
Dulu satu kesalahan kecil membuat seluruh rencana (±Rp1.500 per percobaan) dibuang dan pratinjau jatuh ke
sutradara aturan. Kini kesalahan yang aman diperbaiki mesin; hanya yang menyangkut makna/adab yang tidak bisa
diperbaiki pasti yang tetap dikembalikan ke LLM.

Prinsip: perbaikan TIDAK pernah menambah keputusan makna baru selain bawaan yang netral (tempat "tengah",
bidikan "lebar", dsb.), dan tidak pernah melonggarkan adab: figuran di beat bertokoh mulia diganti kerumunan
siluet (yang memang diizinkan penjaga), bukan dibiarkan.
"""
from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from newmotion.application.katalog_renderer import katalog_subjek
from newmotion.application.katalog_suara import INTONASI, KERAS, katalog_suara
from newmotion.application.kemampuan_tokoh import HADAP, SUKU, gerak_sah, kemampuan

from .rencana_sutradara import (
    AKSEN,
    BIDIKAN,
    LORONG,
    MAKS_FIGURAN,
    MAKS_TEKS_LAYAR,
    PERAN_KAMU,
    PINDAH,
    POLA_SAKRAL,
    RELASI,
    TEMPAT_DASAR,
    _polos,
)

SIMPUL_SILUET = {"genangan_tubuh", "naungan_kelompok"}


def _bukti_dari(narasi: str, kata: int = 6) -> str:
    return " ".join(narasi.split()[:kata]) or narasi


def _potong_teks(t: str) -> str:
    t = " ".join(str(t).replace("\n", " ").split())
    if len(t) <= MAKS_TEKS_LAYAR:
        return t
    return t[:MAKS_TEKS_LAYAR].rsplit(" ", 1)[0] or t[:MAKS_TEKS_LAYAR]


def perbaiki_rencana(r: Any, narasi_beat: list[str], *, beat_berdalil: set[int] | None = None,
                     maks_kartu: int = 2) -> list[str]:
    """Perbaiki `r` DI TEMPAT. Kembalikan catatan perbaikan (untuk status/log). Aman dipanggil berulang."""
    if not isinstance(r, dict):
        return []
    catat: list[str] = []
    kat = katalog_subjek()
    n_beat = len(narasi_beat)

    inti = r.get("objek_inti")
    if inti is not None and (not isinstance(inti, Mapping) or inti.get("jenis") not in kat):
        r["objek_inti"] = None
        catat.append("objek_inti tidak dikenal -> null")
    if r.get("suku", "umum") not in SUKU:
        r["suku"] = "umum"
    if not isinstance(r.get("belum_ada", []), list):
        r.pop("belum_ada", None)

    # beat: buang yang rusak/ganda/di luar rentang, tambahkan yang hilang (mesin melengkapi isinya)
    daftar = r.get("beat") if isinstance(r.get("beat"), list) else []
    per_nomor: dict[int, dict] = {}
    for b in daftar:
        if isinstance(b, dict) and isinstance(b.get("beat"), int) and 1 <= b["beat"] <= n_beat and b["beat"] not in per_nomor:
            per_nomor[b["beat"]] = b
    for n in range(1, n_beat + 1):
        if n not in per_nomor:
            per_nomor[n] = {"beat": n, "bukti": _bukti_dari(narasi_beat[n - 1]), "subjek": [], "kamu": "saksi",
                            "kamera": {"bidikan": "lebar", "aksen": None}, "teks_layar": None, "klimaks": False}
            catat.append(f"beat {n} hilang -> beat bawaan")
    r["beat"] = [per_nomor[n] for n in range(1, n_beat + 1)]

    sk = katalog_suara()
    pegang_sah = set(kemampuan()["pegang"])
    gerak = gerak_sah()
    kartu = 0
    for b in r["beat"]:
        n, narasi = b["beat"], narasi_beat[b["beat"] - 1]
        lbl, polos = f"beat {n}", _polos(narasi)
        sakral = bool(POLA_SAKRAL.search(narasi))
        if not isinstance(b.get("bukti"), str) or not b["bukti"].strip() or _polos(b["bukti"]) not in polos:
            b["bukti"] = _bukti_dari(narasi)
            catat.append(f"{lbl}: bukti diganti potongan narasi")
        if not isinstance(b.get("belum_ada", []), list):
            b.pop("belum_ada", None)
        else:
            b["belum_ada"] = [k for k in b.get("belum_ada", []) if isinstance(k, Mapping)
                              and isinstance(k.get("bukti"), str) and _polos(k["bukti"]) in polos] or None
            if b["belum_ada"] is None:
                b.pop("belum_ada")

        subjek = [s for s in (b.get("subjek") if isinstance(b.get("subjek"), list) else []) if isinstance(s, dict)]
        bersih = []
        for s in subjek:
            j = s.get("jenis")
            if j not in kat:
                b.setdefault("belum_ada", []).append({"nama": str(j), "alasan": "jenis belum ada di renderer",
                                                       "bukti": _bukti_dari(narasi, 4)})
                catat.append(f"{lbl}: {j!r} belum ada di renderer -> dicatat sebagai kebutuhan")
                continue
            if j in SIMPUL_SILUET and sakral:
                catat.append(f"{lbl}: {j} dibuang (beat menyebut tokoh mulia)")
                continue
            bersih.append(s)
        jenis_beat = {s["jenis"] for s in bersih}
        for s in bersih:
            j, tempat = s["jenis"], s.get("tempat", "tengah")
            if isinstance(tempat, str) and ":" in tempat:
                rel, target = tempat.split(":", 1)
                if rel not in RELASI or target not in jenis_beat or (rel == "di_lubang" and target != "ngarai"):
                    s["tempat"] = "tengah"
            elif tempat not in TEMPAT_DASAR:
                s["tempat"] = "tengah"
            keadaan = s.get("keadaan") if isinstance(s.get("keadaan"), dict) else {}
            rapi = {}
            for k, v in keadaan.items():
                if k not in kat[j]["parameter"]:
                    continue
                if isinstance(v, list):
                    if len(v) == 2 and all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in v):
                        rapi[k] = v if k in kat[j].get("animasi", ()) else v[-1]
                    continue
                if isinstance(v, (int, float, str, bool)):
                    rapi[k] = v
            if rapi != keadaan or not isinstance(s.get("keadaan", {}), dict):
                catat.append(f"{lbl}: keadaan {j} dirapikan")
                s["keadaan"] = rapi
        b["subjek"] = bersih

        if b.get("kamu", "utama") not in PERAN_KAMU:
            b["kamu"] = "saksi"
        kam = b.get("kamera") if isinstance(b.get("kamera"), dict) else {}
        if not isinstance(b.get("kamera", {}), dict) or kam.get("bidikan", "lebar") not in BIDIKAN or kam.get("aksen") not in AKSEN:
            b["kamera"] = {"bidikan": kam.get("bidikan") if kam.get("bidikan") in BIDIKAN else "lebar",
                           "aksen": kam.get("aksen") if kam.get("aksen") in AKSEN else None}
        t = b.get("teks_layar")
        if t is not None and (not isinstance(t, str) or not t.strip() or len(t) > MAKS_TEKS_LAYAR or t.count("\n") > 2):
            b["teks_layar"] = _potong_teks(t) if isinstance(t, str) and t.strip() else None
        for k in ("klimaks", "kartu_dalil"):
            if k in b and not isinstance(b[k], bool):
                b[k] = bool(b[k])
        if b.get("kartu_dalil") and ((beat_berdalil is not None and n not in beat_berdalil) or kartu >= maks_kartu):
            b["kartu_dalil"] = False
            catat.append(f"{lbl}: kartu_dalil dimatikan")
        kartu += bool(b.get("kartu_dalil"))

        if "suara" in b:
            sr = b["suara"] if isinstance(b["suara"], dict) else {}
            if sr.get("suasana") not in (None, *sk["suasana"]):
                sr["suasana"] = None
            if sr.get("intonasi", "tenang") not in INTONASI:
                sr["intonasi"] = "tenang"
            efek = []
            for e in sr.get("efek", []) if isinstance(sr.get("efek"), list) else []:
                if not isinstance(e, dict) or e.get("nama") not in sk["efek"]:
                    continue
                if e.get("pada") is not None and (not isinstance(e["pada"], str) or _polos(e["pada"]) not in polos):
                    e["pada"] = None
                if e.get("keras", "sedang") not in KERAS:
                    e["keras"] = "sedang"
                u = e.get("ulang", 1)
                if not (isinstance(u, int) and not isinstance(u, bool) and 1 <= u <= 12):
                    e["ulang"] = min(12, max(1, u)) if isinstance(u, int) and not isinstance(u, bool) else 1
                efek.append(e)
            if "efek" in sr or efek:
                sr["efek"] = efek[:3]
            if "transisi" in sr and not isinstance(sr["transisi"], bool):
                sr["transisi"] = bool(sr["transisi"])
            b["suara"] = sr

        if "figuran" in b:
            fig = [f for f in (b["figuran"] if isinstance(b["figuran"], list) else []) if isinstance(f, dict)]
            if fig and sakral:
                # adab: figuran berwajah tidak boleh di beat bertokoh mulia -> kerumunan siluet
                total = sum(f.get("jumlah", 1) if isinstance(f.get("jumlah"), int) else 1 for f in fig)
                b["subjek"].append({"jenis": "arus", "tempat": "tengah",
                                    "keadaan": {"mode": "lorong" if "laut_terbelah" in jenis_beat else "lari", "n": max(6, min(20, total * 3)), "maju": [0.1, 0.9]}})
                b.pop("figuran")
                catat.append(f"{lbl}: figuran diganti kerumunan siluet (beat menyebut tokoh mulia)")
                continue
            for f in fig:
                jml = f.get("jumlah", 1)
                if not (isinstance(jml, int) and not isinstance(jml, bool) and 1 <= jml <= MAKS_FIGURAN):
                    f["jumlah"] = min(MAKS_FIGURAN, max(1, jml)) if isinstance(jml, int) and not isinstance(jml, bool) else 1
                tf = f.get("tempat", "tengah")
                ok_lorong = isinstance(tf, str) and tf.startswith("di_lorong:") and tf.split(":", 1)[1] in LORONG \
                    and tf.split(":", 1)[1] in jenis_beat
                if not ok_lorong and tf not in TEMPAT_DASAR:
                    f["tempat"] = "tengah"
                if f.get("gerak", "berdiri") not in gerak:
                    f["gerak"] = "berdiri"
                if f.get("hadap", "depan") not in HADAP:
                    f["hadap"] = "depan"
                if f.get("pindah") not in (None, *PINDAH):
                    f["pindah"] = None
                if f.get("suku", "umum") not in SUKU:
                    f["suku"] = "umum"
                if f.get("pegang") is not None and f["pegang"] not in pegang_sah:
                    f.pop("pegang")
                if f.get("naik") is not None and f["naik"] not in jenis_beat:
                    f["naik"] = None
                if f.get("nama") is not None and (not isinstance(f["nama"], str)
                                                  or not re.fullmatch(r"[a-zA-Z][a-zA-Z0-9_-]{0,23}", f["nama"])):
                    for k in ("nama", "hadap_ke", "serahkan_ke"):
                        f.pop(k, None)
            nama = [f.get("nama") for f in fig if f.get("nama")]
            for f in fig:
                if f.get("hadap_ke") is not None and (f.get("nama") is None or f["hadap_ke"] not in nama or f["hadap_ke"] == f["nama"]):
                    f.pop("hadap_ke")
            while sum(f.get("jumlah", 1) for f in fig) > MAKS_FIGURAN and fig:
                fig[-1]["jumlah"] = fig[-1].get("jumlah", 1) - 1
                if fig[-1]["jumlah"] < 1:
                    fig.pop()
            b["figuran"] = fig
    return catat


def buang_serah_terima(r: dict) -> list[str]:
    """Serah-terima punya banyak syarat posisi; bila validator masih menolaknya, aksi itu dibuang
    (figuran tetap tampil) daripada seluruh rencana ditolak."""
    catat = []
    for b in r.get("beat", []) if isinstance(r, dict) else []:
        for f in b.get("figuran", []) if isinstance(b, dict) and isinstance(b.get("figuran"), list) else []:
            if isinstance(f, dict) and f.pop("serahkan_ke", None) is not None:
                catat.append(f"beat {b.get('beat')}: serah-terima dibuang")
    return catat
