"""Produksi final setelah pemilik menyetujui pratinjau visual: narasi TTS -> arah ulang -> render bersuara.

    python -m newmotion.application.produksi_final <id>            # narasi + render
    python -m newmotion.application.produksi_final <id> --kirim-saja  # kirim MP4 yang sudah dibuat

Rencana sutradara yang dipakai di pratinjau (antrean/<id>/rencana.json) dipakai lagi tanpa
memanggil LLM; yang berubah hanya waktu: shot, efek suara, dan subtitle mengikuti narasi asli.
Kredit ElevenLabs hanya dipakai sekali: audio yang sudah ada di antrean/<id>/audio dipakai ulang.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from newmotion.application.pratinjau_visual import (
    AKAR,
    ANTREAN,
    kirim_ke_telegram,
    naskah_untuk_pengarah,
)

PENGATURAN_SUARA = {"sub_kotak": True, "ekor_suara": 2.5, "duck_rasio": 3, "keras_lufs": -16}


def _status(d: Path) -> dict:
    return json.loads((d / "status.json").read_text(encoding="utf-8"))


def _simpan_status(d: Path, st: dict) -> None:
    st["diperbarui"] = datetime.now(UTC).isoformat()
    (d / "status.json").write_text(json.dumps(st, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def papan_final(id_: str, *, folder: Path = ANTREAN, tts_fn=None) -> Path:
    """Buat narasi (bila belum ada) lalu papan_final.json bersuara. Mengembalikan jalur papan."""
    from newmotion.application.pengarah_inti import arahkan_naskah
    from newmotion.paket_genre.kisah_islami.narasi_final import buat_narasi, tts
    from newmotion.paket_genre.kisah_islami.rencana_sutradara import terapkan_rencana
    from newmotion.paket_genre.kisah_islami.sutradara_hibrida import baca_rencana

    d = folder / id_
    st = _status(d)
    tahap = st.get("tahap", {})
    if tahap.get("tinjau_visual") != "selesai":
        raise ValueError("Render final hanya setelah pratinjau visual disetujui pemilik.")
    if tahap.get("dalil") != "selesai":
        raise ValueError("Render final diblokir: dalil belum lolos verifikasi.")
    naskah = json.loads((d / "naskah.json").read_text(encoding="utf-8"))
    genre = st.get("genre") or naskah.get("genre")
    sumber = naskah_untuk_pengarah(naskah, genre=genre, konteks_konten=st.get("konteks_konten") or naskah.get("konteks_konten"))
    rencana = baca_rencana(d)

    w = buat_narasi(sumber, rencana, d / "audio", tts_fn=tts_fn or tts)
    sumber = dict(sumber, _waktu_adegan=w["waktu_adegan"], _waktu_kata=w["waktu_kata"])
    arah = terapkan_rencana(sumber, rencana) if rencana else sumber
    spek, _, _ = arahkan_naskah(arah, genre_pilihan=sumber["genre"])
    spek.pop("durasi", None)  # durasi mengikuti narasi asli
    spek.update(PENGATURAN_SUARA, suara="audio/narasi.mp3", waktu="audio/narasi.waktu.json",
                _judul=sumber["judul"], genre=sumber["genre"])  # tanpa "judul": papan.js menggambarnya sebagai catatan tempel
    papan = d / "papan_final.json"
    papan.write_text(json.dumps(spek, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return papan


def render(papan: Path, video: Path) -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join([str(AKAR), str(AKAR / "mesin-video"), env.get("PYTHONPATH", "")]).rstrip(os.pathsep)
    subprocess.run([sys.executable, str(AKAR / "mesin-video" / "papan_buat.py"), str(papan), "-o", str(video)],
                   cwd=AKAR, env=env, check=True)
    if not video.is_file() or video.stat().st_size < 10_000:
        raise RuntimeError("Renderer tidak menghasilkan video final yang valid.")


def produksi(id_: str, *, folder: Path = ANTREAN, video: Path | None = None) -> Path:
    d = folder / id_
    st = _status(d)
    st.setdefault("tahap", {})["narasi"] = "jalan"
    _simpan_status(d, st)
    papan = papan_final(id_, folder=folder)
    st = _status(d)
    st["tahap"]["narasi"] = "selesai"
    st["tahap"]["render"] = "jalan"
    st.setdefault("ket", {})["narasi"] = "narasi ElevenLabs (Ozhy) dengan intonasi dan jeda dari rencana sutradara"
    _simpan_status(d, st)
    video = video or Path(os.environ.get("RUNNER_TEMP", "/tmp")) / f"newmotion-{id_}-final.mp4"
    render(papan, video)
    st = _status(d)
    st["tahap"]["render"] = "selesai"
    st["ket"]["render"] = "video final bersuara siap ditinjau"
    from newmotion.application.antrean_naskah import simpan_contoh_disetujui
    naskah = json.loads((d / "naskah.json").read_text(encoding="utf-8"))
    simpan_contoh_disetujui(d, naskah, st)
    st["papan_final"] = str(papan.relative_to(AKAR)) if papan.is_relative_to(AKAR) else str(papan)
    _simpan_status(d, st)
    try:  # ciri video untuk statistik (Tugas 9); tidak boleh menggagalkan produksi
        from newmotion.application.statistik_video import simpan_ciri

        simpan_ciri(d)
    except Exception as e:  # noqa: BLE001
        print(f"ciri video tidak tersimpan: {e}")
    return video


def kirim(id_: str, video: Path) -> None:
    st = _status(ANTREAN / id_)
    tombol = {"inline_keyboard": [[{"text": "📊 Catat hasil", "callback_data": f"sh:{id_}"}]]}  # Tugas 9: statistik tayang
    kirim_ke_telegram(id_, video, tombol=tombol, nama_berkas="final.mp4", caption=(
        f"🎞️ Video final — {st.get('judul') or id_}\n"
        "Sudah bersuara (narasi, efek, subtitle). Dengarkan di speaker HP dan headphone sebelum diunggah.\n"
        "Label AI tetap wajib aktif saat unggah.\n"
        "Setelah tayang, ketuk 📊 Catat hasil pada hari ke-1 dan ke-7."))


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("id")
    ap.add_argument("--kirim-saja", action="store_true")
    a = ap.parse_args()
    video = Path(os.environ.get("RUNNER_TEMP", "/tmp")) / f"newmotion-{a.id}-final.mp4"
    if a.kirim_saja:
        kirim(a.id, video)
        print(f"Video final dikirim: {video}")
        return
    produksi(a.id, video=video)
    print(f"Video final selesai: {video}")


if __name__ == "__main__":
    main()
