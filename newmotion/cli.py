"""Antarmuka baris perintah NewMotion."""

import argparse
from pathlib import Path
import sys

from newmotion import __version__
from newmotion.application.jalankan_job import LayananJalankanJob
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
    render.add_argument("--naskah", action="store_true", help="Arahkan naskah menjadi papan kisah melalui sutradara inti sebelum render")
    render.add_argument("--genre", help="Pilih paket genre secara eksplisit untuk mode --naskah")
    render.add_argument("--tanpa-suara", action="store_true", help="Jangan gabungkan trek efek suara")
    render.add_argument("-d", "--durasi", type=float, help="Paksa durasi render dalam detik")
    ukur = perintah.add_parser("ukur", help="Ukur kedalaman spek papan dibanding referensi Nuh/Mahsyar/Ya'juj")
    ukur.add_argument("spek", nargs="*", help="Berkas spek papan; kosongkan untuk tolok ukur pengarah")
    ukur.add_argument("--json", action="store_true", help="Cetak hasil sebagai JSON")
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
            if args.perintah == "ukur":
                from newmotion.application.ukur_kedalaman import main as ukur_main

                return ukur_main(list(args.spek) + (["--json"] if args.json else []))
            if args.perintah == "render":
                if args.genre and not args.naskah:
                    raise ValueError("--genre hanya dapat digunakan bersama --naskah")
                keluaran = Path(args.keluaran)
                if not keluaran.is_absolute():
                    keluaran = konfigurasi.direktori_hasil / keluaran
                layanan = LayananJalankanJob(konfigurasi, runtime.log)
                argumen_tambahan = []
                if args.tanpa_suara:
                    argumen_tambahan.append("--tanpa-suara")
                if args.durasi is not None:
                    argumen_tambahan.extend(["-d", str(args.durasi)])
                job, hasil = layanan.jalankan_render(
                    args.spesifikasi, keluaran, argumen_tambahan, naskah=args.naskah, genre_pilihan=args.genre
                )
                print(f"Job {job.id}: {job.status.value}")
                print(hasil.stdout, end="")
                if hasil.stderr:
                    print(hasil.stderr, file=sys.stderr, end="")
                return hasil.kode_keluar
    except (OSError, ValueError, TimeoutError) as galat:
        print(f"Galat NewMotion: {galat}", file=sys.stderr)
        return 2
    return 0
