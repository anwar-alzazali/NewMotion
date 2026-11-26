"""Rencana sutradara (ditulis LLM) -> keputusan per beat yang dipakai pengarah Kisah Islami.

LLM memutuskan MAKNA: objek inti dan perkembangannya, subjek tiap beat, peran tokoh "kamu",
bidikan kamera, teks layar, klimaks. LLM TIDAK menulis koordinat: penempatan memakai
"bahasa panggung" (`tempat`), lalu mesin menerjemahkannya dengan aturan pasti
(posisi relatif, komposisi, lapisan) yang sudah ada di pengarah_naskah.

Format (per naskah):
{
  "objek_inti": {"jenis": "ngarai", "perkembangan": "lubang membesar tiap hari, utuh lagi, akhirnya jebol"},
  "beat": [
    {"beat": 1, "bukti": "potongan PERSIS dari narasi beat ini",
     "subjek": [{"jenis": "ngarai", "tempat": "tengah", "keadaan": {"lubang": [0.2, 0.5]}},
                {"jenis": "penggali", "tempat": "di_lubang:ngarai"}],
     "kamu": "saksi", "kamera": {"bidikan": "lebar", "aksen": null},
     "teks_layar": "DIGALI SETIAP HARI", "klimaks": false}
  ]
}
Nilai keadaan: angka, teks pilihan, atau [awal, akhir] (berubah halus sepanjang shot).
"""
from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping
from typing import Any

from newmotion.application.katalog_renderer import katalog_subjek

from .pengarah_subjek import _properti_benda

PERAN_KAMU = ("utama", "saksi", "tidak")
BIDIKAN = ("lebar", "sedang", "dekat")
AKSEN = (None, "hentak", "guncang")
TEMPAT_DASAR = {
    "tengah": {"x": 540},
    "kiri": {"x": 300},
    "kanan": {"x": 780},
    "jauh": {"x": 540, "y": 1240, "s": 0.6, "belakang": True},
    "depan_kiri": {"x": 250, "y": 1720, "s": 1.15, "depan": True},
    "depan_kanan": {"x": 830, "y": 1720, "s": 1.15, "depan": True},
}
RELASI = ("di_lubang",)  # tempat "di_lubang:<jenis>" (mis. penggali di lubang dinding)
MAKS_TEKS_LAYAR = 40


def _polos(s: str) -> str:
    s = unicodedata.normalize("NFKC", str(s)).casefold()
    s = s.replace("’", "'").replace("‘", "'").replace("…", "...")
    return re.sub(r"[^\w']+", " ", s).strip()


