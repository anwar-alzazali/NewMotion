#!/usr/bin/env python3
"""Satu tombol: naskah JSON -> gambar -> suara -> rakit -> video (+ status di Supabase).

Pakai:
  python3 otomatis.py naskah/contoh_satu_tombol.json [-o hasil] [--tanpa-suara] [--ulang semua|nama1,nama2]

Format naskah (kompatibel dengan gambar.py):
{
  "judul": "Kenapa ChatGPT ngarang",
  "caption": "teks caption TikTok (opsional)",
  "gaya": "gaya gambar umum, dipakai di semua adegan",
  "musik": "path/musik.mp3",            # opsional
  "adegan": [
    {"nama": "s1_hook", "teks": "narasi adegan ini", "kunci": ["kata", "kunci"],
     "prompt": "deskripsi gambar adegan"}
  ]
}

Rahasia hanya dari variabel lingkungan (GitHub Secrets), tidak pernah ditulis ke berkas:
  CLOUDFLARE_API_TOKEN, CLOUDFLARE_ACCOUNT_ID      (gambar, lewat gambar.py)
  ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID          (suara; tanpa ini video dibuat tanpa narasi)
  SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY          (catatan status; tanpa ini dilewati)

Adegan yang gambar atau suaranya sudah ada di folder hasil dilewati, jadi menjalankan ulang
setelah gagal tidak memboroskan kuota. Pakai --ulang untuk memaksa dibuat ulang.
"""
import argparse, json, math, os, re, shutil, subprocess, sys, time, traceback
import urllib.error, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
LAP = []


def catat(*a):
    t = " ".join(str(x) for x in a)
    print(t, file=sys.stderr, flush=True)
    LAP.append(t)


def slug(s):
    return re.sub(r"\W+", "_", s.lower()).strip("_") or "video"


# ---------- Supabase (opsional; kegagalannya tidak boleh menggagalkan video) ----------
class Supabase:
    def __init__(self):
        self.url = os.environ.get("SUPABASE_URL", "").rstrip("/")
        self.key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
        self.aktif = bool(self.url and self.key)
        self.video_id = None

    def _req(self, metode, path, body=None, tipe="application/json", ekstra=None, mentah=False):
        data = body if mentah else (json.dumps(body).encode() if body is not None else None)
        h = {"apikey": self.key, "Authorization": "Bearer " + self.key, "Content-Type": tipe}
        h.update(ekstra or {})
        r = urllib.request.Request(self.url + path, data, h, method=metode)
        with urllib.request.urlopen(r, timeout=300) as f:
            isi = f.read()
        return json.loads(isi) if isi and not mentah else isi

    def aman(self, fn, *a, **k):
        if not self.aktif:
            return None
        try:
            return fn(*a, **k)
        except urllib.error.HTTPError as e:
            catat(f"  supabase HTTP {e.code}: {e.read().decode()[:300]}")
        except Exception as e:
            catat(f"  supabase gagal: {type(e).__name__}: {e}")
        return None

    def mulai(self, judul, naskah, caption, run_url):
        def f():
            r = self._req("POST", "/rest/v1/mv_video", {
                "judul": judul, "status": "naskah", "naskah": naskah,
                "caption": caption, "run_url": run_url}, ekstra={"Prefer": "return=representation"})
            self.video_id = r[0]["id"]
            baris = [{"video_id": self.video_id, "urutan": i + 1, "nama": a["nama"], "teks": a["teks"],
                      "kunci": a.get("kunci", []), "prompt_gambar": a.get("prompt")}
                     for i, a in enumerate(naskah["adegan"])]
            self._req("POST", "/rest/v1/mv_adegan", baris)
        self.aman(f)

    def status(self, st, **lain):
        if not self.video_id:
            return
        self.aman(self._req, "PATCH", f"/rest/v1/mv_video?id=eq.{self.video_id}", {"status": st, **lain})

    def adegan(self, nama, **kolom):
        if not self.video_id:
            return
        self.aman(self._req, "PATCH",
                  f"/rest/v1/mv_adegan?video_id=eq.{self.video_id}&nama=eq.{urllib.parse.quote(nama)}", kolom)

    def unggah(self, path_lokal, nama_berkas):
        if not self.video_id:
            return None
        lokasi = f"{self.video_id}/{nama_berkas}"
        def f():
            self._req("POST", f"/storage/v1/object/mesin-video/{lokasi}", open(path_lokal, "rb").read(),
                      tipe="video/mp4", ekstra={"x-upsert": "true"}, mentah=True)
            return "mesin-video/" + lokasi
        return self.aman(f)


