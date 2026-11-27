"""Lembar bukti Tugas 6: empat konsep abstrak, dua keadaan, ukuran seperempat layar."""
from __future__ import annotations

import io
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

AKAR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(AKAR / "mesin-video"))
sys.path.insert(0, str(AKAR))

KONSEP = {
    "genangan_tubuh": ("tinggi", 35, 440, "riak", 0.2, 1),
    "resapan_tanah": ("kedalaman", 0.2, 1, "alir", 0.2, 1),
    "naungan_kelompok": ("luas", 0.25, 1, "kuat", 0.25, 1),
    "timbangan": ("miring", -18, 18, None, None, None),
}
LEBAR, TINGGI = 1080, 1920


def main() -> int:
    from papan_buat import buat_html
    from playwright.sync_api import sync_playwright

    shot = []
    for i, (nama, (param, awal, akhir, param2, awal2, akhir2)) in enumerate(KONSEP.items()):
        for j, q in enumerate((0, 1)):
            keadaan = {param: awal if q == 0 else akhir}
            if param2:
                keadaan[param2] = awal2 if q == 0 else akhir2
            shot.append({
                "at": (i * 2 + j) * 3.0, "horizon": 1990, "debu": 0,
                "kamera": {"z": 1, "x": 540, "y": 960},
                "benda": [{"jenis": nama, "x": 540,
                           "y": 1050 if nama in {"naungan_kelompok", "resapan_tanah"} else 1450,
                           "s": 0.78 if nama == "naungan_kelompok" else 0.95, **keadaan}],
            })
    spek = {"latar": "gelap", "musik": False, "stempel": False, "dekor": False,
            "durasi": len(shot) * 3.0, "cerita": {"shot": shot}}
    html = AKAR / "hasil_lembar_konsep_abstrak.html"
    html.write_text(buat_html(spek, str(AKAR / "mesin-video" / "papan"), sudah_dijaga=True), encoding="utf-8")
    panel = []
    with sync_playwright() as p:
        br = p.chromium.launch()
        pg = br.new_page(viewport={"width": LEBAR, "height": TINGGI}, device_scale_factor=1)
        pg.goto("file://" + str(html))
        pg.wait_for_timeout(500)
        for i in range(len(shot)):
            pg.evaluate(f"setT({i * 3.0 + 1.5})")
            gambar = Image.open(io.BytesIO(pg.screenshot())).convert("RGB")
            panel.append(gambar.resize((270, 480)))
        br.close()
    html.unlink(missing_ok=True)

    kanvas = Image.new("RGB", (4 * 560, 2 * 540), "#f3eee5")
    draw = ImageDraw.Draw(kanvas)
    font = ImageFont.load_default()
    for i, nama in enumerate(KONSEP):
        x, y = (i % 2) * 1120, (i // 2) * 540
        draw.text((x + 10, y + 5), nama, fill="#17130f", font=font)
        kanvas.paste(panel[i * 2], (x + 10, y + 30))
        kanvas.paste(panel[i * 2 + 1], (x + 290, y + 30))
        draw.text((x + 10, y + 515), "awal", fill="#17130f", font=font)
        draw.text((x + 290, y + 515), "akhir", fill="#17130f", font=font)
    keluar = AKAR / "hasil" / "konsep-abstrak.png"
    keluar.parent.mkdir(parents=True, exist_ok=True)
    kanvas.save(keluar)
    print(f"{len(KONSEP)} konsep, dua keadaan, 270x480 px per panel: {keluar}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
