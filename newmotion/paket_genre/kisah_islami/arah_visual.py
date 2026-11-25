"""Lapisan kecerdasan VISUAL untuk Direktur (20 Nov 2026) -- tetap TANPA LLM, murni aturan.

Direktur versi awal (papan/direktur.py) selalu memakai SATU boneka "kamu" polos (badan siluet,
kulit & rambut bawaan), latar bawaan dua gunung kembar + langit gelap, lengan "turun", dan
kamera lebar statis yang nyaris sama tiap adegan. Hasilnya benar tapi monoton begitu dipakai
untuk banyak video. Modul ini menambah tiga lapis keputusan, semuanya dari kosakata yang SUDAH
ada di papan/cerita.js (tidak menambah gambar baru):

1. TAMPILAN TOKOH "kamu" (`pilih_tampilan`): kulit, rambut, kerudung, pakaian dipilih dari
   konteks naskah (kota/kampung/ibadah/dingin/akhirat) + seed per judul, satu tampilan untuk
   satu video (tokohnya orang yang sama dari awal sampai akhir), berbeda antar video. Bisa
   dikunci pemilik/pengguna lewat `kunci` (lihat KUNCI_TAMPILAN_BOLEH).
2. LINGKUNGAN (`pilih_tema`, `rakit_latar`): tema latar dari skor kata kunci seluruh naskah
   (laut, gurun, kota, kampung, kubur, neraka, surga, mahsyar, ibadah, gua, gunung, bumi
   terbelah, langit terbuka), tiap tema punya beberapa KOMPOSISI berbeda yang digilir per shot
   (kesatuan palet, tapi tidak identik), plus ruang dalam (kamar, ruang tamu, kantor, ...) dan
   aksen per kalimat (cahaya hidayah, makam, api, timbangan, ...).
3. POSE, GESTUR, FRAMING (`pilih_pose`, `rencana_framing`): >20 gestur bernama dari POSE
   cerita.js dipetakan dari emosi + konteks kalimat, mode "tokoh hidup" (kedip, goyang,
   reaksi, simbol), dan katalog framing (lebar, samping, sedang, dekat, jauh-dari-belakang,
   turun dari langit, dorong, tarik mundur) yang dirangkai tanpa mengulang tipe yang sama
   berturut-turut.

KENAPA "kamu" SELALU BERPAKAIAN MASA KINI, BUKAN MENGIKUTI ZAMAN KISAH: boneka "kamu" adalah
PENONTON hari ini yang menyaksikan/bereaksi, bukan tokoh dalam kisah. Kalau ia diberi gamis +
janggut di latar gurun saat narasi menyebut nabi/sahabat, gambar itu bisa terbaca sebagai
penggambaran tokoh suci -- melanggar BATAS WAJIB. Jadi zaman kisah HANYA memengaruhi
lingkungan; pakaian "kamu" tetap pakaian Indonesia masa kini (dan janggut tidak pernah dipilih
otomatis). Lihat `_pagar_tampilan`.

KENAPA AKHIRAT = BADAN SILUET: pada video Mahsyar/neraka yang sudah tayang, badan tokoh sengaja
siluet "tanah liat berdebu" (manusia dibangkitkan, bukan orang berbaju sehari-hari). Itu
dipertahankan; yang divariasikan hanya kulit/rambut/kerudung.
"""
from __future__ import annotations

import hashlib
import random
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent


def acak(*kunci) -> random.Random:
    """Random berseed STABIL (judul + nama lapisan + indeks): render ulang naskah yang sama
    menghasilkan pilihan yang sama (bisa diuji/dibandingkan), video lain dapat pilihan lain."""
    s = "|".join(str(k) for k in kunci)
    return random.Random(int(hashlib.sha1(s.encode()).hexdigest(), 16) % (2 ** 32))


def _skor(pola: list[str], teks: str) -> int:
    """Jumlah pola BERBEDA yang muncul (bukan jumlah kemunculan) -- satu kata yang diulang-ulang
    tidak boleh mengalahkan tema yang disinggung dari banyak sisi."""
    return sum(1 for p in pola if re.search(p, teks, re.IGNORECASE))


# Nama tokoh suci/sakral. Dipakai BUKAN untuk menekan emosi (lihat catatan di direktur.py), tapi
# untuk (a) tidak menaruh figuran manusia di shot yang sedang membicarakan mereka (figuran bisa
# disangka penggambaran tokoh itu) dan (b) pagar tampilan "kamu".
POLA_SAKRAL = re.compile(
    r"\b(nabi|rasul(ullah)?|muhammad|ibrahim|musa|isa|nuh|adam|yusuf|sulaiman|daud|yunus|ayyub|"
    r"ismail|ishaq|ya'?qub|harun|zakaria|yahya|idris|hud|shalih|saleh|luth|syu'?aib|dzulkifli|"
    r"ilyas|ilyasa|malaikat|jibril|mikail|israfil|izrail|munkar|nakir|sahabat|abu bakar|umar|"
    r"utsman|usman|ali bin|khadijah|aisyah|fatimah|maryam|zulkarnain|dzulqarnain)\b",
    re.IGNORECASE,
)


# =============================================================================
# 1. TAMPILAN TOKOH "kamu"
# =============================================================================
# Nilai di bawah SEMUANYA nilai yang dibaca boneka() di cerita.js (kulit = warna isi, rambut =
# cabang `rb === "..."`, pakaian.jenis = cabang bajuDetail(), bawah = celana|sarung|gamis).
KULIT = {  # sama dengan palet kulit figuran npc di cerita.js
    "terang": "#f2dcc2", "kuning_langsat": "#e9c6a2", "sawo_muda": "#d9b48c",
    "sawo_matang": "#c99a72", "gelap": "#a87a56",
}
BOBOT_KULIT = {"terang": 1, "kuning_langsat": 3, "sawo_muda": 3, "sawo_matang": 3, "gelap": 1}  # penonton Indonesia
RAMBUT_PRIA = ("pendek", "belah", "keriting", "jambul")
RAMBUT_SEMUA = RAMBUT_PRIA + ("tipis", "kerudung")
WARNA_RAMBUT = ("#1d1520", "#2a1c18", "#3a2a20")
JENIS_BAJU = ("kaus", "koko", "gamis", "jaket", "kemeja", "daster", "hoodie", "blazer")
JENIS_BAWAH = ("celana", "sarung", "gamis")
# Warna baju: kalem & bersaturasi sedang supaya tokoh menonjol di latar gelap TANPA menyala
# berlebihan (konten serius), dan tidak putih bersih (gamis putih = ikon pakaian "orang saleh
# zaman dulu", dihindari untuk "kamu" -- lihat docstring modul).
WARNA_BAJU = ("#3f6a8a", "#5a7a9a", "#6aa6a0", "#4a6a8a", "#7a8a5a", "#c96a4a", "#d9a441",
              "#9a5a3a", "#8a5a7a", "#4f7d6a", "#b5523a", "#5a6a9a")
