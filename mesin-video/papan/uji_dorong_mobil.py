"""Uji visual adegan tokoh mendorong mobil dari tampak samping.

Uji ini terpisah dari uji pose umum dan tidak memakai TTS/audio.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

AKAR = Path(__file__).resolve().parents[2]
PAPAN = AKAR / "mesin-video" / "papan"
sys.path.insert(0, str(AKAR / "mesin-video"))
LEBAR, TINGGI = 1080, 1920


def buat_spek():
    tokoh = {
        "id": 1, "gaya": "umum", "kulit": "#d9b48c", "rambut": "pendek",
        "warna_rambut": "#2a1c18",
        "pakaian": {"jenis": "kaus", "warna": "#3f7890", "bawah": "celana", "bawah_warna": "#34445a"},
        "hidup": True, "profil": "kiri", "wajah": "marah", "mata": "buka",
        "pose": "dorong", "aksi": "dorong", "keringat": 1,
        "jalan": 0, "x": [[0, 320], [4, 260]], "y": 1580, "s": 1.0, "bayangan": True,
    }
    mobil = {
        "jenis": "mobil_luar", "x": [[0, 540], [4, 480]], "y": 1580, "s": 1.0,
        "warna": "#e8e4dc", "aksen": "#5a6472", "jalan": 18, "arah": 1,
        "stiker": "UJI", "sub": "DORONG",
    }
    shot = {"at": 0, "horizon": 1740, "palet": "siang", "benda": [mobil], "boneka": [tokoh]}
    return {"latar": "gelap", "musik": False, "stempel": False, "dekor": False,
            "durasi": 4, "cerita": {"shot": [shot]}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--keluaran", default="hasil/uji_tokoh_dorong_mobil")
    ap.add_argument("--chrome")
    args = ap.parse_args()
    out = Path(args.keluaran)
    out.mkdir(parents=True, exist_ok=True)

    from papan_buat import buat_html
    from playwright.sync_api import sync_playwright

    html = buat_html(buat_spek(), str(PAPAN))
    berkas = out / "adegan_dorong_mobil.html"
    berkas.write_text(html, encoding="utf-8")
    waktu = [0.0, 0.8, 1.6, 2.4, 3.2]
    with sync_playwright() as p:
        opsi = {"executable_path": args.chrome, "args": ["--no-sandbox"]} if args.chrome else {}
        browser = p.chromium.launch(**opsi)
        page = browser.new_page(viewport={"width": LEBAR, "height": TINGGI})
        page.goto("file://" + str(berkas.resolve()))
        page.evaluate("document.fonts.ready")
        page.wait_for_timeout(300)
        for i, t in enumerate(waktu):
            page.evaluate(f"setT({t:.3f})")
            page.screenshot(path=str(out / f"fase_{i+1}_{t:.1f}detik.png"))
        browser.close()

    laporan = [
        "# Uji visual tokoh mendorong mobil", "",
        "- Sudut: tampak samping, menghadap kiri.",
        "- Ekspresi: marah/berusaha keras; keringat aktif.",
        "- Gerak: aksi dorong RIG aktif; tokoh dan mobil bergeser 60 px ke kiri secara serempak.",
        "- Roda: berputar mengikuti perpindahan mobil.",
        "- Audio/TTS: tidak digunakan.", "",
        "Catatan audit: uji ini memeriksa pose dorong RIG dan gerak relatif tokoh-mobil. "
        "Kontak tangan-bodi harus tetap diverifikasi dari kelima fase PNG; ini belum simulasi fisika penuh.", "",
    ]
    (out / "laporan.md").write_text("\n".join(laporan), encoding="utf-8")
    print("\n".join(laporan))


if __name__ == "__main__":
    main()
