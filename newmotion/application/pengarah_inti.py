"""Orkestrator sutradara inti: memilih paket dan menegakkan kontrak arahan.

Modul ini netral genre. Ia tidak menentukan estetika atau isi shot; kebijakan
pengarahan spesifik tetap disediakan oleh paket genre.
"""

from collections.abc import Mapping
from typing import Any

from newmotion.domain.genre import (
    ambil,
    konteks_konten_untuk_naskah,
    nama_genre_untuk_naskah,
)


class GalatPengarahan(ValueError):
    """Naskah atau hasil paket tidak memenuhi kontrak sutradara."""


def arahkan_naskah(
    naskah: Mapping[str, Any], *, genre_pilihan: str | None = None
) -> tuple[dict[str, Any], str, int]:
    """Pilih paket secara eksplisit, panggil pengarahnya, lalu validasi papan."""
    if not isinstance(naskah, Mapping):
        raise GalatPengarahan("Naskah harus berupa objek")

    try:
        nama_genre = nama_genre_untuk_naskah(naskah, pilihan=genre_pilihan)
        konteks_konten = konteks_konten_untuk_naskah(
            naskah, genre=nama_genre, wajib_eksplisit=True
        )
        paket = ambil(nama_genre)
    except (TypeError, ValueError, ImportError) as galat:
        raise GalatPengarahan(str(galat)) from galat

    adegan = naskah.get("adegan")
    if not isinstance(adegan, list) or not adegan:
        raise GalatPengarahan("Naskah harus memiliki daftar 'adegan' yang tidak kosong")
    for nomor, adegan_item in enumerate(adegan, start=1):
        if (
            not isinstance(adegan_item, Mapping)
            or not isinstance(adegan_item.get("teks"), str)
            or not adegan_item["teks"].strip()
        ):
            raise GalatPengarahan(
                f"Adegan ke-{nomor} harus berupa objek dengan teks yang tidak kosong"
            )

    if not callable(paket.pengarah_naskah):
        raise GalatPengarahan(
            f"Paket genre {paket.nama!r} belum menyediakan pengarah naskah"
        )

    spesifikasi = paket.pengarah_naskah(naskah)
    if not isinstance(spesifikasi, dict):
        raise GalatPengarahan("Pengarah genre harus menghasilkan objek spesifikasi")
    cerita = spesifikasi.get("cerita")
    shot = cerita.get("shot") if isinstance(cerita, dict) else None
    if not isinstance(shot, list) or not shot:
        raise GalatPengarahan("Pengarah genre tidak menghasilkan daftar shot yang dapat dirender")

    # Genre menjadi metadata otoritatif untuk gerbang penjaga pada renderer.
    spesifikasi["genre"] = paket.nama
    spesifikasi["konteks_konten"] = konteks_konten
    return spesifikasi, paket.nama, len(shot)
