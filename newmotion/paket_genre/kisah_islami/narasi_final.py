"""Narasi final Kisah Islami: satu permintaan TTS untuk semua beat, intonasi per beat, jeda dramatik.

1. teks_tts(): narasi semua beat digabung, tiap beat diawali tag intonasi ElevenLabs ([calm],
   [whispers], ...) dari rencana sutradara. Satu permintaan = suara konsisten dan hemat kredit.
2. potong(): penjajaran kata dari ElevenLabs dipotong per beat (token tag dibuang).
3. rakit(): potongan disusun ulang dengan jeda per beat (lebih panjang di sekitar klimaks),
   menghasilkan narasi.mp3 + narasi.waktu.json (format narasi_api: kata {teks,t0,t1}) dan
   waktu mulai tiap adegan + waktu kata per adegan untuk pengarah.

Berkas audio yang sudah ada dipakai ulang (kredit ElevenLabs tidak terpakai dua kali).
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

AKAR = Path(__file__).resolve().parents[3]
NARASI_API = AKAR / "mesin-video" / "narasi_api.py"
SUARA_NARATOR = "UdQDnhmw5mrED2XYPXhu"  # Ozhy, narator tetap akun Kisah Islami
INTONASI_TAG = {"tenang": "[calm]", "berat": "[serious]", "tegang": "[tense]", "bisik": "[whispers]",
                "tegas": "[firm]", "haru": "[touched]", "lega": "[relieved]"}
JEDA_DASAR, JEDA_KLIMAKS, JEDA_SEBELUM_KLIMAKS = 0.45, 0.95, 0.7


def _narasi(naskah: Mapping) -> list[str]:
    return [str(a.get("teks", "")) for a in naskah.get("adegan", [])]


def _kata(teks: str) -> list[str]:
    return [w for w in re.sub(r"\[[^\]]*\]", " ", teks).split() if re.search(r"\w", w)]


def _beat(rencana: Mapping | None, i: int) -> Mapping:
    for b in (rencana or {}).get("beat", []):
        if b.get("beat") == i + 1:
            return b
    return {}


def teks_tts(naskah: Mapping, rencana: Mapping | None) -> tuple[str, list[int]]:
    bagian, jumlah = [], []
    for i, teks in enumerate(_narasi(naskah)):
        tag = INTONASI_TAG.get(((_beat(rencana, i).get("suara") or {}).get("intonasi")) or "", "")
        bagian.append(f"{tag} {teks}".strip())
        jumlah.append(len(_kata(teks)))
    return "\n".join(bagian), jumlah


def potong(kata: Sequence[Mapping], jumlah: Sequence[int]) -> list[list[Mapping]]:
    """Kata ElevenLabs ({teks,t0,t1}) -> daftar kata per beat; token tag [..] dibuang."""
    bersih, dalam = [], False
    for k in kata:
        x = str(k["teks"]).strip()
        if x.startswith("["):
            dalam = True
        if not dalam and re.search(r"\w", x):
            bersih.append(k)
        if dalam and "]" in x:
            dalam = False
    keluar, pos = [], 0
    for n in jumlah:
        seg = bersih[pos:pos + n]
        if len(seg) < n:
            raise ValueError(f"penjajaran kata kurang: butuh {n}, tersisa {len(seg)}")
        keluar.append(seg)
        pos += n
    return keluar


def jeda_setelah(rencana: Mapping | None, i: int, n: int) -> float:
    if i == n - 1:
        return 0.0
    if _beat(rencana, i).get("klimaks"):
        return JEDA_KLIMAKS
    if _beat(rencana, i + 1).get("klimaks"):
        return JEDA_SEBELUM_KLIMAKS
    return JEDA_DASAR


def susun_waktu(per_beat: list[list[Mapping]], jeda: Sequence[float]) -> dict[str, Any]:
    """Hitung potongan sumber [a0, a1] tiap beat dan waktu barunya setelah diberi jeda."""
    potongan, mulai, waktu_kata, kata_global, kursor, akhir_lalu = [], [], [], [], 0.0, 0.0
    for i, seg in enumerate(per_beat):
        a0 = max(akhir_lalu, float(seg[0]["t0"]) - 0.08)
        a1 = float(seg[-1]["t1"]) + 0.12
        if i + 1 < len(per_beat):
            a1 = min(a1, float(per_beat[i + 1][0]["t0"]) - 0.02)
        a1 = max(a1, a0 + 0.1)
        potongan.append((round(a0, 3), round(a1, 3)))
        mulai.append(round(kursor, 3))
        wk = []
        for k in seg:
            t0, t1 = kursor + float(k["t0"]) - a0, kursor + float(k["t1"]) - a0
            kata_global.append({"teks": k["teks"], "t0": round(t0, 3), "t1": round(t1, 3)})
            wk.append([round(t0, 3), k["teks"]])
        waktu_kata.append(wk)
        kursor += (a1 - a0) + jeda[i]
        akhir_lalu = a1
    return {"potongan": potongan, "waktu_adegan": mulai, "waktu_kata": waktu_kata, "kata": kata_global,
            "durasi": round(kursor, 3)}


def rakit_audio(mentah: Path, potongan: Sequence[tuple[float, float]], jeda: Sequence[float], keluaran: Path) -> None:
    fc, label = [], []
    for i, ((a0, a1), j) in enumerate(zip(potongan, jeda)):
        fc.append(f"[0:a]atrim={a0}:{a1},asetpts=PTS-STARTPTS,afade=t=in:d=0.03,afade=t=out:st={max(0, a1 - a0 - 0.05):.3f}:d=0.05"
                  + (f",apad=pad_dur={j}" if j > 0 else "") + f"[s{i}]")
        label.append(f"[s{i}]")
    fc.append("".join(label) + f"concat=n={len(label)}:v=0:a=1[a]")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(mentah), "-filter_complex", ";".join(fc),
                    "-map", "[a]", "-c:a", "libmp3lame", "-b:a", "160k", str(keluaran)], check=True)


def tts(teks: str, keluaran: Path, *, suara: str = SUARA_NARATOR, model: str = "eleven_v4") -> list[dict]:
    """Panggil narasi_api.py (ELEVENLABS_API_KEY di env). Mengembalikan kata {teks,t0,t1}."""
    berkas = keluaran.with_suffix(".txt")
    berkas.write_text(teks, encoding="utf-8")
    subprocess.run([sys.executable, str(NARASI_API), str(berkas), "-o", str(keluaran), "--suara", suara, "--model", model],
                   check=True)
    return json.loads(keluaran.with_suffix(".waktu.json").read_text(encoding="utf-8"))["kata"]


def buat_narasi(naskah: Mapping, rencana: Mapping | None, folder: str | Path, *, tts_fn=tts) -> dict[str, Any]:
    """Narasi final di folder: narasi.mp3, narasi.waktu.json, waktu_adegan.json. Pakai ulang bila sudah ada."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    hasil = folder / "waktu_adegan.json"
    if hasil.is_file() and (folder / "narasi.mp3").is_file():
        return json.loads(hasil.read_text(encoding="utf-8"))
    teks, jumlah = teks_tts(naskah, rencana)
    mentah = folder / "mentah.mp3"
    kata = (json.loads(mentah.with_suffix(".waktu.json").read_text(encoding="utf-8"))["kata"]
            if mentah.is_file() and mentah.with_suffix(".waktu.json").is_file() else tts_fn(teks, mentah))
    n = len(jumlah)
    jeda = [jeda_setelah(rencana, i, n) for i in range(n)]
    w = susun_waktu(potong(kata, jumlah), jeda)
    rakit_audio(mentah, w["potongan"], jeda, folder / "narasi.mp3")
    (folder / "narasi.waktu.json").write_text(json.dumps({"kata": w["kata"]}, ensure_ascii=False, indent=1) + "\n",
                                              encoding="utf-8")
    hasil.write_text(json.dumps(w, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return w
