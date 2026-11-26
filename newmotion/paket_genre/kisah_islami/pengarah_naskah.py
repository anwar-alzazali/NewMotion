"""Direktur (Director) RULE-BASED -- TANPA LLM, murni skrip Python -- langkah 3 dari
rencana mesin kecerdasan video (lihat ARAH BESAR di CLAUDE.md).

Input: naskah JSON hasil penulis/tulis.py ({"judul","adegan":[{nama,teks,kunci}],
"dalil_dipakai":[{surah,ayat,di_adegan}], ...}).
Output: spesifikasi "papan" siap dirender lewat papan_buat.py, gaya "langit terbuka"
(seperti seri Mahsyar/Dabbatul-Ard-style -- lihat papan/kisah/mahsyar_uji.json), yaitu
{"cerita": {"shot": [...]}}.

KENAPA TANPA LLM (keputusan pemilik 19 Nov 2026): kosakata visual cerita.js itu TERBATAS
dan BERNAMA (17 ekspresi wajah, beberapa pose lengan, beberapa tipe objek) -- bukan piksel
bebas. Untuk kosakata tertutup seperti ini, heuristik Python yang dirancang baik bisa
sama bagus (bahkan lebih konsisten & lebih murah) daripada memanggil LLM tiap adegan, dan
hasilnya 100% bisa diprediksi/diuji ulang. Risiko heuristik: gampang jadi monoton -- makanya
dua hal ini DISENGAJA: (1) posisi adegan dalam alur (hook/isi/klimaks/penutup) ikut menentukan
intensitas kamera, bukan cuma kata kunci; (2) variasi berseed per-judul (lihat `_seed_dasar`)
supaya video lain tidak selalu dapat pola identik.

PAGAR KESELAMATAN (kode, tidak bisa "dibujuk" lewat kata-kata di naskah):
- `boneka` di modul ini SELALU "kamu" (avatar penonton yang bereaksi), TIDAK PERNAH diberi
  identitas/nama tokoh sakral -- jadi menyebut "Allah"/"Rasul"/nabi dkk di narasi TIDAK
  menekan emosi boneka (itu bug versi awal: kata "Allah" wajar sering muncul di konten
  Islami, menekan emosi di hampir semua adegan cuma karena kata itu disebut adalah
  overkill yang tidak menambah keamanan nyata). PERINGATAN untuk pengembang berikutnya:
  kalau modul ini nanti diberi field "tokoh"/identitas pada boneka, filter sakral pada
  IDENTITAS itu WAJIB ditambah lagi sebelum dipakai.
- Kalau narasi bilang wujud sesuatu TIDAK dijelaskan/tidak diketahui (lihat
  PENANDA_WUJUD_TAK_DIJELASKAN -- ini risiko NYATA & spesifik, beda dari sekadar menyebut
  nama), makhluk itu TIDAK digambar sama sekali -- cuma suasana gelap/misterius + reaksi
  "kamu", bukan tebakan bentuk.
- Dalil (kartu_dalil) diambil ulang melalui sumber resmi paket genre Kisah Islami saat
  Direktur berjalan (bukan dari teks naskah) -- re-verifikasi, bukan percaya kutipan lama.
  Ayat yang gagal diverifikasi SEKARANG dibuang dari kartu, tidak pernah diganti karangan.
"""
from __future__ import annotations

import hashlib
import re
import statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[3]

from .dalil import ambil_ayat
from . import arah_visual as AV
from .pengarah_subjek import arahkan_subjek
from .rencana_sutradara import subjek_dari_rencana

