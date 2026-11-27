"""Statistik video (Tugas 9): ciri tiap video + hasil tayang, dan analisis pola dengan kekuatan bukti.

    python -m newmotion.application.statistik_video ciri <id>     # tulis antrean/<id>/ciri.json
    python -m newmotion.application.statistik_video analisis      # bandingkan ciri vs hasil

Hasil tayang dicatat pemilik lewat tombol "📊 Catat hasil" di bot (antrean/<id>/statistik.json, satu catatan
per platform + hari 1/7). Ciri naskah dicatat otomatis setelah produksi final (ciri.json).

Usulan pedoman TIDAK dipakai otomatis: sama dengan Tugas 5d, pemilik yang memutuskan. Di bawah AMBANG video
alat ini menyatakan terang-terangan bahwa pola belum bisa dipercaya.
"""
from __future__ import annotations

import json
import re
import statistics
from collections import defaultdict
from collections.abc import Callable
from pathlib import Path

AKAR = Path(__file__).resolve().parents[2]
ANTREAN = AKAR / "antrean"
AMBANG = 20          # jumlah video minimum sebelum pola layak dipercaya
MIN_KELOMPOK = 3     # anggota minimum tiap kelompok untuk dibandingkan


def _baca(p: Path) -> dict | None:
    try:
        return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else None
    except (json.JSONDecodeError, OSError):
        return None


# ---------------- ciri video ----------------
def jenis_hook(kalimat: str) -> str:
    k = kalimat.strip().lower()
    if not k:
        return "kosong"
    if "?" in k:
        return "pertanyaan"
    if re.search(r"\d", k):
        return "angka"
    if re.search(r"\b(kamu|anda|kau)\b", k):
        return "menyapa_kamu"
    if re.search(r"\b(jangan|berhenti|awas|hati-hati)\b", k):
        return "peringatan"
    return "pernyataan"


def _durasi(d: Path) -> float | None:
    w = _baca(d / "audio" / "narasi.waktu.json")
    if w and w.get("kata"):
        return round(float(w["kata"][-1]["t1"]), 1)
    papan = _baca(d / "papan_final.json") or {}
    return papan.get("durasi")


def ciri_video(d: Path) -> dict:
    """Ciri yang bisa dibandingkan antar video. Hanya dari berkas antrean; tanpa LLM."""
    st = _baca(d / "status.json") or {}
    n = _baca(d / "naskah.json") or {}
    r = _baca(d / "rencana.json") or {}
    beat = n.get("beat") or [{"narasi": a.get("teks", "")} for a in n.get("adegan", [])]
    narasi = [str(b.get("narasi") or "") for b in beat]
    kalimat1 = re.split(r"(?<=[.!?])\s+", narasi[0])[0] if narasi else ""
    rb = r.get("beat") or []
    efek = sum(len((b.get("suara") or {}).get("efek") or []) for b in rb)
    suasana = [((b.get("suara") or {}).get("suasana")) for b in rb]
    papan = _baca(d / "papan_final.json") or _baca(d / "papan_manual.json") or {}
    shot = ((papan.get("cerita") or {}).get("shot")) or []
    suku = (papan.get("cerita") or {}).get("suku") or sorted({b.get("suku") for s in shot for b in s.get("boneka", []) if b.get("suku")})
    return {
        "id": d.name,
        "judul": st.get("judul") or n.get("judul"),
        "genre": st.get("genre") or n.get("genre"),
        "jalur": "manual" if (d / "papan_manual.json").is_file() else "hibrida",
        "jenis_hook": jenis_hook(kalimat1),
        "kata_hook": len(kalimat1.split()),
        "jumlah_beat": len(beat),
        "durasi": _durasi(d),
        "tokoh": sorted({p for b in beat for p in (b.get("peran") or []) if isinstance(p, str)}),
        "ada_klimaks": any(b.get("klimaks") for b in rb),
        "ada_dialog": any(b.get("dialog") for b in beat),
        "jumlah_dalil": len(n.get("dalil") or []),
        "suku": suku if isinstance(suku, list) else [suku],
        "latar": sorted({b.get("suasana") for b in beat if b.get("suasana")}),
        "jumlah_efek": efek,
        "pakai_ambience": any(suasana),
        "jumlah_shot": len(shot),
    }


