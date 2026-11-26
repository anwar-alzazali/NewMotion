#!/usr/bin/env python3
"""'Satu kata yang menjebol dinding Ya'juj Ma'juj' (13 Nov 2026): kisah satu narator (Ozhy), siluet menggali dinding besi di celah gunung.
Benda baru cerita.js: ngarai, penggali, pemimpin, arus, danau, batu (+ kabur). Pakai: python papan/kisah/yajuj1_buat.py -> papan/kisah/yajuj1.json"""
import json, sys
sys.path.insert(0, "/home/claude/mesin-video/papan/kisah")
import dlib
from yajuj1_naskah import B

SLUG = "yajuj1"
G = dlib.rakit(SLUG, B, jeda=0.35, awal=0.4, jeda_khusus={4: 0.75, 6: 0.65, 7: 0.75, 10: 0.9})
AKHIR = G[-1]["t1"]; END = AKHIR + 3.6
t = lambda i: G[i]["t0"]
W = lambda i, n: G[i]["kata2"][min(n, len(G[i]["kata2"]) - 1)][0]
KUNING, PUTIH = "#ffd27a", "#ffffff"


def K(z, x, y, **k): return dict({"z": z, "x": x, "y": y}, **k)
def Bd(j, x, y, s=1, **k): return dict(jenis=j, x=x, y=y, s=s, **k)
def T(at, teks, y, ukuran, warna=KUNING, sampai=None):
    pj = max(len(b) for b in teks.split("\n"))
    d = {"at": round(max(0, at), 2), "teks": teks, "y": y, "ukuran": int(min(ukuran, 960 / (0.72 * pj))), "warna": warna}
    if sampai is not None: d["sampai"] = round(sampai, 2)
    return d
def NG(**k): return dict(jenis="ngarai", x=540, y=1500, s=1, **k)
def PG(**k): return dict(jenis="penggali", x=540, y=1310, s=1, **k)
def PM(x=250, y=1700, **k): return dict(jenis="pemimpin", x=x, y=y, s=1.25, depan=True, **k)
BATU = [Bd("batu", 40, 1990, 1.35, kabur=True, depan=True), Bd("batu", 1060, 2010, 1.55, kabur=True, depan=True)]
LANGIT = [Bd("bintang", 540, -1250, 1, seed=4, tinggi=1500, n=90), Bd("bulan", 830, -620, 1.1)]
LATAR = dict(langit=0.03, malam=1, horizon=1500, debu=18)
SH, REK = [], []


def shot(at, **k):
    d = dict(LATAR); d["at"] = round(max(0, at), 2); d.update(k); SH.append(d); return d
def R(berkas, at, vol, **k): REK.append(dict(berkas=berkas, at=round(max(0, at), 2), vol=vol, **k))
def denting(a0, a1, vol=0.3):  # denting beliung mengikuti percikan (3,4 hantaman/dtk, waktu relatif awal shot)
    n = 1
    while a0 + n / 3.4 < a1: R("timbangan_denting", a0 + n / 3.4, vol if n % 2 else vol * 0.6); n += 2


# 0 HOOK: siluet mengayun beliung ke dinding besi, percikan, teks besar sejak frame 0
shot(0, kamera=K([1.15, 1.42], 540, 1235), benda=LANGIT + [NG(lubang=[0.3, 0.7]), PG(n=6)] + BATU, teks=[T(0, "DIGALI\nSETIAP HARI", 330, 150, KUNING)])
R("braam", 0, 0.7); R("drone_gelap", 0, 0.35, ulang=True, sampai=round(t(9) + 3.3, 2)); denting(0, W(0, 7))
a = W(0, 7) - 0.1  # "Dan satu kata…": dekat ke galian yang makin terang
shot(a, kamera=K([2.2, 2.6], 540, 1300), benda=[NG(lubang=[0.7, 0.95]), PG(n=4)], teks=[T(0.15, "SATU KATA", 330, 150, PUTIH)])
denting(a, t(1) - 0.3, 0.22); R("hentak_serius", a + 0.1, 0.6)
# 1 dinding Zulkarnain: kamera naik dan mundur memperlihatkan seluruh dinding di celah dua gunung
a = t(1) - 0.15
shot(a, kamera=K([[0, 1.2], [1.2, 1.2], [4.6, 0.62]], 540, [[0, 1260], [1.2, 1260], [4.6, 660]]), benda=LANGIT + [NG(lubang=0.5), PG(n=6)] + BATU,
     teks=[T(W(1, 5) - a, "DINDING BESI\nZULKARNAIN", 330, 110, KUNING), T(W(1, 5) - a + 0.4, "QS Al-Kahfi 94-97", 620, 46, PUTIH)])
