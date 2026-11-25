"""Penjaga kartu dalil: verifikasi ulang SETIAP `kartu_dalil` terhadap sumber dalil sebelum render.

BATAS WAJIB CLAUDE.md: "hanya dalil sahih/hasan, sumber tampil di layar, nomor dicek";
dalil (Qur'an/Hadis) tidak boleh dikarang AI.

Untuk tiap benda `{"jenis": "kartu_dalil", kitab, no, arab, teks, ...}`:
1. Rujukan (kitab + no) diurai: Qur'an ("QS. An-Naml" + "82", "QS 27:82", "Ayat 164", rentang
   "1-3") atau hadis ("HR. Bukhari" + "6507"). Nomor wajib ada.
2. Sumber diambil lewat jalur resmi repo: `dalil.quran_foundation.ambil_ayat` dan
   `dalil.hadis_dataset.ambil_hadis` (keduanya membaca cache lokal `dalil/cache*/` dulu,
   lalu API). Hadis dha'if ditolak oleh modul itu sendiri.
3. Bila kartu memuat `arab`, kerangka hurufnya (tanpa harakat/tanda waqaf/variasi alif,
   tanpa spasi) WAJIB merupakan potongan utuh dari teks sumber. Kutipan sebagian ayat/hadis
   boleh; satu huruf karangan pun membuat kartu ditolak.
4. Kartu yang rujukannya bukan Qur'an/hadis (mis. "FATWA MUI") tetapi memuat teks Arab ->
   DITOLAK (Arab di kartu dalil harus bisa diverifikasi). Tanpa Arab -> hanya peringatan.

GAGAL TERTUTUP: bila sumber tidak bisa dihubungi (tanpa jaringan/secret dan tanpa cache),
kartu dinyatakan TIDAK DAPAT DIVERIFIKASI dan render DITOLAK. Tidak ada jalan pintas di CLI.

Yang TIDAK diverifikasi: teks terjemahan/arti (`teks`) -- di video terkirim banyak yang
"terjemahan ringkas", jadi tidak bisa dicocokkan kata per kata; diberi peringatan saja.
Dimiliki sepenuhnya oleh paket genre Kisah Islami; renderer memanggilnya melalui kait kontrak PaketGenre.
"""
from __future__ import annotations

import re
import sys
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

# ---------------------------------------------------------------------------
# Sumber dalil (bisa diganti untuk uji; CLI selalu memakai SumberResmi)
# ---------------------------------------------------------------------------


class SumberTidakTersedia(RuntimeError):
    """Sumber tidak bisa dijangkau / menolak (jaringan, secret, ayat tidak ada, dha'if...)."""


class SumberDalil(Protocol):
    def teks_ayat(self, surah: int, ayat: int) -> str: ...
    def teks_hadis(self, kitab: str, nomor: int) -> str: ...


class SumberResmi:
    """Adapter ke sumber dalil milik paket genre Kisah Islami NewMotion."""

    def teks_ayat(self, surah: int, ayat: int) -> str:
        from newmotion.paket_genre.kisah_islami.dalil import ambil_ayat
        try:
            return ambil_ayat(surah, ayat)["teks_arab"]
        except Exception as e:  # Jaringan, secret, izin, atau ayat tidak tersedia -> gagal tertutup
            raise SumberTidakTersedia(f"Quran Foundation: {type(e).__name__}: {str(e)[:200]}") from e

    def teks_hadis(self, kitab: str, nomor: int) -> str:
        from newmotion.paket_genre.kisah_islami.dalil import ambil_hadis
        try:
            return ambil_hadis(kitab, nomor)["teks_arab"]
        except Exception as e:  # Dataset tidak tersedia atau hadis tidak lolos -> gagal tertutup
            raise SumberTidakTersedia(f"dataset hadis Sunnah.com: {type(e).__name__}: {str(e)[:200]}") from e


# ---------------------------------------------------------------------------
# Rujukan
# ---------------------------------------------------------------------------

