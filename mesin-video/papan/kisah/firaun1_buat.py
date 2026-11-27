"""Papan manual "Tobat yang Terlambat Beberapa Detik" (Firaun dan laut terbelah), ditulis tangan tanpa LLM.

    python mesin-video/papan/kisah/firaun1_buat.py   # menulis firaun1.json di folder ini

Naskah disetujui pemilik 27 Nov 2026. Konsistensi tokoh (keputusan pemilik):
- pengikut Nabi Musa = selalu siluet bertepi cahaya krem; pasukan Firaun = selalu siluet bertepi merah + tombak;
- Firaun = satu-satunya tokoh berwajah (nemes, janggut upacara, jubah + bisht, kalung usekh);
- Nabi Musa = cahaya nur bernama (tidak pernah digambar).
Satu lokasi pantai yang sama dari awal sampai akhir, waktu pagi (QS 26:60 "musyriqin"), menggelap hanya saat azab.
Kedalaman: langit -> matahari di garis laut -> laut/dinding air -> rombongan (baris belakang lebih kecil/gelap)
-> tokoh depan; cahaya dari matahari di kanan (sisi tepi cahaya siluet = 1).
"""
import json
import sys
from pathlib import Path

AKAR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(AKAR))
from newmotion.paket_genre.kisah_islami.kartu_dalil import buat_kartu  # noqa: E402

H = 880                      # garis laut terjauh = cakrawala (tidak ada daratan di belakang laut)
LT = {"jenis": "laut_terbelah", "x": 540, "y": 1450, "s": 1, "warna": ["#5bb4dc", "#3f8ac9", "#245f9a"]}
SURYA = {"jenis": "surya", "x": 790, "y": H - 40, "r": 115, "terang": 1, "belakang": True}
SINAR = {"jenis": "cahaya", "x": 790, "y": 200, "s": 1.1, "belakang": True}  # berkas cahaya pagi dari arah matahari
KREM, MERAH = "#ffe6b0", "#ff5a3a"
FIRAUN = {"penutup_kepala": "nemes", "janggut": True, "janggut_model": "firaun", "jenis_kelamin": "pria",
          "pakaian": {"jenis": "jubah", "warna": "#f4ecd8", "bisht": "#3a2a1e", "kalung": "usekh"}}
PAGI = {"palet": "pantai_pagi", "malam": 0, "langit": 0.5, "horizon": H, "tanah": "pasir"}

NASKAH = json.loads((AKAR / "antrean/261127-1134-buatkan-saya-naskah-tentang/naskah.json").read_text(encoding="utf-8"))
DALIL = {d["id"]: d for d in NASKAH["dalil"]}


def laut(**k):
    return dict(LT, **k)


def bani_israil(**k):
    return dict({"jenis": "kerumunan", "x": 860, "y": 1640, "n": 16, "w": 360, "k": 0.55, "baris": 3,
                 "rim": 0.9, "rimwarna": KREM, "sisi": 1, "seed": 11}, **k)


def pasukan(**k):
    return dict({"jenis": "kerumunan", "y": 1590, "n": 22, "w": 420, "k": 0.45, "baris": 3, "rim": 0.8,
                 "rimwarna": MERAH, "sisi": 1, "tombak": True, "seed": 23}, **k)


def nur(**k):
    return dict({"jenis": "nur", "x": 720, "y": 1660, "s": 0.55, "nama": "Nabi Musa a.s.", "nama_letak": "atas"}, **k)


def teks(t, sub=None, at=0.3, **k):
    o = {"at": at, "teks": t, "y": 330, "ukuran": 92 if max(len(x) for x in t.split("\n")) <= 14 else 72}
    if sub:
        o["sub"] = sub
    o.update(k)
    return o


