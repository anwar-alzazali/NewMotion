"""Pembuat draf cabang benda renderer dari satu kebutuhan visual."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from newmotion.application.katalog_renderer import katalog
from newmotion.infrastructure.llm import panggil

AKAR = Path(__file__).resolve().parents[2]
SKILL = AKAR / "newmotion" / "paket_genre" / "kisah_islami" / "skill" / "pembuat_komponen.md"
DRAF = AKAR / "hasil" / "komponen-draf"
POLA_NAMA = re.compile(r"^[a-z][a-z0-9_]{1,47}$")
POLA_CABANG = re.compile(r'else\s+if\s*\(\s*j\s*===\s*["\']([a-z][a-z0-9_]*)["\']\s*\)\s*\{')
KUNCI_DILARANG = (
    "fetch(", "XMLHttpRequest", "data:image/", "<image", "http://", "https://",
    "Allah", "Muhammad", "rasul", "nabi", "م",
)


class GalatKomponen(ValueError):
    """Draf tidak memenuhi kontrak renderer/adab."""


def validasi_draf(data: Any, nama: str, *, daftar: dict | None = None) -> list[str]:
    tersedia = daftar if daftar is not None else katalog()
    galat: list[str] = []
    if not POLA_NAMA.fullmatch(nama):
        galat.append("nama kebutuhan harus snake_case ASCII")
    if nama in tersedia:
        galat.append(f"{nama} sudah ada di katalog renderer")
    if not isinstance(data, dict):
        return galat + ["keluaran LLM harus berupa objek JSON"]
    kode = data.get("kode")
    if not isinstance(kode, str) or not kode.strip():
        return galat + ["kode cabang wajib berupa teks"]
    cocok = list(POLA_CABANG.finditer(kode))
    if len(cocok) != 1:
        galat.append("kode harus berisi tepat satu cabang else if untuk satu benda")
    elif cocok[0].group(1) != nama:
        galat.append("nama pada kondisi JavaScript tidak sama dengan nama kebutuhan")
    if not re.search(r"//[^\n]{5,}", kode):
        galat.append("cabang wajib memiliki komentar keterangan yang menjelaskan benda")
    parameter = data.get("parameter")
    if not isinstance(parameter, str) or not re.fullmatch(r"[a-z][a-z0-9_]*", parameter):
        galat.append("parameter animasi utama wajib snake_case")
    elif not re.search(rf"\bv\(\s*o\.{re.escape(parameter)}\s*,\s*t\s*,\s*d\s*,", kode):
        galat.append("parameter utama harus dibaca lewat v(o.parameter, t, d, bawaan)")
    elif not re.search(rf"o\.{re.escape(parameter)}", kode):
        galat.append("parameter utama tidak digunakan untuk menggambar")
    if "INK" not in kode:
        galat.append("cabang harus memakai garis tinta INK")
    if not re.search(r"g\s*\+?=", kode):
        galat.append("cabang harus menggambar bentuk SVG ke variabel g")
    if any(x.casefold() in kode.casefold() for x in KUNCI_DILARANG):
        galat.append("kode mengandung gambar eksternal, jaringan, atau rujukan tokoh yang dilarang")
    if re.search(r"<text\b", kode, re.I):
        galat.append("komponen tidak boleh menanam teks di dalam gambar")
    if "function " in kode or "return " in kode:
        galat.append("jangan mendeklarasikan fungsi atau return di dalam cabang")
    return galat


def buat_draf(nama: str, alasan: str, bukti: str, *, http=None) -> dict:
    """Minta satu cabang baru dan tolak keluaran yang tak memenuhi kontrak."""
    if nama in katalog():
        raise GalatKomponen(f"{nama} sudah ada di katalog renderer")
    if not POLA_NAMA.fullmatch(nama):
        raise GalatKomponen("nama kebutuhan harus snake_case ASCII")
    if not alasan.strip() or not bukti.strip():
        raise GalatKomponen("alasan dan bukti narasi wajib diisi")
    pemanggil = panggil if http is None else lambda *a, **k: panggil(*a, http=http, **k)
    jawaban = pemanggil(
        "komponen_renderer",
        SKILL.read_text(encoding="utf-8"),
        json.dumps({"nama": nama, "alasan": alasan, "bukti_narasi": bukti,
                    "katalog_ada": sorted(katalog())}, ensure_ascii=False),
        json=True,
        maks_token=5000,
        validasi=lambda data: validasi_draf(data, nama),
    )
    hasil = dict(jawaban.data)
    hasil.update({
        "nama": nama,
        "alasan": alasan,
        "bukti_narasi": bukti,
        "model": jawaban.model,
        "penyedia": jawaban.penyedia,
        "token_masuk": jawaban.token_masuk,
        "token_keluar": jawaban.token_keluar,
        "biaya_usd": jawaban.biaya_usd,
        "status": "draf_kode_belum_diverifikasi",
    })
    return hasil


def simpan_draf(data: dict, tujuan: Path | None = None) -> Path:
    """Simpan kode dan manifest sebagai bahan kerja; tidak mengubah cerita.js."""
    nama = data["nama"]
    if validasi_draf(data, nama):
        raise GalatKomponen("; ".join(validasi_draf(data, nama)))
    folder = tujuan or DRAF
    folder.mkdir(parents=True, exist_ok=True)
    jalur = folder / f"{nama}.json"
    if jalur.exists():
        raise FileExistsError(f"draf {nama} sudah ada: {jalur}")
    jalur.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return jalur


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Buat draf kode komponen renderer dari kebutuhan visual")
    parser.add_argument("--nama", required=True, help="nama kebutuhan dalam snake_case")
    parser.add_argument("--alasan", required=True, help="mengapa komponen diperlukan")
    parser.add_argument("--bukti", required=True, help="potongan persis narasi yang membutuhkan komponen")
    parser.add_argument("--buat-pr", action="store_true", help="buat branch dan PR komponen-draf terpisah")
    args = parser.parse_args(argv)
    hasil = buat_draf(args.nama, args.alasan, args.bukti)
    jalur = simpan_draf(hasil)
    print(f"Draf tersimpan: {jalur.relative_to(AKAR)}")
    if args.buat_pr:
        from newmotion.application.penerbit_komponen import terbitkan
        print(f"PR draf dibuat: {terbitkan(hasil)}")
    else:
        print("Belum menjadi PR; tambahkan --buat-pr untuk menerbitkan draf terpisah.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
