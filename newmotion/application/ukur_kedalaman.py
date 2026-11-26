"""Alat ukur kedalaman spek papan (JSON renderer) dibanding referensi buatan tangan.

Tujuan: memberi angka untuk "seberapa dekat JSON hasil mesin dengan Nuh 1, Mahsyar 1,
Ya'juj 1, dan Ya'juj 2". Yang diukur adalah KEDALAMAN struktur (berapa banyak keputusan
penyutradaraan yang benar-benar diambil), bukan mutu artistik. Skor tinggi tidak menjamin
video bagus; skor rendah hampir pasti berarti visualnya miskin. Penilaian akhir tetap
lewat pratinjau visual oleh pemilik.

Aspek (semua dihitung dari `cerita.shot`, kecuali subtitle):
- ritme      : jumlah shot dan rata-rata durasi shot.
- kamera     : porsi shot dengan kamera bergerak, aksen kamera (hentak/guncang).
- lingkungan : rata-rata elemen lingkungan per shot dan variasi suasana antar-shot.
- benda      : rata-rata benda per shot, ragam jenis, porsi benda beranimasi/berlapis.
- tokoh      : rata-rata boneka per shot dan porsi boneka yang punya ekspresi/gerak.
- teks_layar : rata-rata teks overlay per shot (angka kunci, rujukan, judul).
- gerak      : rata-rata properti beranimasi per shot (semua objek).
- cerita     : benda PELAKU cerita (bukan latar umum seperti bintang/gunung/batu) per shot,
               ragamnya, dan keragaman komposisi antar-shot. Aspek ini paling berbobot:
               papan yang hanya mengulang latar + satu tokoh bergestur bisa tinggi di aspek
               lain tetapi tidak menceritakan apa pun.
"""
from __future__ import annotations

import json
import re
import statistics
from collections.abc import Mapping
from pathlib import Path
from typing import Any

AKAR = Path(__file__).resolve().parents[2]
FOLDER_REFERENSI = AKAR / "mesin-video" / "papan" / "kisah"
REFERENSI = ("nuh1", "mahsyar1", "yajuj1", "yajuj2")

# Kunci shot yang mengubah tampilan lingkungan (bukan kamera/benda/boneka/teks/waktu).
KUNCI_LINGKUNGAN = (
    "langit", "malam", "horizon", "debu", "hujan", "panas", "matahari", "naungan",
    "kerumunan", "retak", "resap", "ruang", "palet", "salju", "kabut", "api",
)
KUNCI_EKSPRESI_TOKOH = ("wajah", "reaksi", "mata", "pose", "tunduk", "keringat", "lengan", "naik", "jalan")
KUNCI_LAPIS = ("depan", "belakang", "kabur", "lapis", "jarak")
# Benda latar yang bisa muncul di cerita apa saja; tidak dihitung sebagai pelaku/subjek cerita.
LATAR_UMUM = frozenset({
    "bintang", "bulan", "batu", "gunung", "awan", "kota", "bukit", "rumput", "pohon",
    "tanah", "kabut", "surya", "matahari", "langit",
})

