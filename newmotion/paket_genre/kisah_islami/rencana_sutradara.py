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
from newmotion.application.kemampuan_tokoh import HADAP, SUKU, gerak_sah, kemampuan
from newmotion.application.katalog_suara import (
    INTONASI,
    KERAS,
    VOL_SUASANA,
    berkas,
    katalog_suara,
)

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
JEDA_ULANG = 0.6  # detik antar-bunyi efek berulang (mis. ayunan beliung)


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
    from newmotion.application.kebutuhan_renderer import validasi_kebutuhan

    g.extend(validasi_kebutuhan(rencana.get("belum_ada"), label="belum_ada"))
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
        g.extend(validasi_kebutuhan(b.get("belum_ada"), label=f"{lbl}.belum_ada"))
        for kebutuhan in b.get("belum_ada", []) if isinstance(b.get("belum_ada"), list) else []:
            if isinstance(kebutuhan, Mapping):
                bukti_kebutuhan = kebutuhan.get("bukti", "")
                if isinstance(bukti_kebutuhan, str) and _polos(bukti_kebutuhan) not in narasi:
                    g.append(f"{lbl}.belum_ada: bukti harus potongan narasi beat itu")
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
                elif isinstance(v, list) and k not in kat[j].get("animasi", ()):
                    g.append(f"{lbl}: {j}.{k} tidak bisa dianimasikan; pakai satu nilai "
                             f"(yang bisa [awal, akhir]: {', '.join(kat[j].get('animasi', ())) or '-'})")
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
        if "suara" in b:
            g += _validasi_suara(b["suara"], narasi, lbl)
        if "figuran" in b:
            g += _validasi_figuran(b["figuran"], jenis_beat, narasi_beat[n - 1], lbl)
    if rencana.get("suku", "umum") not in SUKU:
        g.append(f"suku harus salah satu {SUKU}")
    return g


MAKS_FIGURAN = 6
PINDAH = ("ke_kiri", "ke_kanan", "berpencar")  # gerak figuran sepanjang beat (berpencar = saling menjauh)
JARAK_PINDAH = 300
POLA_SAKRAL = re.compile(r"\b(?:rasulullah|rasul|nabi|malaikat|jibril|mikail|israfil|sahabat|abu bakar|umar|"
                         r"utsman|usman|ali bin abi thalib)\b", re.IGNORECASE)


def _validasi_figuran(fig: Any, jenis_beat: set, narasi: str, lbl: str) -> list[str]:
    """Figuran = orang biasa (bukan siluet). Tidak boleh di beat yang menyebut tokoh sakral:
    figuran bisa terbaca sebagai sosok nabi/sahabat/malaikat."""
    if not isinstance(fig, list):
        return [f"{lbl}: figuran harus daftar"]
    if fig and POLA_SAKRAL.search(narasi):
        return [f"{lbl}: figuran tidak boleh di beat yang menyebut nabi, malaikat, atau sahabat (adab); pakai kerumunan siluet atau tanpa tokoh"]
    g, total, kait = [], 0, kemampuan()["kait"]
    for f in fig:
        if not isinstance(f, Mapping):
            g.append(f"{lbl}: figuran harus objek")
            continue
        n = f.get("jumlah", 1)
        if not isinstance(n, int) or not 1 <= n <= MAKS_FIGURAN:
            g.append(f"{lbl}: figuran.jumlah 1..{MAKS_FIGURAN}")
            n = 1
        total += n
        if f.get("suku", "umum") not in SUKU:
            g.append(f"{lbl}: figuran.suku harus {SUKU}")
        if f.get("tempat", "tengah") not in TEMPAT_DASAR:
            g.append(f"{lbl}: figuran.tempat harus salah satu {tuple(TEMPAT_DASAR)}")
        if f.get("gerak", "berdiri") not in gerak_sah():
            g.append(f"{lbl}: figuran.gerak {f.get('gerak')!r} tidak dikenal renderer")
        if f.get("hadap", "depan") not in HADAP:
            g.append(f"{lbl}: figuran.hadap harus {HADAP}")
        if f.get("pindah") not in (None, *PINDAH):
            g.append(f"{lbl}: figuran.pindah harus salah satu {PINDAH} atau null")
        if f.get("naik") is not None:
            if f["naik"] not in kait:
                g.append(f"{lbl}: figuran.naik hanya untuk {tuple(kait)}")
            elif f["naik"] not in jenis_beat:
                g.append(f"{lbl}: figuran.naik {f['naik']!r} harus ada di subjek beat ini")
            elif n != 1:
                g.append(f"{lbl}: figuran yang naik/duduk di benda jumlahnya 1")
    if total > MAKS_FIGURAN:
        g.append(f"{lbl}: total figuran maksimal {MAKS_FIGURAN} per beat")
    return g


