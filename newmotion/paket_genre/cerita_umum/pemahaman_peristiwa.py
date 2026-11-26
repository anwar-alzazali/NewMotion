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

_AKSI_BUTUH_BENDA = {"menaiki", "mengendarai_motor"}
_KEADAAN_AKSI = {
    "jatuh": "terjatuh",
    "terjatuh": "terjatuh",
    "duduk": "duduk",
    "berdiri": "berdiri",
}


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
                pola = re.compile(r"(?<![\w])" + re.escape(label) + r"(?![\w])", re.I)
                for cocok in pola.finditer(teks):
                    hasil.append((cocok.start(), cocok.end(), identitas, label))
    unik = {(item[0], item[1], item[2]): item for item in hasil}
    return sorted(unik.values())


def _peristiwa_klausa(
    klausa: str,
    peran: Sequence[str],
    nomor: int,
    aktor_default: str | None = None,
    benda: Sequence[Mapping] = (),
) -> tuple[dict | None, str | None]:
    klausa = _normalisasi(klausa).strip(" ,;")
    if not klausa:
        return None, None
    if re.search(r"\b(?:tidak|bukan|belum|jangan)\b", klausa, re.I):
        return None, "klausa_negatif_tidak_dijadikan_aksi"
    # Frasa tujuan "untuk <aksi>" bukan aksi yang sudah terjadi.
    # Pisahkan hanya jika verba tujuan dikenal dan muncul di awal frasa tujuan.
    klausa_utama = klausa
    klausa_tujuan = None
    pemisah_tujuan = re.search(r"\buntuk\s+", klausa, re.I)
    if pemisah_tujuan:
        # Sufiks "untuk ..." tidak boleh keliru dianggap sasaran langsung
        # aksi utama, terutama bila menyebut nama benda.
        klausa_utama = klausa[:pemisah_tujuan.start()].strip()
        calon_tujuan = klausa[pemisah_tujuan.end():].strip()
        aksi_tujuan = list(_AKSI_REGEX.finditer(calon_tujuan))
        if (
            len(aksi_tujuan) == 1
            and not calon_tujuan[:aksi_tujuan[0].start()].strip()
        ):
            klausa_tujuan = calon_tujuan
        elif len(aksi_tujuan) > 1:
            return None, "tujuan_aksi_ambigu"

    aksi = list(_AKSI_REGEX.finditer(klausa_utama))
    if len(aksi) != 1:
        if len(aksi) > 1:
            return None, "lebih_dari_satu_aksi_dalam_klausa"
        return None, "pola_aksi_belum_dikenali"
    verba = aksi[0]
    subjek = _posisi_peran(klausa_utama[:verba.start()], peran)
    objek = _posisi_peran(klausa_utama[verba.end():], peran)
    objek_benda = _posisi_benda(klausa_utama[verba.end():], benda)
    bentuk = verba.group(1).casefold()
    pasif = bentuk.startswith("di")
    if pasif:
        oleh = re.search(r"\boleh\b", klausa_utama[verba.end():], re.I)
        if oleh:
            kandidat_aktor = _posisi_peran(klausa_utama[verba.end() + oleh.end():], peran)
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
    tujuan = None
    if klausa_tujuan is not None:
        verba_tujuan = _AKSI_REGEX.search(klausa_tujuan)
        if verba_tujuan is None:
            return None, "tujuan_aksi_belum_dikenali"
        teks_sasaran_tujuan = klausa_tujuan[verba_tujuan.end():]
        sasaran_tujuan = _posisi_peran(teks_sasaran_tujuan, peran)
        benda_tujuan = _posisi_benda(teks_sasaran_tujuan, benda)
        if len(sasaran_tujuan) > 1:
            return None, "sasaran_tujuan_tokoh_ambigu"
        if len(benda_tujuan) > 1:
            return None, "sasaran_tujuan_benda_ambigu"
        if sasaran_tujuan and benda_tujuan:
            return None, "sasaran_tujuan_tokoh_dan_benda_ambigu"
        tujuan = {"aksi": _POLA_AKSI[verba_tujuan.group(1).casefold()]}
        if sasaran_tujuan:
            tujuan["sasaran"] = sasaran_tujuan[0][2]
        if benda_tujuan:
            tujuan["sasaran_benda_id"] = benda_tujuan[0][2]
            tujuan["sasaran_benda"] = benda_tujuan[0][3]
    if not kandidat_aktor and aktor_default and not pasif:
        aktor = aktor_default
    elif kandidat_aktor:
        aktor = kandidat_aktor[-1][2]
    else:
        return None, "aktor_tidak_tunggal_atau_tidak_ditemukan"
    sasaran = kandidat_sasaran[0][2] if kandidat_sasaran else None
    hasil = {
        "id": f"peristiwa-{nomor:03d}",
        "aktor": aktor,
        "aksi": _POLA_AKSI[bentuk],
        "bukti_teks": klausa,
        "hubungan_temporal": "simultan",
    }
    if sasaran:
        hasil["sasaran"] = sasaran
    if tujuan is not None:
        hasil["tujuan"] = tujuan
    elif pemisah_tujuan:
        hasil["_diagnostik_pemahaman"] = {
            "kode": "frasa_untuk_belum_diklasifikasikan",
            "bukti_teks": klausa[pemisah_tujuan.start():],
        }
    if kandidat_benda:
        hasil["sasaran_benda_id"] = kandidat_benda[0][2]
        hasil["sasaran_benda"] = kandidat_benda[0][3]
    keadaan_akhir = _KEADAAN_AKSI.get(bentuk)
    if keadaan_akhir is not None:
        # Hanya keadaan akhir yang didukung langsung oleh verba; keadaan awal
        # tidak dibuat jika naskah tidak menyatakannya.
        hasil["perubahan_keadaan"] = {
            "entitas": aktor,
            "menjadi": keadaan_akhir,
        }
    return hasil, None


