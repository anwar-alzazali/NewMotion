#!/usr/bin/env python3
"""Papan: spesifikasi JSON -> halaman HTML animasi 9:16 -> (opsional) video mp4.
Pakai:
  python papan_buat.py papan/contoh/alur_pesan.json -o hasil.mp4      # render video
  python papan_buat.py papan/contoh/alur_pesan.json --html out.html   # hanya HTML
  python papan_buat.py spec.json --pratinjau 1.5,4,8 -o /tmp/frame    # PNG pada detik tertentu
Spesifikasi boleh memuat "suara" (narasi mp3, durasi ikut audio), "subtitle" [[t0,t1,teks]], "tokoh" (folder gambar mulut),
"adegan" [{at, isi:[...]}] (layar berganti) dan "peta" {item, at, aktif:[[detik, indeks|-1]]}.
Komponen dan contoh: papan/papan.js, papan/contoh/*.json (lihat bagian Papan di CLAUDE.md)."""
import argparse, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))


def cari(path, dasar):
    """Jalur relatif: coba terhadap folder spesifikasi, lalu folder kerja, lalu folder repo."""
    for d in (dasar, os.getcwd(), HERE):
        f = os.path.join(d, path)
        if os.path.exists(f):
            return f
    raise SystemExit(f"berkas tidak ditemukan: {path}")