# ---------------------------------------------------------------------------
# Pagar keselamatan: deteksi frasa, bukan keputusan AI. (Lihat catatan sakral di atas --
# TIDAK ADA filter nama Allah/nabi dkk di sini dgn sengaja, karena boneka tidak pernah
# merepresentasikan mereka; satu-satunya guard nyata adalah wujud-tak-dijelaskan.)
# ---------------------------------------------------------------------------
PENANDA_WUJUD_TAK_DIJELASKAN = re.compile(
    r"tidak (disebutkan|dijelaskan|diketahui) (wujud|bentuk)|"
    r"tidak menyebutkan wujud|wujud(nya)? (pasti )?tidak|"
    r"tidak (tahu|jelas) (bentuk|wujud|rupa)nya",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Leksikon emosi Bahasa Indonesia -> enum `wajah` cerita.js (17 nilai nyata di kode,
# lihat papan/cerita.js sekitar baris 1269 -- JANGAN menambah nilai yang tidak ada di sana).
# ---------------------------------------------------------------------------
LEKSIKON_EMOSI: list[tuple[str, tuple[str, ...]]] = [
    ("takut", ("takut", "ngeri", "mengerikan", "gentar", "cemas", "mengancam", "mencekam", "horor", "seram", "panik")),
    ("kaget", ("tiba-tiba", "mendadak", "kaget", "terkejut", "tersentak", "mengejutkan")),
    ("marah", ("marah", "geram", "murka")),
    ("kesal", ("kesal", "jengkel", "sebal")),
    ("sedih", ("sedih", "menangis", "duka", "pilu", "kehilangan", "terluka")),
    ("bingung", ("bingung", "heran", "aneh", "membingungkan")),
    ("ragu", ("ragu", "tidak yakin", "bimbang", "dulu tidak yakin")),
    ("mikir", ("kenapa", "mengapa", "bayangkan", "renungkan", "pikirkan", "artinya")),
    ("lega", ("lega", "aman", "selamat", "tenang")),
    ("senang", ("senang", "gembira", "bahagia", "bersyukur")),
    ("malu", ("malu", "segan")),
    ("lelah", ("lelah", "capek", "letih", "lemah")),
]

# (Pose/gestur per emosi kini di arah_visual.POSE_UNTUK_WAJAH -- dulu cuma takut->lindungi.)


def _wajah_dari_teks(teks: str, bawaan: str = "netral") -> str:
    t = teks.lower()
    for wajah, kata in LEKSIKON_EMOSI:
        if any(k in t for k in kata):
            return wajah
    if t.count("?") >= 1:
        return "bingung"
    return bawaan


LEBAR_LAYAR = 1080
MARGIN_LAYAR = 70  # kiri+kanan gabungan, lihat f_128.0.png: ukuran 86 tanpa hitungan ini meluber


def _ukuran_teks_aman(baris: list[str], maksimum: int = 86, minimum: int = 44) -> int:
    """cerita.js (fungsi teks(), tidak seperti kartu_dalil) TIDAK auto-wrap/auto-kecilkan --
    kalau baris kepanjangan untuk `ukuran`, teksnya meluber keluar layar (ditemukan lewat
    pratinjau visual nyata, 19 Nov 2026). DejaVu Sans bold lebar per huruf kira-kira
    0.62x font-size; hitung ukuran terbesar yang masih muat baris TERPANJANG."""
    terpanjang = max((len(b) for b in baris), default=1)
    if terpanjang == 0:
        return maksimum
    muat = int((LEBAR_LAYAR - MARGIN_LAYAR) / (0.62 * terpanjang))
    return max(minimum, min(maksimum, muat))


# Daftar jenis `benda` yang NYATA ada di papan/cerita.js -- diverifikasi LANGSUNG dari kode
# (grep `j === "..."`) 19 Nov 2026, bukan disalin dari dokumen manapun (ditemukan satu
# cabang lama `feat/short-term-production-intelligence` punya katalog serupa tapi sudah
# basi & memuat satu entri yang tidak pernah nyata diimplementasikan di cerita.js --
# "brand_logo" -- jadi dibuat ulang dari sumber kebenaran langsung). Dipakai validasi di
# akhir arahkan(), supaya salah ketik jenis objek ketahuan saat Direktur jalan, bukan baru
# gagal diam-diam saat render.
# DIPERBAIKI 20 Nov 2026: grep 19 Nov mengambil `j === "..."` dari SELURUH berkas, sehingga
# nama RUANG (tamu, dapur, kamar, kantor, ...: cabang fungsi ruang()) dan jenis BAJU (kaus,
# gamis, ...: cabang bajuDetail()) ikut masuk -- padahal sebagai `benda` mereka tidak
# menggambar apa-apa. Daftar ini kini HANYA dari isi fungsi benda() (lihat
# `_jenis_dari_cerita_js`, dan tests/test_direktur.py yang memastikan keduanya sama).
SUPPORTED_JENIS = frozenset({
    "amplop", "api", "arus", "awan", "bahtera", "bambu", "batu", "bawah_laut",
    "bayang_misteri", "belah", "bingkai", "bintang", "buku", "bulan", "cahaya",
    "cawan", "chat", "danau", "dompet", "gapura",
    "gedung", "gelap", "gerbang", "gua", "gunung", "hati", "hewan",
    "hp", "ikan", "infus", "jalan", "jembatan", "jenazah",
    "jendela", "jurang", "kalender", "kamboja", "kantong",
    "kantor_gedung", "kartu_dalil", "kasur", "kelapa", "kerumunan", "kipas",
    "kitab", "koin", "kompor", "kota", "kue", "kulkas", "kursi", "lahar",
    "lapak", "laut", "lemari", "logo_app", "makam", "mangga", "masjid", "masjid_kampung",
    "massa_api", "meja", "meja_belajar", "meja_kantor", "menara", "mik", "mobil_luar",
    "monitor", "motor", "ngarai", "nur", "obat", "ombak", "pagar", "pancar",
    "pantai", "pemimpin", "penggali", "petir", "pisang", "pohon", "ponsel",
    "pot", "rak_buku", "ranjang_rs", "rantai", "rantai_tarik", "retakan", "rincian", "rumah",
    "rumah_kampung", "rumah_sakit_gedung", "rumput", "saf", "sajadah", "sapu", "sawah",
    "sekolah", "semak", "setir", "sofa", "stempel", "surya",
    "tanda", "tebing", "telaga", "tiang_listrik", "timbangan", "toko", "tv",
    "uang", "unta", "warung", "zaqqum",
})
CERITA_JS = ROOT / "mesin-video" / "papan" / "cerita.js"


def _jenis_dari_cerita_js() -> dict[str, frozenset]:
    """Baca kosakata NYATA dari cerita.js (sumber kebenaran): jenis benda (isi fungsi benda()),
    jenis ruang (fungsi ruang()), nama POSE, nama PALET. Dipakai validator & tes -- bukan daftar
    tulisan tangan yang bisa basi."""
    src = CERITA_JS.read_text(encoding="utf-8")

    def potong(mulai: str, akhir: str) -> str:
        a = src.index(mulai)
        return src[a:src.index(akhir, a)]

    jenis = lambda bag: frozenset(re.findall(r'j === "([a-z_0-9]+)"', bag))
    pose = potong("const POSE = {", "\n  };")
    palet = potong("const PALET = {", "\n  };")
    return {
        "benda": jenis(potong("function benda(o, t, d)", "// ---- RANGKA BERSENDI")),
        "ruang": jenis(potong("function ruang(R, t)", "function kerumunan(")),
        "pose": frozenset(re.findall(r"^\s+([a-z_0-9]+): \{", pose, re.M) + re.findall(r"\b([a-z_0-9]+): \{", pose)),
        "palet": frozenset(re.findall(r"\b([a-z_]+): \{ langit", palet)),
    }


def _validasi_benda(spek: dict) -> list[str]:
    """Kembalikan daftar peringatan (bukan exception -- Direktur tetap menulis filenya,
    tapi pemilik/pengembang harus lihat peringatan ini sebelum render final).
    Sejak 20 Nov 2026 juga memeriksa ruang, nama pose, dan palet -- tiga kosakata baru yang
    dipakai lapisan arah_visual; salah satu nama di sana = cerita.js diam-diam memakai bawaan."""
    peringatan = []
    try:
        kos = _jenis_dari_cerita_js()
    except (OSError, ValueError):
        kos = {"benda": SUPPORTED_JENIS, "ruang": AV.JENIS_RUANG, "pose": AV.POSE_SEMUA, "palet": frozenset()}
    for i, s in enumerate(spek["cerita"]["shot"]):
        for b in s.get("benda", []):
            if b.get("jenis") not in SUPPORTED_JENIS or b.get("jenis") not in kos["benda"]:
                peringatan.append(f"shot {i}: jenis benda tidak dikenal: {b.get('jenis')!r}")
        r = s.get("ruang")
        if r is not None:
            rj = r if isinstance(r, str) else r.get("jenis")
            if rj not in kos["ruang"]:
                peringatan.append(f"shot {i}: jenis ruang tidak dikenal: {rj!r}")
        if s.get("palet") is not None and kos["palet"] and s["palet"] not in kos["palet"]:
            peringatan.append(f"shot {i}: palet tidak dikenal: {s['palet']!r}")
        for bn in s.get("boneka", []):
            p = bn.get("pose")
            nama = [k[1] for k in p] if isinstance(p, list) else ([p] if isinstance(p, str) else [])
            for n in nama:
                if isinstance(n, str) and n not in kos["pose"]:
                    peringatan.append(f"shot {i}: pose tidak dikenal: {n!r}")
    return peringatan


def _seed_dasar(judul: str) -> int:
    """Seed stabil per judul (bukan acak ulang tiap render) tapi beda antar video, supaya
    kerumunan/variasi visual tidak selalu identik di semua video (lihat PRINSIP #12)."""
    return int(hashlib.sha1(judul.encode()).hexdigest(), 16) % 10_000


def _posisi(idx: int, total: int) -> str:
    frac = idx / max(1, total - 1)
    if idx == 0:
        return "hook"
    if idx == total - 1:
        return "penutup"
    if frac >= 0.78:
        return "klimaks"
    return "isi"


# Intensitas zoom kamera per posisi (z awal, z akhir) -- hook & klimaks lebih dramatis.
ZOOM_PER_POSISI = {
    "hook": (1.0, 1.07),
    "isi": (1.0, 1.03),
    "klimaks": (1.0, 1.12),
    "penutup": (1.02, 0.98),  # sedikit menjauh -- kesan "menutup", bukan menekan
}

# Suasana langit (gelap=0 terang=1) per posisi -- hook misterius, klimaks paling gelap/tegang.
LANGIT_PER_POSISI = {"hook": 0.08, "isi": 0.14, "klimaks": 0.05, "penutup": 0.22}


def _rentang_ayat(ayat) -> list[int]:
    """'50' -> [50]; '94-95' -> [94, 95]. Rentang terbalik/terlalu panjang ditolak (kartu dilewati)."""
    bagian = str(ayat).replace(" ", "").split("-")
    if not 1 <= len(bagian) <= 2 or not all(x.isdigit() for x in bagian):
        raise ValueError(f"nomor ayat tidak sah: {ayat!r}")
    awal, akhir = int(bagian[0]), int(bagian[-1])
    if awal < 1 or akhir < awal or akhir - awal > 9:
        raise ValueError(f"rentang ayat tidak wajar: {ayat!r}")
    return list(range(awal, akhir + 1))


def _ambil_dalil_untuk_adegan(nama_adegan: str, dalil_dipakai: list[dict]) -> dict | None:
    """Cari dalil_dipakai yang menunjuk adegan ini, lalu AMBIL ULANG teks Arab+terjemahan
    dari API resmi SEKARANG (tidak pernah percaya cache naskah lama). Gagal verifikasi ->
    None (kartu dalil dilewati, tidak diganti karangan)."""
    for d in dalil_dipakai:
        if d.get("di_adegan") != nama_adegan:
            continue
        try:
            surah, rentang = int(d["surah"]), _rentang_ayat(d["ayat"])
            daftar = [ambil_ayat(surah, a) for a in rentang]
            nomor = f"{rentang[0]}-{rentang[-1]}" if len(rentang) > 1 else str(rentang[0])
            terjemah = [x.get("terjemah") or x.get("terjemahan") for x in daftar]
            return {
                "kitab": f"QS {surah}:{nomor}",
                # Ayat dalam rentang digabung berurutan; penjaga dalil memverifikasi gabungan yang sama.
                "arab": " ".join(x["teks_arab"] for x in daftar),
                "teks": " ".join(t for t in terjemah if t) or "(terjemahan tidak tersedia)",
                "label": "QUR'AN",
            }
        except Exception:
            # Sumber tidak tersedia atau rujukan tidak dapat dipastikan: jangan membuat dalil.
            return None
    return None


def _waktu_adegan(adegan: list[dict], waktu_adegan: list[float] | None) -> list[tuple[float, float]]:
    """(mulai, durasi) tiap adegan. Durasi adegan terakhir tidak diketahui dari waktu mulai saja
    -> diperkirakan dari panjang teks (14 huruf/dtk, laju narator Ozhy di video terkirim)."""
    est = [max(3.5, len(a.get("teks", "")) / 14.0) for a in adegan]
    mulai, t = [], 0.0
    for i in range(len(adegan)):
        mulai.append(float(waktu_adegan[i]) if waktu_adegan is not None else t)
        t += est[i]
    return [(m, (mulai[i + 1] - m) if i + 1 < len(mulai) else est[i]) for i, m in enumerate(mulai)]


def _lapisan_dasar(tema: str, palet: str | None, komposisi: list[dict], idx: int, seed0: int) -> list[dict]:
    """Bintang (bila langit malam) + komposisi tema + batu depan berselang-seling. Pola kedalaman
    dari dabbah2.json (bintang + objek tanah + batu kabur di depan) tetap dipakai, tetapi objek
    tanahnya kini dari tema, bukan selalu dua gunung kembar."""
    benda: list[dict] = []
    if tema in AV.TEMA_LANGIT_BINTANG and palet in (None, "malam", "gelap_malam", "subuh", "senja"):
        benda.append({"jenis": "bintang", "x": 540, "y": -1250, "s": 1, "seed": seed0 % 20, "tinggi": 1500, "n": 80})
    benda += [dict(b) for b in komposisi]
    # Tidak ada lagi batu kabur otomatis di sudut depan (27 Nov): resep dari satu video lama
    # yang tidak bermakna di kebanyakan kisah. Lapis depan datang dari benda cerita
    # (tempat depan_kiri/depan_kanan di rencana sutradara).
    return benda


INDEKS_POSISI = {"hook": 0, "isi": 1, "klimaks": 2, "penutup": 3}
DEBU_TEMA = {"kota": 0, "kampung": 0, "surga": 0, "laut": 10, "ibadah": 12, "gua": 20}


def _boneka_kamu(tampilan: dict, letak: dict, wajah: str, pose: str, ds: float, teks: str,
                 posisi: str, R, sisi: int) -> tuple[dict, str]:
    """Boneka "kamu" satu shot: tampilan video + gestur yang BERUBAH di dalam shot (mulai
    berdiri/netral -> reaksi pada ~30% durasi -> untuk shot panjang kembali ke gestur yang
    lebih tenang). Mode tokoh hidup (cerita.js 13 Nov: kedip acak, goyang halus, pose meloncat
    lalu ditahan) dipakai supaya "kamu" tidak membeku selama belasan detik; batas tempo tenang
    untuk konten dalil (maks 2 perubahan per shot, RIWAYAT.md "Tokoh hidup")."""
    import copy
    b = {**letak, **copy.deepcopy(tampilan), "mata": "buka", "hidup": True}
    tk = round(min(1.8, max(0.35, 0.3 * ds)), 2)
    belakang = bool(letak.get("belakang"))
    if belakang and pose in ("tutup_wajah", "doa", "tunjuk_atas", "stop", "stop2", "pegang_hp", "tepuk_dahi", "garuk_kepala", "silang"):
        pose = R.choice(("lemas", "berkacak", "berdiri"))  # gestur "di depan wajah" tak terbaca dari belakang
    kunci_pose = [[0, "berdiri"], [tk, pose]] if pose != "berdiri" else "berdiri"
    if ds > 7.5 and pose != "berdiri":
        tenang = "tangan_dada" if pose not in ("tangan_dada", "doa", "pegang_hp") else "berdiri"
        if belakang:
            tenang = "berdiri"
        kunci_pose.append([round(ds * 0.68, 2), tenang])
    b["pose"] = kunci_pose
    w0 = "netral" if wajah != "netral" else "netral"
    b["wajah"] = [[0, w0], [tk, wajah]] if wajah != w0 else wajah
    a_akhir = 0.0 if sisi == 0 else (0.35 if sisi < 0 else -0.35)
    if belakang:
        a_akhir = -a_akhir * 0.5
    b["arah"] = [[0, round(-a_akhir or R.choice((-0.25, 0.25)), 2)], [tk, a_akhir]]
    if not belakang:
        simbol = AV.SIMBOL_UNTUK_WAJAH.get(wajah)
        if simbol and (simbol != "tanya" or "?" in teks):
            b["simbol"] = [[round(tk + 0.1, 2), simbol]]
        reaksi = AV.REAKSI_UNTUK_WAJAH.get(wajah)
        if posisi == "penutup" and wajah in ("netral", "lega", "senang"):
            reaksi = "angguk"
        if reaksi:
            b["reaksi"] = [[tk, reaksi]]
    return b, pose


# Subjek yang membawa lanskapnya sendiri: `ngarai` sudah berupa dinding di celah dua tebing,
# `istana`/`gerbang` adalah bangunan besar. Latar tema yang bertabrakan dengannya dibuang
# (renderer menggambar benda `belakang` lebih dulu, sehingga gunung latar menimpa dinding).
SUBJEK_PANGGUNG = frozenset({"ngarai", "istana", "gerbang", "rumah", "rumah_kampung", "masjid",
                             "masjid_kampung", "gedung", "kantor_gedung", "sekolah", "rumah_sakit_gedung",
                             "bahtera", "gapura", "menara"})
LATAR_BERTABRAKAN = frozenset({"gunung", "tebing", "kota", "bukit"})
# Subjek suasana/latar: "kamu" tetap tokoh utama (mis. Mahsyar: "keringatmu sampai mana?").
SUBJEK_SUASANA = frozenset({"kerumunan", "ombak", "gunung", "rumah", "makam", "pancar"})


HORIZON_DINDING = 1500  # kaki dinding Zulkarnain di cakrawala (papan Ya'juj 1/2)


def _ikat_posisi_subjek(shot: dict, subjek: list[dict]) -> None:
    """Posisi subjek ditetapkan relatif satu sama lain, bukan angka lepas per benda.

    - Kaki dinding (`ngarai`) berdiri di garis cakrawala; tanah tidak menutupinya.
    - Titik gali `penggali` = lubang dinding (x + lx, y + ly), jadi beliung mengayun ke lubang.
    - `pemimpin` berdiri di depan, di samping dinding, menghadap para penggali.
    Mengubah benda subjek di tempat; dipanggil sebelum benda dimasukkan ke shot.
    """
    dinding = next((o for o in subjek if o.get("jenis") == "ngarai"), None)
    if dinding is None:
        return
    shot["horizon"] = HORIZON_DINDING
    skala = float(dinding.get("s", 1) if not isinstance(dinding.get("s"), list) else 1)
    dinding.update({"x": 540, "y": HORIZON_DINDING})
    dinding.pop("belakang", None)
    lubang_x = 540 + (dinding.get("lx") or 0) * skala
    lubang_y = HORIZON_DINDING + (dinding.get("ly") if dinding.get("ly") is not None else -190) * skala
    for o in subjek:
        if o.get("jenis") == "penggali":
            o.update({"x": round(lubang_x), "y": round(lubang_y), "s": skala})
        elif o.get("jenis") == "pemimpin":
            o.update({"x": 300, "y": 1700, "s": 1.2, "depan": True})


def _awal(v, bawaan):
    """Nilai awal dari angka atau kunci waktu [[t, nilai], ...]."""
    while isinstance(v, list) and v:
        v = v[0][1] if isinstance(v[0], list) else v[0]
    return float(v) if isinstance(v, (int, float)) else bawaan


def _maks(v, bawaan):
    if isinstance(v, list) and v:
        return max(_maks(x, bawaan) for x in v)
    return float(v) if isinstance(v, (int, float)) else bawaan


def _ikat_langit(shot: dict, subjek: list[dict]) -> None:
    """Benda langit duduk di langit relatif terhadap cakrawala shot, bukan di tanah.

    Tanpa ini matahari/bulan subjek mendapat y tanah bawaan dan tertutup tanah/kerumunan
    (ditemukan pemeriksa visual pada Mahsyar: klimaks "matahari didekatkan" tanpa matahari)."""
    h = float(shot.get("horizon") or 1100)
    for o in subjek:
        j = o.get("jenis")
        if j == "surya":
            # piringan (ukuran terbesarnya) hampir utuh di atas cakrawala, digambar di depan
            # gunung latar: matahari subjek adalah pusat perhatian, bukan hiasan di balik bukit.
            r = _maks(o.get("r"), 300)
            o.update({"y": round(h - max(r * 0.85, 230.0)), "s": 1})  # kecil: di atas kepala tokoh depan
            o.pop("belakang", None)
            continue
        elif j == "bulan":
            o.update({"y": round(h - 560), "s": o.get("s", 1)})
        elif j == "awan":
            o.update({"y": round(h - 680)})
        elif j == "bintang":
            o.update({"x": 540, "y": 0, "s": 1})
        else:
            continue
        o.pop("depan", None)
        o["belakang"] = True


def _kamera_bidikan(subjek: dict, kamera: dict, ds: float) -> dict:
    """Bidikan dari rencana sutradara: lebar / sedang / dekat ke pusat subjek, plus aksen."""
    def _x(o):
        x = o.get("x", 540)
        while isinstance(x, list) and x:
            x = x[0][1] if isinstance(x[0], list) else x[0]
        return float(x) if isinstance(x, (int, float)) else 540.0

    pelaku = [o for o in subjek["benda"] if not o.get("belakang")] or subjek["benda"]
    pusat = round(statistics.fmean(_x(o) for o in pelaku)) if pelaku else 540
    bidikan = subjek.get("bidikan", "lebar")
    if bidikan == "dekat":
        baru = {"z": [1.5, 1.6], "x": pusat, "y": 1220}
    elif bidikan == "sedang":
        baru = {"z": [1.18, 1.25], "x": round((pusat + 540) / 2), "y": 1120}
    else:
        baru = {"z": [1.0, 1.06], "x": 540, "y": 1000}
    for kunci in ("hentak", "guncang"):
        if kunci in kamera:
            baru[kunci] = kamera[kunci]
    tk = round(min(ds * 0.35, 1.4), 2)
    if subjek.get("aksen") == "hentak":
        baru["hentak"] = [[tk, 0.11]]
    elif subjek.get("aksen") == "guncang":
        baru["guncang"] = [[tk, 30]]
    return baru


def _susun_ulang_untuk_subjek(benda: list[dict], subjek: list[dict], b: dict, kamera: dict,
                              look: dict, wajah: str, pose: str, ds: float, tx: str,
                              posisi: str, R, paksa_saksi: bool = False) -> tuple[list[dict], dict, dict]:
    """Jadikan subjek narasi fokus shot, bukan tempelan di atas templat "kamu".

    - Latar tema yang bertabrakan dengan subjek panggung (dinding, istana, gerbang) dibuang.
    - Tokoh "kamu" mundur menjadi saksi: kecil, tampak belakang, di sisi yang berlawanan
      dengan subjek, sehingga tidak menutupi atau tampak berdiri di antara pelaku cerita.
    - Kamera melebar ke subjek; bidikan dekat ke wajah "kamu" akan memotong subjek keluar
      bingkai. Aksen kamera (hentak/guncang) yang sudah ditetapkan tetap dipertahankan.
    """
    jenis_subjek = {x.get("jenis") for x in subjek}
    if jenis_subjek & SUBJEK_PANGGUNG:
        benda = [x for x in benda if x.get("jenis") not in LATAR_BERTABRAKAN or any(x is o for o in subjek)]

    def _x_awal(o: dict) -> float:
        x = o.get("x", 540)
        while isinstance(x, list) and x:
            x = x[0][1] if isinstance(x[0], list) else x[0]
        return float(x) if isinstance(x, (int, float)) else 540.0

    pelaku = list(subjek) if paksa_saksi else [o for o in subjek if o.get("jenis") not in SUBJEK_SUASANA]
    if not pelaku:
        return benda, b, kamera
    pusat = statistics.fmean(_x_awal(o) for o in pelaku)
    x_saksi = 880 if pusat < 540 else 200
    # Kaki sedikit di bawah bingkai: "kamu" menjadi siluet saksi di latar paling depan,
    # di bawah garis kaki pelaku sehingga tidak menumpuk dengan mereka.
    letak = {"x": x_saksi, "y": 1980, "s": 0.55, "belakang": True}
    b_baru, _ = _boneka_kamu(look, letak, wajah, pose, ds, tx, posisi, R, -1 if x_saksi > 540 else 1)
    for kunci in ("keringat", "genangan"):
        if kunci in b:
            b_baru[kunci] = b[kunci]

    lebar = {"z": [1.0, 1.06], "x": 540, "y": 1000}
    for kunci in ("hentak", "guncang"):
        if kunci in kamera:
            lebar[kunci] = kamera[kunci]
    return benda, b_baru, lebar


def arahkan(naskah: dict, waktu_adegan: list[float] | None = None,
            waktu_kata: list[list] | None = None, tampilan: dict | None = None,
            latar: str | None = None) -> dict:
    """naskah (output penulis/tulis.py) -> spesifikasi papan {"cerita": {"shot": [...]}}.
    Tiap adegan = 1-3 shot (dipotong di batas kalimat bila adegan panjang): lingkungan sesuai
    tema cerita + boneka "kamu" (penonton) bereaksi dengan gestur & framing yang bervariasi,
    atau kartu_dalil saat adegan itu mengutip ayat terverifikasi.

    waktu_adegan (opsional): waktu mulai (detik) NYATA tiap adegan, dari narasi TTS yang
    sudah direkam (lihat papan/buat_video.py + papan/kisah/dlib.py) -- kalau diberikan,
    MENIMPA kamera/timing tebakan di bawah dengan waktu ucapan sungguhan. Tanpa ini,
    "at" hanya perkiraan kasar (dipakai utk pratinjau cepat sebelum ada suara).
    waktu_kata (opsional): per adegan, [[t_absolut, kata], ...] dari TTS -- dipakai supaya
    potongan shot jatuh TEPAT di batas kalimat yang diucapkan.
    tampilan (opsional): kunci tampilan "kamu" (lihat arah_visual.KUNCI_TAMPILAN_BOLEH), mis.
    {"jenis_kelamin": "wanita", "pakaian": {"jenis": "gamis", "warna": "#6aa6a0"}} atau
    {"polos": True} untuk tampilan lama. latar (opsional): paksa tema (arah_visual.TEMA_SEMUA).
    Keduanya juga bisa ditaruh di naskah["arah_visual"]; parameter fungsi menang.

    Setiap shot diberi "_adegan" (indeks adegan asal; diabaikan cerita.js) supaya pemanggil
    (buat_video.py) bisa memetakan shot kembali ke adegan."""
    adegan = naskah.get("adegan", [])
    total = len(adegan)
    judul = naskah.get("judul", "")
    seed0 = _seed_dasar(judul)
    dalil_dipakai = naskah.get("dalil_dipakai", [])
    teks_gabungan = judul + " " + " ".join(a.get("teks", "") for a in adegan)
    arah = naskah.get("arah_visual") or {}
    tampilan = tampilan if tampilan is not None else arah.get("tampilan")
    latar = latar or arah.get("latar")

    look, catatan, _konteks = AV.pilih_tampilan(teks_gabungan, judul, tampilan)
    if latar and latar not in AV.TEMA_SEMUA:
        catatan.append(f"latar {latar!r} tidak dikenal (pilihan: {AV.TEMA_SEMUA}); dipilih otomatis")
        latar = None
    tema_utama = latar or AV.pilih_tema(judul, teks_gabungan)

    R_vid = AV.acak(judul, "video")
    framing_seb, pose_seb = None, None
    sisi = R_vid.choice((-1, 1))
    varian0 = R_vid.randrange(12)
    shots = []
    jadwal = _waktu_adegan(adegan, waktu_adegan)
    for idx, (a, (t0, dur)) in enumerate(zip(adegan, jadwal)):
        teks, nama = a.get("teks", ""), a.get("nama", f"s{idx}")
        posisi = _posisi(idx, total)
        R = AV.acak(judul, "adegan", idx)
        tema = latar or AV.tema_lokal(teks, tema_utama)
        palet = AV.PALET_TEMA[tema][INDEKS_POSISI[posisi]]
        h = AV.HORIZON_TEMA.get(tema, 1100 + (idx % 3) * 60)
        sisi = -sisi  # boneka "samping/jauh" bergantian kiri-kanan antar adegan
        badai = tema == "laut" and bool(re.search(r"badai|banjir|air bah|ombak (besar|tinggi)", teks, re.I))
        varian = varian0 + idx  # digilir: adegan berurutan tidak pernah dapat komposisi yang sama
        komposisi = AV._k_laut(R, h, sisi, varian, badai=True) if badai else AV.KOMPOSISI[tema](R, h, sisi, varian)
        dasar = _lapisan_dasar(tema, palet, komposisi, idx, seed0)
        ruang = AV.ruang_untuk(teks)
        z0, z1 = ZOOM_PER_POSISI[posisi]
        tak_berwujud = bool(PENANDA_WUJUD_TAK_DIJELASKAN.search(teks))
        # bawaan emosi bila tidak ada kata emosi: hook = bingung (memancing tanya), penutup =
        # lega (ajakan berbuat baik = harapan; versi lama memakai "bingung" juga di penutup).
        wajah_adegan = _wajah_dari_teks(teks, bawaan={"isi": "netral", "hook": "bingung"}.get(posisi, "lega"))

        def shot_dasar(at: float) -> dict:
            s: dict = {
                "at": round(at, 2), "_adegan": idx, "_narasi": teks, "horizon": h
            }
            if palet is not None:
                s["palet"] = palet
                s["malam"] = AV.MALAM_PALET.get(palet, 0)
                s["langit"] = LANGIT_PER_POSISI[posisi]
            else:  # langit Mahsyar bawaan: `langit` = panas (0 gelap .. 1 terik)
                s["langit"] = AV.LANGIT_MAHSYAR[posisi]
                if posisi == "klimaks":
                    s["panas"] = 1
            if tema in DEBU_TEMA:
                s["debu"] = DEBU_TEMA[tema]
            return s

        dalil = _ambil_dalil_untuk_adegan(nama, dalil_dipakai)
        if dalil:
            # Adegan kutipan ayat: kartu dalil jadi fokus utama -- TIDAK diubah dari versi
            # terbukti (kamera hampir diam, z ~1, kartu di tengah). Hanya latar di belakang
            # kartu yang kini mengikuti tema (kartu punya latar sendiri yang menutupi).
            # arab_ukuran: cerita.js TIDAK auto-kecilkan font Arab (beda dari teks terjemahan
            # yang auto-shrink) -- ayat panjang (mis. QS 6:158, 39 kata) bisa bikin kartu lebih
            # tinggi dari layar & terpotong atas-bawah kalau dipaksa ukuran bawaan (56). Kecilkan
            # proporsional jumlah kata, verified lewat render pratinjau lokal (19 Nov 2026).
            s = shot_dasar(t0)
            s["kamera"] = {"z": [z0, z1], "x": 540, "y": 1000 + (idx % 2) * 40}
            n_kata_arab = len(str(dalil["arab"]).split())
            # Rentang ayat bisa jauh lebih panjang dari satu ayat: tambah satu tingkat lebih kecil.
            arab_ukuran = 56 if n_kata_arab <= 20 else (46 if n_kata_arab <= 30 else (38 if n_kata_arab <= 45 else 32))
            s["benda"] = dasar + [{
                "jenis": "kartu_dalil", "x": 540, "y": 960, "at": 0.15,
                "kitab": dalil["kitab"], "teks": dalil["teks"], "arab": dalil["arab"],
                "label": dalil["label"], "arab_ukuran": arab_ukuran,
            }]
            shots.append(s)
            framing_seb = "lebar"
            continue

        if tak_berwujud:
            # Pagar: TIDAK menebak bentuk makhluk. Pola proven dari dabbah2.json: bingkai foto
            # buram beredar + tanda tanya ("ini yang katanya wujudnya -- tidak ada dasarnya"),
            # jauh lebih hidup drpd layar kosong, tapi tetap tidak menggambar sosok apa pun.
            s = shot_dasar(t0)
            s["kamera"] = {"z": [z0, z1], "x": 540, "y": 1000 + (idx % 2) * 40}
            s["benda"] = dasar + [{"jenis": "bingkai", "x": 800, "y": 950, "s": 0.8, "rot": -6, "at": 0.3}]
            b, pose_seb = _boneka_kamu(look, {"x": 540, "y": 1700, "s": 1.1}, "bingung",
                                       "angkat_bahu" if pose_seb != "angkat_bahu" else "garuk_kepala",
                                       dur, teks, posisi, R, 0)
            b["mata"] = "atas"
            s["boneka"] = [b]
            shots.append(s)
            framing_seb = "lebar"
            continue

        kata = waktu_kata[idx] if waktu_kata is not None and idx < len(waktu_kata) else None
        segmen = AV.pecah_segmen(teks, t0, dur, kata)
        for j, (ts, ds, tx) in enumerate(segmen):
            wajah = _wajah_dari_teks(tx, bawaan=wajah_adegan)
            framing = AV.rencana_framing(posisi, wajah, R, framing_seb, idx == 0 and j == 0,
                                         idx == total - 1 and j == len(segmen) - 1, tema)
            if ruang and framing == "jauh":
                framing = "samping"  # ruang dalam sempit: tidak ada "pemandangan" untuk ditatap
            kamera, letak, sisi_b = AV.kamera_dan_boneka(framing, ds, R, sisi)
            pose = AV.pilih_pose(tx, wajah, R, pose_seb)
            b, pose_seb = _boneka_kamu(look, letak, wajah, pose, ds, tx, posisi, R, sisi_b)
            s = shot_dasar(ts)
            pw = AV.palet_waktu(tx, tema) or AV.palet_waktu(teks, tema)
            if pw and "palet" in s:
                s["palet"], s["malam"] = pw, AV.MALAM_PALET.get(pw, 0)
            s["kamera"] = kamera
            if j > 0:
                s["kilat"] = False  # potongan di dalam satu adegan = potong langsung, tanpa kilat hitam
            tk = round(min(1.8, max(0.35, 0.3 * ds)), 2)
            atm = AV.atmosfer(tx)
            if atm.pop("_guncang", False):
                kamera["guncang"] = [[tk, 36]]
            elif posisi == "klimaks" and wajah in ("kaget", "takut"):
                kamera["hentak"] = [[tk, 0.08]]  # satu hentakan di puncak emosi, bukan di semua shot
            s.update(atm)
            if ruang:
                s["ruang"] = ruang
                s.pop("palet", None)
                s.pop("debu", None)
                benda = []
            else:
                benda = [dict(x) for x in dasar]
                if s.get("palet") not in (None, "malam", "gelap_malam", "subuh", "senja"):
                    benda = [x for x in benda if x["jenis"] not in ("bintang", "bulan")]
                fx = AV._fokus_x(sisi_b, R)
                ada = {x["jenis"] for x in benda}
                aksen = AV.aksen_untuk(tx, fx, h, letak["x"], laut=(tema == "laut"))
                if framing == "dekat":  # bidikan wajah: aksen di tepi bingkai cuma terpotong
                    aksen = [x for x in aksen if x["jenis"] in ("cahaya", "gelap")]
                benda += [x for x in aksen if x["jenis"] not in ada]
                if pose == "doa":  # sajadah di kaki saat berdoa (bukan di ruang dalam yang berlantai)
                    benda.append({"jenis": "sajadah", "x": letak["x"], "y": letak["y"] + 14, "s": round(letak["s"] * 0.9, 2)})
            # Subjek yang disebut narasi harus hadir di shot yang mengucapkannya.
            # Pemetaan dimiliki paket genre, terpisah dari leksikon alat ukur.
            # Rencana sutradara (LLM) bila ada: keputusan makna per beat. Tanpanya: aturan subjek.
            rb = a.get("rencana") if isinstance(a.get("rencana"), dict) else None
            subjek = (subjek_dari_rencana(rb, tx, ds, seed0 + idx * 100 + j) if rb
                      else arahkan_subjek(tx, ds, idx * 100 + j, konteks=teks_gabungan))
            if rb:
                # Rencana sutradara: subjek menggantikan latar berjenis sama (mis. gunung tujuan
                # berlindung menggantikan gunung latar), bukan diabaikan karena jenisnya sudah ada.
                jenis_subjek = {x.get("jenis") for x in subjek["benda"]}
                benda = [x for x in benda if x.get("jenis") not in jenis_subjek] + list(subjek["benda"])
            else:
                jenis_ada = {x.get("jenis") for x in benda}
                benda += [x for x in subjek["benda"] if x.get("jenis") not in jenis_ada]
            if subjek["benda"]:
                _ikat_posisi_subjek(s, subjek["benda"])
                _ikat_langit(s, subjek["benda"])
                if not rb or subjek["kamu"] == "saksi":
                    benda, b, kamera = _susun_ulang_untuk_subjek(benda, subjek["benda"], b, kamera, look, wajah,
                                                                  pose, ds, tx, posisi, R, paksa_saksi=bool(rb))
                else:
                    if {x.get("jenis") for x in subjek["benda"]} & SUBJEK_PANGGUNG:
                        benda = [x for x in benda if x.get("jenis") not in LATAR_BERTABRAKAN
                                 or any(x is o for o in subjek["benda"])]
                    if subjek["kamu"] == "utama":
                        # "kamu" tokoh utama: lapisan depan (mis. ombak) tidak boleh menutupi wajahnya
                        for o in benda:
                            if o in subjek["benda"]:
                                o.pop("depan", None)
                for o in benda:
                    o.pop("_di_lubang", None)
            if rb:
                kamera = _kamera_bidikan(subjek, kamera, ds)
            s["kamera"] = kamera
            s["benda"] = benda
            if subjek["teks"]:
                s["teks"] = (s.get("teks") or []) + subjek["teks"]
            if subjek["klimaks"] and not (rb and subjek.get("aksen")):
                kamera["hentak"] = [[round(min(ds * 0.35, 1.4), 2), 0.11]]
                kamera["guncang"] = [[round(min(ds * 0.35, 1.4), 2), 24]]
            # Efek lingkungan dan respons tubuh yang disebut eksplisit oleh narasi.
            # Semua properti ini sudah didukung renderer cerita.js.
            if re.search(r"\bkeringat\w*\b", teks, re.I):
                b["keringat"] = 1
                b["genangan"] = 110 if re.search(r"\b(tenggelam|sampai|setinggi)\b", teks, re.I) else 25
            if re.search(r"\b(meresap|menyerap)\b", teks, re.I):
                s["resap"] = {"p": 0.85, "dalam": 700}
            if re.search(r"\b(naungan|teduh)\b", teks, re.I):
                s["naungan"] = {"x": 540, "y": 1100, "r": 300, "kuat": 1}
            if re.search(r"\b(retak|terbelah|terbelahnya)\b", teks, re.I):
                s["retak"] = {"x": 540, "y": 1500, "p": 0.7}
            if re.search(r"\b(hujan|tercurah)\b", teks, re.I):
                s["hujan"] = 0.8
            s["boneka"] = [] if rb and subjek["kamu"] == "tidak" else [b]
            # Kerumunan latar hanya di tema "padang terbuka" (di kota/kampung/ruang dalam
            # kerumunan siluet di cakrawala terlihat janggal).
            if (tema in AV.TEMA_BOLEH_KERUMUNAN and not ruang
                    and (tema in AV.TEMA_SELALU_KERUMUNAN
                         or re.search(r"\bmanusia\b|\borang\b|\bsemua\b|\bkiamat\b", tx, re.IGNORECASE))):
                s["kerumunan"] = {"n": 180 + (seed0 + idx * 37 + j) % 150,
                                  "y0": 4, "y1": 380, "seed": (seed0 + idx + j) % 97}
            # Teks besar di layar hanya utk adegan hook & penutup (konvensi video lama: hook & CTA
            # besar, adegan tengah mengandalkan subtitle narasi saja) -- tetap tampil di semua
            # potongan adegan itu, hanya potongan pertama yang memudar masuk.
            if posisi in ("hook", "penutup") and a.get("kunci") and not rb:
                baris_teks = a["kunci"][:2]
                s["teks"] = [{"at": 0.1 if j == 0 else 0, "teks": "\n".join(baris_teks), "y": 320,
                              "ukuran": _ukuran_teks_aman(baris_teks)}]
            shots.append(s)
            framing_seb = framing

    spek = {"latar": "gelap", "musik": "santai" if total else False,
            "cerita": {"shot": shots}}
    if waktu_adegan is None and jadwal:
        # Tanpa narasi rekaman, papan.js tidak menghitung cerita.shot saat menebak durasi
        # (hasilnya hanya ~4 dtk = shot pertama). Durasi perkiraan ditulis eksplisit agar
        # pratinjau tanpa TTS memuat semua shot. Dengan audio, durasi tetap mengikuti suara.
        mulai_akhir, durasi_akhir = jadwal[-1]
        spek["durasi"] = round(mulai_akhir + durasi_akhir + 1.0, 2)
    if any("suara" in (a.get("rencana") or {}) for a in adegan):
        # Rencana sutradara mengatur suara: rekaman aset, tanpa musik/efek sintetis otomatis
        # (sama dengan video referensi Nuh/Ya'juj/Mahsyar).
        from .rencana_sutradara import rekaman_dari_rencana

        spek.update(musik=False, volume_efek=0,
                    rekaman=rekaman_dari_rencana(adegan, jadwal, waktu_kata))
    if catatan:
        spek["_catatan_direktur"] = catatan
    return spek


def main():
    import argparse
    import json

    ap = argparse.ArgumentParser(description="Direktur rule-based (naskah -> spesifikasi papan)")
    ap.add_argument("naskah", help="path naskah JSON (output penulis/tulis.py)")
    ap.add_argument("-o", "--out", help="path spesifikasi papan output (bawaan: <naskah>_papan.json)")
    ap.add_argument("--tampilan", help='kunci tampilan "kamu" (JSON), mis. \'{"jenis_kelamin":"wanita"}\'')
    ap.add_argument("--latar", help=f"paksa tema latar: {', '.join(AV.TEMA_SEMUA)}")
    args = ap.parse_args()

    naskah = json.load(open(args.naskah, encoding="utf-8"))
    spek = arahkan(naskah, tampilan=json.loads(args.tampilan) if args.tampilan else None, latar=args.latar)
    out = args.out or str(Path(args.naskah).with_name(Path(args.naskah).stem + "_papan.json"))
    json.dump(spek, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    n_dalil = sum(1 for s in spek["cerita"]["shot"]
                  if any(b.get("jenis") == "kartu_dalil" for b in s.get("benda", [])))
    print(f"Spesifikasi papan ditulis: {out} ({len(spek['cerita']['shot'])} shot, {n_dalil} kartu dalil)")
    for c in spek.get("_catatan_direktur", []):
        print("CATATAN:", c)
    for p in _validasi_benda(spek):
        print("PERINGATAN:", p)


if __name__ == "__main__":
    main()