LETAK_FIGURAN = {  # (x, y kaki, skala, jauh)
    "tengah": (540, 1720, 0.78, False), "kiri": (280, 1720, 0.78, False), "kanan": (800, 1720, 0.78, False),
    "jauh": (540, 1330, 0.45, True), "depan_kiri": (230, 1900, 1.0, False), "depan_kanan": (850, 1900, 1.0, False),
}


def figuran_dari_rencana(rb: Mapping, benda: list[dict], kunci: int, ds: float = 4.0) -> list[dict]:
    """Rencana figuran satu beat -> boneka figuran (npc) dengan posisi, gerak, hadap, pindah, dan kait."""
    keluar: list[dict] = []
    for i, f in enumerate(rb.get("figuran") or []):
        x0, y0, sk, blk = LETAK_FIGURAN[f.get("tempat", "tengah")]
        n = int(f.get("jumlah", 1))
        for k in range(n):
            x = round(x0 + (k - (n - 1) / 2) * 150 * sk)
            gerak = f.get("gerak", "berdiri")
            o = {"npc": kunci * 10 + i * 3 + k, "pose": gerak, "x": x, "y": y0 + (k % 2) * 18, "s": sk}
            if f.get("suku"):  # tanpa suku: ikut suku cerita
                o["suku"] = f["suku"]
            if f.get("hadap") in ("kanan", "kiri"):
                o["profil"] = f["hadap"]
            pindah = f.get("pindah")
            if pindah:  # bergerak sepanjang beat; berpencar = separuh ke kiri, separuh ke kanan (saling menjauh)
                arah = -1 if pindah == "ke_kiri" or (pindah == "berpencar" and k < n / 2) else 1
                o["x"] = [[0, x], [round(max(0.6, ds * 0.9), 2), round(x + arah * JARAK_PINDAH * sk)]]
                o["profil"] = "kiri" if arah < 0 else "kanan"
                if gerak == "berdiri":
                    o["pose"] = "jalan"
            if f.get("naik"):
                target = next((b for b in benda if b.get("jenis") == f["naik"]), None)
                if target is not None:
                    target.setdefault("id", f"kait_{kunci}_{i}")
                    o = {k2: o[k2] for k2 in ("npc", "suku") if k2 in o} | {"kait": target["id"]}
            keluar.append(o)
    return keluar


