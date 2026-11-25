"""Penjaga tokoh suci: menolak spek yang MENGGAMBAR nabi/malaikat/Allah/sahabat.

BATAS WAJIB CLAUDE.md: "Nabi, malaikat, sahabat tidak digambar (cahaya `nur` + nama);
Allah tidak digambar."

Yang diperiksa adalah CARA tokoh itu tampil, bukan sekadar namanya disebut:
- `nur` (cahaya) + nama nabi/malaikat = konvensi resmi -> LULUS.
- boneka `gaya: "siluet"` (tanpa wajah, lih. cerita.js: muka tidak digambar untuk siluet)
  + nama sahabat = konvensi terkirim (utang1.json, Abu Qatadah) -> LULUS.
- boneka berwajah (gaya umum/anwar/dajjal/bawaan, termasuk tampak belakang yang tetap
  menggambar kepala/rambut/kulit), tokoh foto/kartun (`spec.tokoh`), gambar raster
  (`tipe: gambar`, `latar_gambar`) atau benda bersosok manusia yang diberi identitas
  tokoh suci -> DITOLAK.
- nabi/malaikat sebagai boneka siluet -> DITOLAK (konvensinya nur, bukan badan).
- Allah: tidak boleh diwakili sosok APA PUN, termasuk nur.

Penjaga ini hanya mendeteksi dan menolak; TIDAK mengubah/menghapus apa pun di spek.
Teks narasi, subtitle, kartu dalil, papan nama gedung, gelembung dialog, dsb. TIDAK
diperiksa: menyebut nama bukan menggambar.

Batas yang tidak bisa ditutup kode: sosok TANPA nama/identitas di spek (mis. boneka
berwajah yang di narasi "dimaksudkan" sebagai nabi) tidak bisa dikenali; isi piksel
gambar raster juga tidak diperiksa (hanya nama berkas + field identitas).
Dipasang sebagai gerbang wajib di `papan_buat.py` (lihat `jaga_spek`).
"""
from __future__ import annotations

import os
import re
import unicodedata
from dataclasses import dataclass
from typing import Any, Iterator

# Tingkat: 0 = Allah, 1 = nabi/rasul/malaikat, 2 = sahabat/keluarga nabi.
ALLAH, NABI_MALAIKAT, SAHABAT = 0, 1, 2
NAMA_TINGKAT = {ALLAH: "Allah", NABI_MALAIKAT: "nabi/rasul/malaikat", SAHABAT: "sahabat/keluarga nabi"}

# Field yang menyatakan identitas sebuah sosok (bukan teks yang ditampilkan sebagai tulisan).
FIELD_IDENTITAS = ("nama", "tokoh", "identitas", "karakter", "nama_tokoh", "peran", "siapa", "sosok")

# Benda cerita.js yang berupa sosok manusia (identitas pada benda lain = papan nama/tulisan).
BENDA_SOSOK = {"penggali", "pemimpin", "kerumunan", "saf", "jenazah", "bayang_misteri"}
BENDA_CAHAYA = {"nur"}

_PROPHETS = (
    "adam", "idris", "nuh", "hud", "saleh", "shaleh", "shalih", "salih", "ibrahim", "luth", "lut",
    "ismail", "ishaq", "ishak", "yaqub", "yakub", "yusuf", "ayyub", "ayub", "syuaib", "syuab",
    "musa", "harun", "zulkifli", "dzulkifli", "daud", "dawud", "sulaiman", "ilyas", "ilyasa",
    "alyasa", "yunus", "zakaria", "zakariya", "yahya", "isa", "muhammad",
)