# Leksikon narasi -> wujud visual yang sah di renderer. Sengaja ditulis TERPISAH dari pengarah
# agar alat ukur tidak menilai pengarah dengan aturannya sendiri. Kunci "env:<x>" = kunci shot
# lingkungan; "boneka:<x>" = ada boneka dengan kunci itu; "boneka>=N" = minimal N boneka.
# Kata yang tidak ada di leksikon diabaikan (tidak dihukum).
LEKSIKON: tuple[tuple[str, frozenset[str]], ...] = tuple(
    (pola, frozenset(wujud)) for pola, wujud in (
        (r"\b(kapal|bahtera|perahu)", {"bahtera"}),
        (r"\b(hewan|binatang|sepasang)", {"hewan", "unta"}),
        (r"\bunta", {"unta"}),
        (r"\b(ombak|gelombang)", {"ombak"}),
        (r"\bbanjir", {"ombak", "laut", "env:hujan"}),
        (r"\b(hujan|tercurah)", {"env:hujan", "pancar"}),
        (r"\b(mata air|memancar)", {"pancar"}),
        (r"\b(danau|telaga|sungai)", {"danau", "telaga"}),
        # "air mata" bukan air; jenis `arus` di renderer adalah kerumunan berlari, BUKAN air.
        (r"\bair\b(?! mata)(?<!mata air)", {"danau", "telaga", "pancar", "ombak", "laut", "env:hujan"}),
        (r"\b(gunung|bukit)", {"gunung", "tebing"}),
        (r"\b(dinding|tembok|benteng)", {"ngarai", "pagar", "gerbang"}),
        (r"gali", {"penggali"}),
        (r"\b(pemimpin|raja)", {"pemimpin", "istana"}),
        (r"\b(petir|kilat|guntur)", {"petir"}),
        (r"\bmatahari", {"surya", "env:matahari"}),
        (r"\bkeringat", {"boneka:keringat", "boneka:genangan"}),
        (r"\b(seluruh manusia|kerumunan|orang-orang|semua orang|umat)", {"env:kerumunan", "kerumunan", "arus", "boneka>=3"}),
        (r"\b(kaum|pemuka)", {"env:kerumunan", "kerumunan", "arus", "boneka>=2"}),
        (r"\b(berlarian|berhamburan|menyerbu|keluar berbondong)", {"arus", "env:kerumunan", "kerumunan"}),
        (r"\b(terbelah|retak|belah)", {"env:retak", "retakan", "belah"}),
        (r"\b(kubur|makam)", {"makam", "jenazah"}),
        (r"\bmasjid", {"masjid", "masjid_kampung"}),
        (r"\b(api|neraka|bara)", {"api", "lahar", "massa_api"}),
        (r"\b(cahaya|nur)\b", {"nur", "cahaya"}),
        (r"\btimbangan", {"timbangan"}),
        (r"\b(kitab|buku|catatan amal)", {"kitab", "buku"}),
        (r"\brantai", {"rantai", "rantai_tarik"}),
        (r"\bpohon", {"pohon", "kelapa", "zaqqum"}),
        (r"\brumah\b", {"rumah", "rumah_kampung"}),
        (r"\b(kota|negeri)", {"kota", "istana"}),
        (r"\bpenjara", {"penjara"}),
        (r"\b(uang|harta|emas)", {"uang", "koin"}),
        (r"\b(naungan|teduh)", {"env:naungan"}),
    )
)

# Bobot skor gabungan. Benda, tokoh, dan gerak paling membedakan referensi dari papan miskin.
BOBOT = {
    "ritme": 1.0, "kamera": 1.0, "lingkungan": 1.0, "benda": 1.5,
    "tokoh": 1.5, "teks_layar": 0.5, "gerak": 1.5, "cerita": 3.0,
}


def _beranimasi(nilai: Any) -> bool:
    """Sama dengan v() di cerita.js: [a, b] berubah, atau keyframe [[t, nilai], ...] berubah."""
    if not isinstance(nilai, list) or len(nilai) < 2:
        return False
    if isinstance(nilai[0], list):
        isi = [k[1] for k in nilai if isinstance(k, list) and len(k) >= 2]
        return len({json.dumps(x, sort_keys=True) for x in isi}) > 1
    if isinstance(nilai[0], (int, float)) and isinstance(nilai[1], (int, float)):
        return nilai[0] != nilai[1]
    return False


def _hitung_animasi(objek: Mapping) -> int:
    return sum(1 for k, v in objek.items() if k not in ("jenis", "teks", "kata") and _beranimasi(v))


def _rerata(nilai: list[float]) -> float:
    return round(statistics.fmean(nilai), 3) if nilai else 0.0


def _durasi_total(spek: Mapping, shot: list[dict]) -> float | None:
    tengah = (spek.get("cerita") or {}).get("tengah")
    if isinstance(tengah, list) and tengah:
        akhir = [x.get("t1") for x in tengah if isinstance(x, Mapping) and isinstance(x.get("t1"), (int, float))]
        if akhir:
            return float(max(akhir))
    if isinstance(spek.get("durasi"), (int, float)):
        return float(spek["durasi"])
    return None


