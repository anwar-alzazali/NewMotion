"""Pembuat karakter NewMotion: renderer SVG ber-rangka dan ekspresi.

API utama: orang(...), WAJAH, KEPALA, POSE. Penjaga peran/adab tetap milik pipeline NewMotion.
"""
from .tokoh import orang, WAJAH, WAJAH_DASAR, EKSPRESI_DETAIL, KEPALA, POSE

__all__ = ["orang", "WAJAH", "WAJAH_DASAR", "EKSPRESI_DETAIL", "KEPALA", "POSE"]
