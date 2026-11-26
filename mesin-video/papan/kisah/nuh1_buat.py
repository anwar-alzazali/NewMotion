#!/usr/bin/env python3
"""Kisah Nabi Nuh (15 Nov 2026): satu video berdiri sendiri. Naskah + dalil: nuh1_naskah.py. Nabi Nuh = cahaya `nur` + nama; anak beliau = siluet jauh tanpa wajah.
Pakai: python papan/kisah/nuh1_buat.py  -> papan/kisah/nuh1.json  (narasi sudah ada di audio_manual/nuh1; baris 3 tidak dipakai, baris 12 dipotong di kalimat pertama)"""
import json, os, re, shutil, subprocess, sys
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, f"{REPO}/papan/kisah")
import dlib
dlib.REPO = REPO
from nuh1_naskah import B as B0
SLUG = "nuh1"
PAKAI = [0, 1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12]
A0, A1 = f"{REPO}/audio_manual/{SLUG}", f"{REPO}/audio_manual/{SLUG}_v"; os.makedirs(A1, exist_ok=True)
for n, i in enumerate(PAKAI):
    d = json.load(open(f"{A0}/b{i:02d}.json"))
    if i == 12:   # potong setelah "benar." (pertanyaan penutup jadi teks layar)
        k = next(j for j, w in enumerate(d["kata"]) if w[2].strip().lower().startswith("benar"))
        ak = min(d["kata"][k][1] + 0.3, d["kata"][k + 1][0] - 0.05); d["kata"] = d["kata"][:k + 1]; d["lama"] = round(ak, 3)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{A0}/b{i:02d}.mp3", "-af", f"atrim=0:{ak:.3f},afade=t=out:st={ak - 0.12:.3f}:d=0.12", f"{A1}/b{n:02d}.mp3"], check=True)
    else: shutil.copy(f"{A0}/b{i:02d}.mp3", f"{A1}/b{n:02d}.mp3")
    json.dump(d, open(f"{A1}/b{n:02d}.json", "w"), ensure_ascii=False)
B = [B0[i] for i in PAKAI]
# indeks baru: 0 hook, 1 nenek moyang, 2 950 th, 3 membuat kapal, 4 langit dibuka, 5 hewan, 6 ombak, 7 anak, 8 katanya, 9 ombak memisahkan, 10 pelajaran, 11 kirim
G = dlib.rakit(f"{SLUG}_v", B, jeda=0.12, awal=0.25, jeda_khusus={2: 0.3, 4: 0.3, 7: 0.55, 9: 0.3, 10: 1.0, 11: 0.3})
EKOR = 2.1
KUNING, PUTIH = "#ffd27a", "#ffffff"
SH, REK = [], []
def K(z, x, y, **k): return dict({"z": z, "x": x, "y": y}, **k)
def Bd(j, x, y, s=1, **k): return dict(jenis=j, x=x, y=y, s=s, **k)
def T(at, teks, y, ukuran, warna=KUNING, sampai=None):
    pj = max(len(b) for b in teks.split("\n"))
    d = {"at": round(max(0, at), 2), "teks": teks, "y": y, "ukuran": int(min(ukuran, 880 / (0.72 * pj))), "warna": warna}
    if sampai is not None: d["sampai"] = round(sampai, 2)
    return d
def SMB(teks, at=0): return T(at, teks, 232 if "\n" not in teks else 215, 46, PUTIH)
def W(i, awalan, ke=0):
    c = [k[0] for k in G[i]["kata2"] if re.sub(r"\W", "", k[2].lower()).startswith(awalan)]
    return c[min(ke, len(c) - 1)] if c else G[i]["t0"]
BADAI = dict(langit=0.03, malam=1, horizon=2400, debu=0)
DARAT = dict(palet="senja", malam=0.35, horizon=1180, langit=0.2, debu=10)
def shot(at, dasar=BADAI, **k):
    d = dict(dasar); d["at"] = round(max(0, at), 2); d.update(k); SH.append(d); return d
