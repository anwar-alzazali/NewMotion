"""Cetak skor tolok ukur untuk satu folder naskah tanpa mengubah alat ukur."""
from __future__ import annotations

import argparse
from pathlib import Path

from newmotion.application.ukur_kedalaman import tolok_ukur


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--folder", default="tests/data/tolok_ukur")
    args = parser.parse_args()
    hasil = tolok_ukur(Path(args.folder))
    print(f"{'cerita':12} {'gabungan':>9} {'cerita':>8} {'ritme':>7} {'kamera':>7} {'lingkungan':>11} {'benda':>7} {'tokoh':>7} {'teks':>7} {'gerak':>7}")
    for nama, item in hasil.items():
        skor = item["skor_aspek"]
        print(
            f"{nama:12} {item['skor_gabungan']:>9} {skor['cerita']:>8} "
            f"{skor['ritme']:>7} {skor['kamera']:>7} {skor['lingkungan']:>11} "
            f"{skor['benda']:>7} {skor['tokoh']:>7} {skor['teks_layar']:>7} "
            f"{skor['gerak']:>7}"
        )
    for nama, item in hasil.items():
        for rincian in item["metrik"]["_rincian_kesesuaian"]:
            if rincian["tidak_tergambar"]:
                print(
                    f"SHOT_TIDAK_TERGAMBAR {nama}#{rincian['shot']}: "
                    f"{','.join(rincian['tidak_tergambar'])} | {rincian['narasi']}"
                )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