# ---------- suara (ElevenLabs) ----------
def suara(teks, out, voice, key, model):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice}?output_format=mp3_44100_128"
    body = json.dumps({"text": teks, "model_id": model}).encode()
    for pct in range(3):
        r = urllib.request.Request(url, body, {"xi-api-key": key, "Content-Type": "application/json",
                                               "Accept": "audio/mpeg"})
        try:
            with urllib.request.urlopen(r, timeout=180) as f:
                data = f.read()
            if len(data) < 2000:
                raise RuntimeError("audio terlalu kecil: " + data[:200].decode(errors="replace"))
            open(out, "wb").write(data)
            return
        except urllib.error.HTTPError as e:
            isi = e.read().decode(errors="replace")[:400]
            catat(f"  elevenlabs gagal HTTP {e.code} (percobaan {pct + 1}): {isi}")
            if e.code in (401, 402, 403, 404, 422):  # galat tetap: jangan diulang
                raise RuntimeError(f"ElevenLabs menolak (HTTP {e.code}): {isi}")
        except Exception as e:
            catat(f"  elevenlabs gagal (percobaan {pct + 1}): {type(e).__name__}: {e}")
        time.sleep(4 * (pct + 1))
    raise RuntimeError("ElevenLabs gagal setelah 3 percobaan")


def durasi(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                       capture_output=True, text=True)
    try:
        nilai = float(r.stdout.strip())
    except (TypeError, ValueError):
        return None
    if r.returncode != 0 or not math.isfinite(nilai) or nilai <= 0:
        return None
    return nilai


# ---------- alur utama ----------
def periksa(n):
    if not n.get("gaya"):
        sys.exit("naskah tanpa 'gaya'")
    if not n.get("adegan"):
        sys.exit("naskah tanpa 'adegan'")
    pakai = set()
    for i, a in enumerate(n["adegan"]):
        a.setdefault("nama", f"s{i + 1}")
        if a["nama"] in pakai:
            sys.exit(f"nama adegan kembar: {a['nama']}")
        pakai.add(a["nama"])
        for k in ("teks", "prompt"):
            if k == "prompt":
                folder_slug = slug(n.get("judul", ""))
                folder_gambar = os.path.join(HERE, "gambar_manual", folder_slug)
                manual_gambar = any(
                    os.path.isfile(os.path.join(folder_gambar, a["nama"] + ext))
                    for ext in (".png", ".jpg", ".jpeg", ".webp")
                )
                manual_video = os.path.isfile(
                    os.path.join(HERE, "video_manual", folder_slug, a["nama"] + ".mp4")
                )
                # Prompt hanya boleh kosong bila adegan ini sendiri sudah punya visual.
                if a.get("kartu") or a.get("papan") or manual_gambar or manual_video:
                    continue
            if not a.get(k):
                sys.exit(f"adegan '{a['nama']}' tanpa '{k}'")


def tulis_teks_besar(path, baris, y0=50, gelap=False, rgba=False):
    """Tulis teks besar ke gambar (path) atau, bila rgba=True, ke PNG transparan 1080x1920 untuk ditumpuk di atas video."""
    from PIL import Image, ImageDraw, ImageFont
    if rgba:
        im = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    else:
        if not os.path.exists(path):
            return
        im = Image.open(path).convert("RGB")
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype("/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf", 92)
    warna = ["#FFFFFF", "#F28A1E"] if gelap else ["#14284B", "#F28A1E"]
    tepi = "#0E1B3D" if gelap else "#FBFAF6"
    y = y0
    for i, b in enumerate(baris):
        w = d.textlength(b, font=f)
        d.text(((im.width - w) / 2, y), b, font=f, fill=warna[min(i, 1)], stroke_width=9, stroke_fill=tepi)
        y += 112
    im.save(path)


