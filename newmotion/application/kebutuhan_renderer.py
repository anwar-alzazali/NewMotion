"""Antrean kebutuhan visual yang belum dapat digambar renderer."""
from __future__ import annotations

import argparse
import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from newmotion.application.katalog_renderer import katalog_subjek

AKAR = Path(__file__).resolve().parents[2]
BERKAS = AKAR / "newmotion" / "application" / "data" / "kebutuhan_renderer.json"
STATUS = ("menunggu", "dibuat")


def normalisasi(nama: str) -> str:
    teks = unicodedata.normalize("NFKC", nama).casefold().strip()
    teks = re.sub(r"[^a-z0-9]+", "_", teks, flags=re.ASCII).strip("_")
    return teks


def validasi_kebutuhan(data: Any, *, katalog: dict | None = None, label: str = "belum_ada") -> list[str]:
    if data is None:
        return []
    if not isinstance(data, list):
        return [f"{label} harus berupa daftar"]
    tersedia = katalog if katalog is not None else katalog_subjek()
    galat = []
    for i, item in enumerate(data, 1):
        awalan = f"{label}[{i}]"
        if not isinstance(item, dict):
            galat.append(f"{awalan} harus objek")
            continue
        nama, alasan, bukti = (item.get(k) for k in ("nama", "alasan", "bukti"))
        if not isinstance(nama, str) or not nama.strip():
            galat.append(f"{awalan}.nama wajib diisi")
        elif normalisasi(nama) in {normalisasi(x) for x in tersedia}:
            galat.append(f"{awalan}: {nama!r} sudah ada di katalog renderer")
        if not isinstance(alasan, str) or not alasan.strip():
            galat.append(f"{awalan}.alasan wajib diisi")
        if not isinstance(bukti, str) or not bukti.strip():
            galat.append(f"{awalan}.bukti wajib diisi")
    return galat


def _baca(jalur: Path) -> dict:
    if not jalur.is_file():
        return {"versi": 1, "kebutuhan": {}}
    data = json.loads(jalur.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("kebutuhan"), dict):
        raise ValueError(f"Format antrean kebutuhan renderer rusak: {jalur}")
    return data


def catat(data: Any, *, sumber: str, kisah: str, jalur: Path | None = None) -> dict:
    """Gabungkan kebutuhan dari rencana atau pemeriksa visual ke satu antrean."""
    tujuan = jalur or BERKAS
    antrean = _baca(tujuan)
    if sumber not in ("sutradara", "pemeriksa"):
        raise ValueError("sumber harus sutradara atau pemeriksa")
    daftar = data if isinstance(data, list) else []
    sekarang = datetime.now(timezone.utc).isoformat()
    for item in daftar:
        if not isinstance(item, dict):
            continue
        nama = str(item.get("nama", "")).strip()
        kunci = normalisasi(nama)
        if not kunci:
            continue
        entri = antrean["kebutuhan"].setdefault(kunci, {
            "nama": nama, "jumlah": 0, "contoh": [], "sumber": [],
            "status": "menunggu",
        })
        entri["jumlah"] += 1
        if sumber not in entri["sumber"]:
            entri["sumber"].append(sumber)
        contoh = {
            "kisah": str(kisah or "tanpa_judul"),
            "beat": item.get("beat"),
            "alasan": str(item.get("alasan") or item.get("masalah") or ""),
            "bukti": str(item.get("bukti") or ""),
            "dicatat": sekarang,
        }
        if contoh not in entri["contoh"]:
            entri["contoh"].append(contoh)
            entri["contoh"] = entri["contoh"][-20:]
        if len(nama) > len(entri["nama"]):
            entri["nama"] = nama
    tujuan.parent.mkdir(parents=True, exist_ok=True)
    tujuan.write_text(json.dumps(antrean, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return antrean


def dari_rencana(rencana: dict) -> list[dict]:
    hasil = []
    for item in rencana.get("belum_ada", []) if isinstance(rencana, dict) else []:
        if isinstance(item, dict):
            hasil.append(dict(item))
    for beat in rencana.get("beat", []) if isinstance(rencana, dict) else []:
        if not isinstance(beat, dict):
            continue
        for item in beat.get("belum_ada", []) if isinstance(beat.get("belum_ada", []), list) else []:
            if isinstance(item, dict):
                hasil.append(dict(item) | {"beat": beat.get("beat")})
    return hasil


def dari_temuan(temuan: dict) -> list[dict]:
    hasil = []
    for item in temuan.get("temuan", []) if isinstance(temuan, dict) else []:
        if not isinstance(item, dict):
            continue
        kebutuhan = item.get("kebutuhan") or item.get("objek_belum_ada")
        if isinstance(kebutuhan, str):
            kebutuhan = {"nama": kebutuhan, "alasan": item.get("masalah", ""),
                         "bukti": item.get("bukti", ""), "beat": item.get("beat")}
        if isinstance(kebutuhan, dict):
            hasil.append(dict(kebutuhan) | {"beat": item.get("beat")})
    return hasil


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Daftar kebutuhan visual renderer yang belum tersedia")
    parser.add_argument("--jumlah", type=int, default=20)
    parser.add_argument("--status", choices=STATUS)
    args = parser.parse_args(argv)
    data = _baca(BERKAS)["kebutuhan"]
    daftar = sorted(data.values(), key=lambda x: (-x.get("jumlah", 0), x.get("nama", "").casefold()))
    if args.status:
        daftar = [x for x in daftar if x.get("status") == args.status]
    for i, item in enumerate(daftar[:max(0, args.jumlah)], 1):
        print(f"{i}. {item['nama']} — {item['jumlah']} kemunculan [{item['status']}]")
        for contoh in item.get("contoh", [])[-2:]:
            print(f"   {contoh.get('kisah')} / beat {contoh.get('beat')}: {contoh.get('alasan')}")
    if not daftar:
        print("Belum ada kebutuhan renderer yang tercatat.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