def _angka(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def validasi_rencana(rencana: Any, narasi_beat: list[str]) -> list[str]:
    """Daftar galat (kosong = lolos). narasi_beat: teks narasi tiap beat, urut."""
    if not isinstance(rencana, Mapping):
        return ["rencana harus objek JSON"]
    g: list[str] = []
    kat = katalog_subjek()
    inti = rencana.get("objek_inti")
    if inti is not None and (not isinstance(inti, Mapping) or inti.get("jenis") not in kat):
        g.append(f"objek_inti.jenis {(inti or {}).get('jenis')!r} tidak ada di katalog")
    daftar = rencana.get("beat")
    if not isinstance(daftar, list) or not daftar:
        return g + ["beat kosong"]
    nomor = [b.get("beat") for b in daftar if isinstance(b, Mapping)]
    if sorted(nomor) != list(range(1, len(narasi_beat) + 1)):
        g.append(f"rencana harus punya tepat satu entri untuk beat 1..{len(narasi_beat)} (dapat {nomor})")
    for b in daftar:
        if not isinstance(b, Mapping):
            g.append("setiap beat harus objek")
            continue
        n = b.get("beat")
        lbl = f"beat {n}"
        if not isinstance(n, int) or not 1 <= n <= len(narasi_beat):
            continue
        narasi = _polos(narasi_beat[n - 1])
        bukti = b.get("bukti")
        if not isinstance(bukti, str) or not bukti.strip() or _polos(bukti) not in narasi:
            g.append(f"{lbl}: bukti harus potongan persis dari narasi beat itu")
        subjek = b.get("subjek", [])
        if not isinstance(subjek, list):
            g.append(f"{lbl}: subjek harus daftar")
            subjek = []
        jenis_beat = {s.get("jenis") for s in subjek if isinstance(s, Mapping)}
        for s in subjek:
            if not isinstance(s, Mapping):
                g.append(f"{lbl}: subjek harus objek")
                continue
            j = s.get("jenis")
            if j not in kat:
                g.append(f"{lbl}: jenis {j!r} tidak ada di katalog renderer")
                continue
            tempat = s.get("tempat", "tengah")
            if isinstance(tempat, str) and ":" in tempat:
                rel, target = tempat.split(":", 1)
                if rel not in RELASI:
                    g.append(f"{lbl}: relasi tempat {rel!r} tidak dikenal (pilih {', '.join(RELASI)})")
                elif target not in jenis_beat:
                    g.append(f"{lbl}: {j} {tempat!r} merujuk jenis yang tidak ada di beat ini")
                elif rel == "di_lubang" and target != "ngarai":
                    g.append(f"{lbl}: di_lubang hanya untuk ngarai")
            elif tempat not in TEMPAT_DASAR:
                g.append(f"{lbl}: tempat {tempat!r} tidak dikenal (pilih {', '.join(TEMPAT_DASAR)} atau di_lubang:ngarai)")
            keadaan = s.get("keadaan", {})
            if not isinstance(keadaan, Mapping):
                g.append(f"{lbl}: keadaan {j} harus objek")
                continue
            for k, v in keadaan.items():
                if k not in kat[j]["parameter"]:
                    g.append(f"{lbl}: {j} tidak punya keadaan {k!r} (ada: {', '.join(kat[j]['parameter']) or '-'})")
                elif not (_angka(v) or isinstance(v, (str, bool))
                          or (isinstance(v, list) and len(v) == 2 and all(_angka(x) for x in v))):
                    g.append(f"{lbl}: nilai keadaan {j}.{k} harus angka, teks, atau [awal, akhir]")
        if b.get("kamu", "utama") not in PERAN_KAMU:
            g.append(f"{lbl}: kamu harus salah satu {PERAN_KAMU}")
        kamera = b.get("kamera") or {}
        if not isinstance(kamera, Mapping) or kamera.get("bidikan", "lebar") not in BIDIKAN \
                or kamera.get("aksen") not in AKSEN:
            g.append(f"{lbl}: kamera.bidikan {BIDIKAN}, kamera.aksen {AKSEN}")
        teks = b.get("teks_layar")
        if teks is not None and (not isinstance(teks, str) or len(teks) > MAKS_TEKS_LAYAR or teks.count("\n") > 2):
            g.append(f"{lbl}: teks_layar maksimal {MAKS_TEKS_LAYAR} huruf dan 3 baris")
        if not isinstance(b.get("klimaks", False), bool):
            g.append(f"{lbl}: klimaks harus true/false")
    return g


def _nilai(v: Any, ds: float) -> Any:
    """[awal, akhir] -> kunci waktu halus sepanjang shot; selain itu apa adanya."""
    if isinstance(v, list) and len(v) == 2:
        return [[0, v[0]], [round(max(0.5, ds * 0.85), 2), v[1]]]
    return v


def subjek_dari_rencana(rb: Mapping, teks: str, ds: float, seed: int) -> dict:
    """Satu beat rencana -> struktur yang sama dengan arahkan_subjek, plus peran kamu & kamera."""
    benda = []
    for s in rb.get("subjek", []):
        o = _properti_benda(s["jenis"], teks, ds, seed + len(benda) * 31)
        tempat = s.get("tempat", "tengah")
        if tempat in TEMPAT_DASAR:
            o.update(TEMPAT_DASAR[tempat])
            if tempat != "jauh":
                o.pop("belakang", None)
        for k, v in (s.get("keadaan") or {}).items():
            o[k] = _nilai(v, ds)
        if isinstance(tempat, str) and tempat.startswith("di_lubang:"):
            o["_di_lubang"] = True  # diikat ke lubang oleh _ikat_posisi_subjek
        benda.append(o)
    teks_layar = []
    if rb.get("teks_layar"):
        baris = str(rb["teks_layar"]).split("\n")
        teks_layar.append({"at": 0.15, "teks": rb["teks_layar"], "y": 330,
                           "ukuran": 92 if max(len(x) for x in baris) <= 14 else 68})
    kamera = rb.get("kamera") or {}
    return {"benda": benda, "teks": teks_layar, "klimaks": bool(rb.get("klimaks")),
            "kamu": rb.get("kamu", "utama"), "bidikan": kamera.get("bidikan", "lebar"),
            "aksen": kamera.get("aksen")}


def terapkan_rencana(naskah: dict, rencana: Mapping) -> dict:
    """Salin naskah pengarah dan tempelkan rencana tiap beat ke adegan yang sesuai."""
    import copy

    hasil = copy.deepcopy(naskah)
    per_beat = {b["beat"]: b for b in rencana.get("beat", []) if isinstance(b, Mapping)}
    for i, a in enumerate(hasil.get("adegan", []), 1):
        if i in per_beat:
            a["rencana"] = copy.deepcopy(dict(per_beat[i]))
    if rencana.get("objek_inti"):
        hasil["objek_inti"] = copy.deepcopy(dict(rencana["objek_inti"]))
    return hasil
