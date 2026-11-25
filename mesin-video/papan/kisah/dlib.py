#!/usr/bin/env python3
"""Pustaka video DIALOG (7 Nov 2026): suara per tokoh (tag emosi ElevenLabs) -> potong per baris -> rakit -> spek cerita.
Naskah: daftar baris (peran, teks). Teks boleh diawali tag emosi, mis. "[angry] Ibumu terus yang dikasih!".
- suara(slug, baris): kirim SATU permintaan per suara (semua baris tokoh itu digabung), potong per baris dari waktu kata.
  Hasil disimpan audio_manual/<slug>/bNN.mp3 + bNN.json (kata relatif). Baris yang sudah ada tidak dibuat ulang (hemat kredit).
- rakit(slug, baris, jeda): gabung baris -> audio_manual/<slug>/narasi.mp3; kembalikan garis waktu [{peran, t0, t1, kata:[[t, kata]]}].
"""
import base64, json, os, re, subprocess, time
REPO = "/home/claude/mesin-video"
SUARA = {"NR": "UdQDnhmw5mrED2XYPXhu",  # Ozhy (narator)
         "SU": "v70fYBHUOrHA3AKIBjPq", "CU": "v70fYBHUOrHA3AKIBjPq",  # Mahaputra (suami / pemuda / cucu)
         "IS": "OKanSStS6li6xyU1WdXa", "IB": "OKanSStS6li6xyU1WdXa",  # Meraki (istri / ibu)
         "KK": "GcHP6UfXX0zaHYu0b0ut", "TG": "GcHP6UfXX0zaHYu0b0ut",
         "PM": "v70fYBHUOrHA3AKIBjPq", "UA": "v70fYBHUOrHA3AKIBjPq", "AK": "v70fYBHUOrHA3AKIBjPq", "EM": "OKanSStS6li6xyU1WdXa"}  # anak (Mahaputra dinaikkan nadanya), emak (Meraki)  # Mazlan (kakek / tetangga tua)
TAG = re.compile(r"\[[^\]]*\]")


def _kata_baris(teks):
    return [w for w in TAG.sub(" ", teks).split() if re.search(r"\w", w)]


def _picu(teks, keluaran, suara):
    b64 = base64.b64encode(teks.encode()).decode()
    subprocess.run(["gh", "api", "repos/anwar-alzazali/mesin-video/actions/workflows/narasi.yml/dispatches", "-f", "ref=main",
                    "-f", f"inputs[teks_b64]={b64}", "-f", f"inputs[keluaran]={keluaran}", "-f", f"inputs[suara]={suara}"], check=True)
    time.sleep(15)
    for _ in range(60):
        r = subprocess.run(["gh", "api", "repos/anwar-alzazali/mesin-video/actions/workflows/narasi.yml/runs?per_page=1",
                            "--jq", '.workflow_runs[0] | "\\(.status) \\(.conclusion)"'], capture_output=True, text=True).stdout.strip()
        if r.startswith("completed"):
            if "success" not in r: raise SystemExit(f"narasi gagal: {keluaran} {r}")
            break
        time.sleep(8)
    subprocess.run(["git", "-C", REPO, "fetch", "-q", "origin", "+refs/heads/narasi:refs/remotes/origin/narasi"], check=True)
    for ext in (".mp3", ".waktu.json"):
        isi = subprocess.run(["git", "-C", REPO, "show", f"origin/narasi:{keluaran[:-4]}{ext}"], capture_output=True, check=True).stdout
        open(f"{REPO}/{keluaran[:-4]}{ext}", "wb").write(isi)


def suara(slug, baris):
    A = f"{REPO}/audio_manual/{slug}"; os.makedirs(A, exist_ok=True)
    perlu = {}
    for i, (p, teks) in enumerate(baris):
        if not os.path.exists(f"{A}/b{i:02d}.mp3"): perlu.setdefault(SUARA[p], []).append(i)
    for vid, idx in perlu.items():
        nama = f"audio_manual/{slug}/v_{vid[:6]}_{idx[0]:02d}.mp3"
        if not os.path.exists(f"{REPO}/{nama}"): _picu(" ".join(baris[i][1] for i in idx), nama, vid)
        kk, dalam = [], False  # buang token tag emosi (tag bisa terpecah: "[touched," "voice" "breaking]")
        for k in json.load(open(f"{REPO}/{nama[:-4]}.waktu.json"))["kata"]:
            x = k["teks"].strip()
            if x.startswith("["): dalam = True
            if not dalam and re.search(r"\w", x): kk.append(k)
            if dalam and "]" in x: dalam = False
        pos = 0
        for n, i in enumerate(idx):
            m = len(_kata_baris(baris[i][1])); seg = kk[pos:pos + m]
            if len(seg) < m: raise SystemExit(f"kata kurang di baris {i}: {baris[i][1]}")
            a0 = max(0, seg[0]["t0"] - 0.12)
            if n > 0: a0 = max(a0, kk[pos - 1]["t1"] + 0.05)
            a1 = seg[-1]["t1"] + 0.35
            if pos + m < len(kk): a1 = min(a1, kk[pos + m]["t0"] - 0.1)
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{REPO}/{nama}", "-af", f"atrim={a0:.3f}:{a1:.3f},asetpts=PTS-STARTPTS,aresample=44100,aformat=channel_layouts=mono",
                            f"{A}/b{i:02d}.mp3"], check=True)
            json.dump({"teks": baris[i][1], "kata": [[round(k["t0"] - a0, 3), round(k["t1"] - a0, 3), k["teks"]] for k in seg], "lama": round(a1 - a0, 3)},
                      open(f"{A}/b{i:02d}.json", "w"), ensure_ascii=False)
            pos += m


