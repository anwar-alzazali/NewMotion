#!/usr/bin/env python3
"""Pemeriksaan wajib sebelum kirim (ATURAN WAJIB di CLAUDE.md). Berlaku untuk semua mesin (Papan, cerita, sinema, 3D).
Pakai: python periksa.py video.mp4 --html halaman.html [--kata kata.json] [--spek spek.json] [-o folder]
Keluar kode 1 hanya untuk GAGAL teknis yang wajib diperbaiki; pedoman kreatif dilaporkan sebagai PERIKSA. Menulis lembar kontak (lembar.jpg, awal.jpg, kecil.jpg) untuk DILIHAT sesi: tumpukan teks,
teks terpotong, dan komposisi dan keterbacaan tetap perlu dinilai manusia; lembar itu wajib dibuka."""
import argparse, json, math, os, re, subprocess, sys

def jalan(a): return subprocess.run(a, capture_output=True, text=True)
def ff(*a): r = jalan(["ffmpeg", "-hide_banner", "-nostdin", *a]); return r.stderr


JS_TEKS = r"""(() => { const out = [];
 const op = (el) => { let o = 1; for (let e = el; e && e.nodeType === 1; e = e.parentElement) { const c = getComputedStyle(e); if (c.display === 'none' || c.visibility === 'hidden') return 0; o *= parseFloat(c.opacity); } return o; };
 document.querySelectorAll('svg text').forEach((el) => { const r = el.getBoundingClientRect(); if (r.width < 2) return; let bb; try { bb = el.getBBox(); } catch (e) { return; }
   const sk = bb.height ? Math.min(r.width / (bb.width || 1), r.height / bb.height) : 1;
   out.push({ t: el.textContent.trim().replace(/\s+/g, ' ').slice(0, 60), x0: r.left, x1: r.right, y0: r.top, y1: r.bottom, fs: parseFloat(getComputedStyle(el).fontSize) * sk, op: op(el), h: !!el.closest('[data-hias]') }); });
 const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT); let n;
 while ((n = w.nextNode())) { const p = n.parentElement; if (!n.nodeValue.trim() || !p || p.closest('svg,script,style,noscript')) continue;
   const g = document.createRange(); g.selectNodeContents(n); const r = g.getBoundingClientRect(); if (r.width < 2) continue;
   const pr = p.getBoundingClientRect(), sk = p.offsetWidth ? pr.width / p.offsetWidth : 1;
   out.push({ t: n.nodeValue.trim().replace(/\s+/g, ' ').slice(0, 60), x0: r.left, x1: r.right, y0: r.top, y1: r.bottom, fs: parseFloat(getComputedStyle(p).fontSize) * sk, op: op(p), h: !!p.closest('[data-hias]') }); }
 return out; })()"""