def R(berkas, at, vol, **k): REK.append(dict(berkas=berkas, at=round(max(0, at), 2), vol=vol, **k))
SIL = dict(gaya="siluet", belakang=True)
AWAN = [Bd("gunung", 160, 1260, 1.0, warna="#141a2c", belakang=True), Bd("gunung", 940, 1260, 1.15, warna="#10152a", belakang=True)]
def laut(y, tinggi, depan=False, **k): return dict(dict(jenis="ombak", x=540, y=y, s=1, tinggi=tinggi, depan=depan, belakang=not depan), **k)
def kapal(x, y, s, **k): return dict(dict(jenis="bahtera", x=x, y=y, s=s, goyang=2.2, cahaya=1, orang=4), **k)
def nuh(x, y, s=0.8, nama=True, nama_s=1.25, **k): return dict(dict(jenis="nur", x=x, y=y, s=s), **(dict(nama="Nabi Nuh a.s.", nama_s=nama_s) if nama else {}), **k)

# 0 HOOK: kapal bercahaya di tengah badai; teks penuh di frame 0
t = 0; tq = W(0, "itu", 1)
shot(t, kamera=K([1.0, 1.1], 540, 960), hujan=0.8,
     benda=AWAN + [Bd("petir", 820, 60, 1, saat=[0.9], belakang=True), laut(1180, 110, lapis=2, seed=1), kapal(540, 1290, 0.95), nuh(250, 1052, 0.6, nama=False), laut(1330, 120, True, lapis=4, seed=4, jarak=90)],
     teks=[T(0, "KAMU DI\nKAPAL ITU", 450, 150, KUNING)])
R("braam", 0, 0.8); R("guntur_hujan", 0, 0.55); R("laut_malam", 0, 0.5, ulang=True, sampai=round(G[2]["t0"], 2)); R("drone_gelap", 0, 0.35, ulang=True, sampai=round(G[2]["t0"], 2))
shot(tq - 0.1, kamera=K([1.35, 1.5], 560, 1120), hujan=0.8,
     benda=AWAN + [laut(1180, 110, lapis=2, seed=1), kapal(540, 1290, 0.95), nuh(250, 1052, 0.6, nama=False), laut(1330, 120, True, lapis=4, seed=4, jarak=90)],
     teks=[T(0.05, "“Kami membawa kamu\nke dalam kapal”", 400, 84, PUTIH), T(0.3, "QS Al-Haqqah: 11\nterjemahan ringkas", 590, 48, KUNING)])
R("hentak_serius", tq, 0.6)
# 1 nenek moyangmu; hanya segelintir (siluet kecil di geladak)
t = G[1]["t0"] - 0.1; td = W(1, "dan") - t
shot(t, kamera=K([1.7, 1.95], 800, 1010), hujan=0.6,
     benda=AWAN + [laut(1180, 110, lapis=2, seed=1), kapal(540, 1290, 0.95), laut(1330, 120, True, lapis=4, seed=4, jarak=90)],
     teks=[T(0.1, "NENEK\nMOYANGMU", 480, 130, KUNING, sampai=td - 0.05), T(td, "HANYA\nSEGELINTIR", 480, 124, PUTIH), SMB("QS Al-Haqqah: 11\nQS Hud: 40")])
R("kilau_cahaya", t + 0.1, 0.35)
# 2 kilas balik: 950 tahun di tengah kaumnya; mereka berpaling
t = G[2]["t0"] - 0.2
shot(t, DARAT, kamera=K([1.0, 1.14], 540, 960),
     benda=[Bd("gunung", 180, 1190, 1.5, warna="#3a2c44"), Bd("gunung", 900, 1190, 1.7, warna="#2f2438"), Bd("surya", 800, 1010, 1.0, r=150, terang=0.8, belakang=True), Bd("kota", 700, 1200, 0.8, seed=5),
            nuh(360, 1240, 1.2, nama_s=1.0), dict(jenis="arus", mode="lari", x=800, y=1290, s=0.85, n=18, maju=[[0, 0.2], [7, 0.9]], warna="#221a2c", rim=0.5)],
     teks=[T(0.15, "950 TAHUN", 400, 170, KUNING), SMB("QS Al-‘Ankabut: 14")])
R("hentak_serius", t + 0.15, 0.6); R("angin_gurun", t, 0.3, sampai=round(G[4]["t0"], 2)); R("langkah_pelan", t + 0.8, 0.3, sampai=round(G[3]["t0"], 2))
# 3 membuat kapal; pemuka kaum lewat dan mengejek
t = G[3]["t0"] - 0.15; ts = W(3, "setiap") - t
shot(t, DARAT, kamera=K([1.05, 1.2], 560, 1000),
     benda=[Bd("gunung", 180, 1190, 1.5, warna="#3a2c44"), Bd("gunung", 900, 1190, 1.7, warna="#2f2438"), Bd("surya", 800, 1010, 1.0, r=150, terang=0.8, belakang=True),
            Bd("bahtera", 680, 1270, 0.7, darat=True, jadi=[[0, 0.1], [ts, 0.62], [ts + 3, 0.9]], cahaya=0.3, goyang=0), nuh(300, 1240, 0.9, nama=False)],
     teks=[T(0.1, "MEMBUAT KAPAL", 380, 112, KUNING, sampai=ts - 0.05), SMB("QS Hud: 38")])