JUMLAH_AYAT = (
    7, 286, 200, 176, 120, 165, 206, 75, 129, 109, 123, 111, 43, 52, 99, 128, 111, 110, 98, 135,
    112, 78, 118, 64, 77, 227, 93, 88, 69, 60, 34, 30, 73, 54, 45, 83, 182, 88, 75, 85, 54, 53,
    89, 59, 37, 35, 38, 29, 18, 45, 60, 49, 62, 55, 78, 96, 29, 22, 24, 13, 14, 11, 11, 18, 12,
    12, 30, 52, 52, 44, 28, 28, 20, 56, 40, 31, 50, 40, 46, 42, 29, 19, 36, 25, 22, 17, 19, 26,
    30, 20, 15, 21, 11, 8, 8, 19, 5, 8, 8, 11, 11, 8, 3, 9, 5, 4, 7, 3, 6, 3, 5, 4, 5, 6,
)

_NAMA_SURAH = (
    "Al-Fatihah", "Al-Baqarah", "Ali Imran|Al-Imran", "An-Nisa", "Al-Maidah", "Al-An'am", "Al-A'raf",
    "Al-Anfal", "At-Taubah|At-Tawbah|Bara'ah", "Yunus", "Hud", "Yusuf", "Ar-Ra'd", "Ibrahim", "Al-Hijr",
    "An-Nahl", "Al-Isra|Bani Israil", "Al-Kahf|Al-Kahfi", "Maryam", "Taha|Thaha", "Al-Anbiya",
    "Al-Hajj", "Al-Mu'minun", "An-Nur", "Al-Furqan", "Asy-Syu'ara", "An-Naml", "Al-Qasas|Al-Qashash",
    "Al-Ankabut", "Ar-Rum", "Luqman", "As-Sajdah", "Al-Ahzab", "Saba", "Fatir|Fathir", "Yasin|Ya Sin",
    "As-Saffat|Ash-Shaffat", "Sad|Shad", "Az-Zumar", "Ghafir|Al-Mu'min", "Fussilat|Fushshilat",
    "Asy-Syura", "Az-Zukhruf", "Ad-Dukhan", "Al-Jasiyah|Al-Jatsiyah", "Al-Ahqaf", "Muhammad",
    "Al-Fath", "Al-Hujurat", "Qaf", "Az-Zariyat|Adz-Dzariyat", "At-Tur|Ath-Thur", "An-Najm",
    "Al-Qamar", "Ar-Rahman", "Al-Waqi'ah", "Al-Hadid", "Al-Mujadilah|Al-Mujadalah", "Al-Hasyr",
    "Al-Mumtahanah", "As-Saff|Ash-Shaff", "Al-Jumu'ah", "Al-Munafiqun", "At-Tagabun|At-Taghabun",
    "At-Talaq|Ath-Thalaq", "At-Tahrim", "Al-Mulk", "Al-Qalam", "Al-Haqqah", "Al-Ma'arij", "Nuh",
    "Al-Jinn", "Al-Muzzammil", "Al-Muddassir|Al-Muddatstsir", "Al-Qiyamah", "Al-Insan|Ad-Dahr",
    "Al-Mursalat", "An-Naba", "An-Nazi'at", "Abasa", "At-Takwir", "Al-Infitar|Al-Infithar",
    "Al-Mutaffifin|Al-Muthaffifin", "Al-Insyiqaq", "Al-Buruj", "At-Tariq|Ath-Thariq", "Al-A'la",
    "Al-Gasyiyah|Al-Ghasyiyah", "Al-Fajr", "Al-Balad", "Asy-Syams", "Al-Lail|Al-Layl", "Ad-Duha|Adh-Dhuha",
    "Asy-Syarh|Al-Insyirah|Alam Nasyrah", "At-Tin", "Al-Alaq", "Al-Qadr", "Al-Bayyinah", "Az-Zalzalah",
    "Al-Adiyat", "Al-Qari'ah", "At-Takasur|At-Takatsur", "Al-Asr|Al-Ashr", "Al-Humazah", "Al-Fil",
    "Quraisy|Quraish", "Al-Ma'un", "Al-Kausar|Al-Kautsar", "Al-Kafirun", "An-Nasr|An-Nashr",
    "Al-Lahab|Al-Masad", "Al-Ikhlas", "Al-Falaq", "An-Nas",
)