WARNA_BAWAH = ("#2f3a4a", "#3b3f4a", "#4a3a2e", "#2f4a3a", "#3a3448")
WARNA_SARUNG = ("#4a5a3a", "#5a3a3a", "#3a4a6a", "#6a4a3a")
WARNA_KERUDUNG = ("#6aa6a0", "#d98a9a", "#5a7a9a", "#e9e4d8", "#9a7ac9", "#3a3a4a", "#c9a24a", "#7a8a5a")

# Konteks pakaian "kamu" (dari seluruh naskah). Urutan = prioritas bila skor seri.
KONTEKS_TOKOH: dict[str, list[str]] = {
    "akhirat": [r"mahsyar", r"dibangkitkan", r"hari kebangkitan", r"\bneraka", r"\bsurga",
                r"\bhisab\b", r"shirath|sirat", r"\bmizan\b", r"padang (yang )?luas", r"jahannam"],
    "ibadah": [r"s(h)?alat|sholat", r"masjid", r"\bdoa\b|berdoa", r"dzikir|zikir", r"wudhu",
               r"tahajud", r"mengaji", r"puasa|ramadhan", r"sajadah", r"istighfar"],
    "kota": [r"\bkota\b", r"kantor", r"\bkerja\b|bekerja", r"gaji", r"\bhp\b|ponsel|handphone",
             r"media sosial|medsos|scroll|internet", r"\bmall\b", r"gedung", r"macet|jalan raya",
             r"kampus|kuliah"],
    "kampung": [r"kampung", r"\bdesa\b", r"sawah", r"ladang|kebun", r"petani", r"sungai"],
    "dingin": [r"hujan", r"dingin", r"badai", r"angin (kencang|malam)", r"salju|es\b"],
}
# (jenis baju, bawah, ekstra) per konteks -- dipilih berseed; semuanya kombinasi yang sudah
# dirender & dilihat 20 Nov 2026 (lihat lembar uji di laporan cabang).
PAKAIAN_PRIA = {
    "kota": [("kaus", "celana", {}), ("kemeja", "celana", {}), ("hoodie", "celana", {}),
             ("jaket", "celana", {"aksen": "#ffc83d"}), ("kemeja", "celana", {"motif": "batik"})],
    "kampung": [("koko", "sarung", {}), ("kaus", "celana", {}), ("kemeja", "celana", {"motif": "batik"}),
                ("koko", "celana", {})],
    "ibadah": [("koko", "sarung", {"peci": True}), ("koko", "celana", {"peci": "putih"}),
               ("koko", "sarung", {}), ("kemeja", "sarung", {"peci": True})],
    "dingin": [("hoodie", "celana", {}), ("jaket", "celana", {"aksen": "#d9a441"})],
    "umum": [("kaus", "celana", {}), ("kemeja", "celana", {}), ("hoodie", "celana", {}),
             ("koko", "celana", {}), ("jaket", "celana", {"aksen": "#ffc83d"})],
}
PAKAIAN_WANITA = {  # selalu berkerudung; bawah "gamis" = rok/gamis panjang
    "kota": [("kemeja", "gamis", {}), ("hoodie", "gamis", {}), ("gamis", "gamis", {}), ("blazer", "gamis", {})],
    "kampung": [("gamis", "gamis", {}), ("kemeja", "gamis", {"motif": "batik"})],
    "ibadah": [("gamis", "gamis", {}), ("gamis", "gamis", {"motif": "bordir"})],
    "dingin": [("hoodie", "gamis", {}), ("jaket", "gamis", {"aksen": "#d9a441"})],
    "umum": [("gamis", "gamis", {}), ("kemeja", "gamis", {}), ("hoodie", "gamis", {})],
}
PELUANG_WANITA = 0.35  # bila tidak dikunci: sebagian video memakai "kamu" perempuan berkerudung

# Kunci yang boleh diisi pemilik/pengguna (parameter `tampilan` di arahkan()). SENGAJA tidak ada
# "gaya", "nama", "npc", "hidup": gaya khusus (dajjal/anwar/siluet) dan label nama bisa mengubah
# "kamu" jadi tokoh tertentu -- itu bukan wewenang lapisan tampilan.
KUNCI_TAMPILAN_BOLEH = {"jenis_kelamin", "kulit", "rambut", "warna_rambut", "kerudung", "janggut",
                        "kumis", "kacamata", "pakaian", "polos"}
KUNCI_PAKAIAN_BOLEH = {"jenis", "warna", "bawah", "bawah_warna", "motif", "motif_warna", "peci",
                       "aksen", "bordir", "bunga", "dalam"}
_HEX = re.compile(r"^#[0-9a-fA-F]{6}$")


def konteks_tokoh(teks: str) -> str:
    skor = {k: _skor(p, teks) for k, p in KONTEKS_TOKOH.items()}
    if skor["akhirat"] >= 2 and skor["akhirat"] >= max(skor.values()):
        return "akhirat"
    skor.pop("akhirat")
    terbaik = max(skor, key=lambda k: skor[k])
    return terbaik if skor[terbaik] >= 2 else "umum"


def _validasi_kunci(kunci: dict) -> tuple[dict, list[str]]:
    """Buang kunci/nilai yang tidak dikenal cerita.js (bukan diam-diam dirender salah)."""
    bersih, catat = {}, []
    for k, v in (kunci or {}).items():
        if k not in KUNCI_TAMPILAN_BOLEH:
            catat.append(f"tampilan: kunci {k!r} diabaikan (tidak boleh/tidak dikenal)")
            continue
        if k == "kulit" and not (v in KULIT or (isinstance(v, str) and _HEX.match(v))):
            catat.append(f"tampilan: kulit {v!r} diabaikan (pakai {sorted(KULIT)} atau #rrggbb)")
            continue
        if k == "rambut" and v not in RAMBUT_SEMUA:
            catat.append(f"tampilan: rambut {v!r} diabaikan (pilihan: {RAMBUT_SEMUA})")
            continue
        if k == "jenis_kelamin" and v not in ("pria", "wanita"):
            catat.append(f"tampilan: jenis_kelamin {v!r} diabaikan (pria|wanita)")
            continue
        if k == "pakaian":
            if not isinstance(v, dict):
                catat.append("tampilan: pakaian harus objek {jenis, warna, bawah, ...}")
                continue
            p = {}
            for pk, pv in v.items():
                if pk not in KUNCI_PAKAIAN_BOLEH:
                    catat.append(f"tampilan: pakaian.{pk} diabaikan")
                elif pk == "jenis" and pv not in JENIS_BAJU:
                    catat.append(f"tampilan: pakaian.jenis {pv!r} diabaikan (pilihan: {JENIS_BAJU})")
                elif pk == "bawah" and pv not in JENIS_BAWAH:
                    catat.append(f"tampilan: pakaian.bawah {pv!r} diabaikan (pilihan: {JENIS_BAWAH})")
                else:
                    p[pk] = pv
            v = p
        bersih[k] = KULIT.get(v, v) if k == "kulit" else v
    return bersih, catat