def _kata_berwaktu(spek: Mapping, folder: Path | None) -> list[tuple[float, str]]:
    """Kata narasi bertimestamp dari cerita.tengah, atau dari berkas `waktu` (.waktu.json) bila ada."""
    tengah = (spek.get("cerita") or {}).get("tengah")
    if isinstance(tengah, list) and tengah:
        return [(float(k[0]), str(k[1])) for x in tengah if isinstance(x, Mapping)
                for k in (x.get("kata") or []) if isinstance(k, list) and len(k) >= 2]
    if folder is not None and isinstance(spek.get("waktu"), str):
        berkas = (folder / spek["waktu"]).resolve()
        if berkas.is_file():
            data = json.loads(berkas.read_text(encoding="utf-8"))
            return [(float(k["t0"]), str(k["teks"])) for k in data.get("kata", [])
                    if isinstance(k, Mapping) and "t0" in k and "teks" in k]
    return []


def _narasi_per_shot(spek: Mapping, shot: list[Mapping], folder: Path | None = None) -> list[str] | None:
    """Teks narasi tiap shot: dari rencana_cerita (hasil mesin) atau kata bertimestamp (referensi)."""
    rencana = spek.get("rencana_cerita")
    if isinstance(rencana, Mapping) and isinstance(rencana.get("adegan"), list):
        teks = {a.get("id"): a.get("teks", "") for a in rencana["adegan"] if isinstance(a, Mapping)}
        urut = [a.get("teks", "") for a in rencana["adegan"] if isinstance(a, Mapping)]
        hasil = []
        for s in shot:
            if s.get("_beat_id") in teks:
                hasil.append(teks[s["_beat_id"]])
            elif isinstance(s.get("_adegan"), int) and 0 <= s["_adegan"] < len(urut):
                hasil.append(urut[s["_adegan"]])
            else:
                hasil.append("")
        return hasil
    kata = _kata_berwaktu(spek, folder)
    if not kata:
        return None
    mulai = [float(s.get("at", 0)) for s in shot]
    batas = mulai[1:] + [float("inf")]
    return [" ".join(w for t, w in kata if a <= t < b) for a, b in zip(mulai, batas)]


def _wujud_ada(wujud: str, s: Mapping) -> bool:
    if wujud.startswith("env:"):
        return bool(s.get(wujud[4:]))
    if wujud.startswith("boneka>="):
        return len(s.get("boneka") or []) >= int(wujud[8:])
    if wujud.startswith("boneka:"):
        return any(isinstance(b, Mapping) and b.get(wujud[7:]) for b in (s.get("boneka") or []))
    return any(isinstance(b, Mapping) and b.get("jenis") == wujud for b in (s.get("benda") or []))


def _kesesuaian_narasi(
    spek: Mapping, shot: list[Mapping], folder: Path | None = None
) -> tuple[float | None, list[dict]]:
    """Rerata, per shot, porsi benda yang disebut narasi dan benar-benar tergambar di shot itu.

    Hanya shot yang narasinya menyebut kata di LEKSIKON yang dinilai. "Kapal berlayar di
    tengah ombak" dengan ombak tetapi tanpa kapal bernilai 0,5, bukan lolos. Mengembalikan
    (nilai, rincian per shot) supaya kesenjangan bisa ditunjuk satu per satu.
    """
    narasi = _narasi_per_shot(spek, shot, folder)
    if narasi is None:
        return None, []
    rincian, nilai = [], []
    for i, (s, teks) in enumerate(zip(shot, narasi)):
        kecil = teks.lower()
        disebut = [(pola, wujud) for pola, wujud in LEKSIKON if re.search(pola, kecil)]
        if not disebut:
            continue
        nama = lambda pola: re.sub(r"\\b|[()]", "", pola)  # noqa: E731
        tergambar = [nama(pola) for pola, wujud in disebut if any(_wujud_ada(w, s) for w in wujud)]
        nilai.append(len(tergambar) / len(disebut))
        rincian.append({
            "shot": i, "narasi": teks[:80],
            "tergambar": tergambar,
            "tidak_tergambar": [nama(p) for p, _ in disebut if nama(p) not in tergambar],
        })
    return (round(statistics.fmean(nilai), 3) if nilai else None), rincian