def kunci_surah(nama: str) -> str:
    """Nama surah ejaan Latin apa pun -> kunci kanonik (ejaan Kemenag/Inggris/tanpa apostrof)."""
    t = unicodedata.normalize("NFKD", nama).encode("ascii", "ignore").decode().lower()
    t = re.sub(r"['`]", "", t).strip()
    t = re.sub(r"^(al|an|ar|as|at|ad|az|asy|ash|adz|adh|ath|ats)[\s\-]+", "", t)
    t = re.sub(r"[^a-z]", "", t)
    for a, b in (("ts", "s"), ("sy", "s"), ("sh", "s"), ("dz", "z"), ("dh", "d"), ("th", "t"),
                 ("kh", "k"), ("gh", "g"), ("q", "k"), ("w", "u")):
        t = t.replace(a, b)
    return re.sub(r"(.)\1+", r"\1", t)


SURAH: dict[str, int] = {}
for _i, _alias in enumerate(_NAMA_SURAH, 1):
    for _n in _alias.split("|"):
        SURAH[kunci_surah(_n)] = _i

KITAB_HADIS = (  # (pola, kunci dataset)
    (r"bukh[aā]r[iī]", "bukhari"), (r"muslim", "muslim"), (r"ab[uū]\s*d[aā]w[uū]d|ab[uū]\s*da'?ud", "abudawud"),
    (r"tirmi(dz|dh|z)[iī]|turmu(dz|dh)[iī]", "tirmidhi"), (r"nas[aā]'?[iīy]", "nasai"),
    (r"ibnu?\s*m[aā]jah", "ibnmajah"), (r"m[aā]lik|muwat?th?a", "malik"),
)


@dataclass
class Rujukan:
    jenis: str  # "quran" | "hadis"
    kitab: str = ""  # kunci dataset hadis
    surah: int = 0
    ayat: tuple[int, ...] = ()
    nomor: int = 0

    def __str__(self) -> str:
        if self.jenis == "quran":
            a = f"{self.ayat[0]}-{self.ayat[-1]}" if len(self.ayat) > 1 else str(self.ayat[0])
            return f"QS {self.surah}:{a}"
        return f"HR {self.kitab} {self.nomor}"


class RujukanTidakValid(ValueError):
    pass


def _rentang(teks: str) -> tuple[int, ...]:
    m = re.search(r"(\d{1,3})(?:\s*[-–]\s*(\d{1,3}))?", teks)
    if not m:
        return ()
    a, b = int(m.group(1)), int(m.group(2) or m.group(1))
    if b < a or b - a > 20:
        raise RujukanTidakValid(f"rentang ayat tidak wajar: {m.group(0)!r}")
    return tuple(range(a, b + 1))