def _pagar_tampilan(t: dict, teks: str, catat: list[str]) -> dict:
    """PAGAR BATAS WAJIB (kode, tidak bisa ditimpa kunci): "kamu" tidak boleh terbaca sebagai
    tokoh suci. Kombinasi paling ikonik "orang saleh zaman dulu" = janggut + gamis terang/putih
    + peci/sorban; bila naskah menyebut nabi/sahabat/malaikat, kombinasi janggut + gamis itu
    dibuang janggutnya. Juga: tidak ada gaya khusus, tidak ada label nama."""
    for k in ("gaya", "nama", "npc"):
        t.pop(k, None)
    p = t.get("pakaian") or {}
    if t.get("janggut") and p.get("jenis") == "gamis" and POLA_SAKRAL.search(teks):
        t.pop("janggut", None)
        catat.append("tampilan: janggut dibuang -- janggut + gamis pada naskah yang menyebut "
                     "nabi/sahabat bisa terbaca sebagai penggambaran tokoh suci")
    return t


def pilih_tampilan(teks_semua: str, judul: str, kunci: dict | None = None) -> tuple[dict, list[str], str]:
    """-> (field tampilan untuk boneka "kamu", peringatan, konteks). Satu tampilan per VIDEO."""
    kunci, catat = _validasi_kunci(kunci or {})
    konteks = konteks_tokoh(teks_semua)
    if kunci.get("polos"):  # jalan keluar: tampilan lama (badan siluet, kulit bawaan)
        return {}, catat, konteks
    R = acak(judul, "tampilan")
    wanita = (kunci.get("jenis_kelamin") == "wanita") if "jenis_kelamin" in kunci else (
        kunci.get("rambut") == "kerudung" or R.random() < PELUANG_WANITA)
    nama_kulit = R.choices(list(BOBOT_KULIT), weights=list(BOBOT_KULIT.values()))[0]
    t: dict = {"kulit": KULIT[nama_kulit]}
    if wanita:
        t.update(rambut="kerudung", kerudung=R.choice(WARNA_KERUDUNG))
    else:
        t.update(rambut=R.choice(RAMBUT_PRIA), warna_rambut=R.choice(WARNA_RAMBUT))
        if R.random() < 0.18:
            t["kacamata"] = True  # sesekali: aksesori netral yang menambah "orang biasa"
    if konteks != "akhirat":
        daftar = (PAKAIAN_WANITA if wanita else PAKAIAN_PRIA)[konteks]
        jenis, bawah, ekstra = R.choice(daftar)
        warna = R.choice(WARNA_BAJU)
        if wanita and t["kerudung"] == warna:
            warna = R.choice([w for w in WARNA_BAJU if w != warna])
        p = {"jenis": jenis, "warna": warna, "bawah": bawah,
             "bawah_warna": R.choice(WARNA_SARUNG if bawah == "sarung" else WARNA_BAWAH)}
        if bawah == "gamis":
            p["bawah_warna"] = warna if jenis == "gamis" else R.choice(WARNA_BAWAH + ("#6a5a7a", "#5a4a3a"))
        p.update(ekstra)
        t["pakaian"] = p
    # kunci pengguna MENANG atas pilihan otomatis (kecuali pagar di bawah)
    for k, v in kunci.items():
        if k in ("jenis_kelamin", "polos"):
            continue
        if k == "pakaian":
            t["pakaian"] = {**t.get("pakaian", {}), **v}
        else:
            t[k] = v
    if t.get("rambut") != "kerudung":
        t.pop("kerudung", None)
    return _pagar_tampilan(t, teks_semua, catat), catat, konteks


# =============================================================================
# 2. LINGKUNGAN
# =============================================================================
# Pola kata kunci tema (dicocokkan ke judul+naskah; judul dihitung 2x). Semua benda yang dipakai
# di komposisi diverifikasi ada di benda() cerita.js oleh direktur._validasi_benda.
POLA_TEMA: dict[str, list[str]] = {
    "bumi_terbelah": [r"keluar dari bumi", r"bumi terbelah", r"retak(an)? bumi", r"dari dalam tanah",
                      r"bumi (ber)?guncang", r"gempa"],
    "mahsyar": [r"mahsyar", r"dibangkitkan", r"hari kebangkitan", r"matahari (di|sejengkal|didekatkan)",
                r"padang (yang )?luas", r"keringat", r"berkumpul semua", r"hari pembalasan"],
    "neraka": [r"neraka", r"jahannam|jahanam", r"api (yang )?(menyala|berkobar)", r"zaqqum", r"siksa"],
    "surga": [r"\bsurga", r"jannah", r"telaga|kautsar", r"pintu surga", r"bidadari", r"kenikmatan abadi"],
    "kubur": [r"kubur", r"makam", r"\bmati\b|kematian|meninggal|wafat", r"jenazah|kafan", r"barzakh",
              r"nisan|liang lahat"],
    "laut": [r"\blaut", r"samudra|samudera", r"ombak", r"kapal|bahtera|perahu", r"banjir|air bah",
             r"tenggelam", r"pantai"],
    "gurun": [r"gurun", r"padang pasir", r"\bunta", r"\barab\b", r"mekah|makkah|madinah", r"kurma",
              r"kafilah"],
    "kota": [r"\bkota\b", r"gedung", r"pencakar langit|bangunan tinggi", r"jalan raya|macet",
             r"kantor", r"\bmall\b|pasar"],
    "kampung": [r"kampung", r"\bdesa\b", r"sawah", r"ladang|kebun", r"petani|bertani", r"pedesaan"],
    "ibadah": [r"masjid", r"s(h)?alat|sholat", r"azan|adzan", r"sajadah", r"tahajud|sepertiga malam",
               r"dzikir|zikir", r"\bdoa\b|berdoa"],
    "gua": [r"\bgua\b|\bgoa\b", r"ashabul kahfi|ash-?habul kahfi", r"dalam gua"],
    "gunung": [r"\bgunung", r"bukit", r"tebing|puncak", r"lembah"],
}
URUTAN_TEMA = list(POLA_TEMA)  # urutan = pemecah seri (yang lebih spesifik di depan)

