"""Lapisan tata letak: benda inti utuh di layar dan tidak tertutup, figuran tidak berdempetan.

Bekerja pada satu shot papan memakai kotak batas tiap jenis benda yang diukur dari renderer
(data/ukuran_benda.json, dibuat mesin-video/papan/ukur_benda.py). Aturan, berurutan:

  1. Subjek (benda yang dipilih sutradara) utuh secara horizontal di bidang kamera.
  2. Benda latar yang digambar di depan subjek dan menutupinya digeser ke samping.
  3. Tokoh "kamu" yang menutupi subjek pindah ke sisi yang lebih lapang.
  4. Figuran tidak menutupi subjek dan tidak berdempetan satu sama lain.

Benda selebar latar (gunung, kota, dinding ngarai, langit) tidak dipindah: mereka memang
memenuhi bingkai. Setiap perubahan dicatat agar bisa dilaporkan.
"""
from __future__ import annotations

import json
from collections.abc import Iterable
from functools import lru_cache
from itertools import pairwise
from pathlib import Path

DATA = Path(__file__).resolve().parent / "data" / "ukuran_benda.json"
TEPI = 36            # jarak minimum dari tepi bingkai (px dunia)
TUTUP_MAKS = 0.25    # bagian subjek yang boleh tertutup
LEBAR_BONEKA, TINGGI_BONEKA = 190, 640  # boneka skala 1, kaki di (0, 0)


@lru_cache(maxsize=1)
def ukuran() -> dict[str, list[int]]:
    return json.loads(DATA.read_text(encoding="utf-8")) if DATA.exists() else {}


def _awal(v, bawaan: float) -> float:
    while isinstance(v, list) and v:
        v = v[0][1] if isinstance(v[0], list) else v[0]
    return float(v) if isinstance(v, (int, float)) else bawaan


def _maks(v, bawaan: float) -> float:
    if isinstance(v, list) and v:
        nilai = [_maks(x[1] if isinstance(x, list) and len(x) == 2 and isinstance(x[1], (int, float)) else x, bawaan)
                 for x in v]
        return max(nilai)
    return float(v) if isinstance(v, (int, float)) else bawaan


def kotak_benda(o: dict) -> tuple[float, float, float, float] | None:
    u = ukuran().get(o.get("jenis"))
    if not u:
        return None
    x, y = _awal(o.get("x"), 540), _awal(o.get("y"), 1000)
    s = _maks(o.get("s"), 1) * _maks(o.get("besar"), 1)  # `besar` = skala tambahan (bayang_misteri dll.)
    ki, at, ka, bw = u
    if o.get("arah") == -1:
        ki, ka = -ka, -ki
    return (x + ki * s, y + at * s, x + ka * s, y + bw * s)


def kotak_boneka(b: dict) -> tuple[float, float, float, float]:
    x, y, s = _awal(b.get("x"), 540), _awal(b.get("y"), 1500), _maks(b.get("s"), 1)
    return (x - LEBAR_BONEKA / 2 * s, y - TINGGI_BONEKA * s, x + LEBAR_BONEKA / 2 * s, y)


def bidang(shot: dict) -> tuple[float, float, float, float]:
    """Bagian dunia yang terlihat kamera (z terbesar = paling sempit)."""
    k = shot.get("kamera") or {}
    z = _maks(k.get("z"), 1) or 1
    kx, ky = _awal(k.get("x"), 540), _awal(k.get("y"), 960)
    return (kx - 540 / z, ky - 960 / z, kx + 540 / z, ky + 960 / z)


def _luas(a) -> float:
    return max(0.0, a[2] - a[0]) * max(0.0, a[3] - a[1])


def _irisan(a, b) -> float:
    return _luas((max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3])))


def _geser_x(o: dict, dx: float) -> None:
    x = o.get("x", 540)
    if isinstance(x, list):  # kunci waktu: geser semua nilai
        o["x"] = [[k[0], round(k[1] + dx)] if isinstance(k, list) else round(k + dx) for k in x]
    else:
        o["x"] = round(float(x) + dx)


def _selebar_latar(kt, bd) -> bool:
    return (kt[2] - kt[0]) >= 1.05 * (bd[2] - bd[0])


def _skala(o: dict, f: float) -> bool:
    if isinstance(o.get("s", 1), list):
        return False
    o["s"] = round(float(o.get("s", 1)) * f, 3)
    return True


