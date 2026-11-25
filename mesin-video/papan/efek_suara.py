"""Pemilih efek suara Kisah Islami -- heuristik lokal, tanpa LLM dan tanpa API.

Desainnya sengaja konservatif: efek hanya dipilih jika ada pemicu makna yang jelas
DAN berkas dengan nama persis tersedia di katalog. Nama berkas tidak ditebak,
karena efek yang hampir cocok justru dapat merusak makna adegan. Fungsi inti
menerima katalog sebagai argumen agar hasilnya deterministik dan mudah diuji;
pembacaan folder aset dipisahkan ke fungsi pembantu yang memiliki efek samping.

Hasil berisi tiga bagian:
- rekaman: langsung dapat digabungkan ke spec["rekaman"] Papan;
- anotasi: alasan setiap efek yang dipilih;
- butuh_efek_baru: usulan untuk keputusan manusia, tidak pernah membuat/mengunduh audio.

Kata waktu mengikuti format narasi_api.py: {"teks", "t0", "t1"} atau
[t0, teks]. Penempatan memakai @kata / @kata#n, sesuai pasang_waktu() Papan.
"""
from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


AKAR_REPO = Path(__file__).resolve().parents[1]
FOLDER_SUARA = AKAR_REPO / "aset" / "suara"

# Tiap aturan menyebut nama aset yang memang dikenal dari penggunaan repo.
# Aturan tidak membuat asumsi bahwa seluruh aset ini pasti ada: katalog aktual
# selalu menjadi sumber kebenaran saat pemilihan dilakukan.
ATURAN_EFEK: tuple[dict[str, Any], ...] = (
    {
        "efek": "tanah_retak",
        "pemicu": ("gempa", "gempa bumi", "retak", "terbelah", "tanah pecah",
                   "bumi berguncang", "bumi terbelah"),
        "alasan": "Peristiwa kerusakan atau gerakan tanah disebut secara langsung.",
        "prioritas": 100,
    },
    {
        "efek": "dentum_jauh",
        "pemicu": ("ledakan", "meledak", "dentuman keras", "dentuman besar"),
        "alasan": "Ledakan atau dentuman besar disebut sebagai peristiwa bunyi.",
        "prioritas": 97,
    },
    {
        "efek": "gemuruh_api",
        "pemicu": ("api berkobar", "kobaran api", "api mengamuk", "kebakaran besar"),
        "alasan": "Kobaran api menjadi sumber bunyi yang dominan dalam adegan.",
        "prioritas": 91,
    },
    {
        "efek": "pintu_besi",
        "pemicu": ("pintu dibanting", "pintu besi ditutup", "pintu besi terbanting",
                   "pintu berat tertutup", "pintu ditutup keras"),
        "alasan": "Pintu berat dibanting atau ditutup keras.",
        "prioritas": 90,
    },
    {
        "efek": "isak_lembut",
        "pemicu": ("menangis", "tangisan", "terisak", "isak tangis", "tersedu"),
        "alasan": "Tangisan manusia disebut secara langsung; gunakan isak lembut.",
        "prioritas": 86,
    },
    {
        "efek": "ratapan_jauh",
        "pemicu": ("meratap", "ratapan", "meraung sedih"),
        "alasan": "Ratapan terdengar sebagai suasana jauh, bukan dialog tokoh utama.",
        "prioritas": 84,
    },
    {
        "efek": "tetes",
        "pemicu": ("air menetes", "tetesan air", "tetes demi tetes", "bunyi tetesan"),
        "alasan": "Tetesan air menjadi detail bunyi yang disebut langsung.",
        "prioritas": 79,
    },
    {
        "efek": "jangkrik",
        "pemicu": ("jangkrik berbunyi", "suara jangkrik", "jangkrik bersahutan"),
        "alasan": "Suara jangkrik menjadi penanda suasana malam yang eksplisit.",
        "prioritas": 73,
    },
    {
        "efek": "angin_sejuk",
        "pemicu": ("angin sejuk", "semilir angin", "angin berembus lembut"),
        "alasan": "Semilir angin yang tenang disebut sebagai detail suasana.",
        "prioritas": 70,
    },
    {
        "efek": "palu_kayu",
        "pemicu": ("palu diketuk", "memukul kayu", "ketukan palu", "palu memukul"),
        "alasan": "Ketukan palu pada benda keras disebut secara langsung.",
        "prioritas": 82,
    },
    {
        "efek": "timbangan_denting",
        "pemicu": ("timbangan berdenting", "anak timbangan", "neraca berdenting"),
        "alasan": "Bunyi timbangan atau anak timbangan relevan dengan adegan.",
        "prioritas": 80,
    },
    {
        "efek": "guntur_hujan",
        "pemicu": ("guntur", "petir", "hujan deras", "badai", "kilat menyambar"),
        "alasan": "Narasi menyebut cuaca badai, petir, atau guntur secara eksplisit.",
        "prioritas": 95,
    },
    {
        "efek": "rantai_seret",
        "pemicu": ("rantai", "belenggu", "dirantai", "rantai diseret"),
        "alasan": "Bunyi rantai relevan dengan benda atau tindakan yang disebut.",
        "prioritas": 94,
    },
    {
        "efek": "langkah_lari",
        "pemicu": ("berlari", "lari", "berlarian", "melarikan diri"),
        "alasan": "Gerakan lari disebut langsung; efek langkah biasa tidak cukup spesifik.",
        "prioritas": 93,
    },
    {
        "efek": "langkah_pelan",
        "pemicu": ("melangkah", "berjalan", "langkah", "berjalan perlahan",
                   "berjalan pelan"),
        "alasan": "Narasi menggambarkan langkah atau gerak berjalan.",
        "prioritas": 90,
    },
    {
        "efek": "getar_hp",
        "pemicu": ("ponsel bergetar", "hp bergetar", "ponselnya bergetar",
                   "telepon bergetar", "getaran ponsel"),
        "alasan": "Ada getaran perangkat yang menjadi peristiwa bunyi.",
        "prioritas": 92,
    },
    {
        "efek": "hp_dering",
        "pemicu": ("telepon berdering", "ponsel berdering", "hp berdering",
                   "telepon berbunyi", "ponsel berbunyi"),
        "alasan": "Ada panggilan/perangkat yang berdering, bukan sekadar disebut.",
        "prioritas": 92,
    },
    {
        "efek": "notif_pesan",
        "pemicu": ("pesan masuk", "notifikasi", "pesan diterima",
                   "ada pesan", "pemberitahuan masuk"),
        "alasan": "Narasi menyebut pesan atau notifikasi masuk.",
        "prioritas": 88,
    },
    {
        "efek": "halaman_buku",
        "pemicu": ("membuka kitab", "membuka buku", "membalik halaman",
                   "lembar kitab", "halaman buku"),
        "alasan": "Ada tindakan membuka atau membalik halaman buku/kitab.",
        "prioritas": 86,
    },
    {
        "efek": "kertas_amplop",
        "pemicu": ("membuka amplop", "kertas", "surat dibuka", "merobek surat"),
        "alasan": "Adegan memuat gerakan kertas atau amplop yang terdengar.",
        "prioritas": 84,
    },
    {
        "efek": "stempel",
        "pemicu": ("stempel", "cap dibubuhkan", "mencap"),
        "alasan": "Tindakan memberi cap/stempel disebut secara langsung.",
        "prioritas": 85,
    },
    {
        "efek": "koin_jatuh",
        "pemicu": ("koin jatuh", "uang logam jatuh", "koin terjatuh"),
        "alasan": "Ada koin atau uang logam yang jatuh.",
        "prioritas": 84,
    },
    {
        "efek": "air_mengalir",
        "pemicu": ("air mengalir", "aliran air", "sungai mengalir",
                   "air mengucur", "mata air"),
        "alasan": "Air bergerak/mengalir menjadi bagian peristiwa adegan.",
        "prioritas": 80,
    },
    {
        "efek": "detak_jantung",
        "pemicu": ("jantung berdegup", "detak jantung", "jantung berdebar",
                   "jantungnya berdegup"),
        "alasan": "Narasi secara eksplisit menggambarkan detak atau debar jantung.",
        "prioritas": 89,
    },
    {
        "efek": "napas_berat",
        "pemicu": ("terengah-engah", "napas berat", "napas tersengal",
                   "terengah", "susah bernapas"),
        "alasan": "Napas berat/tersengal merupakan kejadian audio yang jelas.",
        "prioritas": 87,
    },
    {
        "efek": "jam_dinding",
        "pemicu": ("jam berdetak", "detik berlalu", "waktu terus berjalan",
                   "jarum jam"),
        "alasan": "Adegan menekankan bunyi jam atau waktu yang terus berjalan.",
        "prioritas": 78,
    },
    {
        "efek": "panas_naik",
        "pemicu": ("sangat panas", "panas menyengat", "terik menyengat",
                   "suhu meningkat", "semakin panas"),
        "alasan": "Peningkatan panas disebut sebagai kondisi utama adegan.",
        "prioritas": 76,
    },
    {
        "efek": "kerumunan_cemas",
        "pemicu": ("kerumunan panik", "orang-orang panik", "massa ketakutan",
                   "kerumunan cemas"),
        "alasan": "Reaksi banyak orang menjadi suasana bunyi adegan; bukan untuk satu tokoh.",
        "prioritas": 78,
    },
    {
        "efek": "kilau_cahaya",
        "pemicu": ("cahaya menyilaukan", "cahaya berkilau", "cahaya memancar",
                   "cahaya terang muncul"),
        "alasan": "Munculnya cahaya menjadi peristiwa visual yang layak diberi aksen bunyi.",
        "prioritas": 72,
    },
    {
        "efek": "angin_gurun",
        "pemicu": ("angin gurun", "badai pasir", "pasir berembus",
                   "angin berembus di padang pasir"),
        "alasan": "Lokasi/peristiwa gurun dan angin disebut secara spesifik.",
        "prioritas": 75,
    },
    {
        "efek": "laut_malam",
        "pemicu": ("ombak malam", "laut malam", "laut bergelombang"),
        "alasan": "Suasana laut malam dinyatakan langsung.",
        "prioritas": 72,
    },
    {
        "efek": "bawah_laut",
        "pemicu": ("di bawah laut", "menyelam ke laut", "dasar laut"),
        "alasan": "Adegan berlangsung di bawah permukaan laut.",
        "prioritas": 74,
    },
    {
        "efek": "malam_hening",
        "pemicu": ("malam yang sunyi", "malam hening", "suasana hening"),
        "alasan": "Keheningan malam disebut sebagai suasana penting, bukan sekadar latar umum.",
        "prioritas": 68,
    },
    {
        "efek": "drone_gelap",
        "pemicu": ("suasana mencekam", "ancaman besar", "bahaya mengancam",
                   "kegelapan menyelimuti"),
        "alasan": "Narasi membangun ancaman atau suasana gelap yang berkelanjutan.",
        "prioritas": 65,
    },
    {
        "efek": "braam",
        "pemicu": ("kehancuran besar", "kiamat", "hari penghakiman",
                   "puncak peristiwa", "tak pernah terbayangkan"),
        "alasan": "Pernyataan berdampak besar atau puncak cerita membutuhkan aksen rendah yang singkat.",
        "prioritas": 70,
    },
    {
        "efek": "hentak_serius",
        "pemicu": ("terkejut", "tersentak", "tiba-tiba", "mendadak",
                   "fakta mengejutkan", "tidak disangka"),
        "alasan": "Ada kejutan/perubahan mendadak yang dapat diberi satu hentakan.",
        "prioritas": 82,
    },
    {
        "efek": "whoosh",
        "pemicu": (),
        "alasan": "Perpindahan shot yang dinyatakan eksplisit memerlukan aksen transisi.",
        "prioritas": 40,
        "khusus": "transisi",
    },
)