def simpan_ciri(d: Path) -> dict:
    c = ciri_video(d)
    (d / "ciri.json").write_text(json.dumps(c, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return c


# ---------------- hasil tayang ----------------
def catat_hasil(d: Path, entri: dict, *, waktu: str, sumber: str = "manual") -> dict:
    """Sama dengan gabungStatistik di bot/worker.js: satu catatan per (platform, hari), yang baru menimpa."""
    if entri.get("platform") not in ("tiktok", "facebook") or entri.get("hari") not in (1, 7):
        raise ValueError("platform harus tiktok/facebook dan hari 1 atau 7")
    lama = _baca(d / "statistik.json") or {}
    daftar = [c for c in lama.get("catatan", []) if (c.get("platform"), c.get("hari")) != (entri["platform"], entri["hari"])]
    daftar.append({**entri, "dicatat": waktu, "sumber": sumber})
    daftar.sort(key=lambda c: (c["platform"], c["hari"]))
    isi = {"catatan": daftar}
    (d / "statistik.json").write_text(json.dumps(isi, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return isi


def ambil_dari_facebook(video_id: str) -> list[dict]:  # pragma: no cover - diisi kelak
    """Pengisi otomatis (kelak): Graph API Page -> daftar entri {platform, hari, tayang, suka, komentar, bagikan, tuntas}.
    Ganti fungsi ini (atau PENGISI) tanpa mengubah penyimpanan; catat dengan sumber="facebook_api"."""
    raise NotImplementedError("Pengisi API Facebook belum dibuat; isi lewat tombol 📊 di bot.")


PENGISI: dict[str, Callable[[str], list[dict]]] = {"facebook": ambil_dari_facebook}


# ---------------- analisis ----------------
def nilai(statistik: dict, platform: str) -> dict | None:
    """Ukuran utama per video per platform: hari 7 bila ada, kalau tidak hari 1."""
    cat = {c["hari"]: c for c in statistik.get("catatan", []) if c.get("platform") == platform}
    c = cat.get(7) or cat.get(1)
    if not c or not c.get("tayang"):
        return None
    return {"hari": c["hari"], "tayang": c["tayang"],
            "interaksi": (c.get("suka", 0) + c.get("komentar", 0) + c.get("bagikan", 0)) / c["tayang"] * 100,
            "bagikan": c.get("bagikan", 0) / c["tayang"] * 100, "tuntas": c.get("tuntas")}


def _kelompok(c: dict) -> dict[str, str]:
    """Ciri -> label kelompok yang bisa dibandingkan."""
    dur = c.get("durasi")
    return {
        "jenis hook": c["jenis_hook"],
        "durasi": "?" if dur is None else ("< 45 dtk" if dur < 45 else "45-90 dtk" if dur <= 90 else "> 90 dtk"),
        "jumlah beat": "<= 6" if c["jumlah_beat"] <= 6 else "7-10" if c["jumlah_beat"] <= 10 else "> 10",
        "ada klimaks": "ya" if c["ada_klimaks"] else "tidak",
        "ada dialog": "ya" if c["ada_dialog"] else "tidak",
        "efek suara": "0" if not c["jumlah_efek"] else "1-5" if c["jumlah_efek"] <= 5 else "> 5",
        "jalur": c["jalur"],
    }


def kumpulkan(folder: Path = ANTREAN) -> list[tuple[dict, dict]]:
    out = []
    for d in sorted(p for p in folder.iterdir() if p.is_dir()) if folder.is_dir() else []:
        s = _baca(d / "statistik.json")
        if s and s.get("catatan"):
            out.append((_baca(d / "ciri.json") or ciri_video(d), s))
    return out


def analisis(folder: Path = ANTREAN, *, ukuran: str = "tayang") -> str:
    data = kumpulkan(folder)
    baris = [f"# Statistik video — ukuran: {ukuran} (hari 7, atau hari 1 bila hari 7 belum dicatat)"]
    for platform in ("tiktok", "facebook"):
        rows = [(c, v) for c, s in data if (v := nilai(s, platform)) and v.get(ukuran) is not None]
        baris.append(f"\n## {platform}: {len(rows)} video")
        if not rows:
            baris.append("Belum ada hasil tercatat.")
            continue
        if len(rows) < AMBANG:
            baris.append(f"⚠️ Baru {len(rows)} video (< {AMBANG}). Pola di bawah BELUM bisa dipercaya; anggap catatan awal saja.")
        semua = statistics.median(v[ukuran] for _, v in rows)
        baris.append(f"Median semua video: {semua:,.1f}")
        usulan = []
        per_ciri: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
        for c, v in rows:
            for ciri, label in _kelompok(c).items():
                per_ciri[ciri][label].append(v[ukuran])
        for ciri, grup in per_ciri.items():
            isi = ", ".join(f"{lbl}: median {statistics.median(x):,.1f} (n={len(x)})" for lbl, x in sorted(grup.items()))
            baris.append(f"- {ciri}: {isi}")
            layak = {lbl: x for lbl, x in grup.items() if len(x) >= MIN_KELOMPOK}
            if len(layak) >= 2:
                (lb, xb), (lk, xk) = max(layak.items(), key=lambda kv: statistics.median(kv[1])), min(layak.items(), key=lambda kv: statistics.median(kv[1]))
                mb, mk = statistics.median(xb), statistics.median(xk)
                if mk > 0 and mb / mk >= 1.3:
                    kuat = "lemah" if len(rows) < AMBANG or min(len(xb), len(xk)) < 5 else "sedang" if min(len(xb), len(xk)) < 10 else "cukup"
                    usulan.append(f"- {ciri} = {lb} unggul {mb / mk:.1f}x dibanding {lk} (n {len(xb)} vs {len(xk)}; bukti {kuat})")
        baris.append("\nUsulan pedoman (perlu persetujuan pemilik, tidak dipakai otomatis):")
        baris += usulan or ["- belum ada selisih yang layak diusulkan"]
    return "\n".join(baris)


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="perintah", required=True)
    c = sub.add_parser("ciri")
    c.add_argument("id")
    a = sub.add_parser("analisis")
    a.add_argument("--ukuran", choices=("tayang", "interaksi", "bagikan", "tuntas"), default="tayang")
    x = ap.parse_args()
    if x.perintah == "ciri":
        if not re.fullmatch(r"[a-z0-9_-]{1,60}", x.id):
            raise SystemExit("id tidak sah")
        print(json.dumps(simpan_ciri(ANTREAN / x.id), ensure_ascii=False, indent=1))
    else:
        print(analisis(ukuran=x.ukuran))


if __name__ == "__main__":
    main()