R("palu_kayu", t + 0.1, 0.6)
shot(t + ts, DARAT, kamera=K([1.2, 1.32], 600, 1080),
     benda=[Bd("gunung", 180, 1190, 1.5, warna="#3a2c44"), Bd("gunung", 900, 1190, 1.7, warna="#2f2438"), Bd("surya", 800, 1010, 1.0, r=150, terang=0.8, belakang=True),
            Bd("bahtera", 680, 1270, 0.7, darat=True, jadi=[[0, 0.62], [3, 0.9]], cahaya=0.3, goyang=0), nuh(300, 1240, 0.9, nama=False),
            dict(jenis="arus", mode="lari", x=420, y=1700, s=1.5, n=9, maju=[[0, 0.15], [4, 0.75]], warna="#150f1c", rim=0.6, depan=True)],
     teks=[T(0.1, "MEREKA\nMENGEJEK", 450, 130, PUTIH), SMB("QS Hud: 38")])
R("kerumunan_cemas", t + ts, 0.35, sampai=round(G[4]["t0"] - 0.1, 2)); R("palu_kayu", t + ts + 0.4, 0.35)
# 4 pintu-pintu langit dibuka; bumi memancarkan mata air; air naik
t = G[4]["t0"] - 0.25; tb = W(4, "bumi") - t; tl = W(4, "langit") - t
shot(t, dict(DARAT, malam=[[0, 0.45], [1.6, 1]], debu=0), kamera=K([1.0, 1.14], 540, 980, guncang=[[tl, 36]]), hujan=[[0, 0], [tl, 0.1], [tl + 0.6, 1]],
     benda=[Bd("gunung", 180, 1190, 1.5, warna="#2a2236"), Bd("gunung", 900, 1190, 1.7, warna="#221c30"), Bd("petir", 300, 40, 1, saat=[tl, tb + 1.3], belakang=True),
            Bd("bahtera", 560, 1380, 0.78, darat=True, cahaya=[[0, 0.3], [tl + 0.5, 1]], goyang=0), nuh(330, 1178, 0.5, nama=False),
            Bd("pancar", 170, 1440, 1, kuat=[[0, 0], [tb, 0], [tb + 0.5, 1]], seed=3), Bd("pancar", 930, 1400, 0.8, kuat=[[0, 0], [tb + 0.25, 0], [tb + 0.8, 1]], seed=6),
            laut([[0, 2300], [tb, 2300], [tb + 2.6, 1560]], 30, True, lapis=3, seed=2)],
     teks=[T(tl - 0.1, "PINTU LANGIT\nDIBUKA", 450, 130, KUNING, sampai=tb - 0.05), T(tb, "BUMI MEMANCARKAN\nMATA AIR", 450, 96, PUTIH), SMB("QS Al-Qamar: 11-12")])
R("guntur_hujan", t + tl - 0.05, 0.8); R("braam", t + tl, 0.6); R("air_mengalir", t + tb, 0.6, sampai=round(G[5]["t0"], 2))
R("laut_malam", t + tb, 0.5, ulang=True, sampai=round(G[10]["t0"] - 0.9, 2)); R("drone_gelap", t + tl, 0.35, ulang=True, sampai=round(G[10]["t0"] - 0.9, 2))
# 5 sepasang dari tiap jenis hewan naik
t = G[5]["t0"] - 0.15
shot(t, kamera=K([1.0, 1.1], [[0, 520], [5, 600]], 960), hujan=0.45, horizon=1300, langit=0.03, malam=1, debu=0,
     benda=AWAN + [Bd("bahtera", 930, 1330, 0.95, darat=True, pintu=1, cahaya=1, goyang=0),
            Bd("hewan", [[0, 250], [5, 520]], [[0, 800], [5, 880]], 0.9, macam="burung"),
            Bd("hewan", [[0, 230], [5, 450]], 1396, 0.9, macam="jerapah"), Bd("hewan", [[0, 520], [5, 720]], 1400, 0.92, macam="gajah"),
            Bd("hewan", [[0, -40], [5, 190]], 1404, 0.88, macam="unta"),
            laut(1450, 12, True, lapis=2, seed=7, kilap=0.6)],
     teks=[T(0.1, "SEPASANG\nTIAP JENIS", 450, 130, KUNING), SMB("QS Hud: 40")])
