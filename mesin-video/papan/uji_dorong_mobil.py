"""Uji visual adegan tokoh mendorong mobil dari tampak samping.

Uji ini sengaja terpisah dari uji pose umum: tidak memakai TTS, audio, atau layanan
eksternal. Hasil PNG memperlihatkan beberapa fase agar posisi tangan, postur, keringat,
dan gerak relatif tokoh-mobil dapat diaudit secara visual.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

AKAR = Path(__file__).resolve().parents[2]
PAPAN = AKAR / "mesin-video" / "papan"
LEBAR, TINGGI = 1080, 1920


def buat_spek():
    tokoh = {
        "id": 1, "gaya": "umum", "kulit": "#d9b48c", "rambut": "pendek",
        "warna_rambut": "#2a1c18",
        "pakaian": {"jenis": "kaus", "warna": "#3f7890", "bawah": "celana", "bawah_warna": "#34445a"},
        "hidup": True, "profil": "kiri", "wajah": "marah", "mata": "buka",
        "pose": "condong", "lengan": "tolak", "keringat": 1,
        "jalan": 1, "x": 70, "y": 1580, "s": 1.0, "bayangan": True,
    }
    mobil = {
        "jenis": "mobil_luar", "x": 540, "y": 1580, "s": 1.0,
        "warna": "#e8e4dc", "aksen": "#5a6472", "jalan": 18, "arah": 1,
        "stiker": "UJI", "sub": "DORONG",
    }
    shot = {
        "at": 0, "horizon": 1740, "palet": "siang",
        "benda": [mobil], "boneka": [tokoh],
    }
    return {
        "latar": "gelap", "musik": False, "stempel": False, "dekor": False,
        "durasi": 4,
        "cerita": {"shot": [shot]},
    }


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
        "# Uji visual tokoh mendorong mobil",
        "",
        "- Sudut: tampak samping, menghadap kiri.",
        "- Ekspresi: marah/berusaha keras; keringat aktif.",
        "- Gerak: parameter jalan aktif; mobil luar memiliki gerak roda.",
        "- Audio/TTS: tidak digunakan.",
        "",
        "Catatan audit: ini uji visual konfigurasi renderer saat ini, bukan bukti simulasi fisika "
        "atau kontak tangan-bodi yang terukur. Periksa kelima fase PNG untuk memastikan tangan "
        "benar-benar menyentuh bodi dan gerak tokoh selaras dengan perpindahan mobil.",
        "",
    ]
    (out / "laporan.md").write_text("\n".join(laporan), encoding="utf-8")
    print("\n".join(laporan))


if __name__ == "__main__":
    main()
