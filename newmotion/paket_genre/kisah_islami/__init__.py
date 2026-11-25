"""Manifest paket genre Kisah Islami untuk NewMotion.

Aturan pengarah, arah visual, adab tokoh, dan dalil dimiliki paket ini.
Inti NewMotion hanya mengenal kait kontrak PaketGenre.
"""

from newmotion.domain.genre import PaketGenre
from . import arah_visual
from .penjaga_tokoh import periksa_adab_tokoh
from .penjaga_dalil import periksa_dalil
from .pengarah_naskah import arahkan


def buat_paket() -> PaketGenre:
    """Buat manifest genre Kisah Islami beserta kait pengarah dan visualnya."""
    return PaketGenre(
        nama="kisah_islami",
        pengarah_naskah=arahkan,
        komponen_visual={
            "pilih_tema": arah_visual.pilih_tema,
            "tema_lokal": arah_visual.tema_lokal,
            "pilih_tampilan": arah_visual.pilih_tampilan,
            "pilih_pose": arah_visual.pilih_pose,
            "rencana_framing": arah_visual.rencana_framing,
            "ruang_untuk": arah_visual.ruang_untuk,
            "atmosfer": arah_visual.atmosfer,
        },
        penjaga_tokoh=periksa_adab_tokoh,
        penjaga_dalil=periksa_dalil,
        panduan_gaya="newmotion.paket_genre.kisah_islami.PANDUAN_GAYA.md",
        modul_dalil="newmotion.paket_genre.kisah_islami.dalil",
        modul_legacy={
            "pengarah": "mesin-video/papan/direktur.py",
            "arah_visual": "mesin-video/papan/arah_visual.py",
            "penjaga_dalil": "mesin-video/papan/penjaga_dalil.py",
            "penjaga_tokoh_suci": "mesin-video/papan/penjaga_tokoh_suci.py",
        },
    )