def data_tokoh(spec, dasar, durasi_kira):
    """Tokoh bulat: potong kepala-bahu dari gambar mulut_tutup/oh/aah (+ kedip opsional), mulut mengikuti spec.suara."""
    import base64, io
    import numpy as np
    from PIL import Image
    import puppet
    o = spec["tokoh"] if isinstance(spec["tokoh"], dict) else {"folder": spec["tokoh"]}
    if o.get("gambar"):  # satu gambar saja -> mulut tempel otomatis
        return data_tokoh_tempel(spec, o, dasar, durasi_kira)
    folder = cari(o.get("folder", "karakter/anwar_kartun"), dasar)
    kotak = o.get("potong", [0.24, 0.245, 0.76, 0.535])  # kiri, atas, kanan, bawah (pecahan gambar)
    img = []
    for nm in ["mulut_tutup", "mulut_oh", "mulut_aah", "kedip"]:
        f = next((os.path.join(folder, nm + e) for e in (".png", ".jpg", ".jpeg") if os.path.exists(os.path.join(folder, nm + e))), None)
        if not f:
            continue
        im = Image.open(f).convert("RGB")
        W, H = im.size
        l, t, r, b = kotak[0] * W, kotak[1] * H, kotak[2] * W, kotak[3] * H
        sisi = min(r - l, b - t); cx, cy = (l + r) / 2, (t + b) / 2
        im = im.crop((int(cx - sisi / 2), int(cy - sisi / 2), int(cx + sisi / 2), int(cy + sisi / 2))).resize((300, 300), Image.LANCZOS)
        buf = io.BytesIO(); im.save(buf, "JPEG", quality=85)
        img.append("data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode())
    n = int(round(durasi_kira * 30)) + 30
    if spec.get("suara"):
        amp = puppet.amplop(cari(spec["suara"], dasar), n, o.get("tunda", 0.05))
        mulut = puppet.kelas(amp).tolist()
        amp = np.clip(amp, 0, 1.5).round(2).tolist()
    else:
        mulut, amp = [0] * n, [0] * n
    return {"img": img, "mulut": [int(x) for x in mulut], "amp": amp, "fps": 30, "at": o.get("at", 0.2),
        "ukuran": o.get("ukuran"), "x": o.get("x"), "y": o.get("y")}


def frasa(kata, maks=4):
    """Kata berwaktu -> frasa subtitle: potong di tanda baca / jeda >0,35 dtk / `maks` kata; ekor satu kata digabung."""
    import re
    out, cur = [], []
    for i, k in enumerate(kata):
        cur.append(k)
        nx = kata[i + 1] if i + 1 < len(kata) else None
        jeda = nx and nx["t0"] - k["t1"] > 0.35
        if re.search(r"[.,!?;:]$", k["teks"]) or jeda or len(cur) >= maks or not nx:
            if len(cur) == 1 and out and not re.search(r"[.!?:]$", out[-1][2]) and k["t0"] - out[-1][1] < 0.35 and len(out[-1][2].split()) < maks + 2:
                out[-1] = [out[-1][0], round(k["t1"], 2), out[-1][2] + " " + k["teks"]]
            else:
                out.append([round(cur[0]["t0"], 2), round(cur[-1]["t1"], 2), " ".join(x["teks"] for x in cur)])
            cur = []
    return out


def pasang_waktu(spec, dasar):
    """Bila spec punya "waktu" (berkas .waktu.json dari narasi_api.py): subtitle diisi otomatis (kalau kosong) dan
    setiap nilai waktu berupa teks "@kata" / "@kata#2" / "@kata-0.3" diganti detik awal kata itu (kemunculan ke-n, plus geser)."""
    if not spec.get("waktu"):
        return
    w = json.load(open(cari(spec["waktu"], dasar), encoding="utf-8"))
    if not spec.get("subtitle"):
        spec["subtitle"] = frasa(w.get("kata", [])) or w.get("subtitle", [])
    import re
    bersih = lambda x: re.sub(r"[^\w]", "", x.lower())
    kata = [(bersih(k["teks"]), k["t0"]) for k in w.get("kata", [])]

    def ubah(v, off=0.0):
        if isinstance(v, str) and v.startswith("@"):
            m = re.match(r"@([^#+\-]+)(?:#(\d+))?([+\-][\d.]+)?$", v)
            if not m:
                raise SystemExit(f"format waktu salah: {v}")
            cari_k, ke, geser = bersih(m.group(1)), int(m.group(2) or 1), float(m.group(3) or 0)
            hit = [t for k, t in kata if k == cari_k]
            if len(hit) < ke:
                raise SystemExit(f"kata tidak ada di narasi: {v}")
            return round(max(0, hit[ke - 1] + geser - off), 2)
        if isinstance(v, list):
            return [ubah(x, off) for x in v]
        if isinstance(v, dict):
            return {k: ubah(x, off) for k, x in v.items()}
        return v
    # adegan: waktu adegan absolut; komponen di dalamnya relatif terhadap awal adegan
    for a in spec.get("adegan", []):
        a["at"] = ubah(a.get("at", 0))
        a["isi"] = ubah(a.get("isi", []), a["at"])
    for k in ("peta", "isi", "bawah", "efek_suara", "rekaman"):
        if k in spec:
            spec[k] = ubah(spec[k])
    C = spec.get("cerita") or {}
    for sh in C.get("shot", []):  # shot: waktu absolut; isi di dalamnya (teks, kunci boneka, dll) relatif awal shot
        sh["at"] = ubah(sh.get("at", 0))
        for k in list(sh):
            if k != "at":
                sh[k] = ubah(sh[k], sh["at"])
    if "meteran" in C:
        C["meteran"] = ubah(C["meteran"])


def sematkan_gambar(spec, dasar):
    """Nilai "src" (komponen gambar) dan "latar_gambar" (adegan) berupa jalur berkas -> data URI, supaya HTML mandiri."""
    import base64, mimetypes
    cache = {}

    def uri(v):
        if not isinstance(v, str) or v.startswith(("data:", "http://", "https://")):
            return v
        if v not in cache:
            f = cari(v, dasar)
            mt = mimetypes.guess_type(f)[0] or "image/jpeg"
            cache[v] = f"data:{mt};base64," + base64.b64encode(open(f, "rb").read()).decode()
        return cache[v]

    def ikon(v):  # "i:nama" -> SVG garis (Lucide, ISC) dari papan/ikon/
        f = os.path.join(HERE, "papan", "ikon", v[2:].strip() + ".svg")
        if not os.path.exists(f):
            raise SystemExit(f"ikon tidak ada: {v} (lihat papan/ikon/)")
        return open(f, encoding="utf-8").read().replace('<svg ', '<svg class="ig" ')

    def jalan(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if k == "ikon" and isinstance(v, str) and v.startswith("i:"):
                    o[k] = ikon(v)
                elif k in ("src", "latar_gambar"):
                    o[k] = uri(v)
                else:
                    jalan(v)
        elif isinstance(o, list):
            for x in o:
                jalan(x)
    jalan(spec)


def data_tokoh_tempel(spec, o, dasar, durasi_kira):
    """Tokoh dari SATU gambar (mis. kartun pelanggan): wajah dideteksi (OpenCV), kepala-bahu dipotong bulat,
    bentuk mulut kartun (tutup/oh/aah) digambar di atas mulut asli mengikuti suara. o.mulut={x,y,w} (pecahan gambar) menimpa deteksi."""
    import base64, io
    import numpy as np
    from PIL import Image
    import puppet
    f = cari(o["gambar"], dasar)
    im = Image.open(f).convert("RGB"); W, H = im.size
    m = o.get("mulut")
    if m:
        mx, my, mw = m["x"] * W, m["y"] * H, m.get("w", 0.12) * W
        fw = mw / 0.3; fcx, fcy = mx, my - 0.32 * fw
    else:
        import cv2
        g = cv2.cvtColor(np.asarray(im)[:, :, ::-1], cv2.COLOR_BGR2GRAY)
        wajah = []
        for c in ("haarcascade_frontalface_alt2.xml", "haarcascade_frontalface_default.xml"):
            wajah = list(cv2.CascadeClassifier(cv2.data.haarcascades + c).detectMultiScale(g, 1.1, 4, minSize=(int(min(W, H) * 0.12),) * 2))
            if wajah:
                break
        if wajah:
            x, y, w, h = max(wajah, key=lambda r: r[2] * r[3])
            fw = w; fcx, fcy = x + w / 2, y + h / 2; mx, my, mw = fcx, y + 0.83 * h, 0.3 * w
        else:  # cadangan: anggap wajah di tengah atas
            fw = min(W, H) * 0.4; fcx, fcy = W / 2, H * 0.4; mx, my, mw = fcx, fcy + 0.33 * fw, 0.3 * fw
    sisi = fw * 1.75; cx, cy = fcx, fcy + fw * 0.12
    l, t = int(max(0, cx - sisi / 2)), int(max(0, cy - sisi / 2)); r, b = int(min(W, l + sisi)), int(min(H, t + sisi))
    kot = im.crop((l, t, r, b)); kw, kh = kot.size
    a = np.asarray(im).astype(float)
    # warna kulit: rata-rata cincin di sekitar mulut, tanpa piksel gelap (garis, kumis)
    yy, xx = np.mgrid[int(my - mw * 0.9):int(my + mw * 0.9), int(mx - mw * 1.1):int(mx + mw * 1.1)]
    yy = yy.clip(0, H - 1); xx = xx.clip(0, W - 1)
    sampel = a[yy, xx].reshape(-1, 3); terang = sampel[sampel.sum(1) > np.percentile(sampel.sum(1), 55)]
    kulit = "#%02x%02x%02x" % tuple(int(v) for v in np.median(terang, axis=0))
    kot = kot.resize((320, int(320 * kh / kw)), Image.LANCZOS)
    buf = io.BytesIO(); kot.save(buf, "JPEG", quality=86)
    n = int(round(durasi_kira * 30)) + 30
    if spec.get("suara"):
        amp = puppet.amplop(cari(spec["suara"], dasar), n, o.get("tunda", 0.05))
        mulut = puppet.kelas(amp).tolist(); amp = np.clip(amp, 0, 1.5).round(2).tolist()
    else:
        mulut, amp = [0] * n, [0] * n
    return {"img": ["data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()], "tempel": {
        "x": (mx - l) / kw, "y": (my - t) / kh, "w": mw / kw, "kulit": kulit, "bibir": o.get("bibir", "#7a2e2a")},
        "mulut": [int(x) for x in mulut], "amp": amp, "fps": 30, "at": o.get("at", 0.2),
        "ukuran": o.get("ukuran"), "x": o.get("x"), "y": o.get("y")}


def render_cepat(html, durasi, out, fps=30):
    """Lebih cepat dari kartu.render: tangkapan JPEG langsung dialirkan ke ffmpeg (tanpa PNG ke disk)."""
    import subprocess
    from playwright.sync_api import sync_playwright
    n = int(round(durasi * fps))
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-c:v", "mjpeg", "-framerate", str(fps), "-i", "-",
                           "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", "-crf", "19", out], stdin=subprocess.PIPE)
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1080, "height": 1920})
        pg.goto("file://" + os.path.abspath(html)); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(400)
        for i in range(n):
            pg.evaluate(f"setT({i / fps:.4f})")
            ff.stdin.write(pg.screenshot(type="jpeg", quality=92))
        b.close()
    ff.stdin.close(); ff.wait()
    if ff.returncode:
        raise SystemExit("ffmpeg gagal")


