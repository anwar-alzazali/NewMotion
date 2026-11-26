"""Orkestrator sutradara inti: memilih paket dan menegakkan kontrak arahan.

Modul ini netral genre. Ia tidak menentukan estetika atau isi shot; kebijakan
pengarahan spesifik tetap disediakan oleh paket genre.
"""

import copy
from collections.abc import Mapping
from typing import Any

from newmotion.domain.genre import (
    ambil,
    konteks_konten_untuk_naskah,
    nama_genre_untuk_naskah,
)


class GalatPengarahan(ValueError):
    """Naskah atau hasil paket tidak memenuhi kontrak sutradara."""


def _rencana_cerita(naskah: Mapping[str, Any], shot: list[dict]) -> dict[str, Any]:
    """Pisahkan data cerita semantik dari instruksi visual yang dikonsumsi renderer."""
    tokoh = naskah.get("tokoh", [])
    if not isinstance(tokoh, list):
        raise GalatPengarahan("Daftar tokoh pada rencana cerita harus berupa daftar")
    id_tokoh = set()
    for nomor, item in enumerate(tokoh, start=1):
        if not isinstance(item, Mapping):
            raise GalatPengarahan(f"Tokoh ke-{nomor} harus berupa objek")
        identitas, nama = item.get("id"), item.get("nama")
        if not isinstance(identitas, str) or not identitas.strip():
            raise GalatPengarahan(f"Tokoh ke-{nomor} tidak memiliki ID stabil")
        if not isinstance(nama, str) or not nama.strip():
            raise GalatPengarahan(f"Tokoh ke-{nomor} tidak memiliki nama")
        if identitas in id_tokoh:
            raise GalatPengarahan(f"ID tokoh {identitas!r} digunakan lebih dari sekali")
        id_tokoh.add(identitas)

    daftar_adegan = []
    id_adegan = set()
    for nomor, adegan in enumerate(naskah["adegan"], start=1):
        identitas = adegan.get("id") or f"beat-{nomor:03d}"
        if not isinstance(identitas, str) or not identitas.strip():
            raise GalatPengarahan(f"ID beat ke-{nomor} tidak valid")
        if identitas in id_adegan:
            raise GalatPengarahan(f"ID beat {identitas!r} digunakan lebih dari sekali")
        id_adegan.add(identitas)

        tokoh_ids = adegan.get("tokoh_ids", [])
        if not isinstance(tokoh_ids, list) or any(x not in id_tokoh for x in tokoh_ids):
            raise GalatPengarahan(
                f"Beat {identitas!r} merujuk ID tokoh yang tidak terdaftar"
            )
        butir = {
            "id": identitas,
            "nama": str(adegan.get("nama") or f"adegan_{nomor}"),
            "teks": adegan["teks"],
            "peran": copy.deepcopy(adegan.get("peran", [])),
            "tokoh_ids": list(tokoh_ids),
            "dialog": copy.deepcopy(adegan.get("dialog", [])),
        }
        for kunci in ("peristiwa", "aksi", "sasaran", "tujuan", "perubahan_keadaan"):
            if kunci in adegan:
                butir[kunci] = copy.deepcopy(adegan[kunci])
        daftar_adegan.append(butir)

    # Kaitkan shot ke ID beat stabil; indeks _adegan tetap dipakai untuk kompatibilitas lama.
    for nomor, item_shot in enumerate(shot, start=1):
        indeks = item_shot.get("_adegan")
        if indeks is None:
            continue
        if type(indeks) is not int or not 0 <= indeks < len(daftar_adegan):
            raise GalatPengarahan(
                f"Shot ke-{nomor} memiliki indeks _adegan di luar daftar beat"
            )
        item_shot["_beat_id"] = daftar_adegan[indeks]["id"]

    return {
        "tokoh": copy.deepcopy(tokoh),
        "adegan": daftar_adegan,
    }


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

    # Rencana semantik disimpan terpisah dari instruksi visual renderer.
    # Renderer tetap menerima cerita.shot; lapisan blocking berikutnya memakai rencana_cerita.
    spesifikasi["rencana_cerita"] = _rencana_cerita(naskah, shot)

    # Genre menjadi metadata otoritatif untuk gerbang penjaga pada renderer.
    spesifikasi["genre"] = paket.nama
    spesifikasi["konteks_konten"] = konteks_konten
    return spesifikasi, paket.nama, len(shot)