def _validasi_suara(sr: Any, narasi_polos: str, lbl: str) -> list[str]:
    if not isinstance(sr, Mapping):
        return [f"{lbl}: suara harus objek"]
    k = katalog_suara()
    g = []
    if sr.get("suasana") not in (None, *k["suasana"]):
        g.append(f"{lbl}: suasana {sr.get('suasana')!r} tidak ada di katalog suara (atau null)")
    if sr.get("intonasi", "tenang") not in INTONASI:
        g.append(f"{lbl}: intonasi harus salah satu {INTONASI}")
    efek = sr.get("efek", [])
    if not isinstance(efek, list) or len(efek) > 3:
        return g + [f"{lbl}: suara.efek harus daftar maksimal 3"]
    for e in efek:
        if not isinstance(e, Mapping) or e.get("nama") not in k["efek"]:
            g.append(f"{lbl}: efek {(e or {}).get('nama') if isinstance(e, Mapping) else e!r} tidak ada di katalog suara")
            continue
        pada = e.get("pada")
        if pada is not None and (not isinstance(pada, str) or not pada.strip() or _polos(pada) not in narasi_polos):
            g.append(f"{lbl}: efek.pada harus kata/potongan persis dari narasi beat itu (atau null = awal beat)")
        if e.get("keras", "sedang") not in KERAS:
            g.append(f"{lbl}: efek.keras harus {tuple(KERAS)}")
        if not (isinstance(e.get("ulang", 1), int) and 1 <= e.get("ulang", 1) <= 12):
            g.append(f"{lbl}: efek.ulang harus bilangan 1..12 (ritme berulang, jeda 0,6 dtk)")
    if not isinstance(sr.get("transisi", False), bool):
        g.append(f"{lbl}: suara.transisi harus true/false")
    return g


def _waktu_pada(pada: str | None, teks: str, t0: float, dur: float, kata: list | None) -> float:
    """Detik absolut kata `pada` di beat: dari waktu kata TTS bila ada, selain itu perkiraan proporsional."""
    if not pada:
        return round(t0 + 0.05, 2)
    kepala = _polos(pada).split()[0] if _polos(pada).split() else ""
    for t, k in kata or []:
        if _polos(str(k)).startswith(kepala):
            return round(float(t), 2)
    posisi = _polos(teks).find(_polos(pada))
    return round(t0 + dur * max(0, posisi) / max(1, len(_polos(teks))), 2)


def rekaman_dari_rencana(adegan: list[Mapping], jadwal: list[tuple[float, float]],
                         waktu_kata: list | None = None) -> list[dict]:
    """Suara rencana tiap beat -> daftar `rekaman` papan. Suasana yang sama di beat berurutan
    digabung menjadi satu putaran; berganti/berhenti dengan silang 0,6 dtk."""
    keluar: list[dict] = []
    aktif: dict | None = None
    for i, (a, (t0, dur)) in enumerate(zip(adegan, jadwal)):
        sr = (a.get("rencana") or {}).get("suara")
        if sr is None:
            continue
        nama = sr.get("suasana")
        if aktif and aktif["_nama"] != nama:
            aktif["sampai"] = round(t0 + 0.6, 2)
            aktif = None
        if nama and not aktif:
            aktif = {"_nama": nama, "berkas": berkas(nama), "at": round(t0, 2), "vol": VOL_SUASANA,
                     "ulang": True, "masuk": 0.8, "keluar": 1.2}
            keluar.append(aktif)
        kata = waktu_kata[i] if waktu_kata and i < len(waktu_kata) else None
        if sr.get("transisi") and i > 0:
            keluar.append({"berkas": berkas("whoosh"), "vol": 0.25, "at": round(max(0, t0 - 0.05), 2), "masuk": 0.02})
        for e in sr.get("efek", []):
            at = _waktu_pada(e.get("pada"), a.get("teks", ""), t0, dur, kata)
            for u in range(int(e.get("ulang", 1))):
                if at + u * JEDA_ULANG >= t0 + dur:
                    break  # ritme berhenti di akhir beat
                keluar.append({"berkas": berkas(e["nama"]), "vol": KERAS[e.get("keras", "sedang")],
                               "at": round(at + u * JEDA_ULANG, 2), "masuk": 0.02})
    for r in keluar:
        r.pop("_nama", None)
    return sorted(keluar, key=lambda r: r["at"])


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
            if isinstance(a["rencana"].get("suara"), Mapping) and a["rencana"]["suara"].get("intonasi"):
                a["intonasi"] = a["rencana"]["suara"]["intonasi"]  # dibaca tahap TTS
    if rencana.get("objek_inti"):
        hasil["objek_inti"] = copy.deepcopy(dict(rencana["objek_inti"]))
    if rencana.get("suku") in ("arab",):
        hasil["suku"] = rencana["suku"]
    return hasil