def kartu_layar(dalil: dict, kam: dict, at: str, layar_y: float = 660, layar_s: float = 0.95) -> dict:
    """Kartu tembus pandang yang tetap di layar (kamera shot ini diam)."""
    k = buat_kartu(dalil, at=0)
    z = kam["z"]
    k.update(x=kam["x"], y=round(kam["y"] + (layar_y - 960) / z, 1), s=round(layar_s / z, 3), at=at)
    return k


def kartu_quran(id_):
    d = DALIL[id_]
    surah, ayat = d["surah"], d["ayat"]
    return {"kitab": f"QS {surah}:{ayat}", "teks": d["terjemah"], "arab": d["teks_ar"], "label": "QUR'AN"}


shot = []
# 1. Hook: detik terakhir (badai, gelap) -- digambar di awal, diulang di beat 8
shot.append({
    "narasi": "Firaun sempat menyatakan beriman. Tapi imannya ditolak, karena diucapkan saat air sudah menenggelamkannya.",
    "intonasi": "berat", "jeda": 0.5,
    "palet": "pantai_badai", "malam": 0.3, "langit": 0.2, "horizon": 1150, "hujan": 0.7,
    "kamera": {"z": [1.3, 1.45], "x": 540, "y": [1260, 1300]},
    "benda": [{"jenis": "awan_badai", "x": 540, "y": 420, "gelap": 1, "hujan": 0.6},
              {"jenis": "ombak", "x": 540, "y": 1150, "tinggi": 180, "lapis": 2, "seed": 3},
              {"jenis": "ombak", "x": 540, "y": [[0, 1640], ["@ditolak", 1500], ["@menenggelamkannya", 1340]],
               "tinggi": 110, "lapis": 3, "seed": 9, "jarak": 90, "depan": True}],
    "boneka": [dict(FIRAUN, x=540, y=1600, s=1.0, utama=True, pose="dua_naik", wajah="takut", mata="atas")],
    "teks": [teks("TERLAMBAT\nBEBERAPA DETIK", "QS YUNUS 90-91", warna="#ffd27a")],
})
# 2. Pagi, tersusul di tepi laut
shot.append({
    "narasi": "Pagi itu, saat matahari terbit, Firaun dan bala tentaranya menyusul Nabi Musa sampai ke tepi laut.",
    "intonasi": "tegang", **PAGI, "debu": 30,
    "kamera": {"z": [1.25, 1.0], "x": 540, "y": [1250, 1060]},
    "benda": [SURYA, SINAR, laut(belah=0), bani_israil(), nur(), pasukan(x=[[0, -330], ["@tepi", -170]])],
    "teks": [teks("MENYUSUL SAAT\nMATAHARI TERBIT", "QS ASY-SYU'ARA 60", at="@terbit")],
})
# 3. Terkepung
shot.append({
    "narasi": "Di depan, laut. Di belakang, pasukan. Pengikut Musa berseru: kita pasti tersusul!",
    "intonasi": "tegang", **PAGI, "debu": 45,
    "kamera": {"z": [1.0, 1.1], "x": [470, 650], "y": 1060},
    "benda": [SURYA, laut(belah=0), bani_israil(pose="angkat"), nur(), pasukan(x=[[0, -170], ["@tersusul", -40]])],
    "teks": [teks("TERKEPUNG", "QS ASY-SYU'ARA 61", at="@berseru")],
})
# 4. Jawaban Nabi Musa (kartu dalil, kamera diam agar kartu tetap di layar)
k4 = {"z": 1.2, "x": 700, "y": 1250}
shot.append({
    "narasi": "Nabi Musa menjawab: sekali-kali tidak. Tuhanku bersamaku, Dia akan memberiku petunjuk.",
    "intonasi": "tegas", **PAGI, "debu": 20, "jeda": 1.2,
    "kamera": k4,
    "benda": [SURYA, laut(belah=0), bani_israil(), nur(nama=""), pasukan(x=-40),
              dict(kartu_layar(kartu_quran("syuara62"), k4, "@menjawab"), tulis=2.6, sorot="Tuhanku bersamaku")],
})
# 5. Laut terbelah (klimaks pertama)
shot.append({
    "narasi": "Musa diperintahkan memukul laut dengan tongkatnya. Laut terbelah, setiap belahannya seperti gunung yang besar.",
    "intonasi": "tegas", "jeda": 0.6, **PAGI, "debu": 20,
    "kamera": {"z": [1.2, 0.92], "x": [700, 540], "y": [1250, 1000], "guncang": [["@terbelah", 30]]},
    "benda": [SURYA, laut(belah=[["@memukul", 0], ["@gunung", 1]]), bani_israil(), nur(x=[[0, 720], ["@gunung", 560]]),
              pasukan(x=-40)],
    "teks": [teks("LAUT TERBELAH", "QS ASY-SYU'ARA 63", at="@gunung")],
})
# 6. Jalan kering, Bani Israil menyeberang
shot.append({
    "narasi": "Di antara dua dinding air terbentang jalan yang kering. Bani Israil menyeberang, semuanya selamat.",
    "intonasi": "tenang", **PAGI, "debu": 15,
    "kamera": {"z": [0.92, 1.0], "x": 540, "y": 1000},
    "benda": [SURYA, laut(belah=1),
              {"jenis": "arus", "mode": "lorong", "x": 540, "y": 1450, "s": 1, "n": 26, "rim": 0.8, "rimwarna": KREM,
               "maju": [[0, 0.05], ["@selamat", 0.95]], "seed": 11},
              nur(x=560, y=[[0, 1600], ["@selamat", 1180]], s=[[0, 0.55], ["@selamat", 0.28]]), pasukan(x=-20)],
    "teks": [teks("JALAN YANG KERING", "QS THAHA 77", at="@kering")],
})
# 7. Firaun masuk (wajahnya pertama kali tampak jelas)
shot.append({
    "narasi": "Firaun tidak berhenti. Ia dan pasukannya masuk ke jalan yang sama.",
    "intonasi": "tegang", **PAGI, "debu": 25,
    "kamera": {"z": [1.0, 1.12], "x": [560, 600], "y": [1000, 1080]},
    "benda": [SURYA, laut(belah=1),
              {"jenis": "arus", "mode": "lorong", "x": 540, "y": 1450, "s": 1, "n": 24, "rim": 0.8, "rimwarna": MERAH,
               "tombak": True, "maju": [["@masuk", 0.0], ["@sama", 0.55]], "seed": 23}],
    "boneka": [dict(FIRAUN, x=[[0, 700], ["@sama", 590]], y=[[0, 1700], ["@sama", 1560]], s=[[0, 0.85], ["@sama", 0.7]],
                    profil="kiri", pose="jalan", wajah="marah")],
    "teks": [teks("IA TIDAK BERHENTI", at="@berhenti")],
})
# 8. Laut menutup (langit menggelap) -- kembali ke detik pembuka
tutup = [[0, 1], ["@menutup", 0.92], ["@berkata", 0.3], ["@Israil#2", 0.05]]
shot.append({
    "narasi": "Lalu laut menutup. Saat air menenggelamkannya, Firaun berkata: aku percaya tidak ada tuhan selain yang dipercayai Bani Israil.",
    "intonasi": "berat", "jeda": 0.8,
    "palet": "pantai_badai", "malam": 0.2, "langit": 0.25, "horizon": H, "tanah": "pasir", "hujan": 0.5,
    "kamera": {"z": [1.15, 1.5], "x": 560, "y": [1150, 1300], "guncang": [["@menutup", 26]]},
    "benda": [{"jenis": "awan_gelap", "x": 540, "y": 380, "kilat": 0.8}, laut(belah=tutup, warna=None),
              {"jenis": "arus", "mode": "lorong", "x": 540, "y": 1450, "s": 1, "n": 24, "rim": 0.6, "rimwarna": MERAH,
               "tombak": True, "maju": 0.4, "seed": 23},
              laut(belah=tutup, warna=None, lapis="tutup", depan=True)],
    "boneka": [dict(FIRAUN, x=560, y=1490, s=0.85, pose="dua_naik", wajah="takut", mata="atas")],
    "teks": [teks("SUDAH TERLAMBAT", "QS YUNUS 90", at="@berkata", warna="#ffd27a")],
})
# 9. Jawaban: apakah baru sekarang? (hening)
shot.append({
    "narasi": "Jawabannya: apakah baru sekarang? Padahal sebelumnya engkau durhaka.",
    "intonasi": "bisik", "jeda": 1.2,
    "palet": "pantai_badai", "malam": 0.1, "langit": 0.35, "horizon": H, "tanah": "pasir",
    "kamera": {"z": [1.0, 0.96], "x": 540, "y": 1000},
    "benda": [laut(belah=0, warna=["#4a7fa8", "#2c5a82", "#163a5c"])],
    "teks": [teks("APAKAH BARU\nSEKARANG?", "QS YUNUS 91", at="@sekarang")],
})
# 10. Pengetahuan: batas tobat (kartu hadis), langit cerah kembali
k10 = {"z": 1.0, "x": 540, "y": 1000}
shot.append({
    "narasi": "Rasulullah shallallahu 'alaihi wa sallam bersabda: Allah menerima tobat seorang hamba selama nyawanya belum sampai di kerongkongan.",
    "intonasi": "tenang", **PAGI, "jeda": 1.0,
    "kamera": k10,
    "benda": [SURYA, laut(belah=0), {"jenis": "cahaya", "x": 790, "y": 300, "s": 1.2, "belakang": True},
              kartu_layar({"kitab": "HR. Tirmidzi", "no": "3537", "label": "HADIS",
                           "teks": "Sesungguhnya Allah menerima tobat seorang hamba selama nyawanya belum sampai di kerongkongan.",
                           "arab": "إِنَّ اللَّهَ يَقْبَلُ تَوْبَةَ الْعَبْدِ مَا لَمْ يُغَرْغِرْ"}, k10, "@bersabda", layar_y=700) | {"tulis": 3.0, "sorot": "belum sampai di kerongkongan"}],
})
# 11. Badan Firaun diselamatkan (pantai siang)
shot.append({
    "narasi": "Dan badan Firaun diselamatkan, agar menjadi tanda bagi orang-orang sesudahnya.",
    "intonasi": "haru", "palet": "pantai_siang", "malam": 0, "langit": 0.6, "horizon": H, "tanah": "pasir",
    "kamera": {"z": [1.05, 1.15], "x": 540, "y": [1150, 1250]},
    "benda": [dict(SURYA, y=560, r=95), {"jenis": "pantai", "x": 540, "y": 1380, "tinggi": 500,
                                         "warna": ["#3f8ac9", "#6ac9d9"]}],
    "boneka": [dict(FIRAUN, x=540, y=1560, s=0.9, pose="rebahan", mata="tutup")],
    "teks": [teks("MENJADI TANDA", "QS YUNUS 92", at="@tanda")],
})
# 12. Pengetahuan: puasa Asyura
shot.append({
    "narasi": "Hari itu Allah menyelamatkan Musa dan menenggelamkan Firaun. Karena itu Rasulullah shallallahu 'alaihi wa sallam berpuasa di hari Asyura, dan menyuruh umatnya berpuasa.",
    "intonasi": "tenang", "palet": "pantai_siang", "malam": 0, "langit": 0.6, "horizon": H, "tanah": "pasir",
    "kamera": {"z": [1.15, 1.0], "x": 540, "y": [1250, 1000]},
    "benda": [dict(SURYA, y=560, r=95), {"jenis": "pantai", "x": 540, "y": 1380, "tinggi": 500,
                                         "warna": ["#3f8ac9", "#6ac9d9"]},
              {"jenis": "kalender", "x": 540, "y": 1120, "s": 0.85, "at": "@Asyura", "bulan": "MUHARRAM", "tgl": 10,
               "mulai": 2, "lingkar": [["@Asyura", 0], ["@menyuruh", 1]], "teks": "ASYURA"}],
    "teks": [teks("PUASA ASYURA", "HR BUKHARI 3397", at="@Asyura")],
})
# 13. Penutup: jalan keluar
shot.append({
    "narasi": "Kamu masih bernapas. Pintu tobatmu masih terbuka. Jangan tunggu air sampai ke leher.",
    "intonasi": "lega", **PAGI,
    "kamera": {"z": [1.0, 1.08], "x": 540, "y": 1000},
    "benda": [SURYA, laut(belah=0), {"jenis": "cahaya", "x": 790, "y": 300, "s": 1.3, "belakang": True}],
    "teks": [teks("PINTU TOBAT\nMASIH TERBUKA", at="@terbuka", warna="#ffd27a")],
})