def salin_manual(folder_slug, gdir, nama_all, paksa):
    """Gambar buatan sendiri (Gemini/Meta AI dll) di gambar_manual/<slug>/<adegan>.png|jpg|jpeg|webp
    dipakai langsung: dipotong ke 9:16 (1080x1920) lalu disimpan sebagai gambar adegan."""
    from PIL import Image
    src = os.path.join(HERE, "gambar_manual", folder_slug)
    if not os.path.isdir(src):
        return []
    dipakai = []
    for nama in nama_all:
        tujuan = os.path.join(gdir, nama + ".png")
        if nama in paksa or os.path.exists(tujuan):
            continue
        for ext in (".png", ".jpg", ".jpeg", ".webp"):
            p = os.path.join(src, nama + ext)
            if os.path.exists(p):
                im = Image.open(p).convert("RGB")
                W, H = 1080, 1920
                s = max(W / im.width, H / im.height)
                im = im.resize((round(im.width * s), round(im.height * s)))
                l, t = (im.width - W) // 2, (im.height - H) // 2
                im.crop((l, t, l + W, t + H)).save(tujuan)
                dipakai.append(nama)
                break
    return dipakai


def jalankan(a, sb):
    n = json.load(open(a.naskah, encoding="utf-8"))
    periksa(n)
    judul = n.get("judul") or os.path.splitext(os.path.basename(a.naskah))[0]
    folder = os.path.join(a.keluar, slug(judul))
    gdir, adir = os.path.join(folder, "gambar"), os.path.join(folder, "audio")
    os.makedirs(gdir, exist_ok=True); os.makedirs(adir, exist_ok=True)
    nama_all = [x["nama"] for x in n["adegan"]]
    paksa = set(nama_all) if a.ulang == "semua" else set(filter(None, (a.ulang or "").split(",")))
    tidak_dikenal = paksa - set(nama_all)
    if tidak_dikenal:
        raise ValueError("--ulang memuat nama adegan yang tidak ada: " + ", ".join(sorted(tidak_dikenal)))
    vdir = os.path.join(folder, "video"); os.makedirs(vdir, exist_ok=True)
    ada_video = set()
    for nm in nama_all:
        sv = os.path.join(HERE, "video_manual", slug(judul), nm + ".mp4")
        if os.path.exists(sv):
            shutil.copyfile(sv, os.path.join(vdir, nm + ".mp4")); ada_video.add(nm)
            print("video manual dipakai:", nm, flush=True)
    kartu_map = {x["nama"]: x["kartu"] for x in n["adegan"] if x.get("kartu")}
    # adegan "papan": shot cerita.js (sama format papan/kisah/*.json) dirender jadi HTML lalu
    # diperlakukan persis seperti "kartu" (kartu.render() pakai setT(t) yang sama; cerita.js
    # menumpangi window.setT milik papan.js). Dipakai untuk konten yang tidak boleh pakai gambar AI
    # (mis. Kisah Islami: nabi/malaikat/sahabat/Allah tidak digambar), vs "prompt" = gambar Cloudflare.
    papan_adegan = [x for x in n["adegan"] if x.get("papan") and x["nama"] not in kartu_map]
    if papan_adegan:
        pdir = os.path.join(folder, "papan_html")
        os.makedirs(pdir, exist_ok=True)
        for x in papan_adegan:
            nm = x["nama"]
            shot = dict(x["papan"])
            shot.setdefault("at", 0)
            spek_papan = {"cerita": {"cerah": shot.pop("cerah", False), "shot": [shot], "tengah": shot.pop("tengah", [])}}
            sp_papan = os.path.join(pdir, nm + ".json")
            json.dump(spek_papan, open(sp_papan, "w", encoding="utf-8"), ensure_ascii=False)
            html_out = os.path.join(pdir, nm + ".html")
            r = subprocess.run([sys.executable, os.path.join(HERE, "papan_buat.py"), sp_papan, "--html", html_out],
                               capture_output=True, text=True)
            if r.returncode != 0 or not os.path.exists(html_out):
                raise RuntimeError(f"gagal buat HTML papan untuk adegan '{nm}': {r.stderr[-800:]}")
            kartu_map[nm] = html_out
            print(f"papan -> kartu: {nm}", flush=True)
    ada_video |= set(kartu_map)
    manual = salin_manual(slug(judul), gdir, nama_all, paksa)
    if manual:
        print("gambar manual dipakai:", ", ".join(manual), flush=True)
    # teks besar dibakar ke gambar adegan (terlihat sejak frame pertama): "teks_besar": ["baris 1", "baris 2"]
    for x in n["adegan"]:
        if x.get("teks_besar") and x["nama"] not in ada_video:
            tulis_teks_besar(os.path.join(gdir, x["nama"] + ".png"), x["teks_besar"], gelap=x.get("teks_gelap", False))
        elif x.get("teks_besar"):
            os.makedirs(os.path.join(folder, "overlay"), exist_ok=True)
            tulis_teks_besar(os.path.join(folder, "overlay", x["nama"] + ".png"), x["teks_besar"], gelap=x.get("teks_gelap", False), rgba=True)
    run_url = None
    if os.environ.get("GITHUB_RUN_ID"):
        run_url = f"{os.environ.get('GITHUB_SERVER_URL', 'https://github.com')}/{os.environ.get('GITHUB_REPOSITORY')}/actions/runs/{os.environ['GITHUB_RUN_ID']}"
    sb.mulai(judul, n, n.get("caption"), run_url)

    # 1) gambar
    sb.status("gambar")
    perlu = [x for x in nama_all if x not in ada_video and (x in paksa or not os.path.exists(os.path.join(gdir, x + ".png")))]
    if perlu:
        print(f"== gambar: {len(perlu)} adegan ==", flush=True)
        r = subprocess.run([sys.executable, os.path.join(HERE, "gambar.py"), a.naskah, "-o", gdir,
                            "--hanya", ",".join(perlu)])
        lap = os.path.join(gdir, "laporan.txt")
        if os.path.exists(lap):
            LAP.append(open(lap).read())
        kurang = [x for x in nama_all if x not in ada_video and not os.path.exists(os.path.join(gdir, x + ".png"))]
        if kurang and r.returncode == 3:
            raise RuntimeError("Jatah gratis harian Cloudflare Workers AI habis (reset 07.00 WIB). "
                               "Upgrade ke Workers Paid, tunggu reset, atau pakai penyedia gambar lain. Belum jadi: " + ", ".join(kurang))
        if kurang:
            raise RuntimeError("gambar gagal dibuat: " + ", ".join(kurang) + f" (gambar.py kode {r.returncode})")
    else:
        print("== gambar: semua sudah ada, dilewati ==", flush=True)
    for x in nama_all:
        sb.adegan(x, status="gambar_siap")

    # 2) suara
    key, voice = os.environ.get("ELEVENLABS_API_KEY"), os.environ.get("ELEVENLABS_VOICE_ID")
    # suara buatan sendiri: audio_manual/<judul>/<adegan>.mp3 disalin bila belum ada
    src_a = os.path.join(HERE, "audio_manual", slug(judul))
    for nm in nama_all:
        sp_ = os.path.join(src_a, nm + ".mp3"); tj = os.path.join(adir, nm + ".mp3")
        if os.path.exists(sp_) and nm not in paksa and not os.path.exists(tj):
            shutil.copyfile(sp_, tj); print("suara manual dipakai:", nm, flush=True)
    semua_manual = all(os.path.exists(os.path.join(adir, nm + ".mp3")) for nm in nama_all)
    punya_api_suara = bool(key and voice)
    if not a.tanpa_suara and not punya_api_suara and semua_manual and paksa:
        raise RuntimeError("--ulang meminta pembuatan ulang adegan, tetapi ElevenLabs belum dikonfigurasi. "
                           "Tambahkan ELEVENLABS_API_KEY dan ELEVENLABS_VOICE_ID, atau jalankan tanpa --ulang.")
    pakai_suara = not a.tanpa_suara and (punya_api_suara or semua_manual)
    if not a.tanpa_suara and not pakai_suara:
        catat("PERINGATAN: ELEVENLABS_API_KEY / ELEVENLABS_VOICE_ID belum diset; video dibuat TANPA narasi.")
    if pakai_suara:
        sb.status("suara")
        model = os.environ.get("ELEVENLABS_MODEL", "eleven_multilingual_v2")
        for x in n["adegan"]:
            p = os.path.join(adir, x["nama"] + ".mp3")
            if x["nama"] in paksa or not os.path.exists(p):
                print(f"suara {x['nama']}", flush=True)
                suara(x["teks"], p, voice, key, model)
            d = durasi(p)
            if d is None:
                raise RuntimeError(f"Audio adegan '{x['nama']}' tidak valid atau durasinya tidak terbaca: {p}")
            sb.adegan(x["nama"], durasi_detik=d, status="suara_siap")

    # kartu animasi (HTML -> mp4), durasi mengikuti narasi adegan
    sfx_map = {}
    for nm, hp in kartu_map.items():
        ap_ = os.path.join(adir, nm + ".mp3")
        dk = (durasi(ap_) + 1.2) if os.path.exists(ap_) else 6.5
        print(f"kartu {nm}: {hp} ({dk:.1f} dtk)", flush=True)
        import kartu as _k
        st = _k.render(os.path.join(HERE, hp), dk, os.path.join(vdir, nm + ".mp4"), suara=(durasi(ap_) if os.path.exists(ap_) else None))
        # efek suara: whoosh saat kartu masuk, pop saat baris muncul, ding saat centang
        sfx_map[nm] = [[0.15, "whoosh"]] + [[t, "pop"] for t in st] + [[round(t + 0.55, 2), "ding"] for t in st]

    # 3) spec + rakit
    sb.status("rakit")
    spec = {"judul": judul, "latar": n.get("latar", "FBFAF6"), "adegan": []}
    if n.get("musik"):
        spec["musik"] = os.path.abspath(os.path.join(HERE, n["musik"]))
    for x in n["adegan"]:
        s = {"gambar": f"gambar/{x['nama']}.png", "teks": x["teks"], "kunci": x.get("kunci", [])}
        if x["nama"] in ada_video:
            s = {"video": f"video/{x['nama']}.mp4", "teks": x["teks"], "kunci": x.get("kunci", [])}
        if x["nama"] in sfx_map and not n.get("tanpa_sfx"):
            s["sfx"] = sfx_map[x["nama"]]
        if x.get("teks_besar") and x["nama"] in ada_video:
            s["overlay"] = f"overlay/{x['nama']}.png"
        if pakai_suara:
            s["audio"] = f"audio/{x['nama']}.mp3"
        spec["adegan"].append(s)
    sp = os.path.join(folder, "spec.json")
    json.dump(spec, open(sp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    video = os.path.join(folder, "video.mp4")
    print("== rakit ==", flush=True)
    subprocess.run([sys.executable, os.path.join(HERE, "rakit.py"), sp, "-o", video], check=True)
    total = durasi(video)

    # 4) QC otomatis: hanya GAGAL teknis yang menghentikan pengiriman.
    def periksa_hasil(berkas_video, berkas_spek, nama):
        print(f"== pemeriksaan kualitas: {nama} ==", flush=True)
        cmd = [sys.executable, os.path.join(HERE, "periksa.py"), berkas_video,
               "--spek", berkas_spek, "-o", os.path.join(folder, "periksa_" + nama)]
        if not pakai_suara:
            cmd.append("--tanpa-audio")
        subprocess.run(cmd, check=True)

    periksa_hasil(video, sp, "utama")

    if n.get("inti") and len(spec["adegan"]) > 2:
        # versi tanpa adegan pertama (hook) dan terakhir (penutup), untuk digabung di YouTube
        spi = dict(spec); spi["adegan"] = spec["adegan"][1:-1]
        spp = os.path.join(folder, "spec_inti.json")
        json.dump(spi, open(spp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        video_inti = os.path.join(folder, "video_inti.mp4")
        subprocess.run([sys.executable, os.path.join(HERE, "rakit.py"), spp, "-o", video_inti], check=True)
        periksa_hasil(video_inti, spp, "inti")
    if n.get("caption"):
        open(os.path.join(folder, "caption.txt"), "w", encoding="utf-8").write(n["caption"])

    # 4) simpan
    lokasi = sb.unggah(video, slug(judul) + ".mp4")
    sb.status("review", url_hasil=lokasi, durasi_detik=total, galat=None)
    print(f"SELESAI: {video} ({total:.1f} dtk)" + (f" | supabase: {lokasi}" if lokasi else ""), flush=True)
    return folder


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("naskah")
    ap.add_argument("-o", "--keluar", default="hasil")
    ap.add_argument("--tanpa-suara", action="store_true")
    ap.add_argument("--ulang", default="", help="'semua' atau nama adegan (pisah koma) yang dibuat ulang")
    a = ap.parse_args()
    sb = Supabase()
    folder = None
    try:
        folder = jalankan(a, sb)
    except BaseException as e:
        catat("GAGAL:", type(e).__name__, str(e))
        catat(traceback.format_exc()[-1500:])
        sb.status("gagal", galat=f"{type(e).__name__}: {e}"[:500])
        os.makedirs(a.keluar, exist_ok=True)
        open(os.path.join(folder or a.keluar, "laporan_otomatis.txt"), "w").write("\n".join(LAP))
        sys.exit(1)
    open(os.path.join(folder, "laporan_otomatis.txt"), "w").write("\n".join(LAP) or "tanpa catatan")


if __name__ == "__main__":
    main()