denting(a, W(1, 5), 0.2); R("angin_gurun", W(1, 5), 0.35, sampai=round(t(2), 2))
# 2 menggali sampai hampir tembus
a = t(2) - 0.15; d2 = t(3) - 0.15 - a
shot(a, kamera=K([1.7, 1.95], 540, 1300, hentak=[[W(2, 6) - a - 0.03, 0.1]]), benda=[NG(lubang=[[0, 0.25], [W(2, 6) - a, 1.0]]), PG(n=6)],
     teks=[T(W(2, 5) - a - 0.05, "HAMPIR TEMBUS", 330, 130, KUNING)])
denting(a, t(3) - 0.2); R("hentak_serius", W(2, 6), 0.7); R("kilau_cahaya", W(2, 6), 0.4)
# 3 pemimpin: "pulanglah, besok kita tembus" -> mereka berbalik pergi
a = t(3) - 0.15
shot(a, kamera=K([1.22, 1.34], 480, 1340), benda=[NG(lubang=1.0), PG(n=6, aktif=[[0, 1], [0.4, 0]], pulang=[[W(3, 4) - a, 0], [W(3, 4) - a + 2.4, 1]]), PM(angkat=[[0.15, 0], [0.5, 1]])] + BATU[1:],
     teks=[T(W(3, 5) - a - 0.05, "“BESOK KITA\nTEMBUS”", 330, 120, PUTIH)])
R("langkah_pelan", W(3, 4), 0.4)
# 4 esoknya: dinding utuh kembali (hening, kilap menyapu)
a = t(4) - 0.4; u = W(4, 1) - a
shot(a, kamera=K([1.34, 1.2], 540, 1260), benda=LANGIT + [NG(lubang=[[0, 1.0], [u, 1.0], [u + 0.22, 0]], kilap=u + 0.08)] + BATU, teks=[T(W(4, 4) - a - 0.05, "UTUH KEMBALI", 330, 140, PUTIH)])
R("kilau_cahaya", a + u, 0.6); R("hentak_serius", W(4, 4), 0.6)
# 5 begitu terus, hari demi hari: tiga ulangan cepat (gali -> hampir tembus -> utuh)
a = t(5) - 0.2; sd = (t(6) - 0.3 - a) / 3
for n, z in enumerate([1.25, 1.75, 2.35]):
    shot(a + n * sd, kamera=K([z, z * 1.08], 540, 1295), benda=[NG(lubang=[[0, 0.1], [sd * 0.68, 1.0], [sd * 0.68 + 0.1, 0]], kilap=sd * 0.68 + 0.04), PG(n=6)],
         teks=[T(0, "HARI DEMI HARI", 330, 120, KUNING)])
    denting(a + n * sd, a + n * sd + sd * 0.68, 0.28); R("kilau_cahaya", a + n * sd + sd * 0.68, 0.35)