R("langkah_pelan", t, 0.5, sampai=round(G[6]["t0"], 2)); R("kilau_cahaya", t + 0.1, 0.35)
# 6 ombak laksana gunung
t = G[6]["t0"] - 0.2; to = W(6, "ombak") - t
shot(t, kamera=K([1.25, 1.0], 540, 960, guncang=[[to, 40]]), hujan=1,
     benda=AWAN + [Bd("petir", 240, 30, 1, saat=[to], belakang=True), laut(1040, 260, lapis=2, seed=3, panjang=430, jarak=120), kapal(540, 1190, 0.5, goyang=6), nuh(385, 1065, 0.34, nama=False),
            laut(1260, 300, True, lapis=3, seed=9, panjang=390, jarak=170, cepat=1.3)],
     teks=[T(to - 0.05, "OMBAK LAKSANA\nGUNUNG", 450, 130, KUNING), SMB("QS Hud: 42")])
R("braam", t + to, 0.85); R("guntur_hujan", t + to, 0.7)
# 7 yang paling menyesakkan… anak beliau sendiri menolak naik
t = G[7]["t0"] - 0.45; ta = W(7, "anak") - t
shot(t, kamera=K([1.5, 1.7], 330, 1080), hujan=0.5,
     benda=AWAN + [laut(1180, 60, lapis=2, seed=1), kapal(540, 1290, 0.95, goyang=1.5), nuh(250, 1052, 0.62), laut(1330, 70, True, lapis=4, seed=4, jarak=90)],
     teks=[T(0.3, "YANG PALING\nMENYESAKKAN…", 450, 92, PUTIH)])
R("detak_jantung", t, 0.6, ulang=True, sampai=round(G[9]["t0"], 2))
TEBING = [Bd("tebing", 200, 1060, 1.0)]
ANAK = dict(SIL, x=200, y=1060, s=0.45)
shot(t + ta - 0.1, kamera=K([1.0, 1.1], 540, 960), hujan=0.6,
     benda=AWAN + [laut(1200, 60, lapis=2, seed=1), kapal(740, 1300, 0.62, goyang=1.5), nuh(545, 1148, 0.42, nama=False)] + TEBING + [laut(1380, 80, True, lapis=4, seed=4, jarak=90)],
     boneka=[dict(ANAK)],
     teks=[T(0.1, "ANAK BELIAU\nMENOLAK NAIK", 450, 124, KUNING), SMB("QS Hud: 42-43")])
R("hentak_serius", t + ta, 0.75)
# 8 "aku akan berlindung ke gunung"
t = G[8]["t0"] - 0.1
shot(t, kamera=K([1.45, 1.7], 300, 1010), hujan=0.6,
     benda=AWAN + [laut(1200, 60, lapis=2, seed=1)] + TEBING + [laut(1380, 90, True, lapis=4, seed=4, jarak=90)],
     boneka=[dict(ANAK)],
     teks=[T(0.35, "“AKU BERLINDUNG\nKE GUNUNG”", 450, 104, PUTIH), SMB("QS Hud: 43")])
# 9 ombak memisahkan keduanya -> hening
t = G[9]["t0"] - 0.15; tm = W(9, "memisahkan") - t
shot(t, kamera=K([1.05, 1.15], 540, 960, guncang=[[tm, 44]]), hujan=0.9,
     benda=AWAN + [Bd("petir", 520, 20, 1, saat=[tm], belakang=True), laut(1200, 60, lapis=2, seed=1), kapal(740, 1300, 0.62, goyang=3), nuh(545, 1148, 0.42, nama=False)] + TEBING +
           [laut([[0, 1380], [tm - 0.2, 1340], [tm + 0.9, 760]], [[0, 90], [tm + 0.9, 300]], True, lapis=4, seed=4, jarak=110, panjang=360)],
     boneka=[dict(ANAK, op=[[0, 1], [tm + 0.3, 1], [tm + 0.8, 0]])],
     teks=[T(tm, "OMBAK\nMEMISAHKAN", 450, 140, PUTIH), SMB("QS Hud: 43")])
