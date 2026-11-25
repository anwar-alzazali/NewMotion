#!/usr/bin/env python3
"""Arah akting per baris naskah -> kunci boneka "tokoh hidup" (cerita.hidup:true). 13 Nov 2026.

baris(pembicara, kata, a, emosi=..., gestur=..., wajah=..., dasar=..., tempo=..., pendengar=[...]) mengisi boneka (dict) dengan:
  ucap    [[t0, t1, kata]]        lip-sync dari vokal kata
  wajah   [[t, nama]]             berganti per FRASA (dipisah , . ? ! …), 0,07 dtk sebelum kata pertama frasa
  pose    [[t, {dari, pakai}]]    gestur bernama per frasa, mendarat 0,1 dtk sebelum kata; kembali ke pose dasar setelah baris
  reaksi  [[t, jenis]]            pemicu tanda baca: "?" kepala miring, "!" hentakan, "," kedip
  simbol  [[t, jenis]]            "?" / "!" di samping kepala (tempo komedi)
Pendengar: menoleh ke pembicara (arah), kedip di koma, angguk di akhir kalimat berita, wajah reaksi bila diminta.
tempo="tenang" (konten dalil serius): wajah & gestur hanya sekali di awal baris, tanpa hentakan/simbol.
Semua waktu keluaran relatif awal shot (a = detik awal shot). kata = [[t0, t1, teks]] absolut (garis["kata2"] dari dlib.rakit).
Mengembalikan daftar efek suara [(detik_absolut, berkas, volume)]."""
import re

VARIAN = {"netral": ["netral", "senang", "ragu"], "senang": ["senang", "nyengir", "lega"], "kesal": ["kesal", "marah", "sinis"], "marah": ["marah", "kesal", "marah"],
          "ragu": ["ragu", "mikir", "bingung"], "bingung": ["bingung", "ragu", "mikir"], "licik": ["licik", "nyengir", "licik"], "kaget": ["kaget", "takut", "bingung"],
          "sedih": ["sedih", "lelah", "sedih"], "sopan": ["nyengir", "lega", "senang"], "takut": ["takut", "kaget", "takut"], "lega": ["lega", "senang", "lega"]}
GESTUR = {"netral": ["jelaskan", "jelaskan_kiri", "buka2"], "senang": ["jelaskan", "buka2", "kepal"], "kesal": ["tunjuk", "buka2", "pinggang1"], "marah": ["tunjuk", "stop2", "buka2"],
          "ragu": ["garuk_kepala", "angkat_bahu", "jelaskan_kiri"], "bingung": ["angkat_bahu", "garuk_kepala", "buka2"], "licik": ["jelaskan", "angkat_bahu", "silang"],
          "kaget": ["dua_naik", "mundur", "stop2"], "sedih": ["lemas", "tangan_dada", "lemas"], "sopan": ["tangan_dada", "jelaskan_kiri", "angkat_bahu"],
          "takut": ["stop2", "mundur", "dua_naik"], "lega": ["tangan_dada", "buka2", "jelaskan"]}
TANDA = re.compile(r"[,.?!…;:]+$")


def frasa(kata):
    F, cur = [], []
    for k in kata:
        cur.append(k)
        if TANDA.search(k[2].strip()): F.append(cur); cur = []
    if cur: F.append(cur)
    return F


def kunci(b, nama, t, nilai):
    """Tambah kunci waktu [t, nilai] ke b[nama]; nilai tunggal lama dijadikan kunci detik 0."""
    cur = b.get(nama)
    if not (isinstance(cur, list) and cur and isinstance(cur[0], list)): cur = [[0, cur]] if cur is not None else []
    t = round(max(0.0, t), 3)
    cur = [k for k in cur if k[0] < t - 1e-6] + [[t, nilai]] if nama in ("wajah", "pose", "arah") else cur + [[t, nilai]]
    b[nama] = sorted(cur, key=lambda k: k[0])


def _pose(dasar, g):
    if g is None or g == dasar: return dasar
    d = dict(dasar) if isinstance(dasar, dict) else {"dari": dasar}  # pose dasar boleh nama atau dict ({"dari": "duduk", "ra": [...]})
    if isinstance(g, dict): d.update(g)
    else: d["pakai"] = g
    return d


def baris(pembicara, kata, a, emosi="netral", gestur=None, wajah=None, dasar="berdiri", tempo="komedi", pendengar=(), simbol=True, tahan=0.35, tatap=None):
    """pendengar = [(boneka, {arah: nilai menoleh ke pembicara, wajah: [(frasa_ke | "akhir", nama)], dasar: pose})]. tatap = arah pembicara per frasa (list) atau satu nilai."""
    b, F, sfx, kom = pembicara, frasa(kata), [], tempo == "komedi"
    b.setdefault("ucap", []); b["ucap"] += [[round(k[0] - a, 3), round(k[1] - a, 3), k[2]] for k in kata]
    V, G = VARIAN.get(emosi, [emosi]), GESTUR.get(emosi, GESTUR["netral"])
    for i, f in enumerate(F):
        t0, tl, tanda = f[0][0] - a, f[-1][0] - a, (TANDA.search(f[-1][2].strip()) or [""])[0]
        if i == 0 or kom:
            kunci(b, "wajah", t0 - 0.07, wajah[i] if wajah and i < len(wajah) and wajah[i] else V[i % len(V)] if kom else V[0])
            g = gestur[i] if gestur and i < len(gestur) else G[i % len(G)] if kom or i == 0 else None
            if g != "-": kunci(b, "pose", t0 - 0.1, _pose(dasar, g))
        if tatap is not None: kunci(b, "arah", t0 - 0.08, tatap[i] if isinstance(tatap, list) and i < len(tatap) else tatap if not isinstance(tatap, list) else tatap[-1])
        if "?" in tanda:
            kunci(b, "reaksi", tl - 0.04, "miring")
            if kom and simbol: kunci(b, "simbol", tl, "tanya"); sfx.append((round(a + tl, 2), "pop_teks", 0.5))
        elif "!" in tanda and kom:
            kunci(b, "reaksi", tl - 0.04, "hentak")
            if simbol: kunci(b, "simbol", tl, "seru"); sfx.append((round(a + tl, 2), "pop_teks", 0.5))
        elif "," in tanda: kunci(b, "reaksi", f[-1][1] - a, "kedip")
        for pd, o in pendengar:
            if "," in tanda or i == 0: kunci(pd, "reaksi", f[-1][1] - a + 0.06 * (1 + i), "kedip")
            if "." in tanda and "…" not in tanda and i == len(F) - 1: kunci(pd, "reaksi", f[-1][1] - a - 0.1, "angguk")
            for ke, nm in o.get("wajah", []):
                if ke == i: kunci(pd, "wajah", f[-1][1] - a - 0.12, nm)
    t1 = kata[-1][1] - a
    kunci(b, "pose", t1 + tahan, dasar)
    for pd, o in pendengar:
        if "arah" in o: kunci(pd, "arah", kata[0][0] - a - 0.15, o["arah"])
        for ke, nm in o.get("wajah", []):
            if ke == "akhir": kunci(pd, "wajah", t1 + 0.1, nm)
    return sfx