# 6 sampai tiba waktunya: lebar dan sunyi -> pemimpin -> INSYA ALLAH
a = t(6) - 0.3
shot(a, kamera=K([1.0, 1.1], 540, 1180), benda=LANGIT + [NG(lubang=[0.15, 0.6]), PG(n=6)] + BATU)
denting(a, W(6, 6) - 0.2, 0.2)
a = W(6, 6) - 0.12
shot(a, kamera=K([1.75, 1.95], 430, 1330), benda=[NG(lubang=1.0), PG(n=4, aktif=0), PM(x=400, angkat=[[0.25, 0], [0.6, 1]])])
a = W(6, 14) - 0.1
shot(a, kamera=K([1.3, 1.42], 500, 1300, hentak=[[0.0, 0.08]]), benda=[NG(lubang=1.0), PG(n=6, aktif=0), PM(x=330, angkat=1)] + BATU[1:],
     teks=[T(0, "INSYA ALLAH", 430, 170, KUNING), T(0.5, "HR Tirmidzi 3153 · Ibnu Majah 4080", 240, 42, PUTIH), T(0.5, "disahihkan Al-Albani", 300, 36, PUTIH)])
R("hentak_serius", a, 0.8); R("kilau_cahaya", a + 0.05, 0.6)
# 7 esoknya masih terbuka -> menembus -> keluar
a = t(7) - 0.15
shot(a, kamera=K([1.2, 1.36], 540, 1270), benda=LANGIT + [NG(lubang=1.0), PG(n=6, aktif=0)] + BATU, teks=[T(W(7, 3) - a - 0.05, "MASIH TERBUKA", 330, 130, PUTIH)])
a = W(7, 8) - 0.12
shot(a, kamera=K([1.3, 1.08], 540, 1200, guncang=[[0.05, 46], [0.45, 30]]), benda=LANGIT + [NG(lubang=1.0, jebol=[[0, 0], [1.0, 1]])] + BATU)
R("braam", a, 0.85); R("tanah_retak", a + 0.05, 0.8)
a = W(7, 10) - 0.1
shot(a, kamera=K([1.08, 1.3], 540, 1230), benda=LANGIT + [NG(jebol=1), dict(jenis="arus", mode="cahaya", x=540, y=1480, s=1, n=46, maju=[[0, 0.45], [2.4, 1.9]], rim=0.5, depan=True)] + BATU,
     teks=[T(0.15, "MEREKA KELUAR", 330, 130, KUNING)])
R("langkah_lari", a, 0.6, sampai=round(t(9), 2), ulang=True); R("kerumunan_cemas", a, 0.3, ulang=True, sampai=round(t(9), 2))
# 8 meminum habis air; manusia berlarian
LUAR = dict(palet="senja", malam=0.35, horizon=1280, langit=0.2, debu=10)
GN = [Bd("gunung", 180, 1290, 1.5, warna="#3a2c44"), Bd("gunung", 900, 1290, 1.7, warna="#2f2438")]
a = t(8) - 0.15
shot(a, **dict(LUAR, kamera=K([1.12, 1.26], 540, 1330), benda=GN + [Bd("danau", 540, 1640, 1.0, isi=[[0, 1], [W(8, 3) - a + 0.5, 0]]), dict(jenis="arus", mode="lereng", x=540, y=1400, s=0.95, n=54, maju=[[0, 0.2], [6, 1.5]])],
               teks=[T(W(8, 2) - a - 0.05, "AIR HABIS", 330, 140, KUNING)]))
R("air_mengalir", a, 0.4, sampai=round(W(8, 3) + 0.5, 2))
a = W(8, 5) - 0.1
shot(a, **dict(LUAR, kamera=K([1.3, 1.18], 540, 1420), benda=GN + [Bd("danau", 540, 1640, 1.0, isi=0), dict(jenis="arus", mode="lereng", x=540, y=1380, s=0.9, n=54, maju=[[0, 0.6], [6, 1.9]]),
                                                                    dict(jenis="arus", mode="lari", x=540, y=1840, s=1.0, n=16, maju=[[0, 0.15], [4, 1.0]], warna="#f0dfc2", depan=True)]))
