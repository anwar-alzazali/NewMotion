"""Pengurai peristiwa narasi Indonesia dengan tata bahasa konservatif.

Pengurai ini bukan model bahasa. Ia hanya mengeluarkan peristiwa untuk pola yang
dikenali dengan bukti frasa sumber; pola lain ditandai agar tidak diisi dengan
dugaan. Cakupan awal sengaja terbatas dan dapat diperluas lewat tes.
"""
from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping, Sequence


# Bentuk kata yang didukung dipetakan ke aksi semantik kanonis.
_POLA_AKSI = {
    "berjalan": "berjalan",
    "berjalan kaki": "berjalan",
    "berlari": "berlari",
    "lari": "berlari",
    "mendekati": "mendekati",
    "menghampiri": "mendekati",
    "menolong": "menolong",
    "ditolong": "menolong",
    "membantu": "menolong",
    "dibantu": "menolong",
    "mengangkat": "mengangkat",
    "diangkat": "mengangkat",
    "menarik": "menarik",
    "ditarik": "menarik",
    "mendorong": "mendorong",
    "didorong": "mendorong",
    "memukul": "memukul",
    "dipukul": "memukul",
    "menyerang": "menyerang",
    "diserang": "menyerang",
    "tergelincir": "tergelincir",
    "jatuh": "jatuh",
    "terjatuh": "jatuh",
    "mengendarai": "mengendarai_motor",
    "menaiki": "menaiki",
    "menunggu": "menunggu",
    "mengamati": "mengamati",
    "duduk": "duduk",
    "berdiri": "berdiri",
}
_AKSI_REGEX = re.compile(
    r"(?<![\w])(" + "|".join(
        re.escape(x) for x in sorted(_POLA_AKSI, key=len, reverse=True)
    ) + r")(?![\w])",
    re.IGNORECASE,
)
_PEMISAH_URUT = re.compile(r"\s+(?:lalu|kemudian|setelah\s+itu|sesudah\s+itu)\s+", re.I)
_PEMISAH_SIMULTAN = re.compile(r"\s+(?:dan|sementara)\s+", re.I)


