"""Ukur kotak batas (bbox) setiap jenis benda renderer, untuk lapisan tata letak.

Setiap jenis digambar sendirian di (540, 1500) skala 1 dengan kamera netral, pada beberapa
waktu (animasi bisa membesar), lalu kotak batas layar dicatat relatif terhadap titik jangkar
(x, y). Hasil: newmotion/application/data/ukuran_benda.json  {jenis: [kiri, atas, kanan, bawah]}.

    python mesin-video/papan/ukur_benda.py
Jalankan ulang setiap kali bentuk benda di cerita.js berubah (uji memeriksa semua jenis tercatat).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

AKAR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(AKAR / "mesin-video"))
sys.path.insert(0, str(AKAR))
KELUARAN = AKAR / "newmotion" / "application" / "data" / "ukuran_benda.json"
X0, Y0, DUR = 540, 1500, 3.0
WAKTU = (0.6, 1.5, 2.8)


def main() -> int:
    from papan_buat import buat_html
    from playwright.sync_api import sync_playwright

    from newmotion.application.katalog_renderer import katalog

    lama = json.loads(KELUARAN.read_text(encoding="utf-8")) if KELUARAN.is_file() else {}
    # Empat benda ini digambar ulang pada Tugas 5b; ukur ulang meski namanya sudah ada.
    ukur_ulang = {"ladang_gandum", "kambing", "rantai_belenggu", "sungai"}
    jenis = sorted((set(katalog()) - set(lama)) | (ukur_ulang & set(katalog())) )
    if not jenis:
        print(f"Semua {len(lama)} jenis sudah terukur.")
        return 0
    shot = [{"at": i * DUR, "horizon": 1990, "palet": "pagi", "debu": 0, "langit": 0, "kamera": {"z": 1, "x": 540, "y": 960},
             "benda": [{"jenis": j, "x": X0, "y": Y0, "s": 1}]} for i, j in enumerate(jenis)]
    spek = {"latar": "gelap", "musik": False, "stempel": False, "dekor": False, "durasi": DUR * len(jenis),
            "cerita": {"shot": shot}}
    html = AKAR / "hasil_ukur_benda.html"
    html.write_text(buat_html(spek, str(AKAR / "mesin-video" / "papan"), sudah_dijaga=True), encoding="utf-8")
    hasil = dict(lama)
    with sync_playwright() as p:
        br = p.chromium.launch()
        pg = br.new_page(viewport={"width": 1080, "height": 1920})
        pg.goto("file://" + str(html))
        pg.wait_for_timeout(300)
        for i, j in enumerate(jenis):
            kotak = None
            for w in WAKTU:
                pg.evaluate(f"setT({i * DUR + w})")
                r = pg.evaluate("""(j) => { const e = document.querySelector(`g[data-j="${j}"]`); if (!e) return null;
                    const b = e.getBoundingClientRect(); return [b.left, b.top, b.right, b.bottom]; }""", j)
                if r and r[2] > r[0]:
                    kotak = r if kotak is None else [min(kotak[0], r[0]), min(kotak[1], r[1]), max(kotak[2], r[2]), max(kotak[3], r[3])]
            if kotak:
                hasil[j] = [round(kotak[0] - X0), round(kotak[1] - Y0), round(kotak[2] - X0), round(kotak[3] - Y0)]
        br.close()
    html.unlink(missing_ok=True)
    KELUARAN.parent.mkdir(parents=True, exist_ok=True)
    KELUARAN.write_text(json.dumps(hasil, indent=0, sort_keys=True) + "\n", encoding="utf-8")
    print(f"{len(jenis)} jenis baru diukur; total {len(hasil)} tercatat -> {KELUARAN}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
