"""Jalur manual: papan JSON tulisan tangan (seperti Mahsyar 1) langsung dirender, tanpa LLM.

    python -m newmotion.application.jalur_manual mesin-video/papan/kisah/mahsyar1.json [-o video.mp4] [--kirim]

Tidak ada naskah, sutradara, atau TTS yang dibuat ulang. Yang tetap dijalankan:
- gerbang adab renderer (`jaga_spek` di papan_buat.py: nabi/malaikat/Allah tidak digambar);
- render papan_buat.py, memakai suara/waktu yang dirujuk JSON (bila ada);
- periksa.py (GAGAL teknis menghentikan kiriman; PERIKSA hanya dilaporkan);
- kirim video + lembar kontak ke Telegram bila diminta.

Jalur relatif di JSON (mis. "../../aset/suara/braam.mp3") dibaca dari folder papan kisah,
sehingga JSON kiriman bot (antrean/<id>/papan_manual.json) memakai rujukan yang sama dengan mahsyar1.json.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

AKAR = Path(__file__).resolve().parents[2]
MV = AKAR / "mesin-video"
DASAR_KISAH = MV / "papan" / "kisah"
POLA_SPEK = re.compile(r"(mesin-video/papan/[A-Za-z0-9_/-]+|antrean/[a-z0-9_-]{1,60}/papan_manual)\.json")


def jalur_spek(teks: str) -> Path:
    """Terima hanya jalur di repo yang memang tempat papan; tolak '..' dan jalur mutlak."""
    if not POLA_SPEK.fullmatch(teks) or ".." in teks:
        raise ValueError(f"Jalur papan tidak sah: {teks!r}")
    p = AKAR / teks
    if not p.is_file():
        raise FileNotFoundError(f"Papan tidak ditemukan: {teks}")
    return p


def baca_spek(p: Path) -> dict:
    try:
        spek = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON tidak terbaca: baris {e.lineno}, kolom {e.colno}: {e.msg}") from e
    if not isinstance(spek, dict):
        raise ValueError("Papan harus berupa objek JSON.")  # noqa: TRY004 - pesan untuk pemilik
    shot = (spek.get("cerita") or {}).get("shot") if isinstance(spek.get("cerita"), dict) else None
    if not shot and not spek.get("kartu") and not spek.get("adegan"):
        raise ValueError("Papan kosong: tidak ada cerita.shot, kartu, atau adegan.")
    return spek


def siapkan(p: Path) -> tuple[Path, bool]:
    """Salin papan ke folder kisah (supaya rujukan relatif berlaku). Kembalikan (papan, ada_narasi)."""
    spek = baca_spek(p)
    dasar = p.parent if p.is_relative_to(MV) else DASAR_KISAH
    ada_narasi = bool(spek.get("suara")) and (dasar / spek["suara"]).resolve().is_file()
    if spek.get("suara") and not ada_narasi:
        raise FileNotFoundError(f"Berkas narasi yang dirujuk tidak ada: {spek['suara']}")
    if dasar == p.parent:
        return p, ada_narasi
    salinan = DASAR_KISAH / f".manual-{p.parent.name}.json"
    salinan.write_text(json.dumps(spek, ensure_ascii=False), encoding="utf-8")
    return salinan, ada_narasi


def _env() -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join([str(AKAR), str(MV), env.get("PYTHONPATH", "")]).rstrip(os.pathsep)
    return env


def jalankan(p: Path, video: Path) -> dict:
    """Render + periksa. Mengembalikan ringkasan; 'lulus' False bila ada GAGAL teknis/batas wajib."""
    kerja = video.parent / (video.stem + "_periksa")
    kerja.mkdir(parents=True, exist_ok=True)
    papan, ada_narasi = siapkan(p)
    html = video.with_suffix(".html")
    r = subprocess.run([sys.executable, str(MV / "papan_buat.py"), str(papan), "--html", str(html), "-o", str(video)],
                       cwd=AKAR, env=_env(), capture_output=True, text=True, check=False)
    if r.returncode != 0 or not video.is_file():
        return {"lulus": False, "tahap": "render", "laporan": (r.stderr or r.stdout)[-1500:], "periksa": str(kerja)}
    perintah = [sys.executable, str(MV / "periksa.py"), str(video), "--html", str(html), "--spek", str(papan), "-o", str(kerja)]
    if not ada_narasi:
        perintah.append("--tanpa-audio")
    c = subprocess.run(perintah, cwd=AKAR, env=_env(), capture_output=True, text=True, check=False)
    baris = [b for b in c.stdout.splitlines() if b.startswith(("GAGAL", "PERIKSA"))]
    return {"lulus": c.returncode == 0, "tahap": "periksa", "ada_narasi": ada_narasi,
            "laporan": "\n".join(baris) or "semua butir LOLOS", "periksa": str(kerja)}


# ---------------- Telegram ----------------
def _kirim_berkas(metode: str, medan: str, berkas: Path, nama: str, jenis: str, keterangan: str) -> None:
    token = (os.environ.get("TELEGRAM_BOT_TOKEN") or "").strip()
    chat = (os.environ.get("TELEGRAM_CHAT_ID") or "").strip()
    if not token or not chat:
        raise RuntimeError("TELEGRAM_BOT_TOKEN atau TELEGRAM_CHAT_ID belum tersedia.")
    batas = "----NewMotionManual"
    tubuh = bytearray()
    for k, v in (("chat_id", chat), ("caption", keterangan[:1000])):
        tubuh += f"--{batas}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode()
    tubuh += (f"--{batas}\r\nContent-Disposition: form-data; name=\"{medan}\"; filename=\"{nama}\"\r\n"
              f"Content-Type: {jenis}\r\n\r\n").encode() + berkas.read_bytes() + f"\r\n--{batas}--\r\n".encode()
    req = urllib.request.Request(f"https://api.telegram.org/bot{token}/{metode}", data=bytes(tubuh),
                                 headers={"Content-Type": f"multipart/form-data; boundary={batas}"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            if not json.load(resp).get("ok"):
                raise RuntimeError(f"Telegram {metode} gagal")
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Telegram {metode} HTTP {e.code}: {e.read().decode(errors='replace')[:200]}") from e


def kirim_pesan(teks: str) -> None:
    token = (os.environ.get("TELEGRAM_BOT_TOKEN") or "").strip()
    chat = (os.environ.get("TELEGRAM_CHAT_ID") or "").strip()
    if token and chat:
        data = json.dumps({"chat_id": chat, "text": teks[:4000]}).encode()
        urllib.request.urlopen(urllib.request.Request(f"https://api.telegram.org/bot{token}/sendMessage", data=data,
                                                      headers={"Content-Type": "application/json"}), timeout=30)


def kirim(nama: str, video: Path, hasil: dict) -> None:
    lembar = Path(hasil["periksa"]) / "lembar.jpg"
    if lembar.is_file():
        _kirim_berkas("sendPhoto", "photo", lembar, "lembar.jpg", "image/jpeg", f"Lembar kontak — {nama}")
    if video.stat().st_size > 49 * 1024 * 1024:
        kirim_pesan(f"🎞️ {nama}: video >49 MB, ambil dari artefak GitHub Actions.\n\n{hasil['laporan']}")
        return
    tanda = "🎞️" if hasil["lulus"] else "⚠️ ADA GAGAL TEKNIS —"
    suara = "dengan narasi dari JSON" if hasil.get("ada_narasi") else "tanpa narasi (JSON tidak merujuk berkas suara)"
    _kirim_berkas("sendVideo", "video", video, f"{nama}.mp4", "video/mp4",
                  f"{tanda} Jalur manual (tanpa LLM) — {nama}, {suara}.\nPeriksa:\n{hasil['laporan']}\nLabel AI tetap wajib aktif saat unggah.")


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("spek", help="jalur papan di repo, mis. mesin-video/papan/kisah/mahsyar1.json")
    ap.add_argument("-o", help="berkas MP4 keluaran")
    ap.add_argument("--kirim", action="store_true", help="kirim hasil ke Telegram")
    a = ap.parse_args()
    nama = Path(a.spek).stem if Path(a.spek).stem != "papan_manual" else Path(a.spek).parent.name
    try:
        p = jalur_spek(a.spek)
        video = Path(a.o or Path(os.environ.get("RUNNER_TEMP", "/tmp")) / f"manual-{nama}.mp4")
        hasil = jalankan(p, video)
    except (ValueError, FileNotFoundError) as e:
        if a.kirim:
            kirim_pesan(f"❌ Jalur manual {nama}: {e}")
        print(f"GAGAL: {e}", file=sys.stderr)
        sys.exit(1)
    print(json.dumps(hasil, ensure_ascii=False, indent=1))
    if a.kirim:
        if video.is_file():
            kirim(nama, video, hasil)
        else:
            kirim_pesan(f"❌ Jalur manual {nama} gagal di tahap {hasil['tahap']}:\n{hasil['laporan']}")
    sys.exit(0 if hasil["lulus"] else 1)


if __name__ == "__main__":
    main()