_RE_ALLAH = re.compile(r"\b(allah|tuhan|rabb|sang pencipta|allah swt|allah taala)\b")
_RE_NABI = re.compile(
    r"\b(nabi|nabiyullah|rasul|rasulullah|rasul allah|malaikat|malakul maut|jibril|jibrail|"
    r"mikail|mikael|mikal|israfil|izrail|azrail|munkar|nakir|raqib|atid|harut|marut|ruhul qudus)\b"
    r"|alaihissalam|alaihimussalam|alaihis salam|shallallahu|sallallahu|\bsaw\b|\bs a w\b|\ba s\b"
)
_RE_SAHABAT = re.compile(
    r"\b(sahabat nabi|sahabat rasul|sahabat rasulullah|ummul mukminin|ummul muminin|ahlul bait|"
    r"radhiyallahu|radiyallahu|radhiallahu|r a|"
    r"abu bakar|abu bakr|umar bin (al )?khatt?ab|utsman bin affan|usman bin affan|uthman bin affan|"
    r"ali bin abi th?alib|khadijah binti khuwailid|aisyah binti abu bakar|fatimah az ?zahra|"
    r"hamzah bin abdul mut?th?alib|bilal bin rabah|abu hurairah|abu qatadah|anas bin malik|"
    r"khalid bin (al )?walid|salman al ?farisi|abdullah bin masud|muadz bin jabal|muaz bin jabal|"
    r"zaid bin haritsah|saad bin abi waqq?ash|abu dzar|abu ubaidah|abdurrahman bin auf|"
    r"thalhah bin ubaidillah|zubair bin (al )?awwam|ibnu abbas|abdullah bin abbas|ibnu umar|"
    r"abdullah bin umar|hasan bin ali|husain bin ali|husein bin ali|asma binti abu bakar|ummu salamah|"
    r"hafshah binti umar|hafsah binti umar)\b"
)
# Honorifik bentuk lambang/Arab (diperiksa pada teks mentah, sebelum NFKC menguraikannya).
_LAMBANG_ALLAH = ("ﷻ", "ﷻ", "جل جلاله", "سبحانه وتعالى", "ﷻ")
_LAMBANG_NABI = ("ﷺ", "ﷶ", "ﷲ", "ﷺ", "صلى الله عليه وسلم", "عليه السلام")
_LAMBANG_SAHABAT = ("رضي الله عنه", "رضي الله عنها", "رضي الله عنهم")


def _normal(teks: str) -> str:
    t = unicodedata.normalize("NFKC", teks).casefold()
    t = re.sub(r"[‘’ʼʿʾ'`´]", "", t)  # apostrof/ain: mu'adz -> muadz
    t = re.sub(r"[^\w\s]|_", " ", t)  # titik/strip/kurung -> spasi ("a.s." -> "a s")
    return " ".join(t.split())


def tingkat_suci(nama: Any) -> int | None:
    """Tingkat tokoh suci yang ditunjuk sebuah string identitas, atau None bila bukan."""
    if not isinstance(nama, str) or not nama.strip():
        return None
    mentah = nama
    n = _normal(nama)
    if "dajjal" in n:  # "Al-Masih Ad-Dajjal" dll: bukan tokoh suci (punya gaya sendiri di cerita.js)
        return None
    if any(s in mentah for s in _LAMBANG_ALLAH) or _RE_ALLAH.search(n):
        return ALLAH
    if any(s in mentah for s in _LAMBANG_NABI) or _RE_NABI.search(n):
        return NABI_MALAIKAT
    # Nama nabi tanpa gelar: hanya bila SELURUH identitas = nama itu (mis. "Musa"), supaya
    # tokoh biasa seperti "Pak Yusuf" atau "Adam Malik" tidak ikut tertolak.
    if n in _PROPHETS:
        return NABI_MALAIKAT
    if any(s in mentah for s in _LAMBANG_SAHABAT) or _RE_SAHABAT.search(n):
        return SAHABAT
    return None


@dataclass(frozen=True)
class Pelanggaran:
    lokasi: str
    identitas: str
    tingkat: int
    alasan: str

    def __str__(self) -> str:
        return f"{self.lokasi}: {self.identitas!r} ({NAMA_TINGKAT[self.tingkat]}) -- {self.alasan}"


class TokohSuciDigambarError(ValueError):
    def __init__(self, pelanggaran: list[Pelanggaran]):
        self.pelanggaran = pelanggaran
        baris = "\n".join(f"  - {p}" for p in pelanggaran)
        super().__init__(
            f"DITOLAK penjaga tokoh suci: {len(pelanggaran)} sosok suci digambar tidak sesuai BATAS WAJIB "
            f"(nabi/malaikat = cahaya `nur` + nama; sahabat = `nur` atau boneka `gaya:\"siluet\"` tanpa wajah; "
            f"Allah tidak diwakili sosok apa pun):\n{baris}"
        )


def _identitas(obj: dict) -> Iterator[tuple[str, str, int]]:
    for f in FIELD_IDENTITAS:
        t = tingkat_suci(obj.get(f))
        if t is not None:
            yield f, obj[f], t


def _bagian_jalur(v: Any) -> list[str]:
    """Setiap bagian jalur berkas (folder dan nama berkas tanpa ekstensi), '_'/'-' jadi spasi."""
    if not isinstance(v, str) or not v or v.startswith("data:"):
        return []
    bagian = [b for b in re.split(r"[\\/]", v.split("?")[0]) if b and b not in (".", "..")]
    if bagian:
        bagian[-1] = os.path.splitext(bagian[-1])[0]
    return [b.replace("_", " ").replace("-", " ") for b in bagian if b]


