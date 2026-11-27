"""Papan manual "Tiga yang Mengantarmu ke Kubur" (HR Bukhari 6514, Muslim 2960), ditulis tangan tanpa LLM.

Visual: keranda diusung ke pemakaman, pengantar berangsur pulang (sedih), yang tinggal hanya amal, divisualkan melalui simbol ibadah dan zikir.
Pengusung dan pengantar laki-laki (sunnah: perempuan tidak mengiringi jenazah ke kubur). Waktu: siang (tanpa dalil
tentang waktu; bawaan siang). Kartu dalil masuk gaya NGOPAI (jatuh + whoosh + stempel otomatis).
Jalankan: python mesin-video/papan/kisah/pengantar1_buat.py  -> pengantar1.json
"""
import json
import sys
from pathlib import Path

AKAR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(AKAR))
from newmotion.paket_genre.kisah_islami.kartu_dalil import buat_kartu  # noqa: E402

H = 1150
SIANG = {"palet": "pantai_siang", "malam": 0, "langit": 0.6, "horizon": H, "tanah": "pasir"}
HIJAU = "#1f6b3a"
ARAB = "يَتْبَعُهُ أَهْلُهُ وَمَالُهُ وَعَمَلُهُ، فَيَرْجِعُ أَهْلُهُ وَمَالُهُ، وَيَبْقَى عَمَلُهُ"  # potongan matan HR Bukhari 6514


def org(npc, x, y, s=0.9, profil="kanan", **k):
    """Laki-laki berjubah (suku arab), wajah sedih."""
    return dict({"npc": npc, "jenis_kelamin": "pria", "x": x, "y": y, "s": s, "profil": profil, "pose": "jalan",
                 "wajah": "sedih", "mata": "bawah"}, **k)


def teks(t, sub=None, at=0.2, **k):
    o = {"at": at, "teks": t, "y": 330, "ukuran": 84 if max(len(x) for x in t.split("\n")) <= 12 else 68}
    if sub:
        o["sub"] = sub
    o.update(k)
    return o


def iring(t0=0.0, dx=900, dur=9.0):
    """Keranda + 4 pengusung + 4 pengantar berjalan ke kanan (posisi menyambung antar-shot lewat t0)."""
    def gerak(x0):
        return [[0, x0 + dx * t0 / dur], [dur - t0, x0 + dx]]

    pikul = [org(3, gerak(140), 1500, 0.82), org(5, gerak(400), 1500, 0.82),
             org(8, gerak(110), 1580, 0.92), org(12, gerak(370), 1580, 0.92)]
    ikut = [org(20 + i, gerak(-260 - i * 95), 1560 + (i % 2) * 40, 0.85 + (i % 2) * 0.05) for i in range(4)]
    keranda = {"jenis": "jenazah", "x": gerak(270), "y": 1075, "s": 0.8, "kain": HIJAU, "dipikul": True, "ayun": 2.2}
    return [keranda], ikut + pikul