def ukur(spek: Mapping, folder: Path | None = None) -> dict[str, Any]:
    """Ukur satu spek papan. `folder` = lokasi berkas spek (untuk membaca berkas `waktu`)."""
    cerita = spek.get("cerita") if isinstance(spek, Mapping) else None
    shot = cerita.get("shot") if isinstance(cerita, Mapping) else None
    if not isinstance(shot, list) or not shot:
        raise ValueError("Spek tidak memiliki cerita.shot yang bisa diukur")
    shot = [s for s in shot if isinstance(s, Mapping)]
    n = len(shot)

    mulai = sorted(float(s["at"]) for s in shot if isinstance(s.get("at"), (int, float)))
    total = _durasi_total(spek, shot)
    if total is None:
        kata_waktu = _kata_berwaktu(spek, folder)
        total = round(kata_waktu[-1][0] + 0.5, 2) if kata_waktu else None
    jeda = [b - a for a, b in zip(mulai, mulai[1:])]
    if total and mulai:
        jeda.append(max(0.0, total - mulai[-1]))

    kamera_gerak, aksen = 0, 0
    for s in shot:
        kam = s.get("kamera") if isinstance(s.get("kamera"), Mapping) else {}
        if any(_beranimasi(kam.get(k)) for k in ("x", "y", "z")):
            kamera_gerak += 1
        aksen += len(kam.get("hentak") or []) + len(kam.get("guncang") or [])

    lingkungan_per_shot = [sum(1 for k in KUNCI_LINGKUNGAN if k in s) for s in shot]
    suasana = {
        json.dumps({k: s.get(k) for k in ("palet", "malam", "langit", "ruang") if k in s}, sort_keys=True)
        for s in shot
    }

    semua_benda = [b for s in shot for b in (s.get("benda") or []) if isinstance(b, Mapping)]
    jenis_benda = {b.get("jenis") for b in semua_benda if b.get("jenis")}
    benda_animasi = sum(1 for b in semua_benda if _hitung_animasi(b))
    # Hiasan latar umum di lapis depan (batu kabur di sudut) tidak dihitung: kedalaman harus
    # datang dari benda cerita, bukan resep yang ditempel di setiap shot.
    benda_lapis = sum(1 for b in semua_benda if any(b.get(k) for k in KUNCI_LAPIS)
                      and not (b.get("jenis") in LATAR_UMUM and b.get("depan")))

    semua_boneka = [b for s in shot for b in (s.get("boneka") or []) if isinstance(b, Mapping)]
    boneka_ekspresif = sum(1 for b in semua_boneka if any(k in b for k in KUNCI_EKSPRESI_TOKOH))
    boneka_gerak = sum(1 for b in semua_boneka if _hitung_animasi(b))

    teks_layar = [len(s.get("teks") or []) for s in shot]
    gerak = [
        sum(_hitung_animasi(o) for o in list(s.get("benda") or []) + list(s.get("boneka") or []) if isinstance(o, Mapping))
        + (_hitung_animasi(s["kamera"]) if isinstance(s.get("kamera"), Mapping) else 0)
        for s in shot
    ]

    jenis_cerita_per_shot = [
        frozenset(b.get("jenis") for b in (s.get("benda") or [])
                  if isinstance(b, Mapping) and b.get("jenis") and b.get("jenis") not in LATAR_UMUM)
        for s in shot
    ]
    ragam_cerita = set().union(*jenis_cerita_per_shot) if jenis_cerita_per_shot else set()
    # Komposisi = himpunan semua jenis benda + jumlah boneka; dihitung berapa yang berbeda.
    komposisi = {
        (frozenset(b.get("jenis") for b in (s.get("benda") or []) if isinstance(b, Mapping)),
         len(s.get("boneka") or []))
        for s in shot
    }

    kesesuaian, rincian_kesesuaian = _kesesuaian_narasi(spek, shot, folder)

    porsi = lambda a, b: round(a / b, 3) if b else 0.0  # noqa: E731
    return {
        "_rincian_kesesuaian": rincian_kesesuaian,
        "ritme": {"jumlah_shot": n, "rerata_durasi_shot": _rerata(jeda), "durasi_total": total},
        "kamera": {"porsi_kamera_bergerak": porsi(kamera_gerak, n), "aksen_per_shot": porsi(aksen, n)},
        "lingkungan": {
            "rerata_elemen_per_shot": _rerata(lingkungan_per_shot),
            "ragam_suasana": len(suasana),
        },
        "benda": {
            "rerata_per_shot": porsi(len(semua_benda), n),
            "ragam_jenis": len(jenis_benda),
            "porsi_beranimasi": porsi(benda_animasi, len(semua_benda)),
            "porsi_berlapis": porsi(benda_lapis, len(semua_benda)),
        },
        "tokoh": {
            "rerata_per_shot": porsi(len(semua_boneka), n),
            "porsi_ekspresif": porsi(boneka_ekspresif, len(semua_boneka)),
            "porsi_bergerak": porsi(boneka_gerak, len(semua_boneka)),
        },
        "teks_layar": {"rerata_per_shot": _rerata(teks_layar)},
        "gerak": {"rerata_properti_animasi_per_shot": _rerata(gerak)},
        "cerita": {
            "kesesuaian_narasi": kesesuaian,
            "ragam_jenis_pelaku": len(ragam_cerita),
            "keragaman_komposisi": porsi(len(komposisi), n),
        },
    }