def durasi_audio(f):
    import subprocess
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f], capture_output=True, text=True)
    return float(r.stdout.strip() or 0)


def campur_rekaman(video, daftar, dur, dasar, duck=12, lufs=None):
    """Efek suara rekaman (mp3 ElevenLabs dll) dicampur ke trek audio video:
    rekaman: [{berkas, at, vol=0.6, gain_db=0, ulang=false, sampai=null, masuk=0.3, keluar=0.8}] (at boleh "@kata").
    duck = rasio penekanan efek saat narasi bicara (bawaan 12; kecil = efek tetap terdengar); lufs = target kekerasan akhir (opsional)."""
    import subprocess
    masukan, fc, label = ["-i", video], [], ["[0:a]"]
    for i, r in enumerate(daftar, 1):
        if r.get("ulang"):
            masukan += ["-stream_loop", "-1"]
        masukan += ["-i", cari(r["berkas"], dasar)]
        at, vol = float(r.get("at", 0)), r.get("vol", 0.6)
        lama = (float(r["sampai"]) - at) if r.get("sampai") is not None else (dur - at if r.get("ulang") else None)
        f = f"[{i}:a]aresample=44100,aformat=channel_layouts=stereo"
        if lama:
            f += f",atrim=0:{lama:.2f},afade=t=out:st={max(0, lama - r.get('keluar', 0.8)):.2f}:d={r.get('keluar', 0.8)}"
        f += f",afade=t=in:d={r.get('masuk', 0.3)},volume={vol},volume={r.get('gain_db', 0)}dB,adelay={int(at * 1000)}|{int(at * 1000)}[r{i}]"
        fc.append(f); label.append(f"[r{i}]")
    # efek digabung jadi satu bus, lalu otomatis MENGECIL saat narasi bicara (ducking), supaya suara narasi tetap jelas
    fc.append("[0:a]asplit[n0][kunci]")
    fc.append("".join(label[1:]) + f"amix=inputs={len(label) - 1}:normalize=0[efek]")
    fc.append(f"[efek][kunci]sidechaincompress=threshold=0.015:ratio={duck}:attack=8:release=450:makeup=1[efekd]")
    fc.append(f"[n0][efekd]amix=inputs=2:duration=first:normalize=0,"
              + (f"loudnorm=I={lufs}:TP=-1.5:LRA=11," if lufs else "") + f"alimiter=limit=0.89:level=false,atrim=0:{dur}[a]")
    tmp = video + ".tmp.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *masukan, "-filter_complex", ";".join(fc),
                    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", tmp], check=True)
    os.replace(tmp, video)