# Konsep kuat yang tidak selalu memiliki aset padanan. Daftar ini sengaja kecil:
# hanya kejadian yang memang mengundang bunyi spesifik, bukan setiap kata benda.
KEJADIAN_TANPA_PADANAN: tuple[tuple[str, str], ...] = (
    ("tembakan", "suara tembakan dari kejadian yang disebut"),
    ("kaca pecah", "kaca yang pecah dan berhamburan"),
    ("jeritan", "jeritan manusia yang jauh/teredam"),
    ("ombak besar", "ombak besar yang menghantam pantai"),
)


def _normalisasi(teks: str) -> str:
    """Samakan ejaan pencarian tanpa mengubah teks asli yang ditampilkan ke pengguna."""
    teks = unicodedata.normalize("NFKD", str(teks))
    teks = "".join(h for h in teks if not unicodedata.combining(h))
    teks = teks.lower().replace("-", " ")
    return re.sub(r"[^a-z0-9]+", " ", teks).strip()


def _kata_adegan(adegan: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Terima dua bentuk kata-waktu yang sudah dipakai pipeline, tanpa mengarang waktu."""
    hasil: list[dict[str, Any]] = []
    for butir in adegan.get("kata", []) or []:
        indeks_global = None
        if isinstance(butir, Mapping):
            teks, t0 = butir.get("teks"), butir.get("t0")
            indeks_global = butir.get("_indeks_global")
        elif isinstance(butir, (list, tuple)) and len(butir) >= 2:
            t0, teks = butir[0], butir[1]
        else:
            continue
        if teks is None or t0 is None:
            continue
        try:
            waktu = float(t0)
        except (TypeError, ValueError):
            continue
        if waktu < 0:
            continue
        entri = {"teks": str(teks), "t0": waktu}
        if isinstance(indeks_global, int) and indeks_global >= 0:
            entri["_indeks_global"] = indeks_global
        hasil.append(entri)
    return sorted(hasil, key=lambda x: x["t0"])


def baca_katalog_suara(folder: str | Path = FOLDER_SUARA) -> list[str]:
    """Baca nama MP3 yang benar-benar tersedia; fungsi inti tetap bebas akses berkas.

    Tidak mengandalkan daftar 47 nama yang ditulis tangan: folder aset adalah sumber
    kebenaran. Berkas selain MP3 diabaikan dan hasil diurutkan agar deterministik.
    """
    lokasi = Path(folder)
    if not lokasi.is_dir():
        return []
    return sorted(p.name for p in lokasi.iterdir()
                  if p.is_file() and p.suffix.lower() == ".mp3")


def _cocok_frasa(teks: str, pemicu: str) -> bool:
    """Cocokkan frasa utuh agar kata seperti 'lari' tidak cocok di dalam kata lain."""
    teks_bersih, pemicu_bersih = _normalisasi(teks), _normalisasi(pemicu)
    if not teks_bersih or not pemicu_bersih:
        return False
    return f" {pemicu_bersih} " in f" {teks_bersih} "


def _kata_adegan_dari_teks(teks: str) -> list[str]:
    """Pecah teks untuk mencari token; token waktu sebenarnya tetap diambil dari data TTS."""
    return re.findall(r"[\w]+(?:[-'][\w]+)*", str(teks), flags=re.UNICODE)


def selaraskan_adegan_dengan_tts(
    adegan: Sequence[Mapping[str, Any]],
    kata_tts: Sequence[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Tempelkan waktu TTS asli ke adegan teks secara berurutan.

    Adegan harus mengikuti urutan narasi yang sama. Kata yang tidak ditemukan
    tidak diberi waktu tebakan; masalahnya dikembalikan sebagai peringatan untuk
    pemeriksaan manual. Adegan yang sudah memiliki field kata dipertahankan.
    """
    hasil: list[dict[str, Any]] = []
    peringatan: list[dict[str, Any]] = []
    daftar_tts = list(kata_tts or [])
    token_tts = [_token_untuk_penempatan(str(k.get("teks", ""))) for k in daftar_tts]
    kursor = 0
    for nomor, sumber in enumerate(adegan):
        bagian = dict(sumber)
        if bagian.get("kata"):
            kata_ada: list[dict[str, Any]] = []
            for kata in _kata_adegan(bagian):
                token = _token_untuk_penempatan(kata["teks"])
                posisi = next((i for i in range(kursor, len(token_tts))
                               if token_tts[i] == token), None)
                if posisi is not None:
                    kata["_indeks_global"] = posisi
                    kursor = posisi + 1
                kata_ada.append(kata)
            bagian["kata"] = kata_ada
            hasil.append(bagian)
            continue

        cocok: list[dict[str, Any]] = []
        hilang: list[str] = []
        for token_asli in _kata_adegan_dari_teks(bagian.get("teks", "")):
            token = _token_untuk_penempatan(token_asli)
            posisi = next((i for i in range(kursor, len(token_tts))
                           if token_tts[i] == token), None)
            if posisi is None:
                hilang.append(token_asli)
                continue
            butir = daftar_tts[posisi]
            if butir.get("t0") is not None:
                salinan = dict(butir)
                salinan["_indeks_global"] = posisi
                cocok.append(salinan)
            kursor = posisi + 1
        bagian["kata"] = cocok
        hasil.append(bagian)
        if hilang:
            peringatan.append({
                "adegan": nomor,
                "status": "perlu_tinjau",
                "kata_tidak_ditemukan": hilang,
                "alasan": "Sebagian kata adegan tidak cocok dengan urutan kata pada berkas waktu TTS.",
            })
        if not cocok and str(bagian.get("teks") or "").strip():
            peringatan.append({
                "adegan": nomor,
                "status": "tanpa_alignment",
                "alasan": "Tidak ada kata adegan yang berhasil dipasangkan dengan waktu TTS.",
            })
    return hasil, peringatan


def _indeks_kata_pemicu(kata: Sequence[Mapping[str, Any]], pemicu: str) -> int | None:
    """Cari seluruh frasa secara berurutan pada alignment, bukan hanya kata pertamanya."""
    target = _normalisasi(pemicu).split()
    if not target:
        return None
    token_kata = [_normalisasi(butir["teks"]).split() for butir in kata]
    # Satu entri alignment kadang berisi lebih dari satu token; ratakan sambil
    # menyimpan indeks entri asal agar penempatan tetap memakai waktu TTS asli.
    rata: list[tuple[str, int]] = []
    for indeks, token in enumerate(token_kata):
        rata.extend((bagian, indeks) for bagian in token)
    for awal in range(0, len(rata) - len(target) + 1):
        if [x[0] for x in rata[awal:awal + len(target)]] == target:
            return rata[awal][1]
    return None


def _token_untuk_penempatan(teks: str) -> str:
    """Bentuk token @kata tanpa tanda baca; ejaan berhubung disatukan seperti aturan Papan."""
    token = _normalisasi(teks).replace(" ", "")
    return token


def _posisi_adegan(adegan: Mapping[str, Any]) -> str:
    return str(adegan.get("jenis_shot") or adegan.get("momen") or
               adegan.get("posisi") or "").strip().lower()


def _buat_peta_kata(
    adegan: Sequence[Mapping[str, Any]],
    kata_tts_global: Sequence[Mapping[str, Any]] | None = None,
) -> dict[tuple[int, int], str]:
    """Buat anchor dengan nomor kemunculan yang sama seperti seluruh berkas TTS."""
    total: dict[str, int] = {}
    if kata_tts_global is not None:
        for butir in kata_tts_global:
            token = _token_untuk_penempatan(str(butir.get("teks", "")))
            if token:
                total[token] = total.get(token, 0) + 1
        hitung_global: dict[str, int] = {}
        nomor_global: dict[int, int] = {}
        for indeks, butir in enumerate(kata_tts_global):
            token = _token_untuk_penempatan(str(butir.get("teks", "")))
            if token:
                hitung_global[token] = hitung_global.get(token, 0) + 1
                nomor_global[indeks] = hitung_global[token]
        peta: dict[tuple[int, int], str] = {}
        for i, bagian in enumerate(adegan):
            for j, butir in enumerate(_kata_adegan(bagian)):
                token = _token_untuk_penempatan(butir["teks"])
                indeks = butir.get("_indeks_global")
                if not token:
                    continue
                if isinstance(indeks, int) and indeks in nomor_global:
                    nomor = nomor_global[indeks]
                    peta[(i, j)] = f"@{token}" if total.get(token, 0) == 1 else f"@{token}#{nomor}"
                elif total.get(token, 0) == 1:
                    peta[(i, j)] = f"@{token}"
                # Kata berulang tanpa indeks global tidak aman dijadikan @kata#n.
                # Pemanggil akan memakai detik TTS asli sebagai cadangan.
        return peta

    hitung: dict[str, int] = {}
    semua: list[tuple[int, int, str]] = []
    for i, bagian in enumerate(adegan):
        for j, butir in enumerate(_kata_adegan(bagian)):
            token = _token_untuk_penempatan(butir["teks"])
            if token:
                semua.append((i, j, token))
                total[token] = total.get(token, 0) + 1
    peta = {}
    for i, j, token in semua:
        hitung[token] = hitung.get(token, 0) + 1
        peta[(i, j)] = f"@{token}" if total[token] == 1 else f"@{token}#{hitung[token]}"
    return peta


def pilih_efek_suara(
    adegan: Sequence[Mapping[str, Any]],
    katalog_suara: Iterable[str],
    *,
    jarak_minimum: float = 4.5,
    batas_per_adegan: int = 1,
    batas_per_menit: int = 6,
    rekaman_ada: Sequence[Mapping[str, Any]] = (),
    kata_tts_global: Sequence[Mapping[str, Any]] | None = None,
    awalan_berkas: str = "aset/suara",
) -> dict[str, list[dict[str, Any]]]:
    """Pilih dan tempatkan efek secara deterministik berdasarkan narasi dan alignment.

    Batas efek per adegan dan jarak minimum antar-efek menjadi pengendali
    kepadatan. Nilai batas lebih dari satu didukung, tetapi efek yang sama tidak
    digandakan dalam adegan yang sama. Jenis shot hanya memengaruhi prioritas,
    bukan menjadi alasan tunggal untuk menambahkan bunyi. Efek latar panjang tidak
    dibuat otomatis karena memerlukan keputusan durasi/penyutradaraan. Katalog
    aktual wajib diberikan agar fungsi tidak menunjuk berkas yang belum ada.
    """
    katalog = {
        Path(str(nama)).name.lower()
        for nama in katalog_suara
        if str(nama).lower().endswith(".mp3")
    }
    rekaman: list[dict[str, Any]] = []
    anotasi: list[dict[str, Any]] = []
    butuh_efek_baru: list[dict[str, Any]] = []
    peta_kata = _buat_peta_kata(adegan, kata_tts_global)
    waktu_terakhir = float("-inf")
    waktu_terpilih: list[float] = []
    waktu_manual: list[float] = []
    for rekaman_lama in rekaman_ada or ():
        at_lama = rekaman_lama.get("at")
        try:
            if isinstance(at_lama, (int, float)):
                waktu_manual.append(float(at_lama))
            elif isinstance(at_lama, str) and not at_lama.startswith("@"):
                waktu_manual.append(float(at_lama))
        except (TypeError, ValueError):
            pass

    for nomor, bagian in enumerate(adegan):
        teks = str(bagian.get("teks") or "")
        kata = _kata_adegan(bagian)
        if not teks.strip():
            continue
        if not kata:
            anotasi.append({
                "adegan": nomor,
                "efek": None,
                "status": "perlu_tinjau",
                "alasan": "Adegan belum memiliki alignment kata TTS; efek otomatis tidak ditempatkan dengan waktu tebakan.",
            })
            continue

        posisi = _posisi_adegan(bagian)
        kandidat: list[tuple[int, int, str, str, str]] = []
        # Konteks shot hanya mengubah prioritas tipis; tidak menciptakan efek
        # tanpa pemicu narasi yang nyata.
        bonus_shot = {
            "hook": 3, "pembuka": 2, "klimaks": 5, "puncak": 5,
            "penutup": -2, "isi": 0, "establishing": -2,
        }.get(posisi, 0)
        for aturan in ATURAN_EFEK:
            if aturan.get("khusus") == "transisi":
                transisi = bool(bagian.get("transisi")) or posisi in {
                    "transisi", "peralihan", "transition"
                }
                if transisi and nomor > 0:
                    kandidat.append((aturan["prioritas"], 0, aturan["efek"],
                                     aturan["alasan"], kata[0]["teks"]))
                continue
            for pemicu in aturan["pemicu"]:
                if not _cocok_frasa(teks, pemicu):
                    continue
                indeks = _indeks_kata_pemicu(kata, pemicu)
                if indeks is None:
                    continue
                kandidat.append((aturan["prioritas"] + bonus_shot, indeks, aturan["efek"],
                                 f'{aturan["alasan"]} Pemicu: "{pemicu}".',
                                 kata[indeks]["teks"]))

        # Momen klimaks hanya memperkuat kejadian yang sudah jelas; tidak otomatis
        # menambahkan braam ke semua adegan yang diberi label klimaks.
        if posisi in {"klimaks", "puncak"} and re.search(
            r"\b(terkejut|kehancuran|mengguncang|mengerikan|tak terbayangkan)\b",
            _normalisasi(teks),
        ):
            idx = _indeks_kata_pemicu(kata, "kehancuran")
            if idx is None:
                idx = next((i for i, k in enumerate(kata)
                            if _normalisasi(k["teks"]) in {"terkejut", "mengerikan"}), None)
            if idx is not None:
                kandidat.append((71, idx, "braam",
                                 "Label klimaks didukung peristiwa kuat dalam narasi; braam dipakai sebagai aksen tunggal.",
                                 kata[idx]["teks"]))

        # Catat kebutuhan efek baru hanya untuk kejadian audio spesifik yang tidak
        # mempunyai aturan/padanan tersedia. Bukan setiap istilah dalam naskah.
        for pemicu, deskripsi in KEJADIAN_TANPA_PADANAN:
            if _cocok_frasa(teks, pemicu):
                butuh_efek_baru.append({
                    "adegan": nomor,
                    "pemicu": pemicu,
                    "deskripsi": deskripsi,
                    "alasan": "Katalog aturan saat ini tidak memiliki padanan yang cukup tepat; perlu keputusan manusia.",
                })

        # Urutkan kandidat dengan prioritas konteks, lalu waktu. Efek yang sama
        # tidak boleh ditambahkan dua kali pada satu adegan.
        kandidat.sort(key=lambda x: (-x[0], x[1], x[2]))
        jumlah_dipilih = 0
        efek_di_adegan: set[str] = set()
        if batas_per_adegan <= 0:
            continue
        for prioritas, indeks, nama_efek, alasan, kata_pemicu in kandidat:
            if jumlah_dipilih >= batas_per_adegan:
                break
            if nama_efek in efek_di_adegan:
                continue
            nama_file = f"{nama_efek}.mp3"
            if nama_file.lower() not in katalog:
                butuh_efek_baru.append({
                    "adegan": nomor,
                    "pemicu": kata_pemicu,
                    "deskripsi": f"Efek {nama_efek} untuk peristiwa: {alasan}",
                    "alasan": f"Berkas {nama_file} tidak ditemukan dalam katalog aset aktual.",
                })
                continue

            waktu = float(kata[indeks]["t0"])
            if waktu - waktu_terakhir < max(0.0, jarak_minimum):
                anotasi.append({
                    "adegan": nomor,
                    "efek": nama_efek,
                    "status": "dilewati",
                    "pemicu": kata_pemicu,
                    "alasan": "Dilewati oleh pengendali kepadatan: terlalu dekat dengan efek sebelumnya.",
                })
                efek_di_adegan.add(nama_efek)
                continue
            if any(abs(waktu - t) < max(0.0, jarak_minimum) for t in waktu_manual):
                anotasi.append({
                    "adegan": nomor,
                    "efek": nama_efek,
                    "status": "konflik_manual",
                    "pemicu": kata_pemicu,
                    "alasan": "Penempatan terlalu dekat dengan rekaman manual yang sudah ada.",
                })
                efek_di_adegan.add(nama_efek)
                continue
            if batas_per_menit > 0 and sum(1 for t in waktu_terpilih if waktu - 60 < t <= waktu) >= batas_per_menit:
                anotasi.append({
                    "adegan": nomor,
                    "efek": nama_efek,
                    "status": "dilewati",
                    "pemicu": kata_pemicu,
                    "alasan": "Batas kepadatan enam puluh detik tercapai; efek tidak ditambahkan.",
                })
                efek_di_adegan.add(nama_efek)
                continue

            token_at = peta_kata.get((nomor, indeks))
            at: str | float = token_at if token_at else round(waktu, 2)
            rekaman.append({
                "berkas": f"{awalan_berkas.rstrip('/')}/{nama_efek}.mp3",
                "at": at,
                "vol": 0.6,
                "gain_db": 0,
                "ulang": False,
                "sampai": None,
                "masuk": 0.3,
                "keluar": 0.8,
            })
            anotasi.append({
                "adegan": nomor,
                "efek": nama_efek,
                "pemicu": kata_pemicu,
                "at": at,
                "prioritas": prioritas,
                "alasan": alasan,
                "konteks_shot": posisi or "tidak_diketahui",
            })
            efek_di_adegan.add(nama_efek)
            jumlah_dipilih += 1
            waktu_terakhir = waktu
            waktu_terpilih.append(waktu)

    return {
        "rekaman": rekaman,
        "anotasi": anotasi,
        "butuh_efek_baru": butuh_efek_baru,
    }


def rancang_efek_suara(
    adegan: Sequence[Mapping[str, Any]],
    kata_tts: Sequence[Mapping[str, Any]],
    katalog_suara: Iterable[str],
    **opsi: Any,
) -> dict[str, Any]:
    """Jalur satu-panggilan: selaraskan teks adegan ke timing TTS lalu pilih efek."""
    adegan_berwaktu, peringatan = selaraskan_adegan_dengan_tts(adegan, kata_tts)
    opsi.setdefault("kata_tts_global", kata_tts)
    hasil = pilih_efek_suara(adegan_berwaktu, katalog_suara, **opsi)
    hasil["peringatan_alignment"] = peringatan
    return hasil


def terapkan_ke_spesifikasi_dari_tts(
    spesifikasi: Mapping[str, Any],
    adegan: Sequence[Mapping[str, Any]],
    kata_tts: Sequence[Mapping[str, Any]],
    katalog_suara: Iterable[str],
    **opsi: Any,
) -> dict[str, Any]:
    """Buat salinan spesifikasi Papan dari teks adegan dan alignment narasi_api."""
    hasil = dict(spesifikasi)
    opsi.setdefault("rekaman_ada", spesifikasi.get("rekaman") or [])
    rancangan = rancang_efek_suara(adegan, kata_tts, katalog_suara, **opsi)
    hasil["rekaman"] = list(spesifikasi.get("rekaman") or []) + rancangan["rekaman"]
    hasil["anotasi_efek_suara"] = rancangan["anotasi"]
    hasil["butuh_efek_baru"] = rancangan["butuh_efek_baru"]
    hasil["peringatan_alignment_efek"] = rancangan["peringatan_alignment"]
    return hasil


def terapkan_ke_spesifikasi(
    spesifikasi: Mapping[str, Any],
    adegan: Sequence[Mapping[str, Any]],
    katalog_suara: Iterable[str],
    **opsi: Any,
) -> dict[str, Any]:
    """Kembalikan salinan spek dengan rekaman terpilih; input tidak dimutasi.

    Rekaman manual yang sudah ada dipertahankan di depan hasil otomatis. Ini
    mencegah modul menghapus keputusan penyutradaraan yang telah dibuat manusia.
    """
    hasil = dict(spesifikasi)
    opsi.setdefault("rekaman_ada", spesifikasi.get("rekaman") or [])
    rancangan = pilih_efek_suara(adegan, katalog_suara, **opsi)
    hasil["rekaman"] = list(spesifikasi.get("rekaman") or []) + rancangan["rekaman"]
    hasil["anotasi_efek_suara"] = rancangan["anotasi"]
    hasil["butuh_efek_baru"] = rancangan["butuh_efek_baru"]
    return hasil


def _uji_contoh() -> None:
    """Uji mandiri dengan alignment palsu; tidak membaca aset, memanggil API, atau merender."""
    adegan = [
        {
            "teks": "Tiba-tiba bumi retak dan tanah terbelah.",
            "jenis_shot": "hook",
            "kata": [
                {"teks": "Tiba-tiba", "t0": 0.0, "t1": 0.4},
                {"teks": "bumi", "t0": 0.5, "t1": 0.8},
                {"teks": "retak", "t0": 0.9, "t1": 1.2},
                {"teks": "dan", "t0": 1.3, "t1": 1.4},
                {"teks": "tanah", "t0": 1.5, "t1": 1.8},
                {"teks": "terbelah.", "t0": 1.9, "t1": 2.4},
            ],
        },
        {
            "teks": "Manusia berjalan perlahan menuju pintu.",
            "jenis_shot": "isi",
            "kata": [
                {"teks": "Manusia", "t0": 7.0, "t1": 7.4},
                {"teks": "berjalan", "t0": 7.5, "t1": 7.9},
                {"teks": "perlahan", "t0": 8.0, "t1": 8.4},
                {"teks": "menuju", "t0": 8.5, "t1": 8.8},
                {"teks": "pintu.", "t0": 8.9, "t1": 9.2},
            ],
        },
        {
            "teks": "Kemudian kisah berlanjut tanpa peristiwa bunyi khusus.",
            "jenis_shot": "penutup",
            "kata": [
                {"teks": "Kemudian", "t0": 14.0, "t1": 14.4},
                {"teks": "kisah", "t0": 14.5, "t1": 14.8},
                {"teks": "berlanjut", "t0": 14.9, "t1": 15.4},
                {"teks": "tanpa", "t0": 15.5, "t1": 15.7},
                {"teks": "peristiwa", "t0": 15.8, "t1": 16.2},
                {"teks": "bunyi", "t0": 16.3, "t1": 16.6},
                {"teks": "khusus.", "t0": 16.7, "t1": 17.1},
            ],
        },
    ]
    hasil = pilih_efek_suara(
        adegan,
        ["tanah_retak.mp3", "hentak_serius.mp3", "langkah_pelan.mp3"],
    )
    assert len(hasil["rekaman"]) == 2, hasil
    assert hasil["rekaman"][0]["berkas"].endswith("/tanah_retak.mp3"), hasil
    assert hasil["rekaman"][0]["at"] == "@retak", hasil
    assert hasil["rekaman"][1]["berkas"].endswith("/langkah_pelan.mp3"), hasil
    assert hasil["rekaman"][1]["at"] == "@berjalan", hasil
    assert hasil["rekaman"][0]["vol"] == 0.6
    assert hasil["butuh_efek_baru"] == [], hasil

    # Penyelarasan adegan memakai waktu kata TTS asli dan melaporkan kata yang hilang.
    adegan_terpasang, peringatan = selaraskan_adegan_dengan_tts(
        [{"teks": "Pintu besi ditutup keras."}],
        [
            {"teks": "Pintu", "t0": 1.0, "t1": 1.2},
            {"teks": "besi", "t0": 1.3, "t1": 1.5},
            {"teks": "ditutup", "t0": 1.6, "t1": 1.9},
            {"teks": "keras.", "t0": 2.0, "t1": 2.3},
        ],
    )
    assert len(adegan_terpasang[0]["kata"]) == 4, adegan_terpasang
    assert adegan_terpasang[0]["kata"][0]["t0"] == 1.0
    assert peringatan == [], peringatan
    assert adegan_terpasang[0]["kata"][0]["_indeks_global"] == 0

    # API satu-panggilan memakai alignment TTS dan menghasilkan anchor yang dapat
    # langsung diproses pasang_waktu() di papan_buat.py.
    rancangan_tts = rancang_efek_suara(
        [{"teks": "Pintu besi ditutup keras."}],
        [
            {"teks": "Pintu", "t0": 20.0, "t1": 20.2},
            {"teks": "besi", "t0": 20.3, "t1": 20.5},
            {"teks": "ditutup", "t0": 20.6, "t1": 20.9},
            {"teks": "keras.", "t0": 21.0, "t1": 21.3},
        ],
        ["pintu_besi.mp3"],
    )
    assert len(rancangan_tts["rekaman"]) == 1, rancangan_tts
    assert rancangan_tts["rekaman"][0]["at"] == "@pintu", rancangan_tts
    assert rancangan_tts["peringatan_alignment"] == [], rancangan_tts

    # Rekaman manual dekat waktu kandidat mencegah tumpang tindih otomatis.
    konflik = pilih_efek_suara(
        adegan[1:2], ["langkah_pelan.mp3"],
        rekaman_ada=[{"berkas": "manual.mp3", "at": 7.6}],
    )
    assert konflik["rekaman"] == [], konflik
    assert any(a.get("status") == "konflik_manual" for a in konflik["anotasi"]), konflik

    # Anchor kata berulang harus mengikuti nomor kemunculan di seluruh audio TTS,
    # meskipun sebagian narasi tidak dimasukkan sebagai adegan visual.
    cuplikan, _ = selaraskan_adegan_dengan_tts(
        [{"teks": "bumi retak"}],
        [
            {"teks": "di", "t0": 0}, {"teks": "bumi", "t0": 1},
            {"teks": "yang", "t0": 2}, {"teks": "lain", "t0": 3},
            {"teks": "bumi", "t0": 4}, {"teks": "retak", "t0": 5},
        ],
    )
    peta_global = _buat_peta_kata(cuplikan, [
        {"teks": "di"}, {"teks": "bumi"}, {"teks": "yang"},
        {"teks": "lain"}, {"teks": "bumi"}, {"teks": "retak"},
    ])
    assert peta_global[(0, 0)] == "@bumi#1", peta_global

    # Frasa majemuk wajib cocok utuh pada alignment, bukan sekadar kata pertama.
    assert _indeks_kata_pemicu(
        [{"teks": "bumi", "t0": 0}, {"teks": "diam", "t0": 1}],
        "bumi berguncang",
    ) is None
    assert _indeks_kata_pemicu(
        [{"teks": "bumi", "t0": 0}, {"teks": "berguncang", "t0": 1}],
        "bumi berguncang",
    ) == 0

    # Batas multi-efek berfungsi dan tidak menggandakan nama efek.
    adegan_multi = [{
        "teks": "Ponsel bergetar lalu telepon berdering.",
        "kata": [
            {"teks": "Ponsel", "t0": 30}, {"teks": "bergetar", "t0": 31},
            {"teks": "lalu", "t0": 32}, {"teks": "telepon", "t0": 33},
            {"teks": "berdering.", "t0": 34},
        ],
    }]
    multi = pilih_efek_suara(
        adegan_multi, ["getar_hp.mp3", "hp_dering.mp3"],
        batas_per_adegan=2, jarak_minimum=0,
    )
    assert len(multi["rekaman"]) == 2, multi
    assert {x["berkas"].rsplit("/", 1)[-1] for x in multi["rekaman"]} == {
        "getar_hp.mp3", "hp_dering.mp3"
    }, multi

    # Spesifikasi asli tidak dimutasi dan rekaman manual tetap dipertahankan.
    awal = {"rekaman": [{"berkas": "manual.mp3", "at": 2}]}
    terapan = terapkan_ke_spesifikasi(
        awal, adegan[1:2], ["langkah_pelan.mp3"]
    )
    assert len(awal["rekaman"]) == 1
    assert terapan["rekaman"][0]["berkas"] == "manual.mp3"
    assert len(terapan["rekaman"]) == 2
    print("Uji contoh berhasil: frasa utuh, kepadatan, multi-efek, dan preservasi manual.")


if __name__ == "__main__":
    _uji_contoh()
