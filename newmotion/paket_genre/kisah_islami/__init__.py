"""Manifest kompatibilitas genre Kisah Islami untuk NewMotion.

Aturan lama tetap dipertahankan selama proses pemindahan bertahap. Modul-modul pada
mesin-video/ dicatat sebagai sumber kompatibilitas; pemindahannya dilakukan satu per
satu setelah adapter dan tes kontraknya tersedia.
"""

from newmotion.domain.genre import PaketGenre


def buat_paket() -> PaketGenre:
    """Buat manifest genre tanpa membuat inti bergantung pada implementasinya."""
    return PaketGenre(
        nama="kisah_islami",
        modul_dalil="mesin-video/dalil",
        panduan_gaya="mesin-video/CLAUDE.md",
        resep="mesin-video/papan/direktur.py",
        bawaan={
            "kepala_tokoh_pria": "imamah",
            "kepala_tokoh_wanita": "kerudung",
            "mode_dalil": "wajib_verifikasi",
        },
        modul_legacy={
            "pengarah": "mesin-video/papan/direktur.py",
            "arah_visual": "mesin-video/papan/arah_visual.py",
            "penjaga_dalil": "mesin-video/papan/penjaga_dalil.py",
            "penjaga_tokoh_suci": "mesin-video/papan/penjaga_tokoh_suci.py",
        },
    )
