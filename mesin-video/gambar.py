#!/usr/bin/env python3
"""Buat gambar adegan dari naskah JSON lewat Gemini API.
Pakai:  GOOGLE_API_KEY=... python3 gambar.py naskah/halusinasi.json [-o gambar_keluar]
Key hanya dari variabel lingkungan (GitHub Secret), tidak pernah ditulis ke berkas."""
import argparse, base64, json, os, sys, time, urllib.request, urllib.error

BASE = "https://generativelanguage.googleapis.com/v1beta"
MODEL_BARU = os.environ.get("MODEL_GAMBAR", "gemini-nano-banana-2.1")
MODEL_LAMA = "gemini-2.5-flash-image"
REF = os.path.join(os.path.dirname(os.path.abspath(__file__)), "referensi", "maskot.png")

LAP = []

class KuotaHabis(Exception):
    pass

def _cek_kuota(e, isi):
    """Cloudflare: HTTP 429 kode 4006 = jatah gratis 10.000 neuron/hari habis. Mengulang percuma."""
    if e.code == 429 and "4006" in isi:
        raise KuotaHabis("jatah gratis harian Cloudflare Workers AI habis (reset 00.00 UTC = 07.00 WIB)")
def catat(*a):
    t = " ".join(str(x) for x in a); print(t, file=sys.stderr); LAP.append(t)

def post(url, body, key):
    r = urllib.request.Request(url, json.dumps(body).encode(), {"Content-Type": "application/json", "x-goog-api-key": key})
    with urllib.request.urlopen(r, timeout=180) as f:
        return json.load(f)

def cari_gambar(o):
    """Cari data base64 gambar di respons (dua format API)."""
    if isinstance(o, dict):
        for k in ("data", "inlineData", "inline_data"):
            v = o.get(k)
            if isinstance(v, str) and len(v) > 2000: return v
            if isinstance(v, dict) and isinstance(v.get("data"), str): return v["data"]
        for v in o.values():
            r = cari_gambar(v)
            if r: return r
    elif isinstance(o, list):
        for v in o:
            r = cari_gambar(v)
            if r: return r
    return None

MASKOT_TEKS = ("cute chibi robot mascot: rounded-square light-blue head with thick navy outline, small orange antenna ball on top, "
               "orange headphone-like ear pieces on both sides, two big round dark eyes with white highlights, small open smile with pink tongue, "
               "small light-blue body with short stubby arms and legs")

def buat_cloudflare(prompt, env):
    """Cloudflare Workers AI (flux-1-schnell): gratis 10.000 neuron/hari, tanpa gambar referensi.
    Coba ukuran potret 768x1344; bila ditolak, ulangi tanpa ukuran lalu dipas ke 9:16 di pasKanvas."""
    acc, tok = env["CLOUDFLARE_ACCOUNT_ID"], env["CLOUDFLARE_API_TOKEN"]
    url = f"https://api.cloudflare.com/client/v4/accounts/{acc}/ai/run/@cf/black-forest-labs/flux-1-schnell"
    p = prompt.replace("exactly like the reference image", MASKOT_TEKS)
    for ekstra in ({},):  # flux-1-schnell menolak width/height (HTTP 400), jadi tanpa ukuran
        body = {"prompt": p[:2000], "steps": 6, **ekstra}
        r = urllib.request.Request(url, json.dumps(body).encode(), {"Content-Type": "application/json", "Authorization": "Bearer " + tok})
        try:
            with urllib.request.urlopen(r, timeout=180) as f:
                j = json.load(f)
            d = (j.get("result") or {}).get("image")
            if d: return d, "cloudflare-flux-schnell" + (" 768x1344" if ekstra else "")
            catat("  cloudflare tanpa gambar:", json.dumps(j)[:300])
        except urllib.error.HTTPError as e:
            isi = e.read().decode()
            catat(f"  cloudflare gagal HTTP {e.code} ({'ukuran' if ekstra else 'tanpa ukuran'}): {isi[:400]}")
            _cek_kuota(e, isi)
    raise RuntimeError("cloudflare gagal")

