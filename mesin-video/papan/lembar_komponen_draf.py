"""Render bukti penuh dan seperempat layar untuk satu komponen-draf."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image

AKAR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(AKAR / "mesin-video"))
sys.path.insert(0, str(AKAR))


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 1:
        raise SystemExit("Pemakaian: python mesin-video/papan/lembar_komponen_draf.py hasil/komponen-draf/komponen_draf.json")
    data = json.loads(Path(args[0]).read_text(encoding="utf-8"))
    nama, parameter = data["nama"], data["parameter"]
    from papan_buat import buat_html
    from playwright.sync_api import sync_playwright

    keluaran = AKAR / "hasil" / "komponen-draf"
    keluaran.mkdir(parents=True, exist_ok=True)
    shot = []
    for i, nilai in enumerate((0.0, 1.0)):
        shot.append({
            "at": i * 3.0, "horizon": 1990, "palet": "pagi", "debu": 0,
            "langit": 0, "kamera": {"z": 1, "x": 540, "y": 960},
            "benda": [{"jenis": nama, "x": 540, "y": 1500, "s": 1, parameter: nilai}],
        })
    spek = {
        "latar": "gelap", "musik": False, "stempel": False, "dekor": False,
        "durasi": 6.0, "cerita": {"shot": shot},
    }
    html = AKAR / "hasil_komponen_draf.html"
    html.write_text(
        buat_html(spek, str(AKAR / "mesin-video" / "papan"), sudah_dijaga=True),
        encoding="utf-8",
    )
    galat_js: list[str] = []
    ukuran = None
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1080, "height": 1920}, device_scale_factor=1)
        page.on("pageerror", lambda error: galat_js.append(str(error)))
        page.goto("file://" + str(html.resolve()))
        page.wait_for_timeout(300)
        for i, label in enumerate(("awal", "akhir")):
            page.evaluate(f"setT({i * 3.0 + 1.5})")
            elemen = page.locator(f'g[data-j="{nama}"]')
            if elemen.count() == 0:
                galat_js.append(f"{nama}: elemen SVG tidak ditemukan pada keadaan {label}")
                continue
            bbox = page.evaluate(
                """(j) => {
                    const e = document.querySelector('g[data-j="' + j + '"]');
                    if (!e) return null;
                    const b = e.getBoundingClientRect();
                    return [b.left, b.top, b.right, b.bottom];
                }""",
                nama,
            )
            if bbox and bbox[2] > bbox[0] and bbox[3] > bbox[1]:
                ukuran = bbox if ukuran is None else [
                    min(ukuran[0], bbox[0]), min(ukuran[1], bbox[1]),
                    max(ukuran[2], bbox[2]), max(ukuran[3], bbox[3]),
                ]
            penuh = keluaran / f"{nama}-{label}-penuh.png"
            seperempat = keluaran / f"{nama}-{label}-seperempat.png"
            page.screenshot(path=str(penuh))
            page.screenshot(path=str(seperempat), clip={"x": 270, "y": 480, "width": 540, "height": 960})
            Image.open(seperempat).convert("RGB").resize((270, 480)).save(seperempat)
        browser.close()
    html.unlink(missing_ok=True)
    laporan = {
        "nama": nama, "parameter": parameter, "nilai_diuji": [0.0, 1.0],
        "bbox_layar": [round(x, 2) for x in ukuran] if ukuran else None,
        "galat_javascript": galat_js,
        "status": "lulus_render" if not galat_js and ukuran else "gagal_render",
        "catatan": "Bukti render saja; audit gaya, makna, dan adab tetap wajib oleh manusia.",
    }
    (keluaran / f"{nama}-laporan.json").write_text(
        json.dumps(laporan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(laporan, ensure_ascii=False, indent=2))
    if galat_js or not ukuran:
        raise RuntimeError(f"Render komponen {nama} gagal: {galat_js}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
