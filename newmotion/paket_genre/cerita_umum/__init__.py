"""Paket cerita umum: pengarahan aksi tokoh non-Islami yang eksplisit."""
from newmotion.domain.genre import PaketGenre
from .pengarah_naskah import arahkan
from .pengarah_tokoh_visual import arahkan_tokoh_visual


def buat_paket() -> PaketGenre:
    return PaketGenre(
        nama="cerita_umum",
        pengarah_naskah=arahkan,
        pengarah_tokoh_visual=arahkan_tokoh_visual,
    )
