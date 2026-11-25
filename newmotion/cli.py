"""Antarmuka baris perintah NewMotion."""

import argparse
from pathlib import Path
import sys

from newmotion import __version__
from newmotion.infrastructure.render.papan_lama import AdapterPapanLama
from newmotion.runtime.konfigurasi import Konfigurasi
from newmotion.runtime.lingkungan import periksa_lingkungan
from newmotion.runtime.lifecycle import Runtime


def buat_parser():
    parser = argparse.ArgumentParser(prog="newmotion", description="Runtime produksi video NewMotion")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--profil", choices=("development", "test", "production", "worker"))
    perintah = parser.add_subparsers(dest="perintah", required=True)
    perintah.add_parser("doctor", help="Periksa prasyarat runtime")
    render = perintah.add_parser("render", help="Render spesifikasi melalui mesin-video lama")
    render.add_argument("spesifikasi", help="Berkas spesifikasi JSON")
    render.add_argument("-o", "--keluaran", required=True, help="Lokasi MP4 keluaran")
    render.add_argument("argumen_tambahan", nargs=argparse.REMAINDER)
    return parser


def main(argv=None):
    args = buat_parser().parse_args(argv)
    try:
        konfigurasi = Konfigurasi.muat(args.profil)
        with Runtime(konfigurasi) as runtime:
            if args.perintah == "doctor":
                pemeriksaan = periksa_lingkungan(periksa_render=True)
                gagal = False
                for item in pemeriksaan:
                    status = "OK" if item.tersedia else "BELUM ADA"
                    print(f"{status:10} {item.nama}: {item.keterangan}")
                    if item.nama in {"FFmpeg", "FFprobe"} and not item.tersedia:
                        gagal = True
                return 1 if gagal else 0
            if args.perintah == "render":
                keluaran = Path(args.keluaran)
                if not keluaran.is_absolute():
                    keluaran = konfigurasi.direktori_hasil / keluaran
                adapter = AdapterPapanLama(konfigurasi.akar_proyek,
                                           konfigurasi.batas_waktu_subproses, runtime.log)
                hasil = adapter.render(args.spesifikasi, keluaran, args.argumen_tambahan)
                print(hasil.stdout, end="")
                if hasil.stderr:
                    print(hasil.stderr, file=sys.stderr, end="")
                return hasil.kode_keluar
    except (OSError, ValueError, TimeoutError) as galat:
        print(f"Galat NewMotion: {galat}", file=sys.stderr)
        return 2
    return 0