# Palet per posisi alur (hook, isi, klimaks, penutup). Penutup cenderung lebih terang (subuh/
# pagi/sore) karena BATAS WAJIB "selalu ada jalan keluar" -- akhir video = harapan, bukan gelap.
# None = langit Mahsyar bawaan cerita.js (gradasi merah-oranye diatur `langit`).
PALET_TEMA = {
    "langit_terbuka": ("gelap_malam", "malam", "gelap_malam", "subuh"),
    "bumi_terbelah": ("gelap_malam", "gelap_malam", "gelap_malam", "subuh"),
    "mahsyar": (None, None, None, None),
    "neraka": ("neraka", "neraka", "neraka", "gelap_malam"),
    "surga": ("pagi", "pagi", "siang", "pagi"),
    "kubur": ("gelap_malam", "malam", "gelap_malam", "subuh"),
    "laut": ("malam", "senja", "gelap_malam", "subuh"),
    "gurun": ("senja", "gurun", "senja", "sore"),
    "kota": ("malam", "kota", "senja", "pagi"),
    "kampung": ("subuh", "pagi", "sore", "pagi"),
    "ibadah": ("malam", "malam", "gelap_malam", "subuh"),
    "gua": ("gua", "gua", "gua", "gua"),
    "gunung": ("senja", "pagi", "mendung", "sore"),
}
LANGIT_MAHSYAR = {"hook": 0.35, "isi": 0.55, "klimaks": 0.95, "penutup": 0.45}
MALAM_PALET = {"malam": 1, "gelap_malam": 1, "gua": 0, "neraka": 0, "senja": 0.25}
HORIZON_TEMA = {"neraka": 1000, "kubur": 1180, "laut": 1430, "kota": 1200, "kampung": 1170, "gua": 1250}


# Tema yang polanya sangat spesifik: SATU kecocokan sudah cukup bila tidak ada tema lain yang
# disinggung (mis. "keluar dari bumi" pada kisah Dabbatul Ard = motif bumi terbelah, seperti
# Direktur versi 19 Nov). Tema umum (kota, gunung, ...) tetap butuh >= 2 pola.
TEMA_SPESIFIK = {"bumi_terbelah", "mahsyar", "neraka", "surga", "gua"}


def pilih_tema(judul: str, teks: str) -> str:
    gab = f"{judul} {judul} {teks}"
    skor = {k: _skor(p, gab) for k, p in POLA_TEMA.items()}
    terbaik = max(URUTAN_TEMA, key=lambda k: (skor[k], -URUTAN_TEMA.index(k)))
    if skor[terbaik] >= 2:
        return terbaik
    if skor[terbaik] == 1 and terbaik in TEMA_SPESIFIK and sum(1 for v in skor.values() if v) == 1:
        return terbaik
    return "langit_terbuka"


def tema_lokal(teks: str, tema_utama: str) -> str:
    """Satu adegan boleh pindah tema (mis. video Dabbatul Ard yang satu adegannya membahas
    neraka) hanya bila pindahnya KUAT (>=2 pola) -- bukan karena satu kata lewat, supaya satu
    video tetap terasa satu dunia."""
    skor = {k: _skor(p, teks) for k, p in POLA_TEMA.items()}
    terbaik = max(URUTAN_TEMA, key=lambda k: (skor[k], -URUTAN_TEMA.index(k)))
    return terbaik if skor[terbaik] >= 2 and terbaik != tema_utama else tema_utama


# ---- komposisi per tema -------------------------------------------------------------------
# Tiap fungsi: (R, h, sisi, v) -> list benda; v = nomor varian komposisi, DIGILIR per adegan
# (bukan diacak) supaya dua adegan berurutan tidak pernah memakai komposisi yang sama. h = garis cakrawala; sisi = -1 bila boneka "kamu" di
# kiri layar, +1 di kanan, 0 di tengah. Benda tinggi diletakkan di SISI LAIN dari boneka
# (pelajaran 19 Nov: menara/bingkai yang ditaruh di x=540 menancap di kepala boneka).
def _fokus_x(sisi: int, R: random.Random) -> int:
    if sisi < 0:
        return R.choice((780, 820, 860))
    if sisi > 0:
        return R.choice((220, 260, 300))
    return R.choice((200, 240, 840, 880))


def _bintang(R, n=80):
    return {"jenis": "bintang", "x": 540, "y": -1250, "s": 1, "seed": R.randint(1, 19), "tinggi": 1500, "n": n}


def _k_langit(R, h, sisi, v=0):
    v %= 4
    fx = _fokus_x(sisi, R)
    w1, w2 = R.choice((("#7fa0b8", "#8fb0c4"), ("#6a7a9a", "#8a96b0"), ("#5a6a8a", "#7a8aa8"), ("#7a6a8a", "#9a8aa8")))
    if v == 0:  # dua gunung (komposisi lama, kini warna/posisi bervariasi)
        return [{"jenis": "gunung", "x": 300 + R.randint(-60, 60), "y": h - 10, "s": 1.2, "warna": w1},
                {"jenis": "gunung", "x": 820 + R.randint(-60, 60), "y": h - 10, "s": 0.9, "warna": w2}]
    if v == 1:  # satu gunung besar di sisi fokus + kota kecil jauh di sisi lain
        return [{"jenis": "gunung", "x": fx, "y": h - 10, "s": 1.05, "warna": w1},
                {"jenis": "kota", "x": 1080 - fx, "y": h, "s": 0.4, "w": 700, "seed": R.randint(1, 30), "warna": "#15111c"}]
    if v == 2:  # padang + siluet kota jauh (manusia & peradaban, kecil di cakrawala)
        return [{"jenis": "kota", "x": 540, "y": h, "s": 0.5, "w": 2200, "seed": R.randint(1, 30), "warna": "#1a1624"},
                {"jenis": "gunung", "x": fx, "y": h - 10, "s": 0.6, "warna": w2}]
    return [{"jenis": "bulan", "x": fx, "y": 420, "s": 0.9},  # padang kosong + bulan + awan tipis
            {"jenis": "gunung", "x": 1080 - fx, "y": h - 10, "s": 0.55, "warna": w1}]


def _k_terbelah(R, h, sisi, v=0):
    dasar = [{"jenis": "belah", "x": 540, "y": h + 80, "s": 1, "buka": [0.3, 0.5], "goyang": 3}]
    fx = _fokus_x(sisi, R)
    v %= 3
    if v == 0:
        return dasar + [{"jenis": "bulan", "x": fx, "y": 430, "s": 0.85}]
    if v == 1:
        return dasar + [{"jenis": "kota", "x": 540, "y": h, "s": 0.45, "w": 2200, "seed": R.randint(1, 30), "warna": "#15111c", "belakang": True}]
    return dasar + [{"jenis": "gunung", "x": fx, "y": h - 10, "s": 0.6, "warna": "#5a6a8a", "belakang": True}]


