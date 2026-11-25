#!/usr/bin/env python3
"""Render kartu animasi HTML -> mp4 9:16.
Kontrak HTML: halaman 1080x1920 dengan fungsi global setT(t) (detik) yang menggambar kondisi pada waktu t.
Pemakaian: python kartu.py kartu/x.html -d 8.0 -o out.mp4"""
import argparse, os, shutil, subprocess, tempfile

FPS = 30


def render(html, durasi, out, suara=None):
    from playwright.sync_api import sync_playwright
    tmp = tempfile.mkdtemp()
    n = int(round(durasi * FPS))
    try:
        with sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_page(viewport={"width": 1080, "height": 1920})
            pg.goto("file://" + os.path.abspath(html))
            pg.evaluate("document.fonts.ready")
            # baris muncul menyebar mengikuti lama narasi (suara = durasi audio, detik)
            nb = pg.evaluate("document.querySelectorAll('.row').length")
            st = [round(0.7 + (i / nb) * max((suara or 6.0) - 0.6, 1.0) * 0.85, 2) for i in range(nb)] if nb else []
            if st:
                pg.evaluate(f"window.__starts = {st}")
            pg.wait_for_timeout(500)
            for i in range(n):
                pg.evaluate(f"setT({i / FPS:.4f})")
                pg.screenshot(path=os.path.join(tmp, f"{i:04d}.png"))
            b.close()
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", os.path.join(tmp, "%04d.png"),
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", out], check=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return st


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("html"); ap.add_argument("-d", type=float, default=6.5); ap.add_argument("-o", required=True)
    a = ap.parse_args()
    render(a.html, a.d, a.o)
