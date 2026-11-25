#!/usr/bin/env python3
"""Siapkan audio_manual/yajuj2: pakai ulang audio Ozhy yajuj1 (potong di kata 'berkata:'), buat 2 baris pemimpin (satu permintaan ElevenLabs), beri efek suara berat."""
import json, os, shutil, subprocess, sys
sys.path.insert(0, os.path.dirname(__file__))
import dlib
from yajuj2_naskah import B
R = dlib.REPO; O, N = f"{R}/audio_manual/yajuj1", f"{R}/audio_manual/yajuj2"; os.makedirs(N, exist_ok=True)
PETA = {0: 0, 1: 1, 2: 2, 5: 4, 6: 5, 9: 7, 10: 8, 11: 9, 12: 10}  # baru -> lama (utuh)
for b, l in PETA.items():
    if not os.path.exists(f"{N}/b{b:02d}.mp3"):
        shutil.copy(f"{O}/b{l:02d}.mp3", f"{N}/b{b:02d}.mp3"); d = json.load(open(f"{O}/b{l:02d}.json")); d["teks"] = B[b][1]; json.dump(d, open(f"{N}/b{b:02d}.json", "w"), ensure_ascii=False)
def potong(b, l, kata_akhir, teks):  # potong b{l} lama sampai kata 'berkata:' pertama / ke-2
    if os.path.exists(f"{N}/b{b:02d}.mp3"): return
    d = json.load(open(f"{O}/b{l:02d}.json")); k = [x for x in d["kata"] if x[2] == kata_akhir][0]; a1 = k[1] + 0.3
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{O}/b{l:02d}.mp3", "-af", f"atrim=0:{a1:.3f},afade=t=out:st={a1 - 0.12:.3f}:d=0.12", f"{N}/b{b:02d}.mp3"], check=True)
    json.dump({"teks": teks, "kata": [x for x in d["kata"] if x[1] <= k[1] + 0.01], "lama": round(a1, 3)}, open(f"{N}/b{b:02d}.json", "w"), ensure_ascii=False)
potong(3, 3, "berkata:", B[3][1]); potong(7, 6, "berkata:", B[7][1])
dlib.suara("yajuj2", B)  # hanya baris yang belum ada (PM x2)
for i, (p, _) in enumerate(B):  # suara pemimpin: berat, dingin, gema pendek
    if p != "PM": continue
    j = json.load(open(f"{N}/b{i:02d}.json"))
    if j.get("berat"): continue
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{N}/b{i:02d}.mp3", "-af",
                    "asetrate=44100*0.84,aresample=44100,atempo=1.19,equalizer=f=140:t=q:w=1.0:g=4,aecho=0.8:0.55:70:0.28,loudnorm=I=-15:TP=-1.5:LRA=9,aresample=44100", "-ac", "1", f"{N}/tmp.mp3"], check=True)
    # asetrate*0.84 lalu atempo 1.19 = nada turun ±16% dengan tempo hampir sama; panjang berubah sedikit -> hitung ulang waktu kata
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f"{N}/tmp.mp3"], capture_output=True, text=True).stdout)
    f = dur / (j["lama"] * 1.0)
    os.replace(f"{N}/tmp.mp3", f"{N}/b{i:02d}.mp3"); j["kata"] = [[round(k[0] * f, 3), round(k[1] * f, 3), k[2]] for k in j["kata"]]; j["lama"] = round(dur, 3); j["berat"] = True
    json.dump(j, open(f"{N}/b{i:02d}.json", "w"), ensure_ascii=False)
print("siap", [round(json.load(open(f'{N}/b{i:02d}.json'))['lama'], 2) for i in range(len(B))])