def _k_mahsyar(R, h, sisi, v=0):
    fx = _fokus_x(sisi, R)
    v %= 3
    if v == 0:
        return [{"jenis": "surya", "x": fx, "y": h - 260, "s": 1, "r": 170, "terang": 0.9}]
    if v == 1:
        return [{"jenis": "gunung", "x": 540, "y": h - 10, "s": 0.8, "warna": "#8a5a4a"},
                {"jenis": "surya", "x": fx, "y": h - 520, "s": 1, "r": 120, "terang": 0.8}]
    return [{"jenis": "gunung", "x": fx, "y": h - 10, "s": 0.55, "warna": "#9a6a5a"}]  # padang hampir kosong


def _k_neraka(R, h, sisi, v=0):
    v %= 3
    dasar = [{"jenis": "lahar", "x": 540, "y": h, "s": 1, "seed": R.randint(1, 20), "kuat": 0.8}]
    if v == 0:
        return dasar + [{"jenis": "massa_api", "x": 540, "y": h - 380, "s": 0.9, "r": 260, "kuat": 0.8}]
    if v == 1:
        return dasar + [{"jenis": "massa_api", "x": _fokus_x(sisi, R), "y": h - 200, "s": 0.45, "r": 220, "kuat": 0.7}]
    return dasar + [{"jenis": "api", "x": _fokus_x(sisi, R), "y": h + 180, "s": 0.8}]


def _k_surga(R, h, sisi, v=0):
    fx = _fokus_x(sisi, R)
    v %= 3
    awan = [{"jenis": "awan", "x": R.randint(150, 400), "y": R.randint(330, 480), "s": 1},
            {"jenis": "awan", "x": R.randint(650, 950), "y": R.randint(520, 700), "s": 0.8}]
    if v == 0:
        return awan + [{"jenis": "gerbang", "x": fx, "y": h + 60, "s": 0.75, "buka": 0.85, "belakang": True}]
    if v == 1:
        return awan + [{"jenis": "mangga", "x": fx, "y": h + 120, "s": 0.75},
                       {"jenis": "semak", "x": 1080 - fx, "y": h + 150, "s": 0.9, "bunga": "#ffd27a"}]
    return awan + [{"jenis": "gunung", "x": 540, "y": h - 10, "s": 0.8, "warna": "#8fbf8a"},
                   {"jenis": "pohon", "x": fx, "y": h + 160, "s": 0.6, "warna": "#4f9a46"}]


def _k_kubur(R, h, sisi, v=0):
    fx = _fokus_x(sisi, R)
    v %= 3
    if v == 0:
        return [{"jenis": "makam", "x": fx, "y": h + 220, "s": 0.75, "n": 3, "jarak": 300},
                {"jenis": "bulan", "x": 1080 - fx, "y": 420, "s": 0.8}]
    if v == 1:
        return [{"jenis": "kamboja", "x": fx, "y": h + 160, "s": 0.7},
                {"jenis": "makam", "x": 1080 - fx, "y": h + 120, "s": 0.55, "n": 2, "jarak": 260}]
    return [{"jenis": "makam", "x": 540, "y": h + 60, "s": 0.5, "n": 5, "jarak": 330},
            {"jenis": "bulan", "x": fx, "y": 380, "s": 0.7}]


def _k_laut(R, h, sisi, v=0, badai=False):
    """Laut di BELAKANG garis tanah: `laut`/`ombak` diberi belakang:true (digambar sebelum tanah)
    dan permukaannya 280 px di atas cakrawala, sehingga tanah tema menjadi PANTAI tempat "kamu"
    berdiri. (Pratinjau 20 Nov: tanpa ini, laut menutup tanah dan boneka berdiri di atas air.)"""
    fx = _fokus_x(sisi, R)
    ly = h - 280
    lautan = [{"jenis": "laut", "x": 540, "y": ly, "s": 1, "pantul": fx - 540, "belakang": True}]
    if badai:
        return [{"jenis": "ombak", "x": 540, "y": ly + 60, "s": 1, "tinggi": 110, "lapis": 3, "belakang": True},
                {"jenis": "petir", "x": fx, "y": 60, "s": 1, "saat": [1.2, 4.5]}]
    v %= 3
    if v == 0:
        return lautan + [{"jenis": "bulan", "x": fx, "y": 430, "s": 0.9}]
    if v == 1:
        return lautan + [{"jenis": "tebing", "x": 1080 - fx + (60 if fx < 540 else -60), "y": ly - 60, "s": 0.5, "warna": "#141020", "belakang": True}]
    return lautan + [{"jenis": "ikan", "x": fx, "y": ly + 150, "s": 0.22, "arah": -1 if fx > 540 else 1, "op": 0.45, "belakang": True}]


def _k_gurun(R, h, sisi, v=0):
    fx = _fokus_x(sisi, R)
    pasir = [{"jenis": "gunung", "x": R.choice((260, 820)), "y": h - 6, "s": 0.7, "warna": "#d9a86a"}]
    v %= 3
    if v == 0:
        return pasir + [{"jenis": "unta", "x": fx, "y": h + 120, "s": 0.55}]
    if v == 1:
        return pasir + [{"jenis": "kota", "x": 540, "y": h, "s": 0.45, "w": 1600, "seed": R.randint(1, 30), "warna": "#3a2a2a"},
                        {"jenis": "surya", "x": fx, "y": h - 300, "s": 1, "r": 110, "terang": 0.7}]
    return pasir + [{"jenis": "kelapa", "x": fx, "y": h + 160, "s": 0.6, "lengkung": -1 if fx > 540 else 1}]


def _k_kota(R, h, sisi, v=0):
    fx = _fokus_x(sisi, R)
    v %= 3
    gedung = {"jenis": "gedung", "x": 540, "y": h, "s": 0.75, "seed": R.randint(1, 30), "malam": 0.7}
    if v == 0:
        return [gedung, {"jenis": "jalan", "x": 540, "y": h + 820, "s": 1.0, "lebar": 600}]
    if v == 1:
        return [gedung, {"jenis": "tiang_listrik", "x": fx, "y": h + 200, "s": 0.8}]
    return [{"jenis": "kantor_gedung", "x": fx, "y": h + 100, "s": 0.55, "nama": ""},
            {"jenis": "gedung", "x": 540, "y": h - 20, "s": 0.55, "seed": R.randint(1, 30), "malam": 0.7, "belakang": True}]