def urai_rujukan(kitab: Any, no: Any) -> Rujukan | None:
    """None = bukan rujukan Qur'an/hadis. RujukanTidakValid = rujukan Qur'an/hadis yang rusak."""
    k = unicodedata.normalize("NFKC", str(kitab or "")).strip()
    n = unicodedata.normalize("NFKC", str(no if no is not None else "")).strip()
    kl = k.lower()
    if re.search(r"\bq\.?\s?s\b|qur'?[aā]n|\bsurah?\b|\bsurat\b", kl):
        m = re.search(r"(\d{1,3})\s*[:.]\s*(\d{1,3}(?:\s*[-–]\s*\d{1,3})?)", k)
        if m:
            surah, ayat = int(m.group(1)), _rentang(m.group(2))
            if n and _rentang(n) and _rentang(n) != ayat:
                raise RujukanTidakValid(f"nomor di kitab ({m.group(0)}) bertentangan dengan no={n!r}")
        else:
            nama = re.sub(r"\bq\.?\s?s\b\.?|qur'?[aā]n|\bsurah?\b|\bsurat\b|\bayat\b|[\[\]():,.]|\d", " ", k, flags=re.I)
            nama = " ".join(nama.split())
            surah = SURAH.get(kunci_surah(nama)) if nama else None
            if not surah:
                raise RujukanTidakValid(f"nama surah tidak dikenali: {nama!r} (kitab={k!r})")
            ayat = _rentang(n) or _rentang(re.sub(r"\[\d+\]", "", k))
        if not 1 <= surah <= 114:
            raise RujukanTidakValid(f"surah {surah} tidak ada (1-114)")
        if not ayat:
            raise RujukanTidakValid(f"nomor ayat tidak ada untuk {k!r} -- nomor wajib dicek")
        if ayat[-1] > JUMLAH_AYAT[surah - 1] or ayat[0] < 1:
            raise RujukanTidakValid(f"QS {surah} hanya {JUMLAH_AYAT[surah - 1]} ayat, kartu menulis ayat {ayat[-1]}")
        return Rujukan("quran", surah=surah, ayat=ayat)
    hadis = re.search(r"\bh\.?\s?r\b|hadi[ts]|riwayat", kl)
    for pola, kunci in KITAB_HADIS:
        if re.search(pola, kl):
            m = re.search(r"\d+", n) or re.search(r"\d+", k)
            if not m:
                raise RujukanTidakValid(f"nomor hadis tidak ada untuk {k!r} -- nomor wajib dicek")
            return Rujukan("hadis", kitab=kunci, nomor=int(m.group(0)))
    if hadis:
        raise RujukanTidakValid(f"kitab hadis {k!r} tidak ada di sumber verifikasi "
                                f"(tersedia: Bukhari, Muslim, Abu Dawud, Tirmidzi, Nasa'i, Ibnu Majah, Malik)")
    return None


# ---------------------------------------------------------------------------
# Pencocokan teks Arab
# ---------------------------------------------------------------------------

_ALIF = set("اأإآٱٲٳٵ")
_GANTI = {"ى": "ي", "ئ": "ي", "ی": "ي", "ؤ": "و", "ة": "ه", "ک": "ك"}


def kerangka_arab(teks: str) -> str:
    """Kerangka huruf: buang harakat, tanda Qur'ani (waqaf, ۞, nomor ayat), tatwil, alif dalam
    bentuk apa pun (rasm Utsmani vs imla'i berbeda di alif: ٱلْكِتَٰبُ vs الكتاب), hamzah lepas,
    spasi, dan semua yang bukan huruf Arab. Satu huruf konsonan berbeda tetap terdeteksi."""
    out = []
    for ch in unicodedata.normalize("NFC", teks):
        if ch in _ALIF or ch == "ء" or ch == "ـ":
            continue
        ch = _GANTI.get(ch, ch)
        if "ء" <= ch <= "ي" or ch in "پچکگ":
            out.append(ch)
    return "".join(out)


MIN_KERANGKA = 6  # potongan Arab lebih pendek dari ini terlalu lemah untuk dibuktikan


# ---------------------------------------------------------------------------
# Pemeriksaan spek
# ---------------------------------------------------------------------------


@dataclass
class HasilKartu:
    lokasi: str
    kitab: str
    status: str  # "lulus" | "ditolak" | "tidak_terverifikasi" | "bukan_dalil"
    alasan: str = ""
    peringatan: list[str] = field(default_factory=list)

    @property
    def memblokir(self) -> bool:
        return self.status in ("ditolak", "tidak_terverifikasi")

    def __str__(self) -> str:
        return f"{self.lokasi} [{self.kitab}] {self.status.upper()}" + (f": {self.alasan}" if self.alasan else "")


class DalilTidakTerverifikasiError(ValueError):
    def __init__(self, hasil: list[HasilKartu]):
        self.hasil = hasil
        blok = [h for h in hasil if h.memblokir]
        baris = "\n".join(f"  - {h}" for h in blok)
        super().__init__(
            f"DITOLAK penjaga dalil: {len(blok)} kartu_dalil tidak lolos verifikasi sumber "
            f"(dalil tidak boleh dikarang; isi kartu harus cocok dengan sumber):\n{baris}"
        )


