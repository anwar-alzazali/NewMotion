"""Penjaga adab tokoh untuk kontrak rencana NewMotion.

Asal aturan: sutradara/paket_genre/kisah_islami/penjaga.py dan
sutradara/paket_genre/kisah_islami/PANDUAN_GAYA.md.
Penjaga ini hanya aktif melalui kait paket genre Kisah Islami.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

NAMA_TAMPIL = {
    "nabi": "nur",
    "rasul": "nur",
    "malaikat": "cahaya_malaikat",
    "sahabat": "wajah_cahaya",
}
KATEGORI_SAKRAL = frozenset(NAMA_TAMPIL)
KATEGORI_ALLAH = frozenset({"allah", "tuhan", "sang_pencipta"})


@dataclass(frozen=True)
class TemuanAdab:
    """Satu pelanggaran aturan penggambaran tokoh."""

    tingkat: str
    kode: str
    pesan: str


def _daftar(nilai: Any) -> list:
    return nilai if isinstance(nilai, list) else []


def periksa_adab_tokoh(rencana: Any) -> list[TemuanAdab]:
    """Periksa identitas tokoh dan cara tampilnya sebelum job diteruskan ke renderer.

    Kontrak shot:
    - shot.nur[] hanya boleh merujuk nabi/rasul.
    - shot.cahaya_malaikat[] hanya boleh merujuk malaikat.
    - shot.tokoh[] tidak boleh memuat nabi/rasul/malaikat.
    - Sahabat tampil sebagai tokoh bertubuh dengan mode='wajah_cahaya'.
    """
    if not isinstance(rencana, dict):
        return []
    peran_list = _daftar(rencana.get("peran"))
    if not peran_list:
        # Format papan lama tetap dijaga oleh adapter paket, bukan oleh inti renderer.
        from .penjaga_tokoh_legacy import periksa_tokoh_suci

        return [
            TemuanAdab("GAGAL", "TOKOH_SAKRAL_FORMAT_LAMA", str(item))
            for item in periksa_tokoh_suci(rencana)
        ]

    temuan: list[TemuanAdab] = []
    peran = {
        str(item.get("id")): item
        for item in peran_list
        if isinstance(item, dict) and item.get("id") is not None
    }

    for item in peran_list:
        if not isinstance(item, dict):
            continue
        pid = str(item.get("id", "tanpa_id"))
        nama = str(item.get("nama", pid))
        kategori = str(item.get("kategori", "")).strip().lower()
        tampil = item.get("tampil")
        if kategori in KATEGORI_ALLAH or nama.strip().lower() in {"allah", "allah swt", "tuhan", "sang pencipta"}:
            temuan.append(TemuanAdab("GAGAL", "ALLAH_TIDAK_DIVISUALKAN",
                                     f"{nama}: Allah tidak boleh divisualisasikan dalam bentuk apa pun"))
            continue
        wajib = NAMA_TAMPIL.get(kategori)
        if wajib and tampil != wajib:
            temuan.append(TemuanAdab("GAGAL", "CARA_TAMPIL_TOKOH_SUCI",
                                     f"{nama} ({kategori}) wajib tampil '{wajib}', bukan '{tampil}'"))
        if not wajib and tampil in {"nur", "cahaya_malaikat", "wajah_cahaya"}:
            temuan.append(TemuanAdab("GAGAL", "BENTUK_CAHAYA_SALAH",
                                     f"{nama} ({kategori or 'kategori tidak diisi'}) tidak boleh memakai bentuk khusus '{tampil}'"))

    for nomor_beat, beat in enumerate(_daftar(rencana.get("beat"))):
        if not isinstance(beat, dict):
            continue
        for nomor_shot, shot in enumerate(_daftar(beat.get("shot"))):
            if not isinstance(shot, dict):
                continue
            lokasi = f"beat {nomor_beat} shot {nomor_shot}"
            for tokoh in _daftar(shot.get("tokoh")):
                if not isinstance(tokoh, dict):
                    continue
                pid = str(tokoh.get("peran", ""))
                identitas = peran.get(pid)
                if identitas is None:
                    continue
                kategori = str(identitas.get("kategori", "")).strip().lower()
                nama = str(identitas.get("nama", pid))
                if kategori in {"nabi", "rasul", "malaikat"}:
                    temuan.append(TemuanAdab("GAGAL", "TOKOH_SUCI_BERTUBUH",
                                             f"{lokasi}: {nama} tidak boleh masuk daftar tokoh bertubuh"))
                elif kategori == "sahabat" and tokoh.get("mode") != "wajah_cahaya":
                    temuan.append(TemuanAdab("GAGAL", "SAHABAT_TANPA_WAJAH_CAHAYA",
                                             f"{lokasi}: {nama} harus berupa tubuh berbaju dengan mode wajah_cahaya"))
                elif kategori not in KATEGORI_SAKRAL and tokoh.get("mode") == "wajah_cahaya":
                    temuan.append(TemuanAdab("GAGAL", "WAJAH_CAHAYA_SALAH",
                                             f"{lokasi}: mode wajah_cahaya hanya untuk sahabat"))

            for cahaya in _daftar(shot.get("nur")):
                if not isinstance(cahaya, dict):
                    continue
                pid = str(cahaya.get("peran", ""))
                identitas = peran.get(pid)
                if identitas is None or str(identitas.get("kategori", "")).lower() not in {"nabi", "rasul"}:
                    nama = identitas.get("nama", pid) if identitas else pid
                    temuan.append(TemuanAdab("GAGAL", "PILAR_NUR_BUKAN_NABI",
                                             f"{lokasi}: pilar nur hanya untuk nabi/rasul; rujukan '{nama}' tidak sah"))

            for cahaya in _daftar(shot.get("cahaya_malaikat")):
                if not isinstance(cahaya, dict):
                    continue
                pid = str(cahaya.get("peran", ""))
                identitas = peran.get(pid)
                if identitas is None or str(identitas.get("kategori", "")).lower() != "malaikat":
                    nama = identitas.get("nama", pid) if identitas else pid
                    temuan.append(TemuanAdab("GAGAL", "BERKAS_CAHAYA_BUKAN_MALAIKAT",
                                             f"{lokasi}: berkas cahaya khusus malaikat tidak boleh dipakai oleh '{nama}'"))

    return temuan


def wajib_lulus_adab_tokoh(rencana: Any) -> None:
    """Gerbang gagal-tertutup untuk pemanggil yang membutuhkan pengecualian eksplisit."""
    temuan = periksa_adab_tokoh(rencana)
    if temuan:
        rincian = "\n".join(f"- [{x.kode}] {x.pesan}" for x in temuan)
        raise ValueError("Rencana melanggar adab penggambaran tokoh:\n" + rincian)