def _k_kampung(R, h, sisi, v=0):
    fx = _fokus_x(sisi, R)
    v %= 3
    if v == 0:
        return [{"jenis": "sawah", "x": 540, "y": h, "s": 1, "seed": R.randint(1, 30)},
                {"jenis": "kelapa", "x": fx, "y": h + 120, "s": 0.6, "lengkung": -1 if fx > 540 else 1}]
    if v == 1:
        return [{"jenis": "rumah_kampung", "x": fx, "y": h + 110, "s": 0.5},
                {"jenis": "pisang", "x": 1080 - fx, "y": h + 150, "s": 0.7}]
    return [{"jenis": "masjid_kampung", "x": fx, "y": h + 80, "s": 0.45},
            {"jenis": "mangga", "x": 1080 - fx, "y": h + 160, "s": 0.6}]


def _k_ibadah(R, h, sisi, v=0):
    fx = _fokus_x(sisi, R)
    v %= 3
    if v == 0:
        return [{"jenis": "masjid", "x": fx, "y": h + 10, "s": 0.6, "warna": "#15111c"},
                {"jenis": "bulan", "x": 1080 - fx, "y": 420, "s": 0.8}]
    if v == 1:
        return [{"jenis": "masjid", "x": 540, "y": h + 10, "s": 0.4, "warna": "#1a1526", "belakang": True},
                {"jenis": "cahaya", "x": 540, "y": 1700, "s": 1.0}]
    return [{"jenis": "masjid_kampung", "x": fx, "y": h + 80, "s": 0.45},
            {"jenis": "bulan", "x": 1080 - fx, "y": 400, "s": 0.7}]


def _k_gua(R, h, sisi, v=0):
    return [{"jenis": "gua", "x": 540, "y": 1500, "s": 1.05 + 0.1 * R.random()}]


def _k_gunung(R, h, sisi, v=0):
    fx = _fokus_x(sisi, R)
    v %= 3
    if v == 0:
        return [{"jenis": "gunung", "x": 540, "y": h - 10, "s": 1.3, "warna": "#6a7a8a"},
                {"jenis": "awan", "x": fx, "y": 600, "s": 1}]
    if v == 1:
        return [{"jenis": "gunung", "x": fx, "y": h - 10, "s": 1.4, "warna": "#5a6a7a"},
                {"jenis": "pohon", "x": 1080 - fx, "y": h + 140, "s": 0.55, "warna": "#3f7a46"}]
    return [{"jenis": "gunung", "x": 280, "y": h - 10, "s": 1.0, "warna": "#5a6a7a"},
            {"jenis": "gunung", "x": 860, "y": h - 10, "s": 1.25, "warna": "#7a8a9a"},
            {"jenis": "awan", "x": fx, "y": 520, "s": 0.8}]


KOMPOSISI = {
    "langit_terbuka": _k_langit, "bumi_terbelah": _k_terbelah, "mahsyar": _k_mahsyar,
    "neraka": _k_neraka, "surga": _k_surga, "kubur": _k_kubur, "laut": _k_laut, "gurun": _k_gurun,
    "kota": _k_kota, "kampung": _k_kampung, "ibadah": _k_ibadah, "gua": _k_gua, "gunung": _k_gunung,
}
TEMA_SEMUA = tuple(KOMPOSISI)
TEMA_LANGIT_BINTANG = {"langit_terbuka", "bumi_terbelah", "kubur", "laut", "ibadah", "kota"}
TEMA_BOLEH_KERUMUNAN = {"langit_terbuka", "bumi_terbelah", "mahsyar"}  # kerumunan siluet di cakrawala
TEMA_SELALU_KERUMUNAN = {"mahsyar"}  # semua manusia dikumpulkan: kerumunan di setiap shot, bukan hanya saat disebut

# Ruang dalam: bila kalimat jelas berlatar di dalam rumah/kantor/rumah sakit. Nilai = argumen
# shot.ruang cerita.js (jenis yang ADA di fungsi ruang(): tamu, dapur, kampung, kamar, kantor,
# rumah_sakit, penjara, ...). Dicek di direktur._validasi_benda juga (lihat JENIS_RUANG).
POLA_RUANG: list[tuple[re.Pattern, dict]] = [
    (re.compile(r"\bkamar\b|di kasur|sebelum tidur|rebahan|tidur malam", re.I), {"jenis": "kamar", "waktu": "malam"}),
    (re.compile(r"rumah sakit|dirawat|opname|sakit keras|terbaring sakit", re.I), {"jenis": "rumah_sakit", "waktu": "malam"}),
    (re.compile(r"\bkantor\b|meja kerja|rapat|lembur", re.I), {"jenis": "kantor", "waktu": "malam"}),
    (re.compile(r"\bdapur\b|memasak", re.I), {"jenis": "dapur"}),
    (re.compile(r"penjara|dipenjara|sel tahanan", re.I), {"jenis": "penjara"}),
    (re.compile(r"ruang tamu|di rumah|keluarga(mu)? berkumpul|orang tua(mu)? di rumah", re.I), {"jenis": "tamu"}),
]
JENIS_RUANG = frozenset({"tamu", "dapur", "kampung", "kamar", "kantor", "rumah_sakit", "mobil",
                         "studio", "penjara", "istana", "teras"})


def ruang_untuk(teks: str) -> dict | None:
    for pola, r in POLA_RUANG:
        if pola.search(teks):
            return dict(r)
    return None