def uraikan_peristiwa(
    teks: str,
    peran: Sequence[str],
    benda: Sequence[Mapping] = (),
) -> dict:
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
    kalimat = [x.strip() for x in re.split(r"(?<=[.!?])\\s+", _normalisasi(teks)) if x.strip()]

    def uraikan_rangkaian(teks_bagian: str, nomor_kalimat: int) -> list[dict]:
        nonlocal nomor
        hasil_rangkaian = []
        bagian_urut = _PEMISAH_URUT.split(teks_bagian)
        aktor_sebelumnya = None
        for nomor_bagian, bagian in enumerate(bagian_urut):
            bagian_simultan = _PEMISAH_SIMULTAN.split(bagian)
            hasil_bagian = []
            for indeks_klausa, klausa in enumerate(bagian_simultan):
                nomor += 1
                aktor_default = (
                    aktor_sebelumnya
                    if nomor_bagian > 0 and indeks_klausa == 0
                    else hasil_bagian[-1]["aktor"]
                    if indeks_klausa > 0 and hasil_bagian
                    else None
                )
                hasil, alasan = _peristiwa_klausa(
                    klausa, peran, nomor,
                    aktor_default=aktor_default,
                    benda=benda,
                )
                if hasil:
                    diagnostik_internal = hasil.pop("_diagnostik_pemahaman", None)
                    if diagnostik_internal:
                        diagnostik.append({
                            **diagnostik_internal,
                            "kalimat": nomor_kalimat,
                        })
                    if hasil.get("aksi") in _AKSI_BUTUH_BENDA and not hasil.get("sasaran_benda_id"):
                        diagnostik.append({
                            "kode": "sasaran_benda_belum_terpetakan",
                            "kalimat": nomor_kalimat,
                            "bukti_teks": klausa.strip(),
                        })
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
            hasil_rangkaian.extend(hasil_bagian)
            if hasil_bagian:
                aktor_sebelumnya = hasil_bagian[-1]["aktor"]
        return hasil_rangkaian

    pemisah_sebab = re.compile(r"\s+(karena|sehingga|akibatnya)\s+", re.I)
    for nomor_kalimat, kalimat_item in enumerate(kalimat, 1):
        pemisah = list(pemisah_sebab.finditer(kalimat_item))
        if len(pemisah) == 1:
            penghubung = pemisah[0].group(1).casefold()
            kiri = kalimat_item[:pemisah[0].start()].strip(" ,;")
            kanan = kalimat_item[pemisah[0].end():].strip(" ,;")
            if not kiri or not kanan:
                diagnostik.append({
                    "kode": "hubungan_sebab_akibat_tidak_lengkap",
                    "kalimat": nomor_kalimat,
                    "bukti_teks": kalimat_item,
                })
                continue
            indeks_awal = len(peristiwa)
            hasil_kiri = uraikan_rangkaian(kiri, nomor_kalimat)
            hasil_kanan = uraikan_rangkaian(kanan, nomor_kalimat)
            peristiwa.extend(hasil_kiri)
            peristiwa.extend(hasil_kanan)
            if penghubung == "karena":
                indeks_akibat = indeks_awal
                indeks_sebab = indeks_awal + len(hasil_kiri)
                teks_sebab = kanan
            else:
                indeks_sebab = indeks_awal
                indeks_akibat = indeks_awal + len(hasil_kiri)
                teks_sebab = None
            if (
                indeks_akibat < len(peristiwa)
                and indeks_sebab < len(peristiwa)
                and hasil_kiri and hasil_kanan
            ):
                peristiwa[indeks_akibat]["hubungan_sebab_akibat"] = {
                    "jenis": "disebabkan_oleh",
                    "_indeks_sebab": indeks_sebab,
                }
            elif penghubung == "karena" and hasil_kiri and not hasil_kanan:
                # Penyebab berupa keadaan/frasa, bukan peristiwa yang dikenali.
                peristiwa[indeks_akibat]["sebab_teks"] = teks_sebab
                diagnostik.append({
                    "kode": "sebab_teks_tidak_dipetakan_ke_peristiwa",
                    "kalimat": nomor_kalimat,
                    "bukti_teks": teks_sebab,
                })
            else:
                diagnostik.append({
                    "kode": "hubungan_sebab_akibat_tidak_dapat_dipetakan",
                    "kalimat": nomor_kalimat,
                    "bukti_teks": kalimat_item,
                })
            continue
        if len(pemisah) > 1:
            # Rantai kausal dipetakan hanya jika setiap klausa menghasilkan
            # tepat satu peristiwa yang dikenali tanpa diagnostik baru.
            batas = [0] + [item.end() for item in pemisah]
            akhir = [item.start() for item in pemisah] + [len(kalimat_item)]
            klausa = [
                kalimat_item[mulai:selesai].strip(" ,;")
                for mulai, selesai in zip(batas, akhir)
            ]
            hasil_klausa = []
            rantai_valid = all(klausa)
            for bagian in klausa:
                jumlah_diagnostik = len(diagnostik)
                hasil_bagian = uraikan_rangkaian(bagian, nomor_kalimat)
                if len(hasil_bagian) != 1 or len(diagnostik) != jumlah_diagnostik:
                    rantai_valid = False
                hasil_klausa.append(hasil_bagian)
            if not rantai_valid:
                diagnostik.append({
                    "kode": "rantai_sebab_akibat_tidak_dapat_dipetakan",
                    "kalimat": nomor_kalimat,
                    "bukti_teks": kalimat_item,
                })
                continue
            indeks_awal = len(peristiwa)
            peristiwa.extend(item[0] for item in hasil_klausa)
            for indeks, pemisah_item in enumerate(pemisah):
                if pemisah_item.group(1).casefold() == "karena":
                    indeks_akibat = indeks_awal + indeks
                    indeks_sebab = indeks_awal + indeks + 1
                else:
                    indeks_sebab = indeks_awal + indeks
                    indeks_akibat = indeks_awal + indeks + 1
                peristiwa[indeks_akibat]["hubungan_sebab_akibat"] = {
                    "jenis": "disebabkan_oleh",
                    "_indeks_sebab": indeks_sebab,
                }
            continue
        peristiwa.extend(uraikan_rangkaian(kalimat_item, nomor_kalimat))

    for nomor_event, item in enumerate(peristiwa, 1):
        item["id"] = f"peristiwa-{nomor_event:03d}"
        item["urutan"] = nomor_event
    for item in peristiwa:
        relasi = item.get("hubungan_sebab_akibat")
        if isinstance(relasi, dict) and "_indeks_sebab" in relasi:
            indeks_sebab = relasi.pop("_indeks_sebab")
            if 0 <= indeks_sebab < len(peristiwa):
                relasi["peristiwa_id"] = peristiwa[indeks_sebab]["id"]
            else:
                item.pop("hubungan_sebab_akibat", None)
                diagnostik.append({
                    "kode": "referensi_sebab_akibat_tidak_valid",
                    "bukti_teks": item.get("bukti_teks", ""),
                })
    return {
        "status": "siap" if peristiwa and not diagnostik else (
            "sebagian" if peristiwa else "perlu_pemeriksaan"
        ),
        "peristiwa": peristiwa,
        "diagnostik": diagnostik,
        "metode": "tata_bahasa_deterministik_konservatif",
    }