def _kartu(spek: Any):
    def jalan(o: Any, lok: str):
        if isinstance(o, dict):
            if o.get("jenis") == "kartu_dalil":
                yield lok, o
            for k, v in o.items():
                if isinstance(v, (dict, list)):
                    yield from jalan(v, f"{lok}.{k}")
        elif isinstance(o, list):
            for i, x in enumerate(o):
                yield from jalan(x, f"{lok}[{i}]")
    yield from jalan(spek, "spek")


def periksa_kartu(kartu: dict, lokasi: str, sumber: SumberDalil) -> HasilKartu:
    kitab = f"{kartu.get('kitab', '')} {kartu.get('no', '')}".strip()
    arab = kartu.get("arab")
    ada_arab = isinstance(arab, str) and arab.strip()
    h = HasilKartu(lokasi, kitab, "lulus")
    try:
        ruj = urai_rujukan(kartu.get("kitab"), kartu.get("no"))
    except RujukanTidakValid as e:
        h.status, h.alasan = "ditolak", f"rujukan tidak valid: {e}"
        return h
    if ruj is None:
        if ada_arab:
            h.status, h.alasan = "ditolak", "memuat teks Arab tetapi rujukannya bukan Qur'an/hadis yang bisa diverifikasi"
        else:
            h.status = "bukan_dalil"
            h.peringatan.append("rujukan bukan Qur'an/hadis (tidak diverifikasi oleh penjaga dalil); pastikan sumbernya manual")
        return h
    try:
        if ruj.jenis == "quran":
            sumber_teks = "".join(sumber.teks_ayat(ruj.surah, a) for a in ruj.ayat)
        else:
            if callable(getattr(sumber, "detail_hadis", None)):
                detail = sumber.detail_hadis(ruj.kitab, ruj.nomor)
                sumber_teks = detail["teks_arab"]
                if detail.get("penilaian_berbeda"):
                    h.peringatan.append(
                        "DERAJAT_DIPERSELISIHKAN: dinilai daif oleh "
                        + ", ".join(detail["penilaian_berbeda"])
                    )
                if detail.get("bukan_marfu"):
                    h.peringatan.append(
                        "BUKAN_MARFU: riwayat mauquf/maqtu; jangan disebut sebagai sabda Nabi ﷺ"
                    )
            else:
                sumber_teks = sumber.teks_hadis(ruj.kitab, ruj.nomor)
    except SumberTidakTersedia as e:
        h.status, h.alasan = "tidak_terverifikasi", f"{ruj}: sumber tidak bisa memastikan -- {e}"
        return h
    if not sumber_teks:
        h.status, h.alasan = "tidak_terverifikasi", f"{ruj}: sumber tidak mengirim teks Arab"
        return h
    if ada_arab:
        ka, ks = kerangka_arab(arab), kerangka_arab(sumber_teks)
        if len(ka) < MIN_KERANGKA:
            h.status, h.alasan = "ditolak", f"{ruj}: teks Arab terlalu pendek ({len(ka)} huruf) untuk dibuktikan"
        elif ka not in ks:
            h.status, h.alasan = "ditolak", f"{ruj}: teks Arab di kartu TIDAK cocok dengan sumber ({arab[:40]!r}...)"
    else:
        h.peringatan.append(f"{ruj}: kartu tanpa teks Arab; hanya nomor yang terbukti ada")
    h.peringatan.append("teks terjemahan/arti tidak diverifikasi otomatis (boleh terjemahan ringkas)")
    return h


def periksa_dalil(spek: Any, sumber: SumberDalil | None = None) -> list[HasilKartu]:
    sumber = sumber or SumberResmi()
    return [periksa_kartu(o, lok, sumber) for lok, o in _kartu(spek)]


def wajib_lulus_dalil(spek: Any, sumber: SumberDalil | None = None) -> list[HasilKartu]:
    hasil = periksa_dalil(spek, sumber)
    if any(h.memblokir for h in hasil):
        raise DalilTidakTerverifikasiError(hasil)
    return hasil