# Aksen per KALIMAT/segmen (tambahan di atas komposisi tema; maks satu per shot). Urutan =
# prioritas. Pola lama dari direktur.py (gerbang/surya/menara/gelap) dipertahankan apa adanya.
def aksen_untuk(teks: str, fx: int, h: int, bx: int, laut: bool = False) -> list[dict]:
    t = teks
    if re.search(r"pintu (taubat )?(sudah )?tertutup|taubat (sudah )?terlambat", t, re.I):
        return [{"jenis": "gerbang", "x": fx, "y": h + 100, "s": 0.8, "buka": 0.1, "belakang": True}]
    if re.search(r"pintu.*(masih )?terbuka|selagi.*(ada waktu|belum)", t, re.I):
        return [{"jenis": "gerbang", "x": fx, "y": h + 100, "s": 0.8, "buka": 0.85, "belakang": True}]
    if re.search(r"hidayah|petunjuk|cahaya|taubat|\bampun(an)?\b|bertobat", t, re.I):
        return [{"jenis": "cahaya", "x": bx, "y": 1720, "s": 1.0}]  # berkas cahaya turun ke "kamu"
    if re.search(r"\bkapal\b|bahtera|perahu", t, re.I):  # benda, bukan tokoh; tanpa orang di geladak
        if laut:
            return [{"jenis": "bahtera", "x": fx, "y": h - 250, "s": 0.26, "goyang": 2, "orang": 0, "belakang": True}]
        return [{"jenis": "bahtera", "x": fx, "y": h + 170, "s": 0.32, "darat": True, "orang": 0}]
    if re.search(r"tanda besar kiamat|menjelang kiamat|tanda akhir", t, re.I):
        return [{"jenis": "menara", "x": fx, "y": h + 80, "s": 0.85, "cahaya": 0.6}]
    if re.search(r"ditimbang|timbangan|\bmizan\b|amal (baik|buruk)", t, re.I):
        return [{"jenis": "timbangan", "x": fx, "y": h + 200, "s": 0.55}]
    if re.search(r"harta|kekayaan|\buang\b|\bkaya\b", t, re.I):
        return [{"jenis": "koin", "x": fx, "y": h + 380, "s": 0.45, "n": 5}]
    if re.search(r"\bmati\b|kematian|meninggal|ajal|kubur", t, re.I):
        return [{"jenis": "makam", "x": fx, "y": h + 260, "s": 0.55, "n": 1}]
    if re.search(r"\bapi\b|terbakar|membakar|\bbara\b", t, re.I):
        return [{"jenis": "api", "x": fx, "y": h + 300, "s": 0.7}]
    if re.search(r"matahari|panas|terik", t, re.I):
        return [{"jenis": "surya", "x": fx, "y": h - 100, "s": 1, "r": 150, "terang": 0.8}]
    if re.search(r"mengerikan|mencekam|gelap|misteri", t, re.I):
        return [{"jenis": "gelap", "x": 540, "y": 1000, "s": 1, "r": 480, "pekat": 0.5}]
    return []


# Waktu yang DISEBUT di kalimat menimpa palet tema (mis. "matahari sudah tinggi" tidak boleh
# tampil di langit malam -- ditemukan di pratinjau 20 Nov: matahari besar di langit gelap).
# Tidak berlaku untuk tema yang paletnya bagian dari makna (neraka, gua, mahsyar, surga).
POLA_WAKTU: list[tuple[re.Pattern, str]] = [
    (re.compile(r"tengah malam|jam (satu|dua|tiga) pagi|larut malam|malam (ini|itu|hari)|sebelum tidur", re.I), "malam"),
    (re.compile(r"subuh|fajar|menjelang pagi", re.I), "subuh"),
    (re.compile(r"matahari (sudah )?tinggi|siang hari|tengah hari|terik", re.I), "siang"),
    (re.compile(r"pagi hari|bangun pagi|pagi-pagi", re.I), "pagi"),
    (re.compile(r"sore|senja|menjelang maghrib|matahari terbenam", re.I), "senja"),
    (re.compile(r"hujan|mendung|badai", re.I), "mendung"),
]
TEMA_PALET_TETAP = {"neraka", "gua", "mahsyar", "surga"}


def palet_waktu(teks: str, tema: str) -> str | None:
    if tema in TEMA_PALET_TETAP:
        return None
    for pola, palet in POLA_WAKTU:
        if pola.search(teks):
            return palet
    return None


def atmosfer(teks: str) -> dict:
    """Kunci level-shot dari cuaca/kejadian di kalimat (bukan benda)."""
    a: dict = {}
    if re.search(r"hujan|badai|banjir|air bah", teks, re.I):
        a["hujan"] = 0.7
    if re.search(r"gempa|guncang|bergetar|runtuh|terbelah", teks, re.I):
        a["_guncang"] = True
    return a


# =============================================================================
# 3. POSE, GESTUR, FRAMING
# =============================================================================
# Nama pose = kunci POSE di cerita.js (rangka bersendi). Dua-tiga kandidat per emosi supaya video
# panjang tidak memakai gestur yang sama terus; dipilih berseed dan tidak mengulang pose shot
# sebelumnya.
POSE_UNTUK_WAJAH: dict[str, tuple[str, ...]] = {
    "takut": ("tutup_wajah", "mundur", "stop2"),
    "kaget": ("kaget", "mundur", "stop"),
    "marah": ("kepal", "berkacak"),
    "kesal": ("berkacak", "silang", "pinggang1"),
    "sedih": ("lemas", "tangan_dada", "tutup_wajah"),
    "bingung": ("angkat_bahu", "garuk_kepala", "buka2"),
    "ragu": ("angkat_bahu", "silang", "garuk_kepala"),
    "mikir": ("silang", "garuk_kepala", "tangan_dada"),
    "lega": ("tangan_dada", "buka2"),
    "senang": ("buka2", "dua_naik"),
    "malu": ("tepuk_dahi", "garuk_kepala"),
    "lelah": ("lemas",),
    "netral": ("berdiri", "jelaskan", "tangan_dada", "condong"),
}
POSE_KONTEKS: list[tuple[re.Pattern, str]] = [  # kalimat lebih spesifik dari emosi -> menang
    (re.compile(r"\bberdoa\b|\bdoa\b|memohon|istighfar|bertobat|minta ampun", re.I), "doa"),
    (re.compile(r"\bhp\b|ponsel|handphone|scroll|media sosial|medsos|notifikasi", re.I), "pegang_hp"),
    (re.compile(r"\bjangan\b|berhenti|stop\b|cukup sudah", re.I), "stop"),
    (re.compile(r"\blangit\b|ke atas|dari atas", re.I), "tunjuk_atas"),
]
SIMBOL_UNTUK_WAJAH = {"bingung": "tanya", "mikir": "tanya", "kaget": "seru", "takut": "tetes", "malu": "tetes"}
REAKSI_UNTUK_WAJAH = {"kaget": "kaget", "takut": "mundur", "lega": "angguk", "mikir": "miring", "bingung": "miring",
                      "marah": "hentak", "kesal": "geleng", "sedih": "geleng"}
POSE_SEMUA = frozenset(p for v in POSE_UNTUK_WAJAH.values() for p in v) | {p for _, p in POSE_KONTEKS}


def pilih_pose(teks: str, wajah: str, R: random.Random, sebelumnya: str | None) -> str:
    for pola, p in POSE_KONTEKS:
        if pola.search(teks):
            return p
    calon = [p for p in POSE_UNTUK_WAJAH.get(wajah, POSE_UNTUK_WAJAH["netral"]) if p != sebelumnya]
    return R.choice(calon or ["berdiri"])


# Framing: (nama, deskripsi). Kamera dunia: layar_y = 960 + (dunia_y - kamera_y) * z. Boneka
# "kamu" berdiri di y 1700 skala 1.1 -> wajah di dunia y ~1160; angka kamera di bawah dihitung
# supaya wajah jatuh di sepertiga atas layar (tidak ditutup subtitle di y 1500).
FRAMING = ("lebar", "samping", "sedang", "dekat", "jauh", "turun", "dorong", "tarik")
FRAMING_ISI = ("lebar", "samping", "sedang", "dekat", "jauh", "dorong")
EMOSI_KUAT = {"takut", "kaget", "marah", "sedih", "kesal"}


