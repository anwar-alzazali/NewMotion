"""Sutradara LLM Kisah Islami: naskah -> rencana sutradara (LLM) -> papan JSON (mesin).

    python -m newmotion.paket_genre.kisah_islami.sutradara_llm naskah.json -o hasil/x
    python -m newmotion.paket_genre.kisah_islami.sutradara_llm naskah.json -o hasil/x --rencana r.json

Model diambil dari tahap "sutradara" di config/model.toml (timpa: NEWMOTION_MODEL_SUTRADARA).
Rencana yang ditolak validator (katalog, bukti teks, format) atau penjaga adab membuat
model berikutnya dicoba dengan daftar galatnya. Bila semua gagal, tidak ada papan yang
dibuat dari rencana; pemanggil boleh kembali ke pengarah aturan.
"""
from __future__ import annotations

import argparse
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from newmotion.application.katalog_renderer import teks_katalog
from newmotion.application.katalog_suara import teks_katalog_suara
from newmotion.application.kemampuan_tokoh import teks_kemampuan_tokoh

from .rencana_sutradara import terapkan_rencana, validasi_rencana

SKILL = Path(__file__).resolve().parent / "skill" / "sutradara.md"
MAKS_KARTU_DALIL = 2


def skill_sutradara() -> str:
    return (SKILL.read_text(encoding="utf-8").replace("{KATALOG}", teks_katalog())
            .replace("{KATALOG_SUARA}", teks_katalog_suara()).replace("{KEMAMPUAN_TOKOH}", teks_kemampuan_tokoh()))


def _narasi(naskah: Mapping) -> list[str]:
    adegan = naskah.get("adegan")
    if isinstance(adegan, list) and adegan:
        return [str(a.get("teks", "")) for a in adegan]
    return [str(b.get("narasi", "")) for b in naskah.get("beat", [])]


def dalil_per_beat(naskah: Mapping) -> dict[int, str]:
    """Nomor beat -> label dalil terverifikasi yang dirujuk beat itu (untuk keputusan kartu_dalil)."""
    nama = {str(a.get("nama")): i for i, a in enumerate(naskah.get("adegan") or [], 1)}
    keluar: dict[int, str] = {}
    for d in naskah.get("dalil_dipakai") or []:
        n = nama.get(str(d.get("di_adegan")))
        if n and n not in keluar:
            keluar[n] = d.get("label") or f"QS {d.get('surah')}:{d.get('ayat')}"
    return keluar


def pesan_sutradara(naskah: Mapping) -> str:
    baris = [f"Judul: {naskah.get('judul', '-')}", "", "Naskah (beat bernomor):"]
    dalil = dalil_per_beat(naskah)
    baris += [f"{i}. {t}" + (f"  [dalil: {dalil[i]}]" if i in dalil else "") for i, t in enumerate(_narasi(naskah), 1)]
    baris += ["", "Tulis rencana sutradara untuk SEMUA beat di atas."]
    return "\n".join(baris)


def validasi_lengkap(rencana: Any, naskah: Mapping) -> list[str]:
    """Validator format + adab pada papan hasil terjemahan rencana."""
    galat = validasi_rencana(rencana, _narasi(naskah))
    if galat:
        return galat
    dalil = dalil_per_beat(naskah)
    kartu = [b.get("beat") for b in rencana.get("beat", []) if b.get("kartu_dalil")]
    if len(kartu) > MAKS_KARTU_DALIL:
        return [f"kartu_dalil paling banyak {MAKS_KARTU_DALIL} per video (dipilih: beat {kartu})"]
    salah = [n for n in kartu if n not in dalil]
    if salah:
        return [f"beat {salah}: kartu_dalil hanya untuk beat yang bertanda [dalil: ...]"]
    from newmotion.application.pengarah_inti import arahkan_naskah

    from .penjaga_tokoh import periksa_adab_tokoh

    try:
        spek, _, _ = arahkan_naskah(terapkan_rencana(dict(naskah), rencana))
    except Exception as e:  # noqa: BLE001 - galat terjemahan dilaporkan ke model berikutnya
        return [f"rencana tidak bisa diterjemahkan: {str(e)[:160]}"]
    return [f"adab: {t}" for t in periksa_adab_tokoh(spek)]


def buat_rencana(naskah: Mapping, *, http=None):
    from newmotion.infrastructure import llm

    opsi = {"http": http} if http else {}
    return llm.panggil("sutradara", skill_sutradara(), pesan_sutradara(naskah), json=True, maks_token=12000,
                       validasi=lambda r: validasi_lengkap(r, naskah), **opsi)


def main(argv=None) -> int:
    from newmotion.application import ukur_kedalaman as U
    from newmotion.application.pengarah_inti import arahkan_naskah

    ap = argparse.ArgumentParser(description="Naskah -> rencana sutradara LLM -> papan JSON")
    ap.add_argument("naskah")
    ap.add_argument("-o", "--keluaran", required=True)
    ap.add_argument("--rencana", help="pakai rencana yang sudah ada (tanpa memanggil LLM)")
    ap.add_argument("--periksa", type=int, default=0, metavar="N",
                    help="putaran periksa visual (vision) + revisi rencana, maksimal N revisi (0 = mati)")
    args = ap.parse_args(argv)
    out = Path(args.keluaran)
    out.mkdir(parents=True, exist_ok=True)
    naskah = json.loads(Path(args.naskah).read_text(encoding="utf-8"))
    info: dict[str, Any] = {"naskah": args.naskah}
    if args.rencana:
        rencana = json.loads(Path(args.rencana).read_text(encoding="utf-8"))
        galat = validasi_lengkap(rencana, naskah)
        if galat:
            raise SystemExit("rencana ditolak:\n- " + "\n- ".join(galat))
        info["model"] = "berkas"
    else:
        j = buat_rencana(naskah)
        rencana = j.data
        info.update(model=j.model, penyedia=j.penyedia, token_masuk=j.token_masuk,
                    token_keluar=j.token_keluar, biaya_usd=j.biaya_usd, percobaan=j.percobaan)
    from newmotion.application.kebutuhan_renderer import catat, dari_rencana

    catat(dari_rencana(rencana), sumber="sutradara", kisah=naskah.get("judul", args.naskah))
    if args.periksa > 0:
        import shutil

        from .periksa_visual import berputar

        rencana, _, log = berputar(naskah, rencana, out / "periksa", putaran=args.periksa)
        info["periksa"] = [{k: v for k, v in e.items() if k not in ("temuan", "lembar")}
                           | {"lulus": (e.get("temuan") or {}).get("lulus"),
                              "jumlah_temuan": len((e.get("temuan") or {}).get("temuan", []))} for e in log]
        info["biaya_usd"] = round(info.get("biaya_usd", 0) + sum(e.get("biaya_usd", 0) + e.get("biaya_revisi_usd", 0)
                                                                for e in log), 4)
        (out / "periksa.json").write_text(json.dumps(log, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        for i, p in enumerate((log[-1].get("lembar") or []) if log else [], 1):
            shutil.copy(p, out / f"lembar_{i}.jpg")
    spek, _, n = arahkan_naskah(terapkan_rencana(naskah, rencana))
    ukur = U.laporan(spek)
    info.update(shot=n, skor_gabungan=ukur["skor_gabungan"], skor_aspek=ukur["skor_aspek"])
    (out / "rencana.json").write_text(json.dumps(rencana, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (out / "papan.json").write_text(json.dumps(spek, ensure_ascii=False) + "\n", encoding="utf-8")
    (out / "info.json").write_text(json.dumps(info, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(info, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
