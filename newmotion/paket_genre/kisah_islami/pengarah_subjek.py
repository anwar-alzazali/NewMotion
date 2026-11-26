"""Penerjemah narasi menjadi subjek dan aksi visual renderer.

Aturan di modul ini sengaja terpisah dari alat ukur. Ia membaca frasa narasi,
memilih jenis benda yang sudah ada di cerita.js, lalu mempertahankan keadaan
antar-shot agar objek tidak muncul sebagai dekorasi yang tidak berubah.
"""
from __future__ import annotations

import re
from copy import deepcopy


# Kosakata milik pengarah, bukan salinan leksikon ukur_kedalaman.
POLA_SUBJEK = (
    ("bahtera", re.compile(r"\b(kapal|bahtera|perahu)\b", re.I)),
    ("ngarai", re.compile(r"\b(dinding|tembok|benteng)\b", re.I)),
    ("penggali", re.compile(r"\b(gali|menggali|digali|penggalian)\w*\b", re.I)),
    ("pemimpin", re.compile(r"\b(pemimpin|raja)\b", re.I)),
    ("ombak", re.compile(r"\b(ombak|gelombang)\b", re.I)),
    ("gunung", re.compile(r"\b(gunung|bukit)\b", re.I)),
    ("hewan", re.compile(r"\b(hewan|binatang|ternak)\b|sepasang dari tiap jenis", re.I)),
    ("arus", re.compile(r"\b(banjir|air bah|tenggelam|arus air)\b", re.I)),
    ("pancar", re.compile(r"mata air|memancarkan air|air yang tercurah", re.I)),
    ("surya", re.compile(r"\b(matahari|surya)\b", re.I)),
    ("retakan", re.compile(r"\b(retak|retakan|terbelah|terbelahnya)\b", re.I)),
    ("kerumunan", re.compile(r"\b(kerumunan|orang-orang|seluruh manusia|semua manusia)\b", re.I)),
    ("koin", re.compile(r"\b(harta karun|emas|kekayaan)\b", re.I)),
    ("petir", re.compile(r"\b(petir|kilat|guntur)\b", re.I)),
    ("awan", re.compile(r"\b(awan|hujan)\b", re.I)),
)

POLA_GALI = re.compile(r"\b(gali|menggali|digali|penggalian)\w*\b", re.I)
POLA_HAMPIR = re.compile(r"hampir (tembus|jebol)|nyaris (tembus|jebol)", re.I)
POLA_JEBOL = re.compile(r"\b(jebol|menjebol|tembus|menerobos|runtuh)\b", re.I)
POLA_UTUH = re.compile(r"(kembali|sudah kembali|lagi) (utuh|seperti semula)|utuh kembali", re.I)
POLA_KONTINUITAS_DINDING = re.compile(
    r"\b(pemimpin|raja|besok|pulanglah|tembus|utuh|mereka)\b", re.I
)
POLA_KLIMAKS = re.compile(
    r"\b(jebol|menjebol|pecah|runtuh|tenggelam|terbelah|meledak|"
    r"terhempas|terjatuh|terselamatkan|muncul|keluar)\b", re.I
)
POLA_WUJUD_TAK_DIJELASKAN = re.compile(
    r"tidak (disebutkan|dijelaskan|diketahui) (wujud|bentuk)|"
    r"tidak menyebutkan wujud|wujud(nya)? (pasti )?tidak|"
    r"tidak (tahu|jelas) (bentuk|wujud|rupa)nya",
    re.I,
)

# Angka dan ukuran ditonjolkan hanya jika narasi memang menyebut kuantitas.
POLA_ANGKA = re.compile(
    r"\b(?:\d+(?:[.,]\d+)?|"
    r"satu|dua|tiga|empat|lima|enam|tujuh|delapan|sembilan|sepuluh|"
    r"sebelas|seratus|seribu|puluh|ratus|ribu|juta|setengah|separuh)"
    r"(?:\s+[a-z]+){0,3}\s+(?:tahun|hari|malam|bulan|mil|meter|"
    r"orang|jiwa|kali|jenis|ayat|pintu|negeri)\b",
    re.I,
)
POLA_KATA_KUNCI = re.compile(
    r"\b(hampir tembus|kembali utuh|tidak ada jalan pulang|"
    r"pintu taubat|hari kiamat|air bah|fitnah terbesar)\b",
    re.I,
)

# Posisi disusun dari ukuran panggung renderer (1080 x 1920), bukan koordinat papan acuan.
POSISI = {
    "bahtera": (540, 1510, 0.38),
    "ngarai": (540, 1770, 0.62),
    "penggali": (540, 1660, 0.72),
    "pemimpin": (760, 1640, 0.72),
    "ombak": (540, 1530, 0.85),
    "gunung": (540, 1510, 0.78),
    "hewan": (540, 1640, 0.58),
    "arus": (540, 1580, 0.82),
    "pancar": (540, 1600, 0.72),
    "surya": (540, 570, 0.9),
    "retakan": (540, 1740, 0.78),
    "kerumunan": (540, 1570, 0.82),
    "koin": (540, 1570, 0.62),
    "petir": (540, 730, 0.9),
    "awan": (540, 760, 0.9),
}