for s in shot:  # warna=None = pakai warna gelap bawaan (badai)
    for b in s.get("benda", []):
        if b.get("warna", 1) is None:
            b.pop("warna")

spek = {
    "latar": "gelap", "stempel": True, "musik": False, "dekor": False, "volume_efek": 0,
    "cerita": {"suku": "arab", "kilat": False, "label": "KISAH FIRAUN", "shot": shot},
    "rekaman": [
        {"berkas": "../../aset/suara/guntur_hujan.mp3", "at": 0, "sampai": "@Pagi", "vol": 0.45, "ulang": True},
        {"berkas": "../../aset/suara/braam.mp3", "at": "@ditolak", "vol": 0.5},
        {"berkas": "../../aset/suara/whoosh.mp3", "at": "@Pagi-0.4", "vol": 0.5},
        {"berkas": "../../aset/suara/angin_gurun.mp3", "at": "@Pagi", "sampai": "@menutup", "vol": 0.25, "ulang": True},
        {"berkas": "../../aset/suara/langkah_lari.mp3", "at": "@bala", "sampai": "@Musa#2", "vol": 0.35, "ulang": True},
        {"berkas": "../../aset/suara/kerumunan_cemas.mp3", "at": "@depan", "sampai": "@Tuhanku", "vol": 0.35, "ulang": True},
        {"berkas": "../../aset/suara/detak_jantung.mp3", "at": "@belakang", "sampai": "@Tuhanku", "vol": 0.45, "ulang": True},
        {"berkas": "../../aset/suara/whoosh.mp3", "at": "@memukul", "vol": 0.6},
        {"berkas": "../../aset/suara/dentum_jauh.mp3", "at": "@terbelah", "vol": 0.7},
        {"berkas": "../../aset/suara/air_mengalir.mp3", "at": "@kering", "sampai": "@menutup", "vol": 0.3, "ulang": True},
        {"berkas": "../../aset/suara/langkah_pelan.mp3", "at": "@menyeberang", "sampai": "@selamat", "vol": 0.3, "ulang": True},
        {"berkas": "../../aset/suara/drone_gelap.mp3", "at": "@berhenti", "sampai": "@Jawabannya", "vol": 0.35, "ulang": True},
        {"berkas": "../../aset/suara/guntur_hujan.mp3", "at": "@menutup", "sampai": "@Jawabannya", "vol": 0.5, "ulang": True},
        {"berkas": "../../aset/suara/tanah_retak.mp3", "at": "@menutup", "vol": 0.6},
        {"berkas": "../../aset/suara/braam.mp3", "at": "@berkata", "vol": 0.45},
        {"berkas": "../../aset/suara/senandung_haru.mp3", "at": "@bersabda", "vol": 0.25, "ulang": True},
        {"berkas": "../../aset/suara/kilau_cahaya.mp3", "at": "@terbuka", "vol": 0.4},
    ],
}
(Path(__file__).with_name("firaun1.json")).write_text(json.dumps(spek, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print("firaun1.json:", len(shot), "shot")