# Metrik yang dipakai untuk skor tiap aspek (dibanding nilai referensi).
# Durasi shot tidak diskor karena ritme yang baik bisa cepat atau lambat.
_METRIK_SKOR = {
    "ritme": ("jumlah_shot",),
    "kamera": ("porsi_kamera_bergerak", "aksen_per_shot"),
    "lingkungan": ("rerata_elemen_per_shot", "ragam_suasana"),
    "benda": ("rerata_per_shot", "ragam_jenis", "porsi_beranimasi", "porsi_berlapis"),
    "tokoh": ("rerata_per_shot", "porsi_ekspresif", "porsi_bergerak"),
    "teks_layar": ("rerata_per_shot",),
    "gerak": ("rerata_properti_animasi_per_shot",),
    "cerita": ("kesesuaian_narasi", "ragam_jenis_pelaku", "keragaman_komposisi"),
}


def muat_referensi(nama: tuple[str, ...] = REFERENSI, folder: Path = FOLDER_REFERENSI) -> dict[str, dict]:
    return {k: ukur(json.loads((folder / f"{k}.json").read_text(encoding="utf-8")), folder) for k in nama}


def patokan(referensi: Mapping[str, Mapping]) -> dict[str, dict[str, float]]:
    """Nilai patokan per metrik: median referensi (tahan pencilan, mis. Mahsyar tanpa benda)."""
    hasil: dict[str, dict[str, float]] = {}
    for aspek, daftar in _METRIK_SKOR.items():
        hasil[aspek] = {}
        for m in daftar:
            nilai = [float(r[aspek][m]) for r in referensi.values() if r[aspek][m] is not None]
            hasil[aspek][m] = round(statistics.median(nilai), 3) if nilai else 0.0
    return hasil


def bandingkan(metrik: Mapping, patok: Mapping) -> dict[str, Any]:
    """Skor 0-100 per aspek = rerata rasio metrik/patokan (dibatasi 1). Skor gabungan berbobot."""
    skor_aspek = {}
    for aspek, daftar in _METRIK_SKOR.items():
        rasio = []
        for m in daftar:
            acuan = patok[aspek][m]
            if acuan <= 0 or metrik[aspek][m] is None:
                continue  # referensi tidak memakai metrik ini / narasi tidak tersedia
            rasio.append(min(1.0, float(metrik[aspek][m]) / acuan))
        skor_aspek[aspek] = round(100 * statistics.fmean(rasio)) if rasio else 100
    total_bobot = sum(BOBOT.values())
    gabungan = round(sum(skor_aspek[a] * BOBOT[a] for a in skor_aspek) / total_bobot)
    return {"skor_aspek": skor_aspek, "skor_gabungan": gabungan}


def laporan(spek: Mapping, referensi: Mapping[str, Mapping] | None = None) -> dict[str, Any]:
    referensi = referensi if referensi is not None else muat_referensi()
    patok = patokan(referensi)
    metrik = ukur(spek)
    return {"metrik": metrik, "patokan": patok, **bandingkan(metrik, patok)}