def ukur_html(a, D, out, catat):
    """Ukur kotak teks SEBENARNYA di halaman (setelah kamera/skala) tiap 0,5 dtk: zona aman x dan y, ukuran minimum, ukuran dan kontras hook, teks bertumpuk."""
    from playwright.sync_api import sync_playwright
    from PIL import Image
    abai = re.compile(a.abaikan, re.I) if a.abaikan else None
    kecil, xl, yl, tumpuk, hias, dom = {}, {}, {}, {}, {}, set()
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1080, "height": 1920})
        if a.kata:
            kj = json.load(open(a.kata)); pg.add_init_script(f"window.KATA={json.dumps(kj.get('kata', kj))};window.OFF_NARASI={a.off};")
        pg.goto("file://" + os.path.abspath(a.html)); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(500)
        dur = pg.evaluate("window.__durasi") or D
        t = 0.0
        while t < dur - 0.05:
            pg.evaluate(f"setT({t:.3f})")
            L = [e for e in pg.evaluate(JS_TEKS) if e["op"] >= 0.3 and 0 <= (e["x0"] + e["x1"]) / 2 <= 1080 and 0 <= (e["y0"] + e["y1"]) / 2 <= 1920]
            if t == 0:
                hk = max(L, key=lambda e: e["fs"], default=None)
                if not hk: catat(False, "hook frame 0", "tidak ada teks di frame 0", True)
                else:
                    catat(hk["fs"] >= 120 and not hk["h"], "ukuran hook", f"{hk['t'][:30]!r} = {hk['fs']:.0f} px (120 px hanya patokan; nilai keterbacaan di layar)", True)
                    nk = sum(len(e["t"].split()) for e in L if e["fs"] >= 0.8 * hk["fs"])
                    catat(nk <= 12, "hook jumlah kata", f"{nk} kata pada teks terbesar di frame 0 (panjang bebas; >12 kata biasanya terlalu padat untuk dibaca sekilas)", True)
                    f0 = f"{out}/frame0.png"; pg.screenshot(path=f0)
                    im = Image.open(f0).convert("L").crop((max(0, int(hk["x0"])), max(0, int(hk["y0"])), min(1080, int(hk["x1"])), min(1920, int(hk["y1"]))))
                    px = sorted(im.tobytes()); lin = lambda v: (v / 255 / 12.92) if v / 255 <= 0.04045 else ((v / 255 + 0.055) / 1.055) ** 2.4
                    lo, hi = lin(px[len(px) // 10]), lin(px[len(px) * 9 // 10]); rasio = (hi + 0.05) / (lo + 0.05)
                    catat(rasio >= 4.5, "kontras hook", f"rasio {rasio:.1f}:1; nilai secara visual, 4,5:1 patokan bukan batas mutlak", True)
            for e in L:
                dom.add(re.sub(r"[^a-zà-ÿ0-9]", "", e["t"].lower()))
                if e["h"] or (abai and abai.search(e["t"])): hias.setdefault(e["t"], (t, e["fs"])); continue
                if e["fs"] < 44: kecil.setdefault(e["t"], (t, e["fs"]))
                kotak = (t, e["x0"], e["x1"], e["y0"], e["y1"])
                if e["x0"] < 60 or e["x1"] > 1020 or e["y0"] < 130 or e["y1"] > 1600 or (e["x1"] > 930 and e["y1"] > 840 and e["y0"] < 1600): xl.setdefault(e["t"], kotak)
                elif e["x0"] < 120 or e["x1"] > 960 or e["y0"] < 240 or e["y1"] > 1260 or (e["x1"] > 780 and e["y1"] > 840): yl.setdefault(e["t"], kotak)
            K = [e for e in L if e["op"] >= 0.6]
            for i in range(len(K)):
                for j in range(i + 1, len(K)):
                    p1, p2 = K[i], K[j]
                    if p1["t"] == p2["t"] or p1["t"] in p2["t"] or p2["t"] in p1["t"]: continue
                    w = min(p1["x1"], p2["x1"]) - max(p1["x0"], p2["x0"]); h = min(p1["y1"], p2["y1"]) - max(p1["y0"], p2["y0"])
                    if w > 0 and h > 0:
                        ar = min((q["x1"] - q["x0"]) * (q["y1"] - q["y0"]) for q in (p1, p2))
                        if ar and w * h / ar > 0.3: kk = (p1["t"][:20], p2["t"][:20]); tumpuk[kk] = tumpuk.get(kk, []) + [t]
            t = round(t + 0.5, 2)
        b.close()
    rk = lambda d, f: "; ".join(f(k, v) for k, v in list(d.items())[:6]) + (f" (+{len(d) - 6} lagi)" if len(d) > 6 else "") if d else "tidak ada"
    catat(not kecil, "teks < 44 px", rk(kecil, lambda k, v: f"{k[:24]!r} {v[1]:.0f}px @{v[0]}s"), True)
    kt = lambda k, v: f"{k[:24]!r} x {v[1]:.0f}-{v[2]:.0f} y {v[3]:.0f}-{v[4]:.0f} @{v[0]}s"
    catat(not xl, "teks di luar zona", "teks di luar zona rekomendasi; periksa apakah tertutup UI atau sulit dibaca: " + rk(xl, kt), True)
    catat(not yl, "zona rekomendasi", "komposisi di luar zona inti; periksa di pratinjau ponsel: " + rk(yl, kt), True)
    tumpuk = {k: v[0] for k, v in tumpuk.items() if len(v) >= 2}  # hanya yang bertahan >= 1 dtk (bukan saat transisi)
    catat(not tumpuk, "teks bertumpuk", rk(tumpuk, lambda k, v: f"{k[0]!r} x {k[1]!r} @{v}s"), True)
    if hias: catat(False, "dikecualikan (hiasan)", f"{len(hias)} teks ditandai hiasan, WAJIB disebut ke pemilik: " + rk(hias, lambda k, v: f"{k[:24]!r} {v[1]:.0f}px"), True)
    return dom


def ocr_video(a, D, out, catat, dom):
    """Baca teks dari GAMBAR video (tesseract) tiap 1,5 dtk: menangkap teks yang digambar sebagai gambar/kanvas/3D (tidak terlihat oleh ukur_html).
    dom = kumpulan kata yang sudah terukur di halaman (None bila tanpa --html: semua kata diperiksa lewat OCR). Tinggi huruf OCR kasar: ukuran huruf ~ tinggi kotak / 0,72."""
    import shutil, glob
    if not shutil.which("tesseract"): catat(False, "OCR", "TIDAK DIUKUR: tesseract tidak terpasang (apt-get install tesseract-ocr tesseract-ocr-ind)", True); return
    for f in glob.glob(f"{out}/ocr_*.png"): os.remove(f)
    ekstrak = jalan(["ffmpeg", "-y", "-hide_banner", "-nostdin", "-i", a.video,
                     "-vf", "fps=1/1.5", f"{out}/ocr_%03d.png"])
    frames = sorted(glob.glob(f"{out}/ocr_*.png"))
    if ekstrak.returncode != 0 or not frames:
        catat(False, "OCR", "TIDAK DIUKUR: gagal mengekstrak frame untuk OCR" +
              (f": {ekstrak.stderr[-400:]}" if ekstrak.stderr else ""), True)
        return
    kata, gagal_ocr = {}, []
    for i, f in enumerate(frames):
        t = max(0.0, i * 1.5 - 0.75) if i else 0.0
        hasil = jalan(["tesseract", f, "-", "-l", "ind", "--psm", "11", "tsv"])
        if hasil.returncode != 0:
            gagal_ocr.append(os.path.basename(f))
            os.remove(f)
            continue
        for ln in hasil.stdout.splitlines()[1:]:
            c = ln.split("\t")
            if len(c) < 12 or c[0] != "5": continue
            try:
                w = re.sub(r"[^a-zà-ÿ0-9]", "", c[11].lower()); cf = float(c[10])
                x, y, ww, hh = map(int, c[6:10])
            except (ValueError, IndexError):
                continue
            if len(w) < 4 or cf < 85: continue
            kata.setdefault(w, []).append((t, x, x + ww, y, y + hh, cf))
        os.remove(f)
    if gagal_ocr:
        catat(False, "OCR sebagian", f"TIDAK LENGKAP: Tesseract gagal pada {len(gagal_ocr)} dari {len(frames)} frame; periksa bahasa/data OCR", True)
    if not kata:
        catat(False, "hasil OCR", "tidak ada hasil OCR yang dapat dibaca; jangan anggap ini bukti tidak ada teks", True)
        return
    yakin = {w: v for w, v in kata.items() if len(v) >= 2 and (dom is None or not any(w in q for q in dom))}
    luar, kecil = {}, {}
    for w, v in yakin.items():
        for (t, x0, x1, y0, y1, cf) in v:
            if x0 < 60 or x1 > 1020 or y0 < 130 or y1 > 1600 or (x1 > 930 and y1 > 840 and y0 < 1600): luar.setdefault(w, (t, x0, x1, y0, y1))
            if (y1 - y0) / 0.72 < 44 * 0.75: kecil.setdefault(w, (t, (y1 - y0) / 0.72))
    rk = lambda d, f: "; ".join(f(k, v) for k, v in list(d.items())[:6]) + (f" (+{len(d) - 6} lagi)" if len(d) > 6 else "") if d else "tidak ada"
    lbl = "teks dari gambar/kanvas (OCR)" if dom is not None else "teks (OCR)"
    catat(True, lbl, f"{len(yakin)} kata terbaca yakin" + ("" if dom is None else " yang tidak ada di halaman") + (": " + ", ".join(list(yakin)[:8]) if yakin else ""))
    catat(not luar, "zona aman (OCR)", rk(luar, lambda k, v: f"{k!r} x {v[1]}-{v[2]} y {v[3]}-{v[4]} @{v[0]}s"), True)
    catat(not kecil, "teks kecil (OCR)", rk(kecil, lambda k, v: f"{k!r} ~{v[1]:.0f}px @{v[0]}s"), True)
    if dom is None:
        f0 = [(w, v[0]) for w, v in kata.items() if v[0][0] == 0.0]
        if not f0: catat(False, "hook frame 0 (OCR)", "tidak ada teks terbaca di frame 0; hook visual tanpa teks boleh, tinjau manual", True)
        else:
            w, k = max(f0, key=lambda q: q[1][4] - q[1][3]); uk = (k[4] - k[3]) / 0.72
            catat(uk >= 120, "ukuran hook (OCR)", f"{w!r} ~{uk:.0f} px; nilai keterbacaan secara visual", True)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("video"); ap.add_argument("--spek"); ap.add_argument("-o")
    ap.add_argument("--html", help="halaman sumber (setT) untuk mengukur teks sebenarnya"); ap.add_argument("--kata", help="json waktu kata (sinema/3D)"); ap.add_argument("--off", type=float, default=0.35)
    ap.add_argument("--abaikan", help="regex teks hiasan yang tidak wajib dibaca (sebutkan ke pemilik bila dipakai)"); ap.add_argument("--lufs", type=float, default=-15); ap.add_argument("--tanpa-audio", action="store_true", help="izinkan video tanpa trek audio bila memang disengaja"); a = ap.parse_args()
    out = a.o or os.path.splitext(a.video)[0] + "_periksa"; os.makedirs(out, exist_ok=True)
    H = []  # (status, butir, keterangan)
    def catat(ok, butir, ket, peringatan=False): H.append(("LOLOS" if ok else ("PERIKSA" if peringatan else "GAGAL"), butir, ket))
    if not os.path.isfile(a.video):
        catat(False, "berkas video", f"file tidak ditemukan: {a.video}")
        for st, b, k in H: print(f"{st:8} {b:24} {k}")
        sys.exit(1)
    if os.path.getsize(a.video) == 0:
        catat(False, "berkas video", "file kosong (0 byte)")
        for st, b, k in H: print(f"{st:8} {b:24} {k}")
        sys.exit(1)
    pr = jalan(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", a.video])
    try:
        p = json.loads(pr.stdout) if pr.returncode == 0 else {}
    except (json.JSONDecodeError, TypeError):
        p = {}
    if not p or not isinstance(p.get("streams"), list) or not isinstance(p.get("format"), dict):
        detail = (pr.stderr or "").strip() or "ffprobe tidak menghasilkan metadata yang valid"
        catat(False, "metadata video", detail[-700:])
        for st, b, k in H: print(f"{st:8} {b:24} {k}")
        sys.exit(1)
    v = next((s for s in p["streams"] if s.get("codec_type") == "video"), None)
    au = [s for s in p["streams"] if s.get("codec_type") == "audio"]
    if not v:
        catat(False, "stream video", "tidak ditemukan stream video yang dapat dibaca")
        for st, b, k in H: print(f"{st:8} {b:24} {k}")
        sys.exit(1)
    try:
        D = float(p["format"]["duration"])
        w, h = int(v["width"]), int(v["height"])
    except (KeyError, TypeError, ValueError):
        D, w, h = 0.0, 0, 0
    if not math.isfinite(D) or D <= 0 or w <= 0 or h <= 0:
        catat(False, "metadata video", f"durasi/resolusi tidak valid: {D}, {w}x{h}")
        for st, b, k in H: print(f"{st:8} {b:24} {k}")
        sys.exit(1)
    catat((w, h) == (1080, 1920), "ukuran", f"{w}x{h}, {D:.1f} dtk")
    # suara (butir 11)
    if au:
        e = ff("-i", a.video, "-af", "ebur128=peak=true", "-f", "null", "-")
        intens = re.findall(r"I:\s+(-?[\d.]+) LUFS", e)
        puncak = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", e)
        if intens and puncak:
            I, pk = float(intens[-1]), float(puncak[-1])
            catat(abs(I - a.lufs) <= 2, "kenyaringan", f"{I} LUFS (target acuan {a.lufs}; dinamika boleh berbeda)", True)
            catat(pk <= -1, "puncak", f"{pk} dBFS (maks -1)")
        else:
            catat(False, "analisis audio", "FFmpeg tidak menghasilkan data LUFS/true peak; pemeriksaan audio belum lengkap: " + e[-500:], True)
        # desain suara (prinsip 5): narasi saja = ada jeda benar-benar hening di antara kalimat
        e = ff("-i", a.video, "-vn", "-af", "silencedetect=noise=-45dB:d=0.25", "-f", "null", "-")
        hening = re.findall(r"silence_duration: ([\d.]+)", e)
        if "silence_start:" in e or "silence_end:" in e or "Output #0" in e:
            hn = sum(float(x) for x in hening)
            catat(hn <= 0.05 * D, "desain suara", f"hening total {hn:.1f} dtk ({hn / D:.0%} durasi; keheningan boleh disengaja)", True)
        else:
            catat(False, "analisis keheningan", "FFmpeg tidak menghasilkan data analisis keheningan; periksa audio secara manual", True)
    else: catat(False, "suara", "tidak ada trek audio; diizinkan karena --tanpa-audio" if a.tanpa_audio else "tidak ada trek suara", a.tanpa_audio)
    # diam > 3 dtk dan layar hitam (butir 6)
    e = ff("-i", a.video, "-vf", "scale=270:-1,freezedetect=n=0.003:d=3", "-map", "0:v", "-f", "null", "-")
    fz = [(float(x), float(y)) for x, y in zip(re.findall(r"freeze_start: ([\d.]+)", e), re.findall(r"freeze_duration: ([\d.]+)", e))]
    catat(not fz, "freeze >3 dtk", ", ".join(f"{s:.1f}s (+{d:.1f})" for s, d in fz) or "tidak ada; shot tenang bisa disengaja", True)
    e = ff("-i", a.video, "-vf", "blackdetect=d=0.4:pix_th=0.06", "-map", "0:v", "-f", "null", "-")
    bl = re.findall(r"black_start:([\d.]+)", e)
    catat(not bl, "layar hitam", ", ".join(bl) or "tidak ada", True)
    dom = ukur_html(a, D, out, catat) if a.html else None
    if not a.html:
        catat(False, "teks halaman", "tidak ada --html: teks hanya diukur lewat OCR (kurang teliti). Papan/cerita: papan_buat.py spek --html x.html; sinema: html + --kata", True)
    ocr_video(a, D, out, catat, dom)
    # lembar untuk dilihat
    n = max(1, int(D // 2) + 1); kol = min(n, 10); bar = -(-n // kol)
    kontak = [
        ("lembar.jpg", ["-i", a.video, "-vf", f"fps=1/2,scale=216:-1,tile={kol}x{bar}", "-frames:v", "1"]),
        ("awal.jpg", ["-t", "3", "-i", a.video, "-vf", "fps=10,scale=216:-1,tile=10x3", "-frames:v", "1"]),
        ("kecil.jpg", ["-i", a.video, "-frames:v", "1", "-vf", "scale=270:-1"]),
    ]
    for nama, argumen in kontak:
        target = os.path.join(out, nama)
        hasil = jalan(["ffmpeg", "-y", "-hide_banner", "-nostdin", *argumen, target])
        if hasil.returncode != 0 or not os.path.isfile(target) or os.path.getsize(target) == 0:
            catat(False, "lembar pemeriksaan", f"gagal membuat {nama}; pemeriksaan visual manual belum tersedia: {hasil.stderr[-400:]}", True)
    # spek (butir 10, 12)
    if a.spek:
        sp = json.load(open(a.spek)); pjg = []
        for it in (sp.get("cerita") or {}).get("tengah") or []:
            if len(it.get("kata", [])) > 4: pjg.append(f"tengah t0={it.get('t0')} ({len(it['kata'])} kata)")
        for it in sp.get("subtitle") or []:
            tk = it[2] if isinstance(it, list) else it.get("teks", "")
            if len(str(tk).split()) > 4: pjg.append(f"subtitle {str(tk)[:28]!r}")
        ada = (bool(sp.get("rekaman")) or bool(sp.get("efek_suara")) or sp.get("musik") not in (None, False) or
               any(bool(it.get("sfx")) or bool(it.get("audio")) for it in sp.get("adegan", [])))
        catat(ada, "desain suara di spek", "ada musik/audio/efek pada spesifikasi" if ada else "tidak ada musik/audio/efek eksplisit; bisa disengaja, dengarkan hasilnya", True)
        catat("watermark" not in sp, "watermark", "tidak dipakai" if "watermark" not in sp else "spek masih memakai watermark")
        # narasi tertutup efek (16 Nov): saat narator bicara, campuran tidak boleh > 6 dB di atas kebiasaannya terhadap narasi
        if sp.get("suara") and au:
            nar = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(a.spek)), sp["suara"]))
            if os.path.exists(nar):
                def ml(f):
                    e2 = ff("-i", f, "-vn", "-af", "ebur128", "-f", "null", "-")
                    return {round(float(x), 1): float(m) for x, m in re.findall(r"t:\s*([\d.]+)\s+TARGET:\S+ LUFS\s+M:\s*(-?[\d.]+)", e2)}
                mx, nr = ml(a.video), ml(nar)
                dd = [(x, mx[x] - nr[x]) for x in sorted(nr) if x in mx and nr[x] > -30]
                if dd:
                    med = sorted(v2 for _, v2 in dd)[len(dd) // 2]; seg = []
                    for x, v2 in dd:
                        if v2 > med + 6:
                            if seg and x - seg[-1][1] <= 0.6: seg[-1][1] = x
                            else: seg.append([x, x])
                    catat(not seg, "narasi tertutup efek", ", ".join(f"{s0:.1f}-{s1:.1f}s" for s0, s1 in seg) + " (efek > 6 dB di atas narasi saat narator bicara: geser ke jeda atau kecilkan)" if seg else "tidak ada", True)
        catat(not pjg, "subtitle > 4 kata", "; ".join(pjg[:6]) + (f" (+{len(pjg) - 6})" if len(pjg) > 6 else "") if pjg else "tidak ada; panjang subtitle fleksibel", True)
    for st, b, k in H: print(f"{st:8} {b:24} {k}")
    print(f"BUKA DAN LIHAT: {out}/lembar.jpg (seluruh video), awal.jpg (3 dtk pertama), kecil.jpg (frame 0 lebar 270)")
    sys.exit(1 if any(s == "GAGAL" for s, _, _ in H) else 0)

if __name__ == "__main__": main()
