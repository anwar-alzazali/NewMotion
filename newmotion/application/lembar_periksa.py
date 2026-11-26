"""Lembar frame untuk diperiksa mata (manusia atau model vision), tanpa membuat MP4.

Satu frame per shot, diambil pada 90% durasi shot (keadaan akhir rencana [awal, akhir] sudah
tercapai di 85%, jadi yang diperiksa adalah keadaan yang dijanjikan narasi),
diberi label nomor beat. Frame disusun menjadi beberapa lembar 4x2 agar tetap terbaca
setelah diperkecil oleh API vision.
"""
from __future__ import annotations

import json
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path

AKAR = Path(__file__).resolve().parents[2]
PAPAN_BUAT = AKAR / "mesin-video" / "papan_buat.py"
KOLOM, BARIS, LEBAR, TINGGI, LABEL = 4, 2, 360, 640, 44


def waktu_frame(spek: Mapping) -> list[tuple[int, float]]:
    """[(nomor beat 1-based, detik)] satu per shot."""
    shots = spek.get("cerita", {}).get("shot", [])
    akhir = [s["at"] for s in shots[1:]] + [float(spek.get("durasi") or shots[-1]["at"] + 4)]
    keluar = []
    for i, (s, b) in enumerate(zip(shots, akhir)):
        a = float(s["at"])
        t = min(a + 0.9 * (b - a), b - 0.2)
        keluar.append((int(s.get("_adegan", i)) + 1, round(max(a, t), 2)))
    return keluar


def buat_lembar(spek: Mapping, folder: str | Path) -> list[Path]:
    """Render frame lewat papan_buat --pratinjau lalu susun lembar JPEG. Mengembalikan jalur lembar."""
    from PIL import Image, ImageDraw, ImageFont

    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    jalur_spek = folder / "papan_periksa.json"
    jalur_spek.write_text(json.dumps(spek, ensure_ascii=False), encoding="utf-8")
    daftar = waktu_frame(spek)
    awalan = folder / "fr"
    subprocess.run([sys.executable, str(PAPAN_BUAT), str(jalur_spek), "-o", str(awalan),
                    "--pratinjau", ",".join(str(t) for _, t in daftar)], check=True, capture_output=True)
    try:
        huruf = ImageFont.truetype("DejaVuSans-Bold.ttf", 30)
    except OSError:
        huruf = ImageFont.load_default()
    per = KOLOM * BARIS
    lembar = []
    for k in range(0, len(daftar), per):
        bagian = daftar[k:k + per]
        img = Image.new("RGB", (KOLOM * LEBAR, BARIS * (TINGGI + LABEL)), "white")
        g = ImageDraw.Draw(img)
        for j, (beat, t) in enumerate(bagian):
            berkas = Path(f"{awalan}_{t}.png")
            x, y = (j % KOLOM) * LEBAR, (j // KOLOM) * (TINGGI + LABEL)
            with Image.open(berkas) as f:
                img.paste(f.convert("RGB").resize((LEBAR - 6, TINGGI)), (x + 3, y + LABEL))
            g.text((x + 10, y + 6), f"BEAT {beat}  ({t:.1f} dtk)", fill="black", font=huruf)
            berkas.unlink(missing_ok=True)
        keluar = folder / f"lembar_{k // per + 1}.jpg"
        img.save(keluar, quality=85)
        lembar.append(keluar)
    for sisa in (jalur_spek, Path(f"{awalan}_papan.html")):
        sisa.unlink(missing_ok=True)
    return lembar