KARAKTER = os.environ.get("REF_GAMBAR") or next(
    (p for p in (os.path.join(os.path.dirname(os.path.abspath(__file__)), "referensi", n) for n in ("karakter.png", "maskot.png")) if os.path.exists(p)), REF)

def _multipart(fields, files):
    import uuid
    b = uuid.uuid4().hex
    out = b""
    for k, v in fields.items():
        out += f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode()
    for k, (nama, data, tipe) in files.items():
        out += f'--{b}\r\nContent-Disposition: form-data; name="{k}"; filename="{nama}"\r\nContent-Type: {tipe}\r\n\r\n'.encode() + data + b"\r\n"
    return out + f"--{b}--\r\n".encode(), f"multipart/form-data; boundary={b}"

def _ref_kecil(path, maks=504):
    """Model FLUX.2 di Workers AI menolak gambar referensi >= 512x512, jadi diperkecil."""
    import io
    from PIL import Image
    im = Image.open(path).convert("RGB"); im.thumbnail((maks, maks))
    buf = io.BytesIO(); im.save(buf, "PNG"); return buf.getvalue()

def buat_cloudflare2(prompt, env):
    """Cloudflare Workers AI FLUX.2 dengan gambar referensi karakter (konsistensi lebih baik dari flux-1-schnell).
    Model dapat diganti lewat MODEL_CF2 (flux-2-klein-9b, flux-2-klein-4b, atau flux-2-dev)."""
    acc, tok = env["CLOUDFLARE_ACCOUNT_ID"], env["CLOUDFLARE_API_TOKEN"]
    model = env.get("MODEL_CF2", "@cf/black-forest-labs/flux-2-klein-9b")
    url = f"https://api.cloudflare.com/client/v4/accounts/{acc}/ai/run/{model}"
    ref = _ref_kecil(KARAKTER)
    p = ("Image 0 is the character reference: keep exactly the same person, face, hairstyle, clothing and art style as image 0. "
         + prompt)[:3500]
    for ekstra in ({"width": "768", "height": "1344"}, {}):
        body, tipe = _multipart({"prompt": p, **ekstra}, {"input_image_0": ("ref.png", ref, "image/png")})
        r = urllib.request.Request(url, body, {"Content-Type": tipe, "Authorization": "Bearer " + tok})
        try:
            with urllib.request.urlopen(r, timeout=300) as f:
                raw, ct = f.read(), f.headers.get("Content-Type", "")
            if ct.startswith("image/"):
                return base64.b64encode(raw).decode(), "cloudflare-" + model.split("/")[-1]
            j = json.loads(raw)
            d = (j.get("result") or {}).get("image")
            if d: return d, "cloudflare-" + model.split("/")[-1] + (" 768x1344" if ekstra else "")
            catat("  cloudflare2 tanpa gambar:", json.dumps(j)[:300])
        except urllib.error.HTTPError as e:
            isi = e.read().decode()
            catat(f"  cloudflare2 gagal HTTP {e.code} ({'ukuran' if ekstra else 'tanpa ukuran'}): {isi[:400]}")
            _cek_kuota(e, isi)
    raise RuntimeError("cloudflare2 gagal")

def buat_cf(prompt, prov, percobaan):
    """cloudflare2 dicoba dulu; pada percobaan terakhir jatuh ke flux-1-schnell agar video tetap jadi."""
    if prov == "cloudflare2" and percobaan < 2:
        return buat_cloudflare2(prompt, os.environ)
    if prov == "cloudflare2":
        catat("  jatuh ke flux-1-schnell (tanpa referensi)")
    return buat_cloudflare(prompt, os.environ)

