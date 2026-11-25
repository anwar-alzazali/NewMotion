"""Alat bersama video kisah 16 Nov 2026 (dabbah2, nuh2, neraka2): gaya Ya'juj (siluet + satu sumber cahaya, teks besar tengah, sumber neon, subtitle pendek)."""
import json, os, re, sys
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, f"{REPO}/papan/kisah")
import dlib
dlib.REPO = REPO
KUNING, PUTIH, MERAH, EMAS = "#ffd27a", "#ffffff", "#ff6a4a", "#ffc061"


class Video:
    def __init__(self, slug, B, **rakit):
        self.slug, self.B = slug, B
        self.G = dlib.rakit(slug, B, **rakit)
        self.SH, self.REK = [], []
        self.AKHIR = self.G[-1]["t1"]

    def t(self, i): return self.G[i]["t0"]

    def W(self, i, awalan, ke=0):
        """waktu mulai kata di baris i yang diawali `awalan` (kemunculan ke-`ke`)."""
        c = [k[0] for k in self.G[i]["kata2"] if re.sub(r"\W", "", k[2].lower()).startswith(awalan.lower())]
        if not c: raise SystemExit(f"kata '{awalan}' tidak ada di baris {i}: {self.B[i][1]}")
        return c[min(ke, len(c) - 1)]

    def shot(self, at, dasar=None, **k):
        d = dict(dasar or {}); d["at"] = round(max(0, at), 2); d.update(k); self.SH.append(d); return d

    def R(self, berkas, at, vol, **k):
        self.REK.append(dict(berkas=berkas, at=round(max(0, at), 2), vol=vol, **k))

    def selesai(self, ekor=2.5, y_sub=1480, uk_sub=64, tanpa_sub=()):
        """tanpa_sub = indeks baris yang tidak diberi subtitle (mis. kartu dalil yang sudah memuat teksnya)."""
        TGH = []
        for gi, g in enumerate(self.G):
            if gi in tanpa_sub: continue
            cur = []
            for n, k in enumerate(g["kata2"]):
                cur.append(k); nx = g["kata2"][n + 1][2] if n + 1 < len(g["kata2"]) else ""
                if len(cur) >= 4 or k[2].rstrip()[-1:] in ",.:?!…" or n == len(g["kata2"]) - 1 or len(" ".join(c[2] for c in cur)) + 1 + len(nx) > 26:
                    TGH.append({"t0": round(cur[0][0] - 0.05, 2), "t1": round(cur[-1][1] + 0.12, 2), "kata": [[c[0], c[2]] for c in cur], "y": y_sub, "ukuran": uk_sub, "maks": 18, "tahan": 0}); cur = []
        for n in range(len(TGH) - 1): TGH[n]["t1"] = min(TGH[n]["t1"], TGH[n + 1]["t0"] - 0.02)
        sp = dlib.spek(self.slug, self.SH, [], TGH, self.REK, self.AKHIR)
        sp["cerita"]["cerah"] = False; sp["cerita"]["badan"] = "siluet"; sp["cerita"]["kilat"] = False
        sp["ekor_suara"] = ekor; sp["keras_lufs"] = -15
        sp["rekaman"] = [r for r in sp["rekaman"] if not r["berkas"].endswith("whoosh.mp3")]
        json.dump(sp, open(f"{REPO}/papan/kisah/{self.slug}.json", "w"), ensure_ascii=False, indent=1)
        print(f"{self.slug}: {self.AKHIR + ekor:.1f} dtk, {len(self.SH)} potongan")
        return sp


def K(z, x, y, **k): return dict({"z": z, "x": x, "y": y}, **k)
def Bd(j, x, y, s=1, **k): return dict(jenis=j, x=x, y=y, s=s, **k)


def T(at, teks, y, ukuran, warna=KUNING, sampai=None, lebar=900):
    pj = max(len(b) for b in teks.split("\n"))
    d = {"at": round(max(0, at), 2), "teks": teks, "y": y, "ukuran": int(min(ukuran, lebar / (0.8 * pj))), "warna": warna}
    if sampai is not None: d["sampai"] = round(sampai, 2)
    return d


def N(at, teks, y=240, warna="#ffd27a", sub=None, sampai=None, ukuran=44):
    """lencana sumber bergaya neon (dalil)."""
    d = {"gaya": "neon", "at": round(max(0, at), 2), "teks": teks, "y": y, "warna": warna, "ukuran": ukuran}
    if sub: d["sub"] = sub
    if sampai is not None: d["sampai"] = round(sampai, 2)
    return d


LANGIT = [Bd("bintang", 540, -1250, 1, seed=4, tinggi=1500, n=90)]
BATU = [Bd("batu", 40, 1990, 1.35, kabur=True, depan=True), Bd("batu", 1060, 2010, 1.55, kabur=True, depan=True)]
