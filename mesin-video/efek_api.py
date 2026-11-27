"""Buat satu efek suara lewat API ElevenLabs Sound Effects (dijalankan di GitHub Actions; kunci di env ELEVENLABS_API_KEY).

Pakai: python mesin-video/efek_api.py <nama> "<deskripsi bahasa Inggris>" [--durasi 7] [--pengaruh 0.5]
Hasil: mesin-video/aset/suara/<nama>.mp3 (+ <nama>.txt berisi deskripsinya, supaya bisa dibuat ulang).
Biaya: dengan durasi ditentukan, dihitung per detik; tanpa durasi, per pembuatan. Berkas yang sudah ada tidak ditimpa
kecuali --timpa, supaya kredit tidak terbuang karena workflow diulang.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

FOLDER = Path(__file__).resolve().parent / "aset" / "suara"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("nama")
    p.add_argument("deskripsi")
    p.add_argument("--durasi", type=float, default=None, help="0,5-30 detik; kosong = ditentukan model")
    p.add_argument("--pengaruh", type=float, default=0.5, help="prompt_influence 0-1 (tinggi = lebih patuh deskripsi)")
    p.add_argument("--timpa", action="store_true")
    a = p.parse_args()
    if not re.fullmatch(r"[a-z0-9_]{2,40}", a.nama):
        sys.exit("nama hanya huruf kecil, angka, garis bawah (2-40)")
    keluar = FOLDER / f"{a.nama}.mp3"
    if keluar.exists() and not a.timpa:
        sys.exit(f"{keluar.name} sudah ada; pakai --timpa untuk membuat ulang")
    kunci = os.environ.get("ELEVENLABS_API_KEY")
    if not kunci:
        sys.exit("ELEVENLABS_API_KEY kosong")
    badan = {"text": a.deskripsi, "prompt_influence": a.pengaruh}
    if a.durasi:
        badan["duration_seconds"] = max(0.5, min(30.0, a.durasi))
    req = urllib.request.Request("https://api.elevenlabs.io/v1/sound-generation?output_format=mp3_44100_128",
                                 data=json.dumps(badan).encode(), method="POST",
                                 headers={"xi-api-key": kunci, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            data = r.read()
    except urllib.error.HTTPError as e:
        pesan = f"ElevenLabs galat {e.code}: {e.read().decode(errors='replace')[:500]}"
        print("::error::" + pesan.replace("\n", " "))
        sys.exit(pesan)
    if len(data) < 2000:
        sys.exit("audio terlalu kecil: " + data[:200].decode(errors="replace"))
    FOLDER.mkdir(parents=True, exist_ok=True)
    keluar.write_bytes(data)
    keluar.with_suffix(".txt").write_text(json.dumps(badan, ensure_ascii=False) + "\n", encoding="utf-8")
    print("selesai", keluar, len(data), "bita")


if __name__ == "__main__":
    main()