shot = []
# 1. Hook: iring-iringan jenazah
b, o = iring(0)
shot.append({
    "narasi": "Saat kamu dikubur, tiga hal ikut mengantarmu.",
    "intonasi": "berat", "jeda": 0.3, **SIANG,
    "kamera": {"z": 1.04, "x": 540, "y": 1280},
    "benda": [{"jenis": "makam", "x": 1150, "y": 1290, "n": 3, "jarak": 140, "s": 0.7}] + b,
    "boneka": o,
    "teks": [teks("TIGA YANG\nMENGANTARMU", "HR BUKHARI 6514", at="@tiga")],
})
# 2. Keluarga: bidikan dekat pengantar di belakang keranda
b, o = iring(3.2)
shot.append({
    "narasi": "Keluargamu.", "intonasi": "haru", "jeda": 0.25, **SIANG,
    "kamera": {"z": 1.28, "x": 480, "y": 1320},
    "benda": b, "boneka": o,
    "teks": [teks("KELUARGA", at=0.1, y=360)],
})
# 3. Harta: karung dan dinar ikut terbawa
shot.append({
    "narasi": "Hartamu.", "intonasi": "haru", "jeda": 0.25, **SIANG,
    "kamera": {"z": 1.12, "x": 540, "y": 1320},
    "benda": [{"jenis": "karung", "x": 440, "y": 1560, "s": 0.55, "penuh": 1},
              {"jenis": "koin", "x": 640, "y": 1580, "s": 0.6, "n": 6, "jatuh": 1}],
    "teks": [teks("HARTA", at=0.1, y=360)],
})
# 4. Amal: cahaya kecil di sisi keranda
b, o = iring(5.0)
shot.append({
    "narasi": "Dan amalmu.", "intonasi": "haru", "jeda": 0.6, **SIANG,
    "kamera": {"z": 1.08, "x": 540, "y": 1320},
    "benda": b + [{"jenis": "sajadah", "x": 190, "y": 1710, "s": 0.82, "op": [[0, 0], [0.55, 1]]}, {"jenis": "buku", "x": 520, "y": 1660, "s": 0.34, "sub": "MUSHAF", "op": [[0, 0], [1.25, 1]]}, {"jenis": "tasbih", "x": 830, "y": 1680, "s": 0.52, "op": [[0, 0], [2.0, 1]]}],
    "boneka": o,
    "teks": [teks("AMAL", at=0.1, y=360)],
})
# 5-6. Di pemakaman: pengantar berangsur pulang
def diam(npc, x, y, s=0.72):
    o = org(npc, x, y, s, pose="berdiri", mata="normal", belakang=False)
    o.pop("profil")  # tampak depan (tanpa profil); "depan" bukan nilai profil
    return o


def pulang(npc, x, y, t0, s=0.72):
    return org(npc, [[0, x], [t0, x], [t0 + 3.2, x - 900]], y, s, profil="kiri",
               pose=[[0, "berdiri"], [t0, "jalan"]], mata="normal", belakang=False)


MAKAM = [{"jenis": "makam", "x": 820, "y": 1290, "n": 2, "jarak": 160, "s": 0.7, "belakang": True},
         {"jenis": "makam", "x": 540, "y": 1640, "n": 1, "baru": True, "s": 1.6, "depan": True}]
MAKAM_SEPI = [{k: v for k, v in m.items() if k != "depan"} for m in MAKAM]  # tanpa tokoh: kartu dalil tetap di atas makam
shot.append({
    "narasi": "Lalu dua di antaranya pulang.", "intonasi": "berat", "jeda": 0.3, **SIANG,
    "kamera": {"z": [1.0, 1.05], "x": 540, "y": 1340},
    "benda": MAKAM,
    "boneka": [diam(20, 260, 1400), diam(21, 380, 1430), diam(3, 700, 1400), diam(5, 820, 1430),
               diam(8, 180, 1460, 0.78), diam(12, 900, 1460, 0.78)],
})
shot.append({
    "narasi": "Keluargamu pulang. Hartamu pun kembali.", "intonasi": "haru", "jeda": 0.8, **SIANG,
    "kamera": {"z": [1.05, 1.0], "x": 540, "y": 1340},
    "benda": MAKAM + [{"jenis": "karung", "x": [[0, 960], [2.9, 960], [6.1, 60]], "y": 1470, "s": 0.32, "penuh": 1,
                       "op": [[0, 1], [5, 0]]}],
    "boneka": [pulang(8, 180, 1460, 0.2, 0.78), pulang(20, 260, 1400, 0.7), pulang(21, 380, 1430, 1.3),
               pulang(3, 700, 1400, 1.8), pulang(5, 820, 1430, 2.4), pulang(12, 900, 1460, 2.9, 0.78)],
})
# 7. Yang tinggal hanya amal
shot.append({
    "narasi": "Yang tetap tinggal bersamamu, hanya satu: amalmu.", "intonasi": "berat", "jeda": 0.9, **SIANG,
    "malam": [[0, 0], ["@amalmu#2", 0.25]],
    "kamera": {"z": 1.12, "x": 540, "y": 1340},
    "benda": MAKAM_SEPI + [{"jenis": "sajadah", "x": 220, "y": 1710, "s": 0.82, "op": [[0, 0], [0.45, 1]]}, {"jenis": "buku", "x": 540, "y": 1660, "s": 0.34, "sub": "MUSHAF", "op": [[0, 0], [1.0, 1]]}, {"jenis": "tasbih", "x": 850, "y": 1680, "s": 0.52, "op": [[0, 0], [1.7, 1]]}],
    "teks": [teks("HANYA AMAL", at="@amalmu#2", warna="#ffd27a")],
})
# 8. Dalil (kartu masuk gaya NGOPAI)
k8 = {"z": 1.0, "x": 540, "y": 1250}
kartu = buat_kartu({"kitab": "HR. Bukhari", "no": "6514", "label": "HADIS", "arab": ARAB,
                    "teks": "Ia diikuti keluarga, harta, dan amalnya. Keluarga dan hartanya kembali, amalnya tetap tinggal."}, at=0)