def rencana_framing(posisi: str, wajah: str, R: random.Random, sebelumnya: str | None,
                    pertama: bool, terakhir: bool, tema: str) -> str:
    """Rangkai tipe shot dengan aturan editor sederhana: buka lebar/dramatis, klimaks mendekat,
    tutup menjauh, emosi kuat = lihat wajah (tidak memakai shot dari belakang), dan tidak pernah
    dua tipe sama berturut-turut (sumber utama kesan "monoton" versi lama)."""
    if posisi == "hook" and pertama:
        return R.choice(("turun", "dorong", "jauh"))
    if posisi == "penutup" and terakhir:
        return "tarik"
    if tema == "neraka":
        # "kamu" menyaksikan dari jauh, tidak di-close-up sedang tersiksa (topik berat tidak
        # dijadikan sensasi -- BATAS WAJIB).
        return "jauh" if sebelumnya != "jauh" else "samping"
    if posisi == "klimaks":
        calon = ["dekat", "dorong", "sedang"]
    elif wajah in EMOSI_KUAT:
        calon = ["dekat", "sedang", "dorong", "samping"]
    else:
        calon = list(FRAMING_ISI)
    calon = [c for c in calon if c != sebelumnya] or ["lebar"]
    if wajah in EMOSI_KUAT and "jauh" in calon:
        calon.remove("jauh")
    return R.choice(calon)


def kamera_dan_boneka(framing: str, dur: float, R: random.Random, sisi_samping: int) -> tuple[dict, dict, int]:
    """-> (kamera, penempatan boneka {x,y,s,belakang?}, sisi boneka -1/0/+1)."""
    gx = R.choice((-1, 1)) * R.randint(8, 22)  # geser horizontal halus (pan) supaya tidak diam
    if framing == "lebar":
        return {"z": [1.0, 1.05], "x": [540 - gx, 540 + gx], "y": 1000}, {"x": 540, "y": 1700, "s": 1.1}, 0
    if framing == "samping":
        bx = 330 if sisi_samping < 0 else 750
        return ({"z": [1.0, 1.04], "x": [540 - gx, 540 + gx], "y": 1020},
                {"x": bx, "y": 1700, "s": 1.0}, sisi_samping)
    if framing == "sedang":
        return {"z": [1.32, 1.4], "x": 540, "y": [1320, 1300]}, {"x": 540, "y": 1700, "s": 1.1}, 0
    if framing == "dekat":
        return {"z": [1.85, 1.98], "x": [540 + gx / 2, 540 - gx / 2], "y": 1290}, {"x": 540, "y": 1700, "s": 1.1}, 0
    if framing == "jauh":
        bx = 380 if sisi_samping < 0 else 700
        return ({"z": [1.0, 1.06], "x": 540, "y": 1000},
                {"x": bx, "y": 1660, "s": 0.62, "belakang": True}, sisi_samping)
    if framing == "turun":  # mulai dari langit, kamera turun ke "kamu"
        k = round(min(2.4, max(0.8, dur * 0.45)), 2)
        return {"z": [[0, 1.08], [k, 1.03]], "x": 540, "y": [[0, 560], [k, 1000]]}, {"x": 540, "y": 1700, "s": 1.1}, 0
    if framing == "dorong":  # dorong pelan dari lebar ke setengah badan
        return {"z": [1.0, 1.45], "x": 540, "y": [1000, 1280]}, {"x": 540, "y": 1700, "s": 1.1}, 0
    if framing == "tarik":  # mundur dari wajah ke lebar (penutup)
        return {"z": [1.75, 1.0], "x": 540, "y": [1270, 1000]}, {"x": 540, "y": 1700, "s": 1.1}, 0
    raise ValueError(framing)


# =============================================================================
# Pemecah adegan -> segmen (shot) berdasarkan kalimat
# =============================================================================
def _token(teks: str) -> list[str]:
    """Token kata PERSIS seperti dlib._kata_baris (tanpa tag emosi) supaya indeks token cocok
    dengan daftar waktu kata TTS."""
    return [w for w in re.sub(r"\[[^\]]*\]", " ", teks).split() if re.search(r"\w", w)]


def pecah_segmen(teks: str, t0: float, dur: float, kata: list | None = None,
                 min_seg: float = 3.2) -> list[tuple[float, float, str]]:
    """Satu adegan narasi (sering 12-17 dtk, beberapa kalimat) -> 1-3 segmen (t_mulai, durasi,
    teks) yang dipotong di BATAS KALIMAT. Satu framing selama 15 dtk = kesan "diam"; potongan
    di batas kalimat terasa seperti suntingan yang disengaja. Waktu batas memakai waktu kata TTS
    nyata bila ada (`kata` = [[t_absolut, kata], ...]); tanpa itu diperkirakan dari panjang huruf."""
    tok = _token(teks)
    if not tok or dur < 2 * min_seg:
        return [(t0, dur, teks)]
    n = 1 if dur < 7.5 else (2 if dur < 15 else 3)
    if n == 1:
        return [(t0, dur, teks)]
    batas = [i + 1 for i, w in enumerate(tok[:-1]) if re.search(r"[.!?:;]['\"”’)]*$|—", w)]
    if not batas:
        return [(t0, dur, teks)]
    pakai_kata = kata is not None and len(kata) == len(tok)
    total_huruf = sum(len(w) + 1 for w in tok)

    def waktu(i):  # waktu mulai token ke-i
        if pakai_kata:
            return float(kata[i][0])
        return t0 + dur * sum(len(w) + 1 for w in tok[:i]) / total_huruf

    pilih: list[int] = []
    for k in range(1, n):
        target = t0 + dur * k / n
        calon = [b for b in batas if b not in pilih and (not pilih or b > pilih[-1])]
        if not calon:
            break
        b = min(calon, key=lambda b: abs(waktu(b) - target))
        mulai_seb = waktu(pilih[-1]) if pilih else t0
        if waktu(b) - mulai_seb >= min_seg and (t0 + dur) - waktu(b) >= min_seg:
            pilih.append(b)
    if not pilih:
        return [(t0, dur, teks)]
    titik = [0] + pilih + [len(tok)]
    seg = []
    for a, b in zip(titik, titik[1:]):
        ta = t0 if a == 0 else waktu(a)
        tb = t0 + dur if b == len(tok) else waktu(b)
        seg.append((round(ta, 2), round(tb - ta, 2), " ".join(tok[a:b])))
    return seg