def _normalisasi(teks: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", teks).split())


def _posisi_peran(teks: str, peran: Sequence[str]) -> list[tuple[int, int, str]]:
    hasil = []
    for nama in sorted(set(peran), key=len, reverse=True):
        nama = _normalisasi(nama)
        if not nama:
            continue
        pola = re.compile(r"(?<![\w])" + re.escape(nama) + r"(?![\w])", re.I)
        for cocok in pola.finditer(teks):
            hasil.append((cocok.start(), cocok.end(), nama))
    return sorted(hasil)



def _posisi_benda(teks: str, benda: Sequence[Mapping]) -> list[tuple[int, int, str, str]]:
    """Cari hanya benda yang sudah terdaftar eksplisit pada roster naskah."""
    hasil = []
    for entitas in benda:
        if not isinstance(entitas, Mapping):
            continue
        identitas = entitas.get("id")
        nama = entitas.get("nama")
        if not isinstance(identitas, str) or not identitas.strip():
            continue
        nama_alias = [nama] if isinstance(nama, str) else []
        alias = entitas.get("alias", [])
        if isinstance(alias, (list, tuple)):
            nama_alias.extend(x for x in alias if isinstance(x, str))
        for label in sorted(set(nama_alias), key=len, reverse=True):
            label = _normalisasi(label)
            if label:
                pola = re.compile(r"(?<![\\w])" + re.escape(label) + r"(?![\\w])", re.I)
                for cocok in pola.finditer(teks):
                    hasil.append((cocok.start(), cocok.end(), identitas, label))
    unik = {(item[0], item[1], item[2]): item for item in hasil}
    return sorted(unik.values())



def _peristiwa_klausa(
    klausa: str, peran: Sequence[str], nomor: int, aktor_default: str | None = None,
    benda: Sequence[Mapping] = (),
) -> tuple[dict | None, str | None]:
    klausa = _normalisasi(klausa).strip(" ,;")
    if not klausa:
        return None, None
    if re.search(r"\b(?:tidak|bukan|belum|jangan)\b", klausa, re.I):
        return None, "klausa_negatif_tidak_dijadikan_aksi"
    aksi = list(_AKSI_REGEX.finditer(klausa))
    if len(aksi) != 1:
        if len(aksi) > 1:
            return None, "lebih_dari_satu_aksi_dalam_klausa"
        return None, "pola_aksi_belum_dikenali"
    verba = aksi[0]
    subjek = _posisi_peran(klausa[:verba.start()], peran)
    objek = _posisi_peran(klausa[verba.end():], peran)
    objek_benda = _posisi_benda(klausa[verba.end():], benda)
    bentuk = verba.group(1).casefold()
    pasif = bentuk.startswith("di")
    if pasif:
        oleh = re.search(r"\\boleh\\b", klausa[verba.end():], re.I)
        if oleh:
            kandidat_aktor = _posisi_peran(klausa[verba.end() + oleh.end():], peran)
            kandidat_sasaran = subjek
            kandidat_benda = []
        else:
            return None, "kalimat_pasif_tanpa_pelaku_eksplisit"
    else:
        kandidat_aktor = subjek
        kandidat_sasaran = objek
        kandidat_benda = objek_benda
    if len(kandidat_aktor) > 1:
        return None, "aktor_tidak_tunggal_atau_tidak_ditemukan"
    if len(kandidat_sasaran) > 1:
        return None, "sasaran_tokoh_ambigu"
    if len(kandidat_benda) > 1:
        return None, "sasaran_benda_ambigu"
    if kandidat_sasaran and kandidat_benda:
        return None, "sasaran_tokoh_dan_benda_ambigu"
    if not kandidat_aktor and aktor_default and not pasif:
        aktor = aktor_default
    elif kandidat_aktor:
        aktor = kandidat_aktor[-1][2]
    else:
        return None, "aktor_tidak_tunggal_atau_tidak_ditemukan"
    sasaran = kandidat_sasaran[0][2] if kandidat_sasaran else None
    bukti = klausa
    hasil = {
        "id": f"peristiwa-{nomor:03d}",
        "aktor": aktor,
        "aksi": _POLA_AKSI[bentuk],
        "bukti_teks": bukti,
        "hubungan_temporal": "simultan",
    }
    if sasaran:
        hasil["sasaran"] = sasaran
    if kandidat_benda:
        hasil["sasaran_benda_id"] = kandidat_benda[0][2]
        hasil["sasaran_benda"] = kandidat_benda[0][3]
    return hasil, None


def uraikan_peristiwa(\n    teks: str, peran: Sequence[str], benda: Sequence[Mapping] = ()\n) -> dict:
    """Urai pola narasi yang didukung; sisanya menjadi diagnostik, bukan tebakan."""
    if not isinstance(teks, str) or not teks.strip():
        raise ValueError("Teks narasi harus berupa string yang tidak kosong.")
    if not isinstance(peran, (list, tuple)) or any(
        not isinstance(nama, str) or not nama.strip() for nama in peran
    ):
        raise ValueError("Daftar peran harus berisi nama tokoh yang tidak kosong.")

    peristiwa = []
    diagnostik = []
    nomor = 0
    kalimat = [x.strip() for x in re.split(r"(?<=[.!?])\s+", _normalisasi(teks)) if x.strip()]
    for nomor_kalimat, kalimat_item in enumerate(kalimat, 1):
        bagian_urut = _PEMISAH_URUT.split(kalimat_item)
        aktor_sebelumnya = None
        for nomor_bagian, bagian in enumerate(bagian_urut):
            bagian_simultan = _PEMISAH_SIMULTAN.split(bagian)
            hasil_bagian = []
            for indeks_klausa, klausa in enumerate(bagian_simultan):
                nomor += 1
                # Klausa simultan boleh mewarisi subjek klausa sebelumnya hanya
                # jika klausa itu sendiri tidak menyebut aktor sebelum verba.
                aktor_default = (
                    aktor_sebelumnya
                    if nomor_bagian > 0 and indeks_klausa == 0
                    else hasil_bagian[-1]["aktor"]
                    if indeks_klausa > 0 and hasil_bagian
                    else None
                )
                hasil, alasan = _peristiwa_klausa(
                    klausa, peran, nomor, aktor_default=aktor_default
                )
                if hasil:
                    hasil["hubungan_temporal"] = (
                        "setelah" if nomor_bagian > 0 else
                        "simultan" if len(bagian_simultan) > 1 else "tidak_dinyatakan"
                    )
                    hasil_bagian.append(hasil)
                elif alasan:
                    diagnostik.append({
                        "kode": alasan,
                        "kalimat": nomor_kalimat,
                        "bukti_teks": klausa.strip(),
                    })
            peristiwa.extend(hasil_bagian)
            if hasil_bagian:
                aktor_sebelumnya = hasil_bagian[-1]["aktor"]

    for nomor_event, item in enumerate(peristiwa, 1):
        item["id"] = f"peristiwa-{nomor_event:03d}"
        item["urutan"] = nomor_event
    return {
        "status": "siap" if peristiwa and not diagnostik else (
            "sebagian" if peristiwa else "perlu_pemeriksaan"
        ),
        "peristiwa": peristiwa,
        "diagnostik": diagnostik,
        "metode": "tata_bahasa_deterministik_konservatif",
    }