class PengarahSubjek:
    """Mengarahkan subjek narasi dengan keadaan lintas-shot yang deterministik."""

    def __init__(self) -> None:
        self.lubang_dinding = 0.0
        self.dinding_aktif = False
        self.jebol = 0.0

    def _perbarui_dinding(self, teks: str) -> tuple[float, float, float]:
        sebelumnya = self.lubang_dinding
        if re.search(r"\b(dinding|tembok|benteng)\b", teks, re.I):
            self.dinding_aktif = True
        if self.dinding_aktif:
            if POLA_UTUH.search(teks):
                self.lubang_dinding = 0.0
                self.jebol = 0.0
            elif POLA_JEBOL.search(teks):
                self.lubang_dinding = 1.0
                self.jebol = 1.0
            elif POLA_HAMPIR.search(teks):
                self.lubang_dinding = max(self.lubang_dinding, 0.86)
            elif POLA_GALI.search(teks):
                self.lubang_dinding = min(0.78, max(0.18, self.lubang_dinding + 0.2))
            elif re.search(r"\blubang\b", teks, re.I):
                self.lubang_dinding = max(0.32, self.lubang_dinding)
        return sebelumnya, self.lubang_dinding, self.jebol

    @staticmethod
    def _objek(jenis: str, durasi: float, indeks: int, teks: str,
               keadaan_dinding: tuple[float, float, float]) -> dict:
        x, y, skala = POSISI[jenis]
        objek = {"jenis": jenis, "x": x, "y": y, "s": skala}
        if jenis == "bahtera":
            objek.update({"orang": 0, "goyang": 2.2 if re.search(r"berlayar|mengapung|ombak", teks, re.I) else 0.5})
            if re.search(r"membuat|membangun|mulai", teks, re.I):
                objek["jadi"] = 1
        elif jenis == "ngarai":
            awal, akhir, jebol = keadaan_dinding
            objek.update({
                "lubang": [[0, round(awal, 3)], [max(0.4, round(durasi, 2)), round(akhir, 3)]],
                "jebol": [[0, 0.0], [max(0.4, round(durasi, 2)), round(jebol, 3)]],
                "seed": (indeks * 17 + 11) % 97,
            })
        elif jenis == "penggali":
            objek.update({"aktif": 1 if POLA_GALI.search(teks) else 0.35, "n": 6, "seed": (indeks * 13 + 7) % 89})
        elif jenis == "pemimpin":
            objek["angkat"] = [[0, 0.15], [min(max(durasi * 0.35, 0.4), 1.8), 0.82]]
        elif jenis == "ombak":
            objek.update({"tinggi": 0.8, "goyang": 1.4})
        elif jenis == "hewan":
            objek["n"] = 2
        elif jenis == "kerumunan":
            objek["n"] = 36
        elif jenis == "retakan":
            objek.update({"buka": 0.85, "cahaya": "#ff9a4a"})
        elif jenis == "arus":
            objek.update({"mode": "lereng", "maju": [0, 0.25]})
        elif jenis == "pancar":
            objek["tinggi"] = 0.8
        return objek

    @staticmethod
    def _teks_layar(teks: str) -> str | None:
        angka = POLA_ANGKA.search(teks)
        if angka:
            return angka.group(0).strip().upper()
        kunci = POLA_KATA_KUNCI.search(teks)
        if kunci:
            return kunci.group(0).strip().upper()
        return None

    def arahkan(self, teks: str, *, indeks: int, durasi: float,
                klimaks: bool = False) -> dict:
        """Kembalikan benda, teks layar, dan sinyal klimaks untuk satu segmen narasi."""
        if not isinstance(teks, str) or not teks.strip():
            return {"benda": [], "teks": None, "klimaks": False}

        # Jangan menebak atau menggambar wujud makhluk yang tidak memiliki deskripsi sahih.
        wujud_tidak_dijelaskan = bool(POLA_WUJUD_TAK_DIJELASKAN.search(teks))
        awal, akhir, jebol = self._perbarui_dinding(teks)
        ditemukan = {
            jenis for jenis, pola in POLA_SUBJEK
            if pola.search(teks) and not (wujud_tidak_dijelaskan and jenis in {"hewan"})
        }

        # Dinding adalah subjek berkelanjutan: tetap hadir pada shot pemimpin/penggali
        # selama narasi masih membahas rangkaian peristiwa dinding yang sama.
        if self.dinding_aktif and POLA_KONTINUITAS_DINDING.search(teks):
            ditemukan.add("ngarai")
        if "penggali" in ditemukan and self.dinding_aktif:
            ditemukan.add("ngarai")

        # Kapal yang berlayar harus berada dalam konteks air, bukan diletakkan di darat.
        if "bahtera" in ditemukan and re.search(r"berlayar|mengapung|ombak|air", teks, re.I):
            ditemukan.add("ombak")

        # Jangan menggambar ulang jenis yang sama dua kali dalam satu shot.
        urutan = (
            "ngarai", "bahtera", "penggali", "pemimpin", "ombak", "gunung",
            "hewan", "arus", "pancar", "surya", "retakan", "kerumunan",
            "koin", "petir", "awan",
        )
        benda = [
            self._objek(jenis, durasi, indeks, teks, (awal, akhir, jebol))
            for jenis in urutan if jenis in ditemukan
        ]
        sedang_jebol = bool(POLA_KLIMAKS.search(teks)) and (
            "ngarai" in ditemukan or "retakan" in ditemukan or "bahtera" in ditemukan
        )
        return {
            "benda": deepcopy(benda),
            "teks": self._teks_layar(teks),
            "klimaks": sedang_jebol or klimaks,
        }
