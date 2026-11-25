"""Kompatibilitas impor lama untuk penjaga dalil paket Kisah Islami.

Implementasi dan kebijakan verifikasi dimiliki oleh NewMotion.
Modul papan lama hanya meneruskan API agar pemanggil lama tidak rusak.
"""
from newmotion.paket_genre.kisah_islami.penjaga_dalil import (
    DalilTidakTerverifikasiError,
    HasilKartu,
    Rujukan,
    RujukanTidakValid,
    SumberDalil,
    SumberResmi,
    SumberTidakTersedia,
    kerangka_arab,
    periksa_dalil,
    periksa_kartu,
    urai_rujukan,
    wajib_lulus_dalil,
)

__all__ = [
    "DalilTidakTerverifikasiError", "HasilKartu", "Rujukan",
    "RujukanTidakValid", "SumberDalil", "SumberResmi",
    "SumberTidakTersedia", "kerangka_arab", "periksa_dalil",
    "periksa_kartu", "urai_rujukan", "wajib_lulus_dalil",
]