def tata_shot(shot: dict, subjek: Iterable[dict]) -> list[str]:
    """Rapikan satu shot di tempat. subjek: objek benda (identitas sama dengan di shot['benda'])."""
    catatan: list[str] = []
    bd = bidang(shot)
    benda = shot.get("benda") or []
    subj = [o for o in benda if any(o is s for s in subjek)]

    # 1. subjek utuh horizontal
    for o in subj:
        kt = kotak_benda(o)
        if not kt or _selebar_latar(kt, bd) or o.get("_di_lubang"):
            continue
        muat = (bd[2] - bd[0]) - 2 * TEPI
        if kt[2] - kt[0] > muat:  # lebih lebar dari bingkai: kecilkan secukupnya lalu ke tengah
            if _skala(o, max(0.6, muat / (kt[2] - kt[0]))):
                catatan.append(f"{o['jenis']} dikecilkan agar muat di layar")
            kt = kotak_benda(o)
            dx = (bd[0] + bd[2]) / 2 - (kt[0] + kt[2]) / 2
        elif kt[0] < bd[0] + TEPI:
            dx = bd[0] + TEPI - kt[0]
        elif kt[2] > bd[2] - TEPI:
            dx = bd[2] - TEPI - kt[2]
        else:
            continue
        _geser_x(o, dx)
        catatan.append(f"{o['jenis']} digeser {dx:+.0f}px agar utuh di layar")

    # 1b. dua subjek tidak saling menutupi: dipisah ke dua sisi, dikecilkan bila tidak muat
    lepas = [o for o in subj if kotak_benda(o) and not _selebar_latar(kotak_benda(o), bd) and not o.get("_di_lubang")]
    for _ in range(3):
        lepas.sort(key=lambda o: _awal(o.get("x"), 540))
        berubah = False
        for a, b in pairwise(lepas):
            ka, kb = kotak_benda(a), kotak_benda(b)
            kecil = min(_luas(ka), _luas(kb)) or 1
            if _irisan(ka, kb) / kecil <= TUTUP_MAKS:
                continue
            ruang = (bd[2] - bd[0]) - 2 * TEPI - 30
            perlu = (ka[2] - ka[0]) + (kb[2] - kb[0])
            if perlu > ruang:
                f = max(0.6, ruang / perlu)
                if _skala(a, f) and _skala(b, f):
                    catatan.append(f"{a['jenis']} & {b['jenis']} dikecilkan x{f:.2f} agar muat berdampingan")
                ka, kb = kotak_benda(a), kotak_benda(b)
            _geser_x(a, bd[0] + TEPI - ka[0])
            _geser_x(b, bd[2] - TEPI - kb[2])
            catatan.append(f"{a['jenis']} ke kiri, {b['jenis']} ke kanan agar tidak saling menutupi")
            berubah = True
        if not berubah:
            break

    kotak_subj = [(o, kotak_benda(o)) for o in subj]
    kotak_subj = [(o, k) for o, k in kotak_subj if k and not _selebar_latar(k, bd)]

    def tertutup(kt) -> tuple[dict, tuple] | None:
        for o, ks in kotak_subj:
            if _luas(ks) and _irisan(kt, ks) / _luas(ks) > TUTUP_MAKS:
                return o, ks
        return None

    def ke_sisi_lapang(kt, ks) -> float:
        """dx terkecil yang membuat kt paling sedikit menutupi SEMUA subjek, tetap di bidang."""
        lebar = kt[2] - kt[0]
        calon = [0.0]
        for _, k in kotak_subj:
            calon += [k[0] - 20 - kt[2], k[2] + 20 - kt[0]]
        calon += [bd[0] + TEPI - kt[0], bd[2] - TEPI - kt[2]]
        urut = sorted(k for _, k in kotak_subj)  # celah di antara dua subjek
        pusat = (kt[0] + kt[2]) / 2
        calon += [(a[2] + b[0]) / 2 - pusat for a, b in pairwise(urut)]

        def nilai(dx):
            g = (kt[0] + dx, kt[1], kt[2] + dx, kt[3])
            keluar = max(0.0, bd[0] + TEPI - g[0]) + max(0.0, g[2] - (bd[2] - TEPI))
            tutup = sum(_irisan(g, k) / (_luas(k) or 1) for _, k in kotak_subj)
            return (round(tutup + 3 * keluar / max(lebar, 1), 3), abs(dx))
        return min(calon, key=nilai)

    # 2. benda latar di depan subjek yang menutupinya
    for i, o in enumerate(benda):
        if any(o is s for s, _ in kotak_subj) or o.get("belakang"):
            continue
        kt = kotak_benda(o)
        if not kt or _selebar_latar(kt, bd):
            continue
        di_depan = o.get("depan") or any(benda.index(s) < i for s, _ in kotak_subj)
        hit = tertutup(kt) if di_depan else None
        if hit:
            dx = ke_sisi_lapang(kt, hit[1])
            _geser_x(o, dx)
            catatan.append(f"{o['jenis']} (latar) digeser {dx:+.0f}px agar tidak menutupi {hit[0]['jenis']}")

    # 3 & 4. boneka: "kamu" dan figuran tidak menutupi subjek; figuran tidak berdempetan
    boneka = [b for b in shot.get("boneka") or [] if b.get("kait") is None and not b.get("belakang")]
    for b in boneka:
        hit = tertutup(kotak_boneka(b))
        if hit:
            dx = ke_sisi_lapang(kotak_boneka(b), hit[1])
            _geser_x(b, dx)
            catatan.append(f"{'figuran' if 'npc' in b else 'kamu'} digeser {dx:+.0f}px agar tidak menutupi {hit[0]['jenis']}")
    fig = sorted((b for b in boneka if "npc" in b), key=lambda b: _awal(b.get("x"), 540))
    for a, b in pairwise(fig):
        ka, kb = kotak_boneka(a), kotak_boneka(b)
        jarak_min = 0.85 * max(ka[2] - ka[0], kb[2] - kb[0])
        celah = _awal(b.get("x"), 540) - _awal(a.get("x"), 540)
        if celah < jarak_min:
            _geser_x(b, jarak_min - celah)
            catatan.append(f"figuran direnggangkan {jarak_min - celah:+.0f}px")
    if fig:  # rombongan tetap di dalam bidang
        kiri = min(kotak_boneka(b)[0] for b in fig)
        kanan = max(kotak_boneka(b)[2] for b in fig)
        dx = (bd[0] + TEPI - kiri) if kiri < bd[0] + TEPI else (bd[2] - TEPI - kanan) if kanan > bd[2] - TEPI else 0
        if dx:
            for b in fig:
                _geser_x(b, dx)
            catatan.append(f"rombongan figuran digeser {dx:+.0f}px ke dalam layar")
    return catatan