# 9 ulat di tengkuk -> binasa serentak
a = t(9) - 0.15; rb = W(9, 9) - a
shot(a, **dict(LUAR, kamera=K([1.32, 1.14], 540, 1380), benda=GN + [dict(jenis="arus", mode="lereng", x=540, y=1420, s=1.0, n=60, maju=0.43, rebah=[[0, 0.001], [rb, 0.001], [rb + 0.4, 1]])],
               teks=[T(0.2, "HR Ibnu Majah 4080 · Tirmidzi 3153", 240, 42, PUTIH), T(rb + 0.1, "BINASA", 420, 170, PUTIH)]))
R("hentak_serius", W(9, 9), 0.9); R("tanah_retak", W(9, 9) + 0.1, 0.5)
# 10 untukmu: jangan berkata "besok aku lakukan" kecuali dengan insya Allah
PEMUDA = dict(gaya="umum", rambut="pendek", kulit="#d9b48c", hidup=True, pakaian={"jenis": "kaus", "warna": "#3f9a9a", "bawah": "celana", "bawah_warna": "#2f3a4a"})
a = t(10) - 0.25
shot(a, ruang={"jenis": "kamar", "waktu": "malam"}, debu=False, kamera=K([1.35, 1.55], 330, 1050, hentak=[[W(10, 13) - a - 0.03, 0.07]]),
     boneka=[dict(PEMUDA, x=265, y=1335, s=0.9, pose="duduk_hp", arah=0.3, wajah=[[0, "mikir"], [W(10, 6) - a, "ragu"], [W(10, 13) - a - 0.05, "senang"]],
                  reaksi=[[W(10, 5) - a, "miring"], [W(10, 13) - a, "angguk"]], utama=True)],
     teks=[T(W(10, 5) - a, "QS Al-Kahfi 23-24", 240, 44, PUTIH), T(W(10, 8) - a - 0.05, "“Besok aku lakukan…”", 390, 84, PUTIH), T(W(10, 13) - a - 0.05, "INSYA ALLAH", 610, 160, KUNING)])
R("dengung_haru", a, 0.45, sampai=round(END, 2)); R("kilau_cahaya", W(10, 13), 0.55)
# penutup: ajakan komentar + bagikan
a = AKHIR + 0.3
shot(a, ruang={"jenis": "kamar", "waktu": "malam"}, debu=False, kamera=K([1.42, 1.32], 330, 930),
     boneka=[dict(PEMUDA, x=265, y=1335, s=0.9, pose="duduk_hp", arah=0.0, wajah="senang", utama=True)],
     teks=[T(0, "Rencana apa yang\nkamu mulai besok?", 330, 88, KUNING), T(0.6, "Tulis di komentar,\npakai insya Allah", 580, 60, PUTIH), T(1.3, "Kirim ke teman yang suka\nbilang “besok aja”", 1600, 52, PUTIH)])

# subtitle pendek: tiap baris narasi dipecah per tanda baca / maksimal 4 kata, satu baris di layar (bukan kalimat menumpuk)
TGH = []
for g in G:
    cur = []
    for n, k in enumerate(g["kata2"]):
        cur.append(k)
        if len(cur) >= 4 or k[2].rstrip()[-1:] in ",.:?!…" or n == len(g["kata2"]) - 1:
            TGH.append({"t0": round(cur[0][0] - 0.05, 2), "t1": round(cur[-1][1] + 0.12, 2), "kata": [[c[0], c[2]] for c in cur], "y": 1640, "ukuran": 72, "maks": 20, "tahan": 0}); cur = []
for n in range(len(TGH) - 1): TGH[n]["t1"] = min(TGH[n]["t1"], TGH[n + 1]["t0"] - 0.02)
sp = dlib.spek(SLUG, SH, [], TGH, REK, AKHIR)
sp["cerita"]["cerah"] = False; sp["cerita"]["kilat"] = False; sp["ekor_suara"] = round(END - AKHIR, 2)
json.dump(sp, open(f"{dlib.REPO}/papan/kisah/{SLUG}.json", "w"), ensure_ascii=False, indent=1)
print(SLUG, round(END, 1), "dtk,", len(SH), "shot;", [round(s["at"], 1) for s in SH])