def pas_kanvas(png_bytes, W=1080, H=1920):
    """Pas gambar ke kanvas 9:16: skala selebar W, sisa dipad dengan warna sudut gambar."""
    import io
    from PIL import Image
    im = Image.open(io.BytesIO(png_bytes)).convert("RGB")
    s = W / im.width; im = im.resize((W, round(im.height * s)))
    if im.height >= H:
        t = (im.height - H) // 2; return im.crop((0, t, W, t + H))
    bg = im.getpixel((4, 4)); k = Image.new("RGB", (W, H), bg); k.paste(im, (0, (H - im.height) // 3))
    return k

def buat(prompt, ref_b64, key):
    # 1) Interactions API (model baru)
    try:
        j = post(f"{BASE}/interactions", {
            "model": MODEL_BARU,
            "input": [{"type": "text", "text": prompt}, {"type": "image", "mime_type": "image/png", "data": ref_b64}],
            "response_format": {"type": "image", "aspect_ratio": "9:16"}}, key)
        d = cari_gambar(j)
        if d: return d, MODEL_BARU
        catat("  respons tanpa gambar (model baru):", json.dumps(j)[:400])
    except urllib.error.HTTPError as e:
        catat(f"  model baru gagal HTTP {e.code}: {e.read().decode()[:500]}")
    # 2) generateContent (model lama)
    j = post(f"{BASE}/models/{MODEL_LAMA}:generateContent", {
        "contents": [{"parts": [{"text": prompt}, {"inline_data": {"mime_type": "image/png", "data": ref_b64}}]}],
        "generationConfig": {"responseModalities": ["IMAGE"], "imageConfig": {"aspectRatio": "9:16"}}}, key)
    d = cari_gambar(j)
    if not d: raise RuntimeError("tidak ada gambar di respons: " + json.dumps(j)[:300])
    return d, MODEL_LAMA

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("naskah"); ap.add_argument("-o", "--keluar", default="gambar_keluar")
    ap.add_argument("--hanya", help="nama adegan tertentu (pisah koma)")
    a = ap.parse_args()
    key = os.environ.get("GOOGLE_API_KEY")
    prov = os.environ.get("PROVIDER") or ("cloudflare" if os.environ.get("CLOUDFLARE_API_TOKEN") else "google")
    if prov == "google" and not key: sys.exit("GOOGLE_API_KEY belum diset (isi lewat GitHub Secrets)")
    if prov.startswith("cloudflare") and not (os.environ.get("CLOUDFLARE_API_TOKEN") and os.environ.get("CLOUDFLARE_ACCOUNT_ID")):
        sys.exit("CLOUDFLARE_API_TOKEN / CLOUDFLARE_ACCOUNT_ID belum diset")
    n = json.load(open(a.naskah)); os.makedirs(a.keluar, exist_ok=True)
    ref = base64.b64encode(open(REF, "rb").read()).decode()
    pilih = set(a.hanya.split(",")) if a.hanya else None
    gagal = 0
    for ad in n["adegan"]:
        if pilih and ad["nama"] not in pilih: continue
        out = os.path.join(a.keluar, ad["nama"] + ".png")
        prompt = n["gaya"] + " Scene: " + ad["prompt"]
        for pct in range(3):
            try:
                d, m = buat_cf(prompt, prov, pct) if prov.startswith("cloudflare") else buat(prompt, ref, key)
                raw = base64.b64decode(d)
                if prov.startswith("cloudflare"): pas_kanvas(raw).save(out)
                else: open(out, "wb").write(raw)
                print(f"ok {ad['nama']} ({m})"); break
            except KuotaHabis as e:
                catat("BERHENTI:", e)
                open(os.path.join(a.keluar, "laporan.txt"), "w").write("\n".join(LAP))
                sys.exit(3)
            except Exception as e:
                catat(f"  percobaan {pct+1} gagal: {type(e).__name__}: {e}" + (" | " + e.read().decode()[:500] if hasattr(e, "read") else "")); time.sleep(4)
        else:
            gagal += 1; print(f"GAGAL {ad['nama']}")
    open(os.path.join(a.keluar, "laporan.txt"), "w").write("\n".join(LAP) or "tanpa catatan")
    sys.exit(1 if gagal else 0)
main()