def _tingkat_jalur(v: Any) -> int | None:
    t = [x for x in (tingkat_suci(b) for b in _bagian_jalur(v)) if x is not None]
    return min(t) if t else None


def _cek_boneka(b: dict, lok: str, out: list[Pelanggaran]) -> None:
    gaya = b.get("gaya", "umum")
    for f, nama, t in _identitas(b):
        if t == SAHABAT and gaya == "siluet":
            continue  # konvensi terkirim: siluet tanpa wajah + nama
        if t == SAHABAT:
            alasan = f"boneka gaya {gaya!r} menggambar wajah/badan; sahabat hanya boleh `nur` atau gaya \"siluet\""
        elif t == ALLAH:
            alasan = "Allah tidak boleh digambar dalam bentuk apa pun"
        else:
            alasan = f"boneka (gaya {gaya!r}) menggambar sosok; nabi/malaikat hanya boleh benda `nur` + nama"
        out.append(Pelanggaran(f"{lok}.{f}", nama, t, alasan))


def _cek_benda(o: dict, lok: str, out: list[Pelanggaran]) -> None:
    jenis = o.get("jenis")
    tj = tingkat_suci(jenis.replace("_", " ")) if isinstance(jenis, str) else None
    if tj is not None:
        out.append(Pelanggaran(f"{lok}.jenis", jenis, tj, "jenis benda berupa tokoh suci (bukan `nur`)"))
    if jenis in BENDA_CAHAYA:
        for f, nama, t in _identitas(o):
            if t == ALLAH:
                out.append(Pelanggaran(f"{lok}.{f}", nama, t, "Allah tidak boleh diwakili sosok, termasuk cahaya `nur`"))
        return
    if jenis in BENDA_SOSOK:
        for f, nama, t in _identitas(o):
            out.append(Pelanggaran(f"{lok}.{f}", nama, t, f"benda bersosok manusia `{jenis}` diberi identitas tokoh suci"))


def _cek_gambar(o: dict, kunci_src: str, lok: str, out: list[Pelanggaran]) -> None:
    """Gambar raster/tokoh foto: isi piksel tak bisa diperiksa, tapi identitas & nama berkas bisa."""
    for f, nama, t in _identitas(o):
        out.append(Pelanggaran(f"{lok}.{f}", nama, t, "gambar/tokoh bergambar tidak boleh menampilkan tokoh suci"))
    for k in (kunci_src, "gambar", "folder"):
        t = _tingkat_jalur(o.get(k))
        if t is not None:
            out.append(Pelanggaran(f"{lok}.{k}", o.get(k), t, "nama berkas gambar menunjuk tokoh suci"))


def periksa_tokoh_suci(spek: Any) -> list[Pelanggaran]:
    """Kembalikan daftar pelanggaran (kosong = lulus). Tidak mengubah spek."""
    out: list[Pelanggaran] = []
    if not isinstance(spek, dict):
        return out
    if spek.get("tokoh"):
        tk = spek["tokoh"] if isinstance(spek["tokoh"], dict) else {"folder": spek["tokoh"]}
        _cek_gambar(tk, "gambar", "spek.tokoh", out)

    def jalan(node: Any, lok: str, dalam_boneka: bool = False) -> None:
        if isinstance(node, dict):
            if dalam_boneka:
                _cek_boneka(node, lok, out)
            elif "jenis" in node:
                _cek_benda(node, lok, out)
            if node.get("tipe") == "gambar":
                _cek_gambar(node, "src", lok, out)
            tl = _tingkat_jalur(node.get("latar_gambar"))
            if tl is not None:
                out.append(Pelanggaran(f"{lok}.latar_gambar", node["latar_gambar"], tl,
                                       "nama berkas gambar latar menunjuk tokoh suci"))
            for k, v in node.items():
                if k == "tokoh" and lok == "spek":
                    continue
                if isinstance(v, (dict, list)):
                    jalan(v, f"{lok}.{k}", dalam_boneka=(k == "boneka"))
        elif isinstance(node, list):
            for i, x in enumerate(node):
                # Item langsung dari list "boneka" = boneka; list bersarang tetap ditelusuri.
                jalan(x, f"{lok}[{i}]", dalam_boneka=dalam_boneka and isinstance(x, dict))

    jalan(spek, "spek")
    return out


def wajib_lulus_tokoh_suci(spek: Any) -> None:
    """Gerbang: lempar TokohSuciDigambarError bila ada pelanggaran."""
    p = periksa_tokoh_suci(spek)
    if p:
        raise TokohSuciDigambarError(p)