class SpekDitolak(SystemExit):
    """Spek melanggar BATAS WAJIB (tokoh suci digambar / dalil tak terverifikasi): render dibatalkan."""


def jaga_spek(spec):
    """GERBANG sebelum render; aturan khusus dijalankan hanya oleh paket genre pemiliknya."""
    sys.path.insert(0, os.path.dirname(HERE))
    from newmotion.domain.genre import (
        ambil,
        dari_rencana,
        konteks_konten_untuk_naskah,
        memakai_kebijakan_islami,
    )

    try:
        paket = dari_rencana(spec)
        konteks_konten = konteks_konten_untuk_naskah(spec, genre=paket.nama)
        paket_kebijakan = [paket]
        if memakai_kebijakan_islami(konteks_konten) and paket.nama != "kisah_islami":
            # Genre penceritaan tetap milik paket utama; pagar Islami dipakai
            # sebagai lapisan kebijakan lintas genre, bukan paket genre baru.
            paket_kebijakan.append(ambil("kisah_islami"))
    except (ValueError, TypeError, ImportError) as galat:
        print(f"GENRE/KONTEKS KONTEN TIDAK VALID: {galat}", file=sys.stderr)
        raise SpekDitolak(3) from galat

    pesan = []
    dalil = []
    penjaga_tokoh = list(dict.fromkeys(
        p.penjaga_tokoh for p in paket_kebijakan if p.penjaga_tokoh is not None
    ))
    penjaga_dalil = list(dict.fromkeys(
        p.penjaga_dalil for p in paket_kebijakan if p.penjaga_dalil is not None
    ))

    for penjaga in penjaga_tokoh:
        temuan_adab = penjaga(spec)
        if temuan_adab:
            rincian = "\n".join(f"[{item.kode}] {item.pesan}" for item in temuan_adab)
            pesan.append("Pelanggaran adab penggambaran tokoh:\n" + rincian)

    for penjaga in penjaga_dalil:
        temuan_dalil = penjaga(spec)
        dalil.extend(temuan_dalil)
        terblokir = [item for item in temuan_dalil if item.memblokir]
        if terblokir:
            rincian = "\n".join(f"- {item}" for item in terblokir)
            pesan.append("Pelanggaran verifikasi dalil:\n" + rincian)
        for item in temuan_dalil:
            if not item.memblokir:
                print(
                    f"penjaga dalil: {item}"
                    + "".join(f"\n    peringatan: {w}" for w in item.peringatan),
                    file=sys.stderr,
                )

    if pesan:
        print("\n\n".join(pesan) + "\nRENDER DIBATALKAN. Perbaiki spek sumber, jangan melewati gerbang.", file=sys.stderr)
        raise SpekDitolak(3)

    cerita = spec.get("cerita") or {}
    if cerita.get("penataan_panggung_otomatis"):
        # Perencanaan panggung opt-in: spek lama tidak berubah.
        from newmotion.penataan_panggung import rencanakan_penataan_panggung
        for hasil in rencanakan_penataan_panggung(cerita):
            print("penataan panggung otomatis:", hasil, file=sys.stderr)
        cerita["pemeriksaan_penataan_panggung"] = True
    if cerita.get("pemeriksaan_penataan_panggung"):
        # Pemeriksaan ini opsional agar spesifikasi lama tetap kompatibel.
        from newmotion.penataan_panggung import periksa_penataan_panggung
        temuan = periksa_penataan_panggung(cerita)
        for item in temuan:
            print("penataan panggung [{}] {}: {}".format(item["tingkat"], item["kode"], item["pesan"]), file=sys.stderr)
        if any(item["tingkat"] == "gagal" for item in temuan):
            print("RENDER DIBATALKAN: perbaiki kontrak penataan panggung pada spesifikasi.", file=sys.stderr)
            raise SpekDitolak(3)
    return dalil


