"""Penerbit PR komponen-draf terpisah dari gpt/integrasi."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from newmotion.application.kebutuhan_renderer import tandai_draf

AKAR = Path(__file__).resolve().parents[2]


def jalankan(perintah: list[str], *, cwd: Path = AKAR) -> str:
    hasil = subprocess.run(perintah, cwd=cwd, capture_output=True, text=True, check=False)
    if hasil.returncode:
        raise RuntimeError(f"{' '.join(perintah)} gagal: {(hasil.stderr or hasil.stdout).strip()}")
    return hasil.stdout.strip()


def sisipkan_cabang(sumber: str, codigo: str, nome: str) -> str:
    if f'j === "{nome}"' in sumber:
        raise ValueError(f"{nome} sudah ada di cerita.js")
    inicio = sumber.find("function benda(o, t, d)")
    fim = sumber.find("// ---- TITIK KAIT", inicio)
    if inicio < 0 or fim < 0:
        raise ValueError("fungsi benda() atau batas TITIK KAIT tidak ditemukan")
    pos = sumber[inicio:fim].rfind("    return ")
    if pos < 1:
        raise ValueError("return akhir fungsi benda() tidak ditemukan")
    absolute = inicio + pos
    if sumber[absolute - 1] != "\n":
        raise ValueError("format return akhir fungsi benda() berubah")
    cabang = " " + codigo.strip() + "\n"
    return sumber[:absolute - 1] + cabang + sumber[absolute:]


def terbitkan(data: dict, *, akar: Path = AKAR) -> str:
    nama = data["nama"]
    if jalankan(["git", "branch", "--show-current"], cwd=akar) != "gpt/integrasi":
        raise RuntimeError("penerbit hanya boleh dijalankan dari gpt/integrasi")
    if jalankan(["git", "status", "--porcelain"], cwd=akar):
        raise RuntimeError("working tree harus bersih")
    cabang = "komponen-draf-" + nama
    jalankan(["git", "switch", "-c", cabang], cwd=akar)
    cerita = akar / "mesin-video" / "papan" / "cerita.js"
    sumber = cerita.read_text(encoding="utf-8")
    cerita.write_text(sisipkan_cabang(sumber, data["kode"], nama), encoding="utf-8")
    folder = akar / "hasil" / "komponen-draf"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "komponen_draf.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    tandai_draf(data, jalur=akar / "newmotion" / "application" / "data" / "kebutuhan_renderer.json")
    jalankan([
        "git", "add", "mesin-video/papan/cerita.js",
        "hasil/komponen-draf/komponen_draf.json",
        "newmotion/application/data/kebutuhan_renderer.json",
    ], cwd=akar)
    jalankan(["git", "commit", "-m", "Draf komponen renderer: " + nama], cwd=akar)
    jalankan(["git", "push", "-u", "origin", cabang], cwd=akar)
    jalankan([
        "gh", "label", "create", "komponen-draf", "--color", "D4A72C",
        "--description", "Draf komponen renderer; wajib ditinjau manusia", "--force",
    ], cwd=akar)
    return jalankan([
        "gh", "pr", "create", "--base", "gpt/integrasi", "--head", cabang,
        "--title", "Draf komponen renderer: " + nama, "--label", "komponen-draf",
        "--body",
        "STATUS: DRAF — JANGAN MERGE OTOMATIS\n"
        + "Kebutuhan: " + nama + "\n"
        + "Alasan: " + data["alasan"] + "\n"
        + "Bukti narasi: " + data["bukti_narasi"] + "\n"
        + "Parameter: " + data["parameter"] + "\n"
        + "Bukti render penuh/seperempat dan laporan CI dilampirkan otomatis.\n"
        + "Wajib ditinjau manusia untuk bentuk, adab, ukuran, dan kesesuaian kisah.",
    ], cwd=akar)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Terbitkan satu PR komponen-draf")
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    print(terbitkan(json.loads(args.manifest.read_text(encoding="utf-8"))))