def rakit(slug, baris, jeda=0.28, awal=0.0, jeda_khusus=None):
    """jeda_khusus = {indeks_baris: detik sebelum baris itu} untuk memberi ruang adegan tanpa suara."""
    A = f"{REPO}/audio_manual/{slug}"; jeda_khusus = jeda_khusus or {}
    garis, pos, fc, cmd = [], awal, [], ["ffmpeg", "-v", "error", "-y"]
    for i, (p, teks) in enumerate(baris):
        d = json.load(open(f"{A}/b{i:02d}.json"))
        if i > 0: pos += jeda_khusus.get(i, jeda)
        garis.append({"peran": p, "t0": round(pos, 3), "t1": round(pos + d["lama"], 3), "kata": [[round(pos + k[0], 3), k[2]] for k in d["kata"]], "teks": teks,
                      "kata2": [[round(pos + k[0], 3), round(pos + k[1], 3), k[2]] for k in d["kata"]]})  # kata2 = dengan waktu akhir (lip-sync akting.py)
        cmd += ["-i", f"{A}/b{i:02d}.mp3"]
        fc.append(f"[{i}:a]adelay={int(pos * 1000)}|{int(pos * 1000)}[d{i}]")
        pos += d["lama"]
    n = len(baris)
    subprocess.run(cmd + ["-filter_complex", ";".join(fc) + ";" + "".join(f"[d{i}]" for i in range(n)) + f"amix=inputs={n}:normalize=0:duration=longest[o]",
                          "-map", "[o]", f"{A}/narasi.mp3"], check=True)
    return garis


def gelembung(g, x, y, ekor, nama=None, warna=None, maks=18, ukuran=52):
    d = {"t0": g["t0"], "t1": g["t1"], "kata": [[t, k] for t, k in g["kata"]], "x": x, "y": y, "ekor": ekor, "maks": maks, "ukuran": ukuran}
    if nama: d.update(nama=nama, warna=warna or "#ff9a3a")
    return d


def tengah(g, y=1500, ukuran=78, sorot=None):
    d = {"t0": g["t0"], "t1": g["t1"] + 0.2, "kata": [[t, k] for t, k in g["kata"]], "y": y, "ukuran": min(ukuran, 64), "maks": 24}
    if sorot: d["sorot"] = sorot
    return d


def spek(slug, shots, dialog, tengah_list, rekaman, akhir, label=None):
    S = lambda f: f"../../aset/suara/{f}.mp3"
    rek = [dict(r, berkas=S(r["berkas"])) for r in rekaman]
    rek += [{"berkas": S("whoosh"), "at": round(s["at"] - 0.05, 2), "vol": 0.25} for s in shots if s["at"] > 0]
    sp = {"latar": "gelap", "stempel": False, "musik": False, "dekor": False, "suara": f"../../audio_manual/{slug}/narasi.mp3",
          "ekor_suara": 1.2, "volume_efek": 0, "duck_rasio": 3, "keras_lufs": -16, "rekaman": rek,
          "cerita": {"cerah": True, "shot": shots, "dialog": dialog, "tengah": tengah_list}}
    if label: sp["cerita"]["label"] = label
    json.dump(sp, open(f"{REPO}/papan/kisah/{slug}.json", "w"), ensure_ascii=False, indent=1)
    return sp


def jernih(slug, baris, eq=("KK", "TG"), lufs=-17):
    """Samakan kekerasan semua baris (loudnorm per baris) + EQ kejernihan untuk suara berat/mendem (Mazlan).
    Sekali per baris (ditandai 'jernih' di json); panjang audio tidak berubah."""
    A = f"{REPO}/audio_manual/{slug}"
    for i, (p, _) in enumerate(baris):
        j = json.load(open(f"{A}/b{i:02d}.json"))
        if j.get("jernih"): continue
        af = "highpass=f=90,equalizer=f=250:t=q:w=1.2:g=-4,equalizer=f=3000:t=q:w=1.0:g=5,equalizer=f=6000:t=q:w=1.0:g=3," if p in eq else ""
        af += f"loudnorm=I={lufs}:TP=-1.5:LRA=11,aresample=44100"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{A}/b{i:02d}.mp3", "-af", af, "-ac", "1", f"{A}/tmp.mp3"], check=True)
        os.replace(f"{A}/tmp.mp3", f"{A}/b{i:02d}.mp3"); j["jernih"] = True
        json.dump(j, open(f"{A}/b{i:02d}.json", "w"), ensure_ascii=False)