def buat_html(spec, dasar=".", sudah_dijaga=False):
    if not sudah_dijaga:  # pemanggil dari modul lain tetap lewat gerbang
        jaga_spek(spec)
    css = open(os.path.join(HERE, "papan", "papan.css"), encoding="utf-8").read()
    js = open(os.path.join(HERE, "papan", "papan.js"), encoding="utf-8").read()
    if spec.get("cerita"):
        from papan.karakter.integrasi import integrasikan_spec
        integrasikan_spec(spec)
        js += "\n" + open(os.path.join(HERE, "papan", "cerita.js"), encoding="utf-8").read()
        fnt = os.path.join(HERE, "papan", "font", "caveat-700.woff2")  # tulisan tangan (OFL) untuk kitab
        if os.path.exists(fnt):
            import base64
            css += ("@font-face{font-family:'Tangan';font-weight:700;src:url(data:font/woff2;base64,"
                    + base64.b64encode(open(fnt, "rb").read()).decode() + ") format('woff2');}")
    data = json.dumps(spec, ensure_ascii=False).replace("</", "<\\/")
    tambahan = ""
    if spec.get("tokoh"):
        kira = max(spec.get("durasi") or 0, durasi_audio(cari(spec["suara"], dasar)) + 2 if spec.get("suara") else 60)
        tambahan = "window.TOKOH=" + json.dumps(data_tokoh(spec, dasar, kira)) + ";"
    return (f'<!doctype html><html lang="id"><head><meta charset="utf-8"><title>papan</title><style>{css}</style></head>'
            f'<body><script>window.SPEC={data};{tambahan}</script><script>{js}</script></body></html>')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec"); ap.add_argument("-o"); ap.add_argument("--html")
    ap.add_argument("--pratinjau", help="detik dipisah koma; simpan PNG ke <o>_<detik>.png")
    ap.add_argument("-d", type=float, help="paksa durasi (detik)")
    ap.add_argument("--tanpa-suara", action="store_true", help="video tanpa trek efek suara (berkas .sfx.wav/.sfx.json tetap dibuat)")
    a = ap.parse_args()
    spec = json.load(open(a.spec, encoding="utf-8"))
    dasar = os.path.dirname(os.path.abspath(a.spec))
    pasang_waktu(spec, dasar)
    jaga_spek(spec)  # gerbang wajib: sebelum gambar disematkan (nama berkas masih terbaca) dan sebelum HTML ditulis
    sematkan_gambar(spec, dasar)
    suara = cari(spec["suara"], dasar) if spec.get("suara") else None
    if suara and not spec.get("durasi"):
        spec["durasi"] = round(durasi_audio(suara) + spec.get("ekor_suara", 1.2), 2)
    html = a.html or (os.path.splitext(a.o or a.spec)[0] + "_papan.html")
    open(html, "w", encoding="utf-8").write(buat_html(spec, dasar, sudah_dijaga=True))
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1080, "height": 1920})
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto("file://" + os.path.abspath(html)); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(300)
        if errs:
            print("GALAT halaman:", errs[0], file=sys.stderr); sys.exit(1)
        dur = a.d or pg.evaluate("window.__durasi")
        sfx = pg.evaluate("window.__sfx") or []
        if a.pratinjau:
            for t in [float(x) for x in a.pratinjau.split(",")]:
                pg.evaluate(f"setT({t})"); pg.screenshot(path=f"{a.o}_{t}.png")
            b.close(); print("durasi", dur); return
        b.close()
    if a.o:
        import kartu, subprocess, papan_suara
        base = os.path.splitext(a.o)[0]
        json.dump(sfx, open(base + ".sfx.json", "w"))
        wav = papan_suara.campur(sfx, dur, base + ".sfx.wav")
        if a.tanpa_suara:
            render_cepat(html, dur, a.o)
        else:
            sunyi = base + "_sunyi.mp4"
            render_cepat(html, dur, sunyi)
            musik = spec.get("musik", "santai" if suara else None)
            if suara and musik:  # narasi + efek + musik latar yang otomatis mengecil saat narasi bicara (ducking)
                import papan_musik
                mw = papan_musik.buat(musik, dur, base + ".musik.wav", seed=spec.get("musik_seed", 3))
                v, vm = spec.get("volume_efek", 0.45), spec.get("volume_musik", 0.2)
                fc = (f"[1:a]apad,asplit[n1][n2];[2:a]volume={v}[s];[3:a]volume={vm}[m0];"
                      f"[m0][n2]sidechaincompress=threshold=0.02:ratio=10:attack=15:release=350[m];"
                      f"[n1][s][m]amix=inputs=3:duration=longest:normalize=0,atrim=0:{dur}[a]")
                subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", sunyi, "-i", suara, "-i", wav, "-i", mw, "-filter_complex", fc,
                                "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", a.o], check=True)
            elif suara:  # narasi + efek suara (efek dikecilkan supaya tidak menutupi suara)
                v = spec.get("volume_efek", 0.45)
                subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", sunyi, "-i", suara, "-i", wav, "-filter_complex",
                                f"[1:a]apad[n];[2:a]volume={v}[s];[n][s]amix=inputs=2:duration=longest:normalize=0,atrim=0:{dur}[a]",
                                "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", a.o], check=True)
            else:
                subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", sunyi, "-i", wav, "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest", a.o], check=True)
            os.remove(sunyi)
        if spec.get("rekaman") and not a.tanpa_suara:
            campur_rekaman(a.o, spec["rekaman"], dur, dasar, spec.get("duck_rasio", 12), spec.get("keras_lufs"))
        print("selesai", a.o, dur, "dtk;", len(sfx), "efek suara")
    else:
        print("html", html, "durasi", dur)


if __name__ == "__main__":
    main()
