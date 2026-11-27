"""Uji visual dan geometri serah-terima benda antartokoh.

Menuntut kedua tangan mengikuti satu lintasan benda yang sama selama perpindahan.
Jarak tangan ke titik genggam harus <= 14 px pada setiap sampel.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from uji_tokoh import LEBAR, TINGGI, TOKOH, render


BATAS_TANGAN = 14.0
WAKTU = [0.5, 0.6, 0.9, 1.3, 1.7, 2.0, 2.1]


def jarak(a, b):
    return math.dist(a, b)


def buat_spek(benda: str = 'surat'):
    pemberi = {**TOKOH, "id": 0, "x": 400, "y": 1700, "s": 0.8, "pose": f"pegang_{benda}", "profil": "kanan"}
    penerima = {**TOKOH, "id": 1, "x": 580, "y": 1700, "s": 0.8, "pose": "berdiri", "profil": "kiri"}
    return {
        "latar": "gelap", "musik": False, "stempel": False, "dekor": False, "durasi": 2.4,
        "cerita": {"shot": [{
            "at": 0, "horizon": 1900, "palet": "siang", "debu": 0,
            "boneka": [pemberi, penerima],
            "serah_terima": {"dari": 0, "ke": 1, "benda": benda, "at": 0.5,
                             "durasi": 1.6, "skala": 0.48},
        }]},
    }


def uji(keluaran: Path, chrome: str | None = None) -> dict:
    keluaran.mkdir(parents=True, exist_ok=True)
    gambar = render(buat_spek("surat"), WAKTU, keluaran, "serah_terima", chrome, ambil_serah=True)
    temuan = []
    bukti = []
    for png, _, catatan in gambar:
        if len(catatan) != 1:
            temuan.append({"kode": "SERAH_DATA_HILANG", "pesan": "catatan lintasan tidak tersedia"})
            continue
        c = catatan[0]
        if not c.get("grafis"):
            temuan.append({"kode": "BENDA_TIDAK_TERGAMBAR", "t": c["t"], "benda": c.get("benda")})
        fase = float(c.get("fase", 0))
        peran_aktif = (("tangan_pemberi",) if fase < 0.25 else
                       ("tangan_pemberi", "tangan_penerima") if fase <= 0.75 else
                       ("tangan_penerima",))
        for peran in peran_aktif:
            tangan = c.get(peran)
            if tangan is None:
                temuan.append({"kode": "TANGAN_TIDAK_TERCATAT", "t": c["t"], "peran": peran})
                continue
            galat = jarak(tangan, c["posisi"])
            bukti.append({"t": c["t"], "fase": fase, "peran": peran, "jarak_px": round(galat, 3),
                          "tangan": tangan, "benda": c["posisi"]})
            if galat > BATAS_TANGAN:
                temuan.append({"kode": "TANGAN_TIDAK_MENEMPEL", "t": c["t"], "peran": peran,
                               "jarak_px": round(galat, 3), "batas_px": BATAS_TANGAN})
    target_bukti = sum(1 if ((t - 0.5) / 1.6) < 0.25 or ((t - 0.5) / 1.6) > 0.75
                       else 2 for t in WAKTU)
    if len(bukti) != target_bukti:
        temuan.append({"kode": "SAMPEL_TIDAK_LENGKAP", "jumlah": len(bukti), "target": target_bukti})
    posisi_awal = gambar[0][2][0]["posisi"] if gambar and gambar[0][2] else None
    posisi_akhir = gambar[-1][2][0]["posisi"] if gambar and gambar[-1][2] else None
    perpindahan = jarak(posisi_awal, posisi_akhir) if posisi_awal and posisi_akhir else 0
    if perpindahan < 20:
        temuan.append({"kode": "BENDA_TIDAK_BERPINDah", "jarak_px": round(perpindahan, 2)})
    from io import BytesIO
    from PIL import Image, ImageDraw, ImageFont

    variasi = []
    gambar_variasi = []
    for jenis in ("surat", "kendi", "gelas", "karung_kecil", "gulungan", "roti", "koin"):
        if jenis == "surat":
            png, _, catatan = gambar[3]
        else:
            [hasil_variasi] = render(buat_spek(jenis), [1.3], keluaran, f"serah_{jenis}", chrome, ambil_serah=True)
            png, _, catatan = hasil_variasi
        c = catatan[0] if catatan else {}
        jarak_variasi = [jarak(c.get(k) or [0, 0], c.get("posisi") or [0, 0])
                         for k in ("tangan_pemberi", "tangan_penerima")]
        maks = max(jarak_variasi, default=float("inf"))
        lulus_variasi = bool(c.get("grafis")) and maks <= BATAS_TANGAN
        variasi.append({"benda": jenis, "grafis": bool(c.get("grafis")), "jarak_tangan_maks_px": round(maks, 3),
                        "lulus": lulus_variasi})
        if not lulus_variasi:
            temuan.append({"kode": "VARIASI_BENDA_GAGAL", "benda": jenis,
                           "jarak_tangan_maks_px": round(maks, 3), "grafis": bool(c.get("grafis"))})
        gambar_variasi.append(png)

    w, h = LEBAR // 3, TINGGI // 3
    kanvas = Image.new("RGB", (w * len(gambar), h + 42), "white")
    d = ImageDraw.Draw(kanvas)
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 20)
    except OSError:
        font = ImageFont.load_default()
    for i, (png, _, catatan) in enumerate(gambar):
        kanvas.paste(Image.open(BytesIO(png)).convert("RGB").resize((w, h)), (w * i, 42))
        d.text((w * i + 8, 10), f"t={WAKTU[i]:.1f}s", font=font, fill="black")
    kanvas.save(keluaran / "lembar_serah_terima.png")
    lembar_variasi = Image.new("RGB", (w * len(gambar_variasi), h + 42), "white")
    d_variasi = ImageDraw.Draw(lembar_variasi)
    for i, (png, variasi_item) in enumerate(zip(gambar_variasi, variasi)):
        lembar_variasi.paste(Image.open(BytesIO(png)).convert("RGB").resize((w, h)), (w * i, 42))
        d_variasi.text((w * i + 8, 10), variasi_item["benda"], font=font, fill="black")
    lembar_variasi.save(keluaran / "lembar_variasi_benda.png")
    laporan = {"lulus": not temuan, "batas_tangan_px": BATAS_TANGAN, "jumlah_sampel": len(WAKTU),
               "perpindahan_px": round(perpindahan, 2), "variasi_benda": variasi,
               "bukti": bukti, "temuan": temuan}
    (keluaran / "laporan_serah_terima.json").write_text(
        json.dumps(laporan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(laporan, ensure_ascii=False))
    return laporan


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("-o", "--keluaran", default="hasil/uji_interaksi")
    ap.add_argument("--chrome")
    args = ap.parse_args(argv)
    return 0 if uji(Path(args.keluaran), args.chrome)["lulus"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
