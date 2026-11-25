#!/usr/bin/env python3
"""Animasi mulut karakter dari audio: gambar mulut tertutup / bulat / terbuka diganti mengikuti volume suara.
Pemakaian: python puppet.py karakter/anwar_kartun audio.mp3 -d 6.5 -o out.mp4 [--tunda 0.15]"""
import argparse, os, shutil, subprocess, tempfile
import numpy as np
from PIL import Image

FPS, W, H = 30, 1080, 1920


def amplop(audio, n, tunda):
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", audio, "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
                         capture_output=True, check=True).stdout
    x = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768
    win = int(16000 / FPS)
    nf = len(x) // win
    r = np.sqrt(np.mean(x[:nf * win].reshape(nf, win) ** 2, axis=1)) if nf else np.zeros(1)
    ref = np.percentile(r, 90) or 1.0
    r = r / ref
    out = np.zeros(n)
    s = int(round(tunda * FPS))
    for i in range(n):
        j = i - s
        if 0 <= j < len(r):
            out[i] = r[j]
    return out


def kelas(a):
    k = np.where(a < 0.22, 0, np.where(a < 0.62, 1, 2))
    # tahan minimal 2 bingkai supaya mulut tidak berkedip cepat
    h = k.copy()
    for i in range(1, len(h) - 1):
        if h[i] != h[i - 1] and h[i] != h[i + 1]:
            h[i] = h[i - 1]
    return h


def render(folder, audio, durasi, out, tunda=0.15):
    n = int(round(durasi * FPS))
    nama = ["mulut_tutup", "mulut_oh", "mulut_aah"]
    tmp = tempfile.mkdtemp()
    try:
        paths = []
        for nm in nama:
            f = next(os.path.join(folder, nm + e) for e in (".png", ".jpg", ".jpeg") if os.path.exists(os.path.join(folder, nm + e)))
            im = Image.open(f).convert("RGB")
            s = max(1188 / im.width, 2112 / im.height)  # sedikit lebih besar, ruang untuk goyangan kamera
            im = im.resize((round(im.width * s), round(im.height * s)))
            l, t = (im.width - 1188) // 2, (im.height - 2112) // 2
            p = os.path.join(tmp, nm + ".png")
            im.crop((l, t, l + 1188, t + 2112)).save(p)
            paths.append(p)
        k = kelas(amplop(audio, n, tunda))
        lst = os.path.join(tmp, "daftar.txt")
        with open(lst, "w") as fh:
            for i in range(n):
                fh.write(f"file '{paths[k[i]]}'\nduration {1 / FPS:.6f}\n")
            fh.write(f"file '{paths[k[-1]]}'\n")
        # kamera maju pelan + goyang halus
        vf = (f"fps={FPS},crop={W}:{H}:x='(iw-{W})/2+12*sin(t*1.1)':y='(ih-{H})/2+10*sin(t*0.8)-t*3',format=yuv420p")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-vf", vf,
                        "-c:v", "libx264", "-crf", "16", out], check=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("folder"); ap.add_argument("audio")
    ap.add_argument("-d", type=float, default=6.5); ap.add_argument("-o", required=True)
    ap.add_argument("--tunda", type=float, default=0.15)
    a = ap.parse_args()
    render(a.folder, a.audio, a.d, a.o, a.tunda)
