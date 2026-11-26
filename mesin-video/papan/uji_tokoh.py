"""Lembar uji tokoh: ukuran "bagus" untuk renderer boneka bersendi di cerita.js.

Merender setiap pose/aksi dari beberapa sudut lewat jalur yang sama dengan video
(papan_buat.buat_html + cerita.js di Chromium), lalu:

  Lapis A (otomatis, dari kait window.__catatBoneka di cerita.js)
    A1 panjang tulang tetap      paha, betis, lengan atas, lengan bawah tidak memanjang/memendek
    A2 kaki menapak              pose berdiri: telapak terendah di garis tanah (bukan melayang/tenggelam)
    A3 arah searah               kepala, badan, dan kaki menghadap sudut yang sama
    A4 bagian per sudut          jumlah telinga sesuai sudut (depan/belakang 2, samping 1)
    A5 gerak tanpa loncatan      aksi berulang: sendi tidak meloncat jauh antar-frame 30 fps
    A6 menempel di benda         tokoh berkait (motor, jok mobil, kursi...): tangan di pegangan, kaki di
                                 pijakan (<= 14 px), badan tampak samping bila benda tampak samping
  Lapis B/C (mata)
    lembar_pose_*.png  pose x sudut      lembar_gerak.png  siklus aksi per waktu
    versi *_kecil.png  ukuran layar HP (keterbacaan)

Pemakaian (dari akar repo):
  python mesin-video/papan/uji_tokoh.py -o hasil/uji_tokoh
  python mesin-video/papan/uji_tokoh.py -o hasil/uji_tokoh --chrome /usr/bin/google-chrome
Hasil: lembar PNG, laporan.json, laporan.md. Kode keluar 0 kecuali --ketat dan ada temuan A.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

AKAR = Path(__file__).resolve().parents[2]
PAPAN = AKAR / "mesin-video" / "papan"
sys.path.insert(0, str(AKAR / "mesin-video"))

# Sudut yang wajib bisa digambar renderer. Nilai = kunci boneka yang dipakai cerita.js saat ini.
# "tiga_perempat" sementara memakai `arah` (hanya kepala menoleh) karena badan 3/4 belum ada;
# "samping_kiri" belum didukung renderer sama sekali -- dibiarkan agar kekurangannya terlihat.
SUDUT = [
    ("depan", {}),
    ("tiga_perempat", {"arah": 0.8}),
    ("samping", {"profil": "kanan"}),
    ("samping_kiri", {"profil": "kiri"}),
    ("belakang", {"belakang": True}),
]
TELINGA_HARUS = {"depan": 2, "tiga_perempat": 2, "samping": 1, "samping_kiri": 1, "belakang": 2}
BADAN_HARUS = {"depan": "depan", "tiga_perempat": "depan", "samping": "samping",
               "samping_kiri": "samping", "belakang": "belakang"}

# Pose yang memang tidak berdiri di tanah dengan dua kaki (A2 tidak berlaku).
TIDAK_MENAPAK = {"duduk", "duduk_tutup_wajah", "duduk_hp", "rebahan", "rebahan_hp", "peluk_lutut",
                 "mengendarai_motor", "lompat", "tergelincir", "bangkit", "lari"}  # lari & lompat: fase melayang wajar
AKSI_UJI = ["jalan", "lari", "gali", "palu", "joget", "lompat", "melambai", "menggeleng", "mengangguk", "tertawa"]

TOKOH = {"gaya": "umum", "kulit": "#d9b48c", "rambut": "pendek", "warna_rambut": "#2a1c18",
         "pakaian": {"jenis": "kaus", "warna": "#3f7890", "bawah": "celana", "bawah_warna": "#34445a"},
         "wajah": "netral", "mata": "buka", "hidup": False, "bayangan": False}
KOLOM, BARIS = 5, 4
LEBAR, TINGGI = 1080, 1920
SKALA = 0.30


def daftar_pose(sumber: str) -> list[str]:
    """Nama pose badan dari objek POSE di cerita.js (urutan asli, tanpa duplikat)."""
    awal = sumber.index("const POSE = {")
    blok = sumber[awal: sumber.index("\n  };", awal)]
    nama = re.findall(r"^\s{4}(\w+): \{", blok, re.M)
    return list(dict.fromkeys(nama))


def _sel(i: int, j: int) -> tuple[int, int]:
    lebar_sel, tinggi_sel = LEBAR // KOLOM, (TINGGI - 120) // BARIS
    return lebar_sel * j + lebar_sel // 2, 120 + tinggi_sel * (i + 1) - 60


def spek_lembar(baris: list[tuple[str, list[tuple[str, dict]]]], durasi: float) -> dict:
    """Satu shot berisi kisi boneka: baris = (label, [(label_kolom, kunci_boneka)])."""
    boneka, nomor = [], 0  # cerita.js menomori boneka 0.. sesuai urutan; label memakai urutan yang sama
    for i, (_, kolom) in enumerate(baris):
        for j, (_, kunci) in enumerate(kolom):
            x, y = _sel(i, j)
            boneka.append({**json.loads(json.dumps(TOKOH)), **kunci, "id": nomor, "x": x, "y": y, "s": SKALA})
            nomor += 1
    return {"latar": "gelap", "musik": False, "stempel": False, "dekor": False, "durasi": durasi,
            "cerita": {"shot": [{"at": 0, "horizon": 1990, "langit": 0.35, "debu": 0, "palet": "pagi", "malam": 0,
                                 "kamera": {"z": 1, "x": 540, "y": 960}, "boneka": boneka}]}}


def render(spek: dict, waktu: list[float], kerja: Path, nama: str, chrome: str | None):
    """Render spek pada beberapa detik. Kembalikan [(png_bytes, catatan_boneka)] per waktu."""
    from papan_buat import buat_html
    from playwright.sync_api import sync_playwright

    html = buat_html(json.loads(json.dumps(spek)), str(PAPAN))
    berkas = kerja / f"{nama}.html"
    berkas.write_text(html, encoding="utf-8")
    hasil = []
    with sync_playwright() as p:
        opsi = {"executable_path": chrome, "args": ["--no-sandbox"]} if chrome else {}
        br = p.chromium.launch(**opsi)
        pg = br.new_page(viewport={"width": LEBAR, "height": TINGGI})
        pg.goto("file://" + str(berkas.resolve()))
        pg.evaluate("document.fonts.ready")
        pg.wait_for_timeout(300)
        for t in waktu:
            pg.evaluate("window.__catatBoneka = []")
            pg.evaluate(f"setT({t:.4f})")
            catatan = pg.evaluate("window.__catatBoneka")
            hasil.append((pg.screenshot(type="png"), catatan))
        br.close()
    return hasil


def beri_label(png: bytes, baris, judul: str, tujuan: Path) -> None:
    from io import BytesIO

    from PIL import Image, ImageDraw, ImageFont

    img = Image.open(BytesIO(png)).convert("RGB")
    d = ImageDraw.Draw(img)
    try:
        f = ImageFont.truetype("DejaVuSans-Bold.ttf", 26)
        fk = ImageFont.truetype("DejaVuSans.ttf", 22)
    except OSError:
        f = fk = ImageFont.load_default()
    d.rectangle([0, 0, LEBAR, 110], fill="#101018")
    d.text((20, 12), judul, font=f, fill="#ffffff")
    for j, (lk, _) in enumerate(baris[0][1]):
        x, _ = _sel(0, j)
        d.text((x - 100, 66), lk, font=fk, fill="#ffd27a")
    for i, (lb, _) in enumerate(baris):
        _, y = _sel(i, 0)
        d.text((10, y + 18), lb, font=fk, fill="#ffffff")
    img.save(tujuan)
    kecil = img.resize((LEBAR // 4, TINGGI // 4))
    kecil.save(tujuan.with_name(tujuan.stem + "_kecil.png"))


# Adegan titik kait: tokoh menempel di benda (kendaraan & perabot). (nama, shot, sudut harus)
TOKOH_KAIT = {k: v for k, v in TOKOH.items() if k != "bayangan"}
ADEGAN_KAIT = [
    ("motor", {"horizon": 1300, "palet": "siang", "benda": [{"jenis": "motor", "id": "m", "x": 540, "y": 1650, "s": 1.4}],
               "boneka": [{**TOKOH_KAIT, "kait": "m"}]}, "samping"),
    ("motor arah kiri", {"horizon": 1300, "palet": "siang",
                         "benda": [{"jenis": "motor", "id": "m", "x": 540, "y": 1650, "s": 1.4, "arah": -1}],
                         "boneka": [{**TOKOH_KAIT, "kait": "m"}]}, "samping"),
    ("mobil", {"ruang": {"jenis": "mobil", "waktu": "sore"},
                                   "benda": [{"jenis": "setir", "x": 900, "y": 1200, "s": 1}],
                                   "boneka": [{**TOKOH_KAIT, "kait": "jok_depan"}, {**TOKOH_KAIT, "kait": "jok_belakang"}]}, "samping"),
    ("kursi", {"ruang": {"jenis": "tamu"}, "benda": [{"jenis": "kursi", "id": "k", "x": 540, "y": 1700, "s": 1.2}],
               "boneka": [{**TOKOH_KAIT, "kait": "k"}]}, "depan"),
    ("sofa", {"ruang": {"jenis": "tamu"}, "benda": [{"jenis": "sofa", "id": "f", "x": 540, "y": 1700, "s": 1.1}],
              "boneka": [{**TOKOH_KAIT, "kait": "f"}]}, "depan"),
]
BATAS_KAIT = 14.0


def periksa_kait(catatan: list[dict], nama: str, sudut: str) -> list[dict]:
    """A6: tokoh berkait menempel di benda dan sudutnya mengikuti benda."""
    temuan = []
    for c in catatan:
        tambah = lambda kode, pesan: temuan.append({"kode": kode, "pose": nama, "sudut": sudut, "t": c["t"], "pesan": pesan})  # noqa: E731
        g = c.get("kait_galat")
        if sudut == "samping":
            if not g:
                tambah("A6_TIDAK_MENEMPEL", "tokoh tidak menerima titik kait benda")
                continue
            for bagian in ("pegang", "pijak"):
                if g.get(bagian) is not None and g[bagian] > BATAS_KAIT:
                    tambah("A6_TIDAK_MENEMPEL", f"{bagian} meleset {g[bagian]:.0f}px dari titik kait")
            if not c.get("badan_samping"):
                tambah("A6_SUDUT_BEDA", "benda tampak samping tetapi badan tokoh tampak depan")
    return temuan


def uji_kait(out: Path, chrome: str | None) -> list[dict]:
    spek = {"latar": "gelap", "musik": False, "stempel": False, "dekor": False, "durasi": 2 * len(ADEGAN_KAIT),
            "cerita": {"shot": [{"at": 2 * i, "debu": 0, **shot} for i, (_, shot, _) in enumerate(ADEGAN_KAIT)]}}
    gambar = render(spek, [2 * i + 1 for i in range(len(ADEGAN_KAIT))], out, "kait", chrome)
    temuan = []
    from io import BytesIO

    from PIL import Image, ImageDraw, ImageFont
    w, h = LEBAR // 4, TINGGI // 4
    kanvas = Image.new("RGB", (w * len(gambar), h + 40), "white")
    d = ImageDraw.Draw(kanvas)
    try:
        f = ImageFont.truetype("DejaVuSans-Bold.ttf", 20)
    except OSError:
        f = ImageFont.load_default()
    for i, ((png, catatan), (nama, _, sudut)) in enumerate(zip(gambar, ADEGAN_KAIT)):
        temuan += periksa_kait(catatan, nama, sudut)
        kanvas.paste(Image.open(BytesIO(png)).convert("RGB").resize((w, h)), (w * i, 40))
        d.text((w * i + 8, 10), nama, font=f, fill="black")
    kanvas.save(out / "lembar_kait.png")
    return temuan


# ---------------- lapis A ----------------
def _jarak(a, b) -> float:
    return math.dist(a, b)


def tulang(c: dict) -> dict[str, list[float]]:
    s = c.get("sendi") or {}
    hasil: dict[str, list[float]] = {"paha": [], "betis": [], "lengan_atas": [], "lengan_bawah": []}
    for kaki in s.get("kaki") or []:
        H, K, F = kaki
        hasil["paha"].append(_jarak(H, K))
        hasil["betis"].append(_jarak(K, F))
    for S, E, Hn in s.get("lengan") or []:
        hasil["lengan_atas"].append(_jarak(S, E))
        hasil["lengan_bawah"].append(_jarak(E, Hn))
    return hasil


def periksa(catatan: list[dict], label: dict[int, tuple[str, str]], acuan: dict[str, float]) -> list[dict]:
    """A1-A4 untuk satu waktu. label: id boneka -> (pose, sudut)."""
    temuan = []
    for c in catatan:
        pose, sudut = label.get(c["id"], ("?", "?"))
        tambah = lambda kode, pesan: temuan.append({"kode": kode, "pose": pose, "sudut": sudut, "t": c["t"], "pesan": pesan})  # noqa: E731
        if not c.get("rig"):
            tambah("A0_TANPA_RANGKA", "boneka digambar tanpa rangka bersendi; geometri tidak bisa diuji")
            continue
        # Pemendekan karena anggota badan mengayun ke arah/menjauhi kamera adalah benar secara
        # anatomi pada sudut depan/tiga perempat/belakang; panjang 2D hanya dituntut tetap pada
        # sudut samping (gerak sebidang layar) dan pada pose diam.
        boleh_pendek = pose in AKSI_UJI and sudut not in ("samping", "samping_kiri")
        for nama, nilai in ({} if boleh_pendek else tulang(c)).items():
            for v in nilai:
                if acuan.get(nama) and abs(v / acuan[nama] - 1) > 0.03:
                    tambah("A1_PANJANG_TULANG", f"{nama} {v:.0f}px, acuan {acuan[nama]:.0f}px")
                    break
        kaki = (c.get("sendi") or {}).get("kaki") or []
        if kaki and pose not in TIDAK_MENAPAK and not c.get("guling"):
            terendah = max(F[1] for _, _, F in kaki)
            if abs(terendah) > 8:
                tambah("A2_KAKI_MENAPAK", f"telapak terendah {terendah:+.0f}px dari tanah ({'melayang' if terendah < 0 else 'tenggelam'})")
        kepala = "samping" if c.get("profil") else ("belakang" if c.get("belakang") else "depan")
        badan = "samping" if c.get("badan_samping") else "depan"
        harus = BADAN_HARUS.get(sudut, "depan")
        if harus == "samping" and badan != "samping":
            tambah("A3_ARAH_TIDAK_SEARAH", f"kepala {kepala}, badan & kaki {badan}")
        if sudut == "samping_kiri" and c.get("profil") not in (None, "kanan", True):
            tambah("A3_SUDUT_TIDAK_DIDUKUNG", f"profil {c.get('profil')!r} tidak dikenal renderer")
        harus_telinga = TELINGA_HARUS.get(sudut)
        if harus_telinga is not None and c.get("telinga") != harus_telinga:
            tambah("A4_BAGIAN_SUDUT", f"telinga {c.get('telinga')}, seharusnya {harus_telinga}")
    return temuan


def periksa_loncatan(urutan: list[list[dict]], label, ambang: float = 35.0) -> list[dict]:
    """A5: gerak sendi tanpa patahan. Yang diukur perubahan kecepatan antar-frame
    (|p[t+1] - 2 p[t] + p[t-1]|, px pada skala 1, 30 fps), bukan kecepatan: gerak cepat
    yang mulus (lompat, ayunan palu) lolos, sendi yang tiba-tiba berpindah tertangkap."""
    temuan, riwayat = [], {}
    for catatan in urutan:
        for c in catatan:
            s = c.get("sendi")
            if not s:
                continue
            titik = [p for kaki in s["kaki"] for p in kaki] + [p for l in s["lengan"] for p in l]
            lalu = riwayat.setdefault(c["id"], [])
            if len(lalu) == 2:
                p0, p1 = lalu
                patah = max(math.hypot(c2[0] - 2 * b[0] + a[0], c2[1] - 2 * b[1] + a[1])
                            for a, b, c2 in zip(p0, p1, titik))
                if patah > ambang:
                    pose, sudut = label[c["id"]]
                    temuan.append({"kode": "A5_LONCATAN", "pose": pose, "sudut": sudut, "t": c["t"],
                                   "pesan": f"gerak sendi patah {patah:.0f}px dalam 1 frame"})
            riwayat[c["id"]] = (lalu + [titik])[-2:]
    return temuan


def ringkas(temuan: list[dict]) -> dict:
    hasil: dict[str, dict] = {}
    for x in temuan:
        k = hasil.setdefault(x["kode"], {"jumlah": 0, "contoh": [], "pose_sudut": set()})
        k["jumlah"] += 1
        k["pose_sudut"].add(f"{x['pose']}/{x['sudut']}")
        if len(k["contoh"]) < 5:
            k["contoh"].append(f"{x['pose']}/{x['sudut']} t={x['t']:.2f}: {x['pesan']}")
    for k in hasil.values():
        k["pose_sudut"] = len(k["pose_sudut"])
    return hasil


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("-o", "--keluaran", default="hasil/uji_tokoh")
    ap.add_argument("--chrome", help="path Chrome bila Chromium Playwright tidak terpasang")
    ap.add_argument("--ketat", action="store_true", help="keluar 1 bila ada temuan lapis A")
    args = ap.parse_args(argv)
    out = Path(args.keluaran)
    out.mkdir(parents=True, exist_ok=True)

    pose_semua = daftar_pose((PAPAN / "cerita.js").read_text(encoding="utf-8"))
    temuan: list[dict] = []
    acuan: dict[str, float] = {}

    # lembar pose x sudut (t=1,5 dtk: transisi pose sudah selesai)
    halaman = [pose_semua[i:i + BARIS] for i in range(0, len(pose_semua), BARIS)]
    for h, kelompok in enumerate(halaman, 1):
        baris = [(pose, [(sudut, {**kunci, "pose": pose}) for sudut, kunci in SUDUT]) for pose in kelompok]
        label = {}
        nomor = 0
        for pose, kolom in baris:
            for sudut, _ in kolom:
                label[nomor] = (pose, sudut)
                nomor += 1
        [(png, catatan)] = render(spek_lembar(baris, 3), [1.5], out, f"pose_{h}", args.chrome)
        if not acuan:
            dasar = next(c for c in catatan if label[c["id"]] == ("berdiri", "depan"))
            acuan = {k: v[0] for k, v in tulang(dasar).items() if v}
        temuan += periksa(catatan, label, acuan)
        beri_label(png, baris, f"Lembar uji tokoh — pose {h}/{len(halaman)} (t=1,5 dtk)", out / f"lembar_pose_{h}.png")

    # lembar gerak: aksi berulang x waktu, sudut depan dan samping
    fase = [0.0, 0.12, 0.24, 0.36, 0.48]
    for sudut in ("depan", "samping"):
        kunci_sudut = dict(SUDUT)[sudut]
        for h in range(0, len(AKSI_UJI), BARIS):
            aksi = AKSI_UJI[h:h + BARIS]
            baris = [(a, [(f"+{f:.2f}s", {**kunci_sudut, "pose": a}) for f in fase]) for a in aksi]
            label = {}
            nomor = 0
            for a, kolom in baris:
                for _ in kolom:
                    label[nomor] = (a, sudut)
                    nomor += 1
            # setiap kolom digeser waktunya lewat fase: render beberapa waktu dan ambil kolom yang sesuai
            waktu = [2.0 + i / 30 for i in range(int(0.5 * 30) + 1)]
            gambar = render(spek_lembar(baris, 4), waktu, out, f"gerak_{sudut}_{h}", args.chrome)
            urutan = [[c for c in catatan if c["id"] % KOLOM == 0] for _, catatan in gambar]
            temuan += periksa_loncatan(urutan, label)
            for _, catatan in gambar:
                temuan += [x for x in periksa(catatan, label, acuan) if x["kode"] != "A2_KAKI_MENAPAK" or x["pose"] not in TIDAK_MENAPAK]
            # lembar: kolom j diambil dari frame pada fase j
            from io import BytesIO

            from PIL import Image
            kanvas = Image.open(BytesIO(gambar[0][0])).convert("RGB")
            lebar_sel = LEBAR // KOLOM
            for j, f in enumerate(fase):
                k = min(len(gambar) - 1, round(f * 30))
                potong = Image.open(BytesIO(gambar[k][0])).convert("RGB").crop((lebar_sel * j, 0, lebar_sel * (j + 1), TINGGI))
                kanvas.paste(potong, (lebar_sel * j, 0))
            buf = BytesIO()
            kanvas.save(buf, format="PNG")
            beri_label(buf.getvalue(), baris, f"Lembar gerak — sudut {sudut}", out / f"lembar_gerak_{sudut}_{h // BARIS + 1}.png")

    temuan += uji_kait(out, args.chrome)

    ring = ringkas(temuan)
    (out / "laporan.json").write_text(json.dumps({"acuan_tulang": acuan, "ringkasan": ring, "temuan": temuan},
                                                 ensure_ascii=False, indent=1), encoding="utf-8")
    md = ["# Laporan uji tokoh", "", f"Pose diuji: {len(pose_semua)}; sudut: {', '.join(s for s, _ in SUDUT)}; aksi: {', '.join(AKSI_UJI)}", ""]
    if not ring:
        md.append("Lapis A: tidak ada temuan.")
    for kode, r in sorted(ring.items()):
        md.append(f"- **{kode}**: {r['jumlah']} temuan pada {r['pose_sudut']} pose/sudut")
        md += [f"  - {c}" for c in r["contoh"]]
    (out / "laporan.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))
    return 1 if args.ketat and ring else 0


if __name__ == "__main__":
    raise SystemExit(main())
