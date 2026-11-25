#!/usr/bin/env python3
"""Perakit video edukasi 9:16 - FIX hook frame 0 27 Okt 2026
Cuma ubah 2 baris: subtitle adegan 1 mulai di 0, bukan 0.15
"""
import argparse, json, math, os, re, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
FADE = 0.35
JEDA_AKHIR = 0.5
KATA_PER_DETIK = 2.4
MIN_ADEGAN = 3.5
HUJUNG_Y = 1520
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
CREAM, NAVY, ORG = (251, 250, 246), (20, 40, 75), (242, 138, 30)
KEY_KLIP = "0xF8F2D6"
LATAR_BAWAAN = "FBFAF6"
SAMBUNG = {"yang", "di", "ke", "dari", "dan", "atau", "untuk", "pada", "bila", "jika", "kalau",
           "tapi", "dengan", "ia", "itu", "ini", "bukan", "agar", "karena", "saat", "ada", "si", "para", "the", "a", "to", "of", "and"}
PUSTAKA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pustaka")

def gagal(pesan):
    print("GALAT:", pesan, file=sys.stderr)
    sys.exit(1)

def jalan(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        gagal("ffmpeg gagal:\n" + r.stderr[-1500:])
    return r

def durasi_berkas(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", path], capture_output=True, text=True)
    try:
        dur = float(r.stdout.strip())
    except (TypeError, ValueError):
        gagal(f"tidak bisa membaca durasi audio/video: {path}")
    if r.returncode != 0 or not math.isfinite(dur) or dur <= 0:
        detail = (r.stderr or "").strip()
        gagal(f"durasi berkas tidak valid: {path}" + (f" ({detail[-500:]})" if detail else ""))
    return dur

def bersih(k):
    return re.sub(r"[^\w]", "", k.lower())

def pecah_frasa(teks, kunci):
    kset = {bersih(w) for k in kunci for w in k.split()}
    frasa, cur = [], []
    for tok in teks.split():
        cur.append((tok, bersih(tok) in kset))
        batas = len(cur) >= 5 and (bersih(tok) not in SAMBUNG or len(cur) >= 7)
        if tok[-1] in ",.?!:;" or batas:
            frasa.append(cur)
            cur = []
    if cur:
        if frasa and len(cur) == 1:
            frasa[-1] += cur
        else:
            frasa.append(cur)
    return frasa

def gambar_frasa(frasa, path, ukuran=76):
    font = ImageFont.truetype(FONT, ukuran)
    tmp = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    spasi = tmp.textlength(" ", font=font)
    maks = 940
    baris, cur, lebar = [], [], 0
    for tok, kd in frasa:
        w = tmp.textlength(tok, font=font)
        if cur and lebar + spasi + w > maks:
            baris.append((cur, lebar)); cur, lebar = [], 0
        lebar += (spasi if cur else 0) + w
        cur.append((tok, kd, w))
    baris.append((cur, lebar))
    lh = int(ukuran * 1.35)
    im = Image.new("RGBA", (1000, lh * len(baris) + 30), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for i, (b, lebar) in enumerate(baris):
        x = (1000 - lebar) / 2
        for tok, kd, w in b:
            d.text((x, 15 + i * lh), tok, font=font, fill=ORG if kd else CREAM,
                   stroke_width=9, stroke_fill=NAVY)
            x += w + spasi
    im.save(path)
    return im.size

def segmen_suara(path):
    d = durasi_berkas(path)
    deteksi = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-af", "silencedetect=noise=-35dB:d=0.2",
                              "-f", "null", "-"], capture_output=True, text=True)
    if deteksi.returncode != 0:
        gagal(f"gagal menganalisis audio untuk sinkronisasi subtitle: {path}\n{deteksi.stderr[-1000:]}")
    out = deteksi.stderr
    hening, mulai = [], None
    for m in re.finditer(r"silence_(start|end): ([0-9.]+)", out):
        if m.group(1) == "start":
            mulai = float(m.group(2))
        elif mulai is not None:
            hening.append((mulai, float(m.group(2)))); mulai = None
    if mulai is not None:
        hening.append((mulai, d))
    seg, t = [], 0.0
    for s, e in hening:
        if s > t + 0.05:
            seg.append((t, s))
        t = max(t, e)
    if d > t + 0.05:
        seg.append((t, d))
    return seg or [(0.0, d)]

def waktu_suara(seg, frac):
    total = sum(e - s for s, e in seg)
    target = max(0.0, min(1.0, frac)) * total
    for s, e in seg:
        if target <= e - s:
            return s + target
        target -= e - s
    return seg[-1][1]

def rencana(a, folder):
    kata = len(a.get("teks", "").split())
    a["_audio"] = None
    if a.get("audio"):
        p = os.path.join(folder, a["audio"])
        if not os.path.exists(p):
            gagal(f"audio tidak ada: {p}")
        a["_audio"] = p
        isi = durasi_berkas(p) + JEDA_AKHIR
    elif a.get("durasi"):
        isi = float(a["durasi"])
    else:
        isi = max(MIN_ADEGAN, kata / KATA_PER_DETIK + 0.8)
    if a.get("klip"):
        p = os.path.join(PUSTAKA, a["klip"] + ".mp4")
        if not os.path.exists(p):
            gagal(f"klip maskot tidak ada: {p}")
        a["_klip"] = p
    elif a.get("video"):
        p = os.path.join(folder, a["video"])
        if not os.path.exists(p):
            gagal(f"video tidak ada: {p}")
        a["_video"] = p
    elif a.get("gambar"):
        p = os.path.join(folder, a["gambar"])
        if not os.path.exists(p):
            gagal(f"gambar tidak ada: {p}")
        a["_gambar"] = p
    else:
        gagal("tiap adegan butuh 'gambar', 'video' atau 'klip'")
    a["_isi"] = isi
    a["_folder"] = folder
    a["_dur"] = isi + FADE
    return a

def render_adegan(a, i, tmp, spec_latar=LATAR_BAWAAN):
    dur = a["_dur"]
    n = int(dur * FPS)
    inputs, filt = [], []
    if a.get("_klip"):
        inputs += ["-i", a["_klip"]]
        latar = str(a.get("latar", spec_latar)).lstrip("#")
        filt.append(f"[0:v]scale={W}:{H}:flags=lanczos,fps={FPS},colorkey={KEY_KLIP}:0.10:0.05,"
                    f"tpad=stop_mode=clone:stop_duration={dur:.2f},trim=duration={dur:.2f},setpts=PTS-STARTPTS[kp]")
        filt.append(f"color=c=0x{latar}:s={W}x{H}:r={FPS},trim=duration={dur:.2f}[bg]")
        filt.append("[bg][kp]overlay=shortest=1[v0]")
        idx = 1
    elif a.get("_video"):
        inputs += ["-i", a["_video"]]
        filt.append(f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},"
                    f"tpad=stop_mode=clone:stop_duration={dur:.2f},trim=duration={dur:.2f},setpts=PTS-STARTPTS[v0]")
        idx = 1
    else:
        inputs += ["-loop", "1", "-framerate", str(FPS), "-i", a["_gambar"]]
        arah = "1+0.10*on/%d" % n if i % 2 == 0 else "1.10-0.10*on/%d" % n
        filt.append(f"[0:v]scale=1620:2880:force_original_aspect_ratio=increase,crop=1620:2880,"
                    f"zoompan=z='{arah}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={n}:s={W}x{H}:fps={FPS}[v0]")
        idx = 1
    cur = "v0"
    m = a.get("maskot")
    if m:
        kp = os.path.join(PUSTAKA, m["klip"] + ".mp4")
        if not os.path.exists(kp):
            gagal(f"klip maskot tidak ada: {kp}")
        inputs += ["-i", kp]
        lb = int(m.get("lebar", 420))
        filt.append(f"[{idx}:v]scale={lb}:-1,fps={FPS},colorkey={KEY_KLIP}:0.12:0.06,"
                    f"tpad=stop_mode=clone:stop_duration={dur:.2f},trim=duration={dur:.2f},setpts=PTS-STARTPTS[mk]")
        filt.append(f"[{cur}][mk]overlay=x={int(m.get('x', 600))}:y={int(m.get('y', 900))}:shortest=0[v1]")
        cur = "v1"
        idx += 1
    if a.get("overlay"):
        po = os.path.join(a["_folder"], a["overlay"])
        inputs += ["-i", po]
        filt.append(f"[{cur}][{idx}:v]overlay=0:0[vo]")
        cur = "vo"; idx += 1
    frasa = pecah_frasa(a.get("teks", ""), a.get("kunci", []))
    total_kata = sum(len(f) for f in frasa) or 1
    seg = segmen_suara(a["_audio"]) if a.get("_audio") else None
    cum, mulai_f = 0, []
    for f in frasa:
        mulai_f.append(cum / total_kata)
        cum += len(f)
    if seg:
        ts = [waktu_suara(seg, fr) for fr in mulai_f]
        ts[0] = 0 if i==0 else 0.15
    else:
        mulai = 0 if i==0 else 0.25
        sisa = max(a["_isi"] - mulai - 0.25, 1.0)
        ts = [mulai + sisa * fr for fr in mulai_f]
    akhir = a["_isi"] - 0.1
    for j, f in enumerate(frasa):
        t = ts[j]
        t2 = ts[j + 1] if j + 1 < len(frasa) else akhir
        png = os.path.join(tmp, f"s{i}_{j}.png")
        w, h = gambar_frasa(f, png)
        inputs += ["-i", png]
        nxt = f"vs{j}"
        filt.append(f"[{cur}][{idx}:v]overlay=x={(W - w) // 2}:y={HUJUNG_Y - h // 2}:"
                    f"enable='gte(t,{t:.3f})*lt(t,{t2:.3f})'[{nxt}]")
        cur = nxt
        idx += 1
    filt.append(f"[{cur}]format=yuv420p[out]")
    skrip = os.path.join(tmp, f"f{i}.txt")
    open(skrip, "w").write(";\n".join(filt))
    out = os.path.join(tmp, f"adegan{i}.mp4")
    jalan(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex_script", skrip,
           "-map", "[out]", "-t", f"{dur:.2f}", "-r", str(FPS), "-c:v", "libx264",
           "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p", out])
    return out

