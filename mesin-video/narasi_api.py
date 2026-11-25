#!/usr/bin/env python3
"""Narasi otomatis lewat ElevenLabs (dijalankan di GitHub Actions; kunci di env ELEVENLABS_API_KEY).
Pakai: python narasi_api.py teks.txt -o audio_manual/<slug>/narasi.mp3 --suara <voice_id> [--model eleven_v4]
Menyimpan juga <keluaran>.waktu.json: waktu tiap kata (dari penjajaran huruf ElevenLabs) dan frasa siap pakai
untuk "subtitle" Papan."""
import argparse, base64, json, os, re, sys, urllib.request, urllib.error
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from papan.penjaga_arab import TeksArabDilarangError, periksa_teks_narasi  # noqa: E402


def frasa_dari_kata(kata, maks=6):
    """Potong jadi frasa subtitle: berhenti di tanda baca atau setelah `maks` kata."""
    out, cur = [], []
    for k in kata:
        cur.append(k)
        if re.search(r"[.,!?;:]$", k["teks"]) or len(cur) >= maks:
            out.append([round(cur[0]["t0"], 2), round(cur[-1]["t1"], 2), " ".join(x["teks"] for x in cur)]); cur = []
    if cur:
        out.append([round(cur[0]["t0"], 2), round(cur[-1]["t1"], 2), " ".join(x["teks"] for x in cur)])
    return out


def kata_dari_huruf(al):
    ch, a, b = al["characters"], al["character_start_times_seconds"], al["character_end_times_seconds"]
    kata, buf, t0, t1, dalam_tag = [], "", None, None, False
    for c, s, e in zip(ch, a, b):
        if c == "<": dalam_tag = True
        if dalam_tag:
            if c == ">": dalam_tag = False
            continue
        if c.isspace():
            if buf: kata.append({"teks": buf, "t0": t0, "t1": t1}); buf = ""
            continue
        if not buf: t0 = s
        buf += c; t1 = e
    if buf: kata.append({"teks": buf, "t0": t0, "t1": t1})
    return kata


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("teks"); ap.add_argument("-o", required=True)
    ap.add_argument("--suara", required=True); ap.add_argument("--model", default="eleven_v4")
    ap.add_argument("--stabil", type=float, default=0.5); ap.add_argument("--mirip", type=float, default=0.75)
    ap.add_argument("--kecepatan", type=float, default=1.0)
    a = ap.parse_args()
    kunci = os.environ.get("ELEVENLABS_API_KEY")
    if not kunci:
        print("::error::ELEVENLABS_API_KEY kosong"); sys.exit(1)
    teks = open(a.teks, encoding="utf-8").read().strip()
    # lafal: ganti kata berlogat Inggris dengan ejaan bunyi Indonesia; subtitle tetap memakai tulisan asli
    lafal = {}
    f_lafal = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lafal.json")
    if os.path.exists(f_lafal):
        lafal = {k: v for k, v in json.load(open(f_lafal, encoding="utf-8")).items() if not k.startswith("_")}
    balik = {}
    for asli, bunyi in lafal.items():
        teks, n = re.subn(r"(?<![\w-])" + re.escape(asli) + r"(?![\w-])", bunyi, teks)
        if n:
            balik[bunyi] = asli
    try:
        periksa_teks_narasi(teks, f"berkas {a.teks}")
    except TeksArabDilarangError as e:
        print(f"::error::{e}")
        sys.exit(str(e))
    badan = {"text": teks, "model_id": a.model,
             "voice_settings": {"stability": a.stabil, "similarity_boost": a.mirip, "speed": a.kecepatan}}
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{a.suara}/with-timestamps?output_format=mp3_44100_128"
    req = urllib.request.Request(url, data=json.dumps(badan).encode(), method="POST",
                                 headers={"xi-api-key": kunci, "Content-Type": "application/json"})
    try:
        r = json.load(urllib.request.urlopen(req, timeout=300))
    except urllib.error.HTTPError as e:
        pesan = f"ElevenLabs galat {e.code}: {e.read().decode(errors='replace')[:500]}"
        print("::error::" + pesan.replace("\n", " "))  # muncul sebagai anotasi (terbaca lewat API check-runs)
        sys.exit(pesan)
    os.makedirs(os.path.dirname(a.o) or ".", exist_ok=True)
    open(a.o, "wb").write(base64.b64decode(r["audio_base64"]))
    al = r.get("normalized_alignment") or r.get("alignment")
    kata = kata_dari_huruf(al) if al else []
    import unicodedata
    polos = lambda x: "".join(c for c in unicodedata.normalize("NFKD", x) if not unicodedata.combining(c)).lower()
    for k in kata:  # kembalikan tulisan asli (kata utuh; penjajaran ElevenLabs bisa membuang aksen)
        m = re.match(r"^(\W*)(.*?)(\W*)$", k["teks"])
        for bunyi, asli in balik.items():
            if polos(m.group(2)) == polos(bunyi):
                k["teks"] = m.group(1) + asli + m.group(3)
                break
    json.dump({"model": a.model, "suara": a.suara, "huruf": len(teks), "kata": kata, "subtitle": frasa_dari_kata(kata)},
              open(os.path.splitext(a.o)[0] + ".waktu.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("selesai", a.o, len(teks), "huruf,", len(kata), "kata")


if __name__ == "__main__":
    main()