kartu.update(at="@bersabda", masuk="jatuh", sorot="amalnya tetap tinggal", tulis=3.2)
kartu["y"] = round(k8["y"] + (kartu["y"] - 960) / k8["z"], 1)  # posisi layar tetap (koordinat dunia mengikuti kamera)
shot.append({
    "narasi": "Rasulullah shallallahu 'alaihi wa sallam bersabda: mayit diikuti tiga hal. Dua kembali, satu tetap bersamanya.",
    "intonasi": "tenang", "jeda": 1.2, **SIANG, "malam": 0.2,
    "kamera": {"z": 1.0, "x": 540, "y": 1250},
    "benda": MAKAM_SEPI + [kartu],
})
# 9. Penutup untuk "kamu"
shot.append({
    "narasi": "Hari ini, kamu sibuk mengumpulkan yang mana?", "intonasi": "tegas", "jeda": 1.0, **SIANG, "malam": 0.2,
    "kamera": {"z": 1.2, "x": 540, "y": 1350},
    "benda": MAKAM_SEPI + [{"jenis": "sajadah", "x": 220, "y": 1710, "s": 0.82}, {"jenis": "buku", "x": 540, "y": 1660, "s": 0.34, "sub": "MUSHAF"}, {"jenis": "tasbih", "x": 850, "y": 1680, "s": 0.52}],
    "teks": [teks("KAMU SIBUK\nMENGUMPULKAN\nYANG MANA?", at="@mengumpulkan", warna="#ffd27a", ukuran=76)],
})

spek = {
    "latar": "gelap", "stempel": True, "musik": False, "dekor": False, "volume_efek": 0,
    "cerita": {"suku": "arab", "kilat": False, "label": "KISAH KUBUR", "shot": shot},
    "rekaman": [
        {"berkas": "../../aset/suara/angin_gurun.mp3", "at": 0, "sampai": "@bersabda", "vol": 0.18, "ulang": True},
        {"berkas": "../../aset/suara/langkah_pelan.mp3", "at": 0, "sampai": "@Lalu", "vol": 0.32, "ulang": True},
        {"berkas": "../../aset/suara/dengung_haru.mp3", "at": "@tiga", "vol": 0.3},
        {"berkas": "../../aset/suara/koin_jatuh.mp3", "at": "@Hartamu", "vol": 0.35},
        {"berkas": "../../aset/suara/dengung_haru.mp3", "at": "@amalmu", "vol": 0.12},
        {"berkas": "../../aset/suara/langkah_pelan.mp3", "at": "@Keluargamu#2", "sampai": "@Yang", "vol": 0.3, "ulang": True},
        {"berkas": "../../aset/suara/isak_lembut.mp3", "at": "@Keluargamu#2", "vol": 0.16},
        {"berkas": "../../aset/suara/dengung_haru.mp3", "at": "@amalmu#2", "vol": 0.12},
        {"berkas": "../../aset/suara/hentak_serius.mp3", "at": "@mengumpulkan", "vol": 0.35},
    ],
}
(Path(__file__).with_name("pengantar1.json")).write_text(json.dumps(spek, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print("pengantar1.json:", len(shot), "shot")