SFX = {
    "pop": "aevalsrc='0.8*sin(2*PI*(450+3500*t)*t)*exp(-t*28)':d=0.18:s=44100",
    "ding": "aevalsrc='0.55*(sin(2*PI*1320*t)*exp(-t*9)+0.5*sin(2*PI*1980*t)*exp(-t*13))':d=0.6:s=44100",
    "whoosh": "anoisesrc=d=0.45:c=pink:r=44100:a=0.5,highpass=f=400,lowpass=f=5000,afade=t=in:d=0.18,afade=t=out:st=0.2:d=0.25",
}
SFX_VOL = {"pop": 0.30, "ding": 0.22, "whoosh": 0.18}

def buat_sfx(jenis, tmp):
    p = os.path.join(tmp, f"sfx_{jenis}.wav")
    if not os.path.exists(p):
        jalan(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", SFX[jenis], "-ac", "2", p])
    return p

def gabung(adegan, klipfiles, spec, folder, keluar, tmp):
    n = len(klipfiles)
    inputs = []
    for k in klipfiles:
        inputs += ["-i", k]
    starts, s = [], 0.0
    for i, a in enumerate(adegan):
        starts.append(s)
        s += a["_dur"] - FADE
    total = s + FADE
    filt = []
    if n == 1:
        filt.append("[0:v]null[vf]")
    else:
        cur, acc = "[0:v]", adegan[0]["_dur"]
        for k in range(1, n):
            off = acc - FADE
            filt.append(f"{cur}[{k}:v]xfade=transition=fade:duration={FADE}:offset={off:.2f}[x{k}]")
            cur = f"[x{k}]"
            acc = off + adegan[k]["_dur"]
        filt.append(f"{cur}null[vf]")
    audio_in, amix = [], []
    base = n
    for i, a in enumerate(adegan):
        if a["_audio"]:
            audio_in += ["-i", a["_audio"]]
            ms = int((starts[i] + 0.15) * 1000)
            amix.append((base, ms, 1.0))
            base += 1
    for i, a in enumerate(adegan):
        for t, jenis in a.get("sfx", []):
            if jenis in SFX:
                audio_in += ["-i", buat_sfx(jenis, tmp)]
                amix.append((base, int((starts[i] + t) * 1000), SFX_VOL[jenis]))
                base += 1
    musik = os.path.join(folder, spec["musik"]) if spec.get("musik") else None
    if musik and not os.path.exists(musik):
        gagal(f"musik tidak ada: {musik}")
    labels = []
    for k, (idx, ms, vol) in enumerate(amix):
        filt.append(f"[{idx}:a]aresample=44100,aformat=channel_layouts=stereo,volume={vol},adelay={ms}|{ms}[n{k}]")
        labels.append(f"[n{k}]")
    if musik:
        audio_in += ["-stream_loop", "-1", "-i", musik]
        midx = base
        filt.append(f"[{midx}:a]aresample=44100,aformat=channel_layouts=stereo,volume=0.10,"
                    f"afade=t=in:d=1.5,atrim=duration={total:.2f},afade=t=out:st={total - 2.0:.2f}:d=2[mus]")
        labels.append("[mus]")
    maps = ["-map", "[vf]"]
    if labels:
        filt.append("".join(labels) + f"amix=inputs={len(labels)}:normalize=0:duration=longest,"
                    f"atrim=duration={total:.2f}[af]")
        maps += ["-map", "[af]", "-c:a", "aac", "-b:a", "160k"]
    skrip = os.path.join(tmp, "gabung.txt")
    open(skrip, "w").write(";\n".join(filt))
    jalan(["ffmpeg", "-y", "-loglevel", "error", *inputs, *audio_in, "-filter_complex_script", skrip,
           *maps, "-t", f"{total:.2f}", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
           "-pix_fmt", "yuv420p", "-movflags", "+faststart", keluar])
    return total

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("-o", "--keluar")
    arg = ap.parse_args()
    folder = os.path.dirname(os.path.abspath(arg.spec))
    spec = json.load(open(arg.spec, encoding="utf-8"))
    if not spec.get("adegan"):
        gagal("spec tanpa 'adegan'")
    adegan = [rencana(a, folder) for a in spec["adegan"]]
    keluar = arg.keluar or os.path.join(folder, re.sub(r"\W+", "_", spec.get("judul", "video")).strip("_").lower() + ".mp4")
    with tempfile.TemporaryDirectory() as tmp:
        files = []
        for i, a in enumerate(adegan):
            print(f"adegan {i + 1}/{len(adegan)} ({a['_dur']:.1f} dtk)", flush=True)
            files.append(render_adegan(a, i, tmp, str(spec.get('latar', LATAR_BAWAAN))))
        total = gabung(adegan, files, spec, folder, keluar, tmp)
    print(f"selesai: {keluar} ({total:.1f} dtk)")

if __name__ == "__main__":
    main()
