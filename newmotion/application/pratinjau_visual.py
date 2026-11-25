"""Pratinjau visual storyboard NewMotion sebelum produksi narasi/TTS.

Alur: naskah terverifikasi -> pengarah Kisah Islami -> papan JSON -> MP4 tanpa audio.
Tidak ada pemanggilan TTS pada modul ini.
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
ANTREAN = AKAR / "antrean"


def naskah_untuk_pengarah(naskah: dict) -> dict:
    """Ubah beat antrean menjadi kontrak adegan sutradara tanpa mengubah narasi."""
    beat = naskah.get("beat")
    if not isinstance(beat, list) or not beat:
        raise ValueError("Naskah tidak memiliki beat untuk diarahkan.")
    adegan = []
    ids_quran = {
        d.get("id"): d for d in naskah.get("dalil", [])
        if isinstance(d, dict) and d.get("jenis") == "quran"
        and isinstance(d.get("surah"), int) and str(d.get("ayat", "")).isdigit()
        and d.get("status") == "terverifikasi"
    }
    dalil_dipakai = []
    for i, b in enumerate(beat, 1):
        if not isinstance(b, dict):
            raise ValueError(f"Beat {i} tidak valid.")
        narasi = b.get("narasi")
        if not isinstance(narasi, str) or not narasi.strip():
            raise ValueError(f"Beat {i} tidak memiliki narasi.")
        nama = str(b.get("nama") or f"adegan_{i}")
        adegan.append({"nama": nama, "teks": narasi.strip(),
                       "kunci": [str(x) for x in b.get("kata_kunci", []) if isinstance(x, str)]})
        for id_dalil in b.get("dalil", []):
            d = ids_quran.get(id_dalil)
            if d:
                dalil_dipakai.append({
                    "surah": d["surah"], "ayat": d["ayat"], "di_adegan": nama,
                })
    return {
        "judul": str(naskah.get("judul") or "Pratinjau NewMotion"),
        "genre": "kisah_islami",
        "konteks_konten": "islami",
        "adegan": adegan,
        "dalil_dipakai": dalil_dipakai,
    }


def buat_pratinjau(id_: str, *, folder: Path = ANTREAN, keluaran: Path | None = None) -> tuple[Path, Path]:
    if not re.fullmatch(r"[a-z0-9_-]{1,60}", id_):
        raise ValueError("ID antrean tidak sah.")
    d = folder / id_
    naskah_path = d / "naskah.json"
    status_path = d / "status.json"
    if not naskah_path.is_file() or not status_path.is_file():
        raise FileNotFoundError("Naskah atau status antrean tidak ditemukan.")
    status = json.loads(status_path.read_text(encoding="utf-8"))
    if status.get("tahap", {}).get("tinjau") != "selesai":
        raise ValueError("Pratinjau visual hanya boleh dibuat setelah naskah disetujui.")
    naskah = json.loads(naskah_path.read_text(encoding="utf-8"))
    from newmotion.application.pengarah_inti import arahkan_naskah

    sumber = naskah_untuk_pengarah(naskah)
    spek, nama_paket, jumlah_shot = arahkan_naskah(sumber, genre_pilihan="kisah_islami")
    spek["judul"] = sumber["judul"]
    spek["genre"] = nama_paket
    spek["konteks_konten"] = "islami"
    d.mkdir(parents=True, exist_ok=True)
    papan = d / "papan_pratinjau.json"
    papan.write_text(json.dumps(spek, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    video = keluaran or (Path(os.environ.get("RUNNER_TEMP", "/tmp")) / f"newmotion-{id_}-pratinjau.mp4")
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(
        [str(AKAR), str(AKAR / "mesin-video"), env.get("PYTHONPATH", "")]
    ).rstrip(os.pathsep)
    subprocess.run(
        [sys.executable, str(AKAR / "mesin-video" / "papan_buat.py"),
         str(papan), "--tanpa-suara", "-o", str(video)],
        cwd=AKAR, env=env, check=True,
    )
    if not video.is_file() or video.stat().st_size < 10_000:
        raise RuntimeError("Renderer tidak menghasilkan video pratinjau yang valid.")
    status.setdefault("tahap", {})["sutradara"] = "selesai"
    status["tahap"]["tinjau_visual"] = "jalan"
    status.setdefault("ket", {})["sutradara"] = f"{jumlah_shot} shot disusun oleh {nama_paket}"
    status["ket"]["tinjau_visual"] = "menunggu tinjauan visual pemilik; TTS belum dibuat"
    status["pratinjau_visual"] = str(papan.relative_to(AKAR))
    status_path.write_text(json.dumps(status, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return papan, video


def kirim_ke_telegram(id_: str, video: Path) -> None:
    status = json.loads((ANTREAN / id_ / "status.json").read_text(encoding="utf-8"))
    token = (os.environ.get("TELEGRAM_BOT_TOKEN") or "").strip()
    chat = str(status.get("chat") or os.environ.get("TELEGRAM_CHAT_ID") or "").strip()
    if not token or not chat:
        raise RuntimeError("TELEGRAM_BOT_TOKEN atau TELEGRAM_CHAT_ID belum tersedia.")
    if video.stat().st_size > 49 * 1024 * 1024:
        raise RuntimeError("Pratinjau melebihi batas unggah Telegram 49 MB; gunakan artefak GitHub Actions.")
    boundary = "----NewMotionVisualPreview"
    tombol = {"inline_keyboard": [[
        {"text": "✅ Setujui visual", "callback_data": f"va:{id_}"},
        {"text": "🔁 Revisi visual", "callback_data": f"vr:{id_}"},
    ]]}
    caption = (
        f"🎬 Pratinjau visual — {status.get('judul') or id_}\n"
        "Video ini tanpa TTS. Tinjau urutan adegan, tokoh, aksi, latar, blocking, dan kamera.\n"
        "TTS dan render final belum dimulai."
    )
    fields = [
        ("chat_id", chat.encode()),
        ("caption", caption.encode()),
        ("supports_streaming", b"true"),
        ("reply_markup", json.dumps(tombol, ensure_ascii=False).encode()),
    ]
    body = bytearray()
    for name, value in fields:
        body.extend(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"\r\n\r\n".encode())
        body.extend(value + b"\r\n")
    body.extend(
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"video\"; filename=\"pratinjau-visual.mp4\"\r\nContent-Type: video/mp4\r\n\r\n".encode()
    )
    body.extend(video.read_bytes() + b"\r\n")
    body.extend(f"--{boundary}--\r\n".encode())
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendVideo", data=bytes(body),
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}, method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as response:
            result = json.load(response)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Telegram sendVideo HTTP {exc.code}: {exc.read().decode(errors='replace')[:300]}") from exc
    if not result.get("ok"):
        raise RuntimeError("Telegram gagal mengirim pratinjau visual.")


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("id")
    parser.add_argument("--kirim", action="store_true", help="kirim setelah render; untuk workflow gunakan --kirim-saja setelah status tersimpan")
    parser.add_argument("--kirim-saja", action="store_true", help="kirim MP4 yang sudah dibuat tanpa render ulang")
    args = parser.parse_args()
    video = Path(os.environ.get("RUNNER_TEMP", "/tmp")) / f"newmotion-{args.id}-pratinjau.mp4"
    if args.kirim_saja:
        kirim_ke_telegram(args.id, video)
        print(f"Pratinjau visual dikirim: {video}")
        return
    _, video = buat_pratinjau(args.id, keluaran=video)
    if args.kirim:
        kirim_ke_telegram(args.id, video)
    print(f"Pratinjau visual selesai: {video}")


if __name__ == "__main__":
    main()