R("braam", t + tm, 0.9); R("guntur_hujan", t + tm, 0.6)
# 10 fajar: yang menyelamatkan bukan keturunan, tapi mau naik atau tidak
FAJAR = dict(palet="senja", malam=0.3, horizon=2400, langit=0.2, debu=8)
PAGI = [Bd("gunung", 160, 1210, 1.4, warna="#3a2c44", belakang=True), Bd("gunung", 930, 1210, 1.6, warna="#2f2438", belakang=True)]
def tenang(x=600, **k): return [laut(1200, 10, lapis=2, seed=1, warna=["#5a5f86", "#1c2244"]), kapal(x, 1290, 0.82, goyang=0.6, cahaya=0.7, **k), laut(1318, 12, True, lapis=3, seed=4, jarak=80, warna=["#4a5280", "#141a3a"])]
t = G[10]["t0"] - 0.6; tt = W(10, "tapi") - t
shot(t, FAJAR, kamera=K([1.0, 1.12], 540, 960),
     benda=PAGI + [Bd("surya", 560, [[0, 1150], [6, 930]], 1.0, r=190, terang=[[0, 0.5], [3, 1]], belakang=True)] + tenang() + [nuh(349, 1085, 0.56, nama_s=1.9)],
     teks=[T(G[10]["t0"] - t + 0.1, "BUKAN\nKETURUNAN", 450, 130, PUTIH, sampai=tt - 0.05), T(tt, "MAU NAIK,\nATAU TIDAK", 450, 130, KUNING)])
R("dengung_haru", t, 0.5); R("kilau_cahaya", t + 0.2, 0.4); R("laut_malam", t, 0.22, ulang=True, sampai=round(G[-1]["t1"] + EKOR, 2)); R("hentak_serius", t + tt, 0.5)
# 11 pemicu bagikan + pertanyaan komentar
t = G[11]["t0"] - 0.1; AKHIR = G[-1]["t1"]; tk = AKHIR - t + 0.15
shot(t, FAJAR, kamera=K([1.12, 1.26], 540, 1010),
     benda=PAGI + [Bd("surya", 560, 900, 1.0, r=190, belakang=True)] + tenang() + [nuh(349, 1085, 0.56, nama=False)],
     teks=[T(0.1, "Kirim ke yang merasa\nsendirian di jalan benar", 330, 84, PUTIH, sampai=tk - 0.05), T(tk, "YAKIN KAMU\nIKUT NAIK?", 450, 130, KUNING), T(tk + 0.5, "Tulis di komentar", 700, 60, PUTIH)])
R("senandung_haru", t, 0.35, sampai=round(AKHIR + EKOR, 2)); R("pop_teks", t + tk, 0.4)

TGH = []
for g in G:
    cur = []
    for n, k in enumerate(g["kata2"]):
        cur.append(k); nx = g["kata2"][n + 1][2] if n + 1 < len(g["kata2"]) else ""
        if len(cur) >= 4 or k[2].rstrip()[-1:] in ",.:?!…" or n == len(g["kata2"]) - 1 or len(" ".join(c[2] for c in cur)) + 1 + len(nx) > 30:
            TGH.append({"t0": round(cur[0][0] - 0.05, 2), "t1": round(cur[-1][1] + 0.12, 2), "kata": [[c[0], c[2]] for c in cur], "y": 1500, "ukuran": 60, "maks": 17, "tahan": 0}); cur = []
for n in range(len(TGH) - 1): TGH[n]["t1"] = min(TGH[n]["t1"], TGH[n + 1]["t0"] - 0.02)
sp = dlib.spek(f"{SLUG}_v", SH, [], TGH, REK, AKHIR)
sp["cerita"]["cerah"] = False; sp["cerita"]["badan"] = "siluet"; sp["cerita"]["kilat"] = False; sp["ekor_suara"] = EKOR; sp["keras_lufs"] = -15
sp["rekaman"] = [r for r in sp["rekaman"] if not r["berkas"].endswith("whoosh.mp3")]
os.remove(f"{REPO}/papan/kisah/{SLUG}_v.json")
json.dump(sp, open(f"{REPO}/papan/kisah/{SLUG}.json", "w"), ensure_ascii=False, indent=1)
print(f"{AKHIR + EKOR:.1f} dtk, {len(SH)} potongan; mulai shot {[s['at'] for s in SH]}")