def teks_laporan(hasil: Mapping) -> str:
    baris = [f"Skor kedalaman gabungan: {hasil['skor_gabungan']}/100 (100 = setara median referensi)"]
    for aspek, skor in hasil["skor_aspek"].items():
        rinci = ", ".join(
            f"{m}={hasil['metrik'][aspek][m]} (patokan {hasil['patokan'][aspek][m]})"
            for m in _METRIK_SKOR[aspek]
        )
        baris.append(f"  {aspek:11} {skor:3}  {rinci}")
    return "\n".join(baris)


# ---------------- tolok ukur: pengarah dijalankan pada naskah keempat referensi ----------------
FOLDER_TOLOK_UKUR = AKAR / "tests" / "data" / "tolok_ukur"


def tolok_ukur(folder: Path = FOLDER_TOLOK_UKUR) -> dict[str, dict]:
    """Arahkan naskah tiap referensi dengan pengarah sekarang, lalu ukur hasilnya.

    Masukan dibekukan di tests/data/tolok_ukur/ (narasi asli keempat video). Hasilnya
    menunjukkan seberapa jauh pengarah otomatis dari papan buatan tangan untuk cerita yang sama.
    """
    from newmotion.application.pengarah_inti import arahkan_naskah

    referensi = muat_referensi()
    patok = patokan(referensi)
    hasil = {}
    for berkas in sorted(folder.glob("*.json")):
        naskah = json.loads(berkas.read_text(encoding="utf-8"))
        spek, _, _ = arahkan_naskah(naskah)
        metrik = ukur(spek)
        hasil[berkas.stem] = {
            "metrik": metrik, "patokan": patok, **bandingkan(metrik, patok),
            "skor_referensi": bandingkan(referensi[berkas.stem], patok)["skor_gabungan"]
            if berkas.stem in referensi else None,
        }
    return hasil


def teks_tolok_ukur(hasil: Mapping[str, Mapping]) -> str:
    aspek = list(BOBOT)
    kepala = f"{'cerita':10} {'mesin':>5} {'ref':>4}  " + " ".join(f"{a[:7]:>7}" for a in aspek)
    baris = [kepala]
    for nama, h in hasil.items():
        baris.append(
            f"{nama:10} {h['skor_gabungan']:>5} {h['skor_referensi'] or '-':>4}  "
            + " ".join(f"{h['skor_aspek'][a]:>7}" for a in aspek)
        )
    baris.append("\nShot yang narasinya menyebut benda tetapi tidak menggambarkannya:")
    for nama, h in hasil.items():
        for r in h["metrik"]["_rincian_kesesuaian"]:
            if r["tidak_tergambar"]:
                baris.append(f"  {nama} shot {r['shot']}: {', '.join(r['tidak_tergambar'])} — \"{r['narasi'][:60]}\"")
    return "\n".join(baris)


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Ukur kedalaman spek papan dibanding Nuh 1, Mahsyar 1, Ya'juj 1-2")
    parser.add_argument("spek", nargs="*", help="Berkas spek papan JSON; kosongkan untuk tolok ukur")
    parser.add_argument("--json", action="store_true", help="Cetak hasil sebagai JSON")
    args = parser.parse_args(argv)
    if not args.spek:
        hasil = tolok_ukur()
        print(json.dumps(hasil, ensure_ascii=False, indent=1) if args.json else teks_tolok_ukur(hasil))
        return 0
    referensi = muat_referensi()
    for jalur in args.spek:
        berkas = Path(jalur)
        h = laporan_berkas(berkas, referensi)
        print(json.dumps(h, ensure_ascii=False, indent=1) if args.json else f"== {berkas}\n{teks_laporan(h)}")
    return 0


def laporan_berkas(berkas: Path, referensi: Mapping[str, Mapping] | None = None) -> dict[str, Any]:
    referensi = referensi if referensi is not None else muat_referensi()
    patok = patokan(referensi)
    metrik = ukur(json.loads(berkas.read_text(encoding="utf-8")), berkas.resolve().parent)
    return {"metrik": metrik, "patokan": patok, **bandingkan(metrik, patok)}


if __name__ == "__main__":
    raise SystemExit(main())
