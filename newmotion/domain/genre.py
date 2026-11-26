"""Kontrak dan registri paket genre; inti tidak mengimpor genre tertentu."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass, field
from importlib import import_module
import re
from threading import RLock
from types import MappingProxyType
from typing import Any, Callable

GENRE_BAWAAN = "kisah_islami"
KONTEKS_KONTEN_BAWAAN = "umum"
KONTEKS_KONTEN_ISLAMI = frozenset({"islami", "sejarah_islam", "kehidupan_muslim"})
KONTEKS_KONTEN_DIKENAL = KONTEKS_KONTEN_ISLAMI | {KONTEKS_KONTEN_BAWAAN}
_POLA_NAMA = re.compile(r"^[a-z][a-z0-9_]*$")
_KUNCI = RLock()
_PAKET: dict[str, "PaketGenre"] = {}


def _bekukan(nilai: Any) -> Any:
    """Salin manifest secara rekursif agar tidak berubah setelah didaftarkan."""
    if isinstance(nilai, Mapping):
        return MappingProxyType({k: _bekukan(v) for k, v in nilai.items()})
    if isinstance(nilai, (list, tuple)):
        return tuple(_bekukan(v) for v in nilai)
    if isinstance(nilai, set):
        return frozenset(_bekukan(v) for v in nilai)
    return deepcopy(nilai)


def salin_data(nilai: Any) -> Any:
    """Ubah data manifest menjadi wadah biasa untuk pustaka eksternal."""
    if isinstance(nilai, Mapping):
        return {k: salin_data(v) for k, v in nilai.items()}
    if isinstance(nilai, (list, tuple)):
        return [salin_data(v) for v in nilai]
    if isinstance(nilai, (set, frozenset)):
        return {salin_data(v) for v in nilai}
    return deepcopy(nilai)


@dataclass(frozen=True)
class PaketGenre:
    """Kontrak ekstensi genre; seluruh kait bersifat opsional."""

    nama: str
    komponen_visual: Mapping[str, Callable[..., Any]] = field(default_factory=dict)
    validator: Callable[..., Any] | None = None
    penjaga_tokoh: Callable[..., Any] | None = None
    penjaga_dalil: Callable[..., Any] | None = None
    pengarah_naskah: Callable[..., Any] | None = None
    pengarah_tokoh_visual: Callable[..., Any] | None = None
    penyesuaian_adegan: Callable[..., Any] | None = None
    skema_tambahan: Mapping[str, Any] = field(default_factory=dict)
    bawaan: Mapping[str, Any] = field(default_factory=dict)
    modul_dalil: str | None = None
    panduan_gaya: str | None = None
    resep: str | None = None
    modul_legacy: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.nama, str) or not _POLA_NAMA.fullmatch(self.nama):
            raise ValueError(f"nama genre tidak sah: {self.nama!r}")
        if any(not isinstance(k, str) or not k.strip() for k in self.komponen_visual):
            raise ValueError("nama komponen visual harus berupa teks yang tidak kosong")
        if any(not callable(v) for v in self.komponen_visual.values()):
            raise TypeError("setiap komponen visual harus berupa fungsi")
        if self.validator is not None and not callable(self.validator):
            raise TypeError("validator paket harus berupa fungsi")
        if self.penjaga_tokoh is not None and not callable(self.penjaga_tokoh):
            raise TypeError("penjaga_tokoh paket harus berupa fungsi")
        if self.penjaga_dalil is not None and not callable(self.penjaga_dalil):
            raise TypeError("penjaga_dalil paket harus berupa fungsi")
        if self.pengarah_naskah is not None and not callable(self.pengarah_naskah):
            raise TypeError("pengarah_naskah paket harus berupa fungsi")
        if self.pengarah_tokoh_visual is not None and not callable(self.pengarah_tokoh_visual):
            raise TypeError("pengarah_tokoh_visual paket harus berupa fungsi")
        if not any((
            self.komponen_visual, self.validator, self.penjaga_tokoh, self.penjaga_dalil, self.pengarah_naskah, self.pengarah_tokoh_visual,
            self.penyesuaian_adegan, self.skema_tambahan, self.bawaan,
            self.modul_dalil, self.panduan_gaya, self.resep, self.modul_legacy,
        )):
            raise ValueError("paket genre harus menyediakan minimal satu kemampuan atau metadata")
        object.__setattr__(self, "komponen_visual", MappingProxyType(dict(self.komponen_visual)))
        object.__setattr__(self, "skema_tambahan", _bekukan(self.skema_tambahan))
        object.__setattr__(self, "bawaan", _bekukan(self.bawaan))
        object.__setattr__(self, "modul_legacy", _bekukan(self.modul_legacy))


def daftarkan(paket: PaketGenre, *, ganti: bool = False) -> None:
    """Daftarkan paket; penggantian harus diminta secara eksplisit."""
    if not isinstance(paket, PaketGenre):
        raise TypeError("paket harus berupa PaketGenre")
    with _KUNCI:
        if paket.nama in _PAKET and not ganti:
            raise ValueError(f"genre sudah terdaftar: {paket.nama}")
        _PAKET[paket.nama] = paket


def ambil(nama: str | None = None) -> PaketGenre:
    """Ambil paket yang sudah terdaftar atau muat modul genre secara malas."""
    nama = GENRE_BAWAAN if nama is None else nama
    if not isinstance(nama, str) or not _POLA_NAMA.fullmatch(nama):
        raise ValueError("nama genre harus berupa nama paket yang sah")
    with _KUNCI:
        if nama in _PAKET:
            return _PAKET[nama]
        jalur = f"newmotion.paket_genre.{nama}"
        try:
            modul = import_module(jalur)
        except ModuleNotFoundError as galat:
            if galat.name != jalur:
                raise
            tersedia = ", ".join(sorted(_PAKET)) or "(belum ada)"
            raise ValueError(f"genre tidak dikenal: {nama!r}; paket terdaftar: {tersedia}") from galat
        pembuat = getattr(modul, "buat_paket", None)
        if not callable(pembuat):
            raise TypeError(f"paket {nama!r} tidak menyediakan buat_paket()")
        paket = pembuat()
        if not isinstance(paket, PaketGenre) or paket.nama != nama:
            raise TypeError(f"buat_paket() harus mengembalikan PaketGenre bernama {nama!r}")
        daftarkan(paket)
        return paket


def daftar() -> tuple[str, ...]:
    """Daftar paket yang sudah dimuat pada proses ini."""
    with _KUNCI:
        return tuple(sorted(_PAKET))


def nama_dari_rencana(rencana: Mapping[str, Any]) -> str:
    """Ambil genre dari rencana; rencana lama tetap memakai genre bawaan."""
    if not isinstance(rencana, Mapping):
        raise ValueError("rencana harus berupa objek")
    nama = rencana.get("genre", GENRE_BAWAAN)
    if not isinstance(nama, str) or not _POLA_NAMA.fullmatch(nama):
        raise ValueError("kolom genre harus berupa nama paket yang sah")
    return nama


def nama_genre_untuk_naskah(
    naskah: Mapping[str, Any], *, pilihan: str | None = None
) -> str:
    """Resolve genre for a new script; never silently guess a genre.

    Explicit CLI/user choice takes precedence over naskah metadata. If neither
    exists, ask the caller to obtain a genre choice. Legacy board specifications
    keep using nama_dari_rencana() and its Kisah Islami compatibility default.
    """
    if not isinstance(naskah, Mapping):
        raise ValueError("naskah harus berupa objek")

    nama = pilihan if pilihan is not None else naskah.get("genre")
    if nama is None:
        raise ValueError(
            "Genre naskah belum ditentukan; isi kolom 'genre' atau gunakan --genre"
        )
    if not isinstance(nama, str) or not _POLA_NAMA.fullmatch(nama):
        raise ValueError("genre harus berupa nama paket yang sah")
    return nama


def konteks_konten_untuk_naskah(
    naskah: Mapping[str, Any], *, genre: str, wajib_eksplisit: bool = False
) -> str:
    """Resolve konteks isi secara terpisah dari genre penceritaan.

    Kisah Islami selalu berada dalam konteks Islami. Genre lain dapat
    menggunakan konteks umum maupun konteks Islami tanpa mengganti genre.
    """
    if not isinstance(naskah, Mapping):
        raise ValueError("naskah harus berupa objek")
    konteks = naskah.get("konteks_konten")
    if konteks is None:
        if genre == "kisah_islami":
            konteks = "islami"
        elif wajib_eksplisit:
            raise ValueError(
                "Konteks konten belum ditentukan; isi kolom 'konteks_konten' "
                "dengan 'umum' atau konteks yang sesuai"
            )
        else:
            konteks = KONTEKS_KONTEN_BAWAAN
    if not isinstance(konteks, str) or konteks not in KONTEKS_KONTEN_DIKENAL:
        pilihan = ", ".join(sorted(KONTEKS_KONTEN_DIKENAL))
        raise ValueError(f"konteks_konten tidak dikenal; gunakan salah satu: {pilihan}")
    if genre == "kisah_islami" and konteks not in KONTEKS_KONTEN_ISLAMI:
        raise ValueError("genre kisah_islami wajib memakai konteks konten Islami")
    return konteks


def memakai_kebijakan_islami(konteks_konten: str) -> bool:
    """Tentukan apakah konteks memerlukan pagar kebijakan Kisah Islami."""
    return konteks_konten in KONTEKS_KONTEN_ISLAMI


def dari_rencana(rencana: Mapping[str, Any]) -> PaketGenre:
    """Pilih paket sesuai kolom genre pada rencana."""
    return ambil(nama_dari_rencana(rencana))
