"""Buat lembar bukti dua keadaan untuk pustaka benda baru (tanpa MP4/TTS)."""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

AKAR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(AKAR / "mesin-video"))
sys.path.insert(0, str(AKAR))

BARU = {
    "tenda_badui": ("buka", 0, 1), "sumur": ("air", 0, 1),
    "kebun_kurma": ("buah", 0, 1), "ladang_gandum": ("matang", 0, 1),
    "sungai": ("arus", 0, 1), "perahu_kecil": ("goyang", 0, 1),
    "lentera": ("nyala", 0, 1), "api_unggun": ("nyala", 0, 1),
    "pintu_kota_kuno": ("buka", 0, 1), "karung": ("penuh", 0, 1),
    "keranjang": ("penuh", 0, 1), "kambing": ("jalan", 0, 1),
    "domba": ("jalan", 0, 1), "burung_kawanan": ("terbang", 0, 1),
    "ular_siluet": ("gerak", 0, 1), "kapal_dagang": ("muatan", 0, 1),
    "menara_pengawas": ("penjaga", 0, 1), "rak_kitab": ("isi", 0, 1),
    "jam_pasir": ("sisa", 0, 1), "rantai_belenggu": ("tegang", 0, 1),
    "pedang_tersarung": ("ornamen", 0, 1), "awan_badai": ("hujan", 0, 1),
    "kios_pasar": ("dagangan", 0, 1), "awan_gelap": ("kilat", 0, 1),
}
DURASI = 3.0
LEBAR, TINGGI = 1080, 1920


def main() -> int:
    from papan_buat import buat_html
    from playwright.sync_api import sync_playwright

    daftar = sorted(BARU)
    shot = []
    for i, nama in enumerate(daftar):
        param, awal, akhir = BARU[nama]
        shot.append({
            "at": i * DURASI, "horizon": 1990, "palet": "pagi", "debu": 0,
            "langit": 0, "kamera": {"z": 1, "x": 540, "y": 960},
            "benda": [{"jenis": nama, "x": 540, "y": 1500, "s": 0.72, param: [awal, akhir]}],
        })
    spek = {"latar": "gelap", "musik": False, "stempel": False, "dekor": False,
            "durasi": DURASI * len(shot), "cerita": {"shot": shot}}
    html = AKAR / "hasil_lembar_benda_baru.html"
    html.write_text(buat_html(spek, str(AKAR / "mesin-video" / "papan"), sudah_dijaga=True), encoding="utf-8")
    ubin = []
    with sync_playwright() as p:
        br = p.chromium.launch()
        pg = br.new_page(viewport={"width": LEBAR, "height": TINGGI}, device_scale_factor=1)
        pg.goto("file://" + str(html))
        pg.wait_for_timeout(500)
        for i, nama in enumerate(daftar):
            panel = []
            for offset in (0.6, 2.8):
                pg.evaluate(f"setT({i * DURASI + offset})")
                mentah = pg.screenshot()
                gambar = Image.open(io.BytesIO(mentah)).convert("RGB")
                panel.append(gambar.crop((140, 900, 940, 1700)).resize((240, 240)))
            ubin.append((nama, panel))
        br.close()
    html.unlink(missing_ok=True)

    kolom, baris = 4, (len(ubin) + 3) // 4
    kanvas = Image.new("RGB", (kolom * 500, baris * 285), "#f3eee5")
    gambar = ImageDraw.Draw(kanvas)
    font = ImageFont.load_default()
    for i, (nama, panel) in enumerate(ubin):
        x, y = (i % kolom) * 500, (i // kolom) * 285
        gambar.text((x + 8, y + 5), nama, fill="#17130f", font=font)
        kanvas.paste(panel[0], (x + 5, y + 28))
        kanvas.paste(panel[1], (x + 250, y + 28))
        gambar.text((x + 5, y + 270), "awal", fill="#17130f", font=font)
        gambar.text((x + 250, y + 270), "akhir", fill="#17130f", font=font)
    keluar = AKAR / "hasil" / "pustaka-benda-baru.png"
    keluar.parent.mkdir(parents=True, exist_ok=True)
    kanvas.save(keluar)
    print(f"{len(ubin)} benda, dua keadaan: {keluar}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
