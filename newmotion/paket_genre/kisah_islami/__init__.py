"""Manifest paket genre Kisah Islami untuk NewMotion.

Aturan adab tokoh dan dalil berada di paket ini; inti hanya memanggil kait kontrak.
"""

from newmotion.domain.genre import PaketGenre
from .penjaga_tokoh import periksa_adab_tokoh
from .penjaga_dalil import periksa_dalil


def buat_paket() -> PaketGenre:
    """Buat manifest genre tanpa membuat inti bergantung pada implementasinya."""
    return PaketGenre(
        nama="kisah_islami",
        penjaga_tokoh=periksa_adab_tokoh,
        penjaga_dalil=periksa_dalil,
        panduan_gaya="newmotion.paket_genre.kisah_islami.PANDUAN_GAYA.md",
        modul_dalil="newmotion.paket_genre.kisah_islami.dalil",
        modul_legacy={
            "pengarah": "mesin-video/papan/direktur.py",
            "arah_visual": "mesin-video/papan/arah_visual.py",
            "penjaga_dalil_kompatibilitas": "mesin-video/papan/penjaga_dalil.py",
            "penjaga_tokoh_suci": "newmotion/paket_genre/kisah_islami/penjaga_tokoh_legacy.py",
        },
    )
