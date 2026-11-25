"""Buat dan kirim pratinjau TTS gratis sebelum pengarahan/render video.

Penyedia: Microsoft Edge Read Aloud melalui paket edge-tts (tanpa API key).
Pratinjau dikirim ke Telegram dengan tombol persetujuan; audio yang disetujui
disimpan sebagai aset antrean untuk dipakai pipeline berikutnya.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

AKAR = Path(__file__).resolve().parents[2]
ANTREAN = AKAR / "antrean"
SUARA = {
    "id-ID-ArdiNeural": "Pria — Bahasa Indonesia",
    "id-ID-GadisNeural": "Wanita — Bahasa Indonesia",
}
BATAS_BAGIAN = 2200


def teks_dari_naskah(naskah: dict) -> str:
    """Gabungkan narasi beat sesuai urutan; jangan mengubah isi naskah."""
    beat = naskah.get("beat")
    if not isinstance(beat, list) or not beat:
        raise ValueError("Naskah tidak memiliki beat untuk dibuat narasi.")
    bagian = []
    for i, b in enumerate(beat, 1):
        if not isinstance(b, dict) or not isinstance(b.get("narasi"), str) or not b["narasi"].strip():
            raise ValueError(f"Beat {i} tidak memiliki narasi.")
        bagian.append(b["narasi"].strip())
    return "\n\n".join(bagian)


def pecah_teks(teks: str, batas: int = BATAS_BAGIAN) -> list[str]:
    """Pecah teks pada batas kalimat agar permintaan TTS tidak terlalu panjang."""
    teks = re.sub(r"\s+", " ", teks).strip()
    if not teks:
        raise ValueError("Teks narasi kosong.")
    hasil, sisa = [], teks
    while len(sisa) > batas:
        potong = max(sisa.rfind(tanda, 0, batas) for tanda in (". ", "! ", "? ", "; ", ", "))
        if potong < batas // 2:
            potong = sisa.rfind(" ", 0, batas)
        if potong <= 0:
            potong = batas
        else:
            potong += 1
        hasil.append(sisa[:potong].strip())
        sisa = sisa[potong:].strip()
    if sisa:
        hasil.append(sisa)
    return hasil


def validasi_suara(nama: str) -> str:
    if nama not in SUARA:
        raise ValueError("Suara tidak dikenal. Pilih id-ID-ArdiNeural atau id-ID-GadisNeural.")
    return nama


def buat_audio(teks: str, suara: str, keluaran: Path) -> None:
    import edge_tts

    async def proses() -> None:
        potongan = pecah_teks(teks)
        sementara = keluaran.parent / ".bagian_tts"
        sementara.mkdir(parents=True, exist_ok=True)
        berkas = []
        try:
            for i, bagian in enumerate(potongan, 1):
                path = sementara / f"bagian-{i:03d}.mp3"
                komunikasi = edge_tts.Communicate(bagian, suara)
                await komunikasi.save(str(path))
                if not path.exists() or path.stat().st_size < 1000:
                    raise RuntimeError(f"Audio TTS bagian {i} kosong atau terlalu kecil.")
                berkas.append(path)
            daftar = sementara / "daftar.txt"
            daftar.write_text("".join(f"file '{p.as_posix()}'\n" for p in berkas), encoding="utf-8")
            subprocess.run(
                ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "concat",
                 "-safe", "0", "-i", str(daftar), "-c", "copy", str(keluaran)],
                check=True,
            )
        finally:
            for p in sementara.glob("*"):
                p.unlink(missing_ok=True)
            sementara.rmdir()

    asyncio.run(proses())


def kirim_audio(chat: str, token: str, audio: Path, id_: str, suara: str) -> None:
    batas = "----NewMotionTTSBoundary"
    tombol = {"inline_keyboard": [[
        {"text": "✅ Setujui suara", "callback_data": f"su:{id_}"},
        {"text": "🔁 Ganti suara", "callback_data": f"sr:{id_}"},
    ]]}
    caption = (
        f"🎙️ Pratinjau narasi — {id_}\n"
        f"Suara: {SUARA[suara]} ({suara})\n"
        "Dengarkan sampai selesai. Video belum dibuat sebelum suara ini disetujui."
    )
    with audio.open("rb") as f:
        data_audio = f.read()
    bagian = [
        (b"chat_id", chat.encode()),
        (b"caption", caption.encode()),
        (b"reply_markup", json.dumps(tombol, ensure_ascii=False).encode()),
        (b"parse_mode", b""),
    ]
    badan = bytearray()
    for nama, isi in bagian:
        badan.extend(f"--{batas}\r\nContent-Disposition: form-data; name=\"{nama}\"\r\n\r\n".encode())
        badan.extend(isi + b"\r\n")
    badan.extend(
        f"--{batas}\r\nContent-Disposition: form-data; name=\"audio\"; filename=\"narasi-pratinjau.mp3\"\r\nContent-Type: audio/mpeg\r\n\r\n".encode()
    )
    badan.extend(data_audio + b"\r\n")
    badan.extend(f"--{batas}--\r\n".encode())
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendAudio",
        data=bytes(badan),
        headers={"Content-Type": f"multipart/form-data; boundary={batas}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as res:
            jawaban = json.load(res)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Telegram sendAudio HTTP {exc.code}: {exc.read().decode(errors='replace')[:300]}") from exc
    if not jawaban.get("ok"):
        raise RuntimeError("Telegram gagal mengirim pratinjau suara.")


def proses(id_: str, suara: str | None = None, *, folder: Path = ANTREAN, kirim: bool = False) -> dict:
    if not re.fullmatch(r"[a-z0-9_-]{1,60}", id_):
        raise ValueError("ID antrean tidak sah.")
    d = folder / id_
    st_path, naskah_path = d / "status.json", d / "naskah.json"
    if not st_path.exists() or not naskah_path.exists():
        raise FileNotFoundError("Status atau naskah antrean tidak ditemukan.")
    st = json.loads(st_path.read_text(encoding="utf-8"))
    naskah = json.loads(naskah_path.read_text(encoding="utf-8"))
    suara = validasi_suara(suara or st.get("suara_pilihan") or "id-ID-ArdiNeural")
    teks = teks_dari_naskah(naskah)
    audio = d / "narasi_pratinjau.mp3"
    if kirim:
        token = (os.environ.get("TELEGRAM_BOT_TOKEN") or "").strip()
        chat = str(st.get("chat") or os.environ.get("TELEGRAM_CHAT_ID") or "").strip()
        if not token or not chat:
            raise RuntimeError("TELEGRAM_BOT_TOKEN atau TELEGRAM_CHAT_ID belum tersedia.")
        if not audio.exists():
            raise FileNotFoundError("Audio pratinjau belum dibuat.")
        kirim_audio(chat, token, audio, id_, suara)
        return st
    buat_audio(teks, suara, audio)
    st.setdefault("tahap", {})["narasi"] = "selesai"
    st["tahap"]["tinjau_suara"] = "jalan"
    st.setdefault("ket", {})["narasi"] = f"Pratinjau gratis siap · {SUARA[suara]}"
    st["ket"]["tinjau_suara"] = "menunggu persetujuan pemilik"
    st["suara_pilihan"] = suara
    st["suara_pratinjau"] = "antrean/" + id_ + "/narasi_pratinjau.mp3"
    st["diperbarui"] = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(timespec="seconds")
    st_path.write_text(json.dumps(st, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (d / "narasi_pratinjau.txt").write_text(teks + "\n", encoding="utf-8")
    return st


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("id")
    ap.add_argument("--suara", default=None)
    ap.add_argument("--kirim", action="store_true")
    a = ap.parse_args()
    st = proses(a.id, a.suara, kirim=a.kirim)
    print(json.dumps({"id": a.id, "tahap": st.get("tahap"), "suara": st.get("suara_pilihan")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
