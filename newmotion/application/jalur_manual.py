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


def folder_audio(p: Path) -> Path:
    """Tempat narasi buatan jalur manual (di-commit supaya kredit ElevenLabs tidak terpakai dua kali)."""
    if p.is_relative_to(MV):
        return MV / "audio_manual" / f"{p.stem}_auto"
    return p.parent / "audio"


def siapkan(p: Path, *, tts_fn=None) -> tuple[Path, bool]:
    """Salin papan ke folder kisah (supaya rujukan relatif berlaku). Kembalikan (papan, ada_narasi).

    Bila shot berisi "narasi" dan papan belum merujuk berkas suara, narasi ElevenLabs dibuat dulu
    dan waktu shot diisi mengikuti rekaman."""
    spek = baca_spek(p)
    dasar = p.parent if p.is_relative_to(MV) else DASAR_KISAH
    if butuh_narasi(spek):
        from newmotion.application.validasi_papan_manual import laporan, periksa

        galat, awas = periksa(spek)  # sebelum TTS: JSON salah tidak memakan kredit ElevenLabs
        for x in awas:
            print("peringatan papan:", x)
        if galat:
            raise ValueError(laporan(galat))
        fa = folder_audio(p)
        buat_narasi_spek(spek, fa, tts_fn=tts_fn)
        for k, v in PENGATURAN_SUARA.items():
            spek.setdefault(k, v)
        spek["suara"] = os.path.relpath(fa / "narasi.mp3", dasar)
        spek["waktu"] = os.path.relpath(fa / "narasi.waktu.json", dasar)
        salinan = dasar / f".manual-{p.stem if dasar == p.parent else p.parent.name}.json"
        salinan.write_text(json.dumps(spek, ensure_ascii=False), encoding="utf-8")
        return salinan, True
    ada_narasi = bool(spek.get("suara")) and (dasar / spek["suara"]).resolve().is_file()
    if spek.get("suara") and not ada_narasi:
        raise FileNotFoundError(f"Berkas narasi yang dirujuk tidak ada: {spek['suara']}")
    if dasar == p.parent:
        return p, ada_narasi
    salinan = DASAR_KISAH / f".manual-{p.parent.name}.json"
    salinan.write_text(json.dumps(spek, ensure_ascii=False), encoding="utf-8")
    return salinan, ada_narasi


# ---------------- narasi dari teks di JSON (satu permintaan ElevenLabs) ----------------
ARAB = re.compile(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]")
PENGATURAN_SUARA = {"sub_kotak": True, "ekor_suara": 2.5, "duck_rasio": 3, "keras_lufs": -16}


def butuh_narasi(spek: dict) -> bool:
    shot = (spek.get("cerita") or {}).get("shot") or []
    return not spek.get("suara") and any(isinstance(x, dict) and str(x.get("narasi") or "").strip() for x in shot)


def susun_teks_narasi(spek: dict) -> tuple[str, list[int], list[int], list[float]]:
    """Kembalikan (teks TTS, indeks shot bernarasi, jumlah kata per segmen, jeda setelah tiap segmen).

    Shot tanpa narasi wajib punya "durasi" (detik layar tenang); durasinya menjadi jeda setelah segmen sebelumnya.
    """
    from newmotion.paket_genre.kisah_islami.narasi_final import (
        INTONASI_TAG,
        JEDA_DASAR,
        _kata,
    )

    shot = spek["cerita"]["shot"]
    bagian, idx, jumlah, jeda = [], [], [], []
    for i, sh in enumerate(shot):
        teks = str(sh.get("narasi") or "").strip()
        if not teks:
            if not isinstance(sh.get("durasi"), (int, float)) or sh["durasi"] <= 0:
                raise ValueError(f"shot {i + 1} tanpa narasi wajib punya \"durasi\" (detik)")
            if not idx:
                raise ValueError("shot pertama harus bernarasi (fakta terkuat di detik 0)")
            jeda[-1] += float(sh["durasi"])
            continue
        if ARAB.search(teks):
            raise ValueError(f"shot {i + 1}: bacaan Arab tidak disuarakan AI; tulis Arabnya di teks layar, narasi pakai arti/latin")
        tag = INTONASI_TAG.get(str(sh.get("intonasi") or ""), "")
        if sh.get("intonasi") and not tag:
            raise ValueError(f"shot {i + 1}: intonasi {sh['intonasi']!r} tidak dikenal ({', '.join(INTONASI_TAG)})")
        bagian.append(f"{tag} {teks}".strip())
        idx.append(i)
        jumlah.append(len(_kata(teks)))
        jeda.append(float(sh.get("jeda", JEDA_DASAR)))
    jeda[-1] = 0.0 + sum(float(shot[j].get("durasi", 0)) for j in range(idx[-1] + 1, len(shot)))
    return "\n".join(bagian), idx, jumlah, jeda


def buat_narasi_spek(spek: dict, folder: Path, *, tts_fn=None) -> dict:
    """Narasi ElevenLabs untuk papan manual. Audio mentah dipakai ulang selama teks dan suara tidak berubah."""
    from newmotion.paket_genre.kisah_islami import narasi_final as NF

    teks, idx, jumlah, jeda = susun_teks_narasi(spek)
    suara = str(spek.get("narator") or NF.SUARA_NARATOR)
    folder.mkdir(parents=True, exist_ok=True)
    mentah, jejak = folder / "mentah.mp3", folder / "mentah.teks.txt"
    kunci = f"{suara}\n{teks}"
    if mentah.is_file() and mentah.with_suffix(".waktu.json").is_file() and jejak.is_file() and jejak.read_text(encoding="utf-8") == kunci:
        kata = json.loads(mentah.with_suffix(".waktu.json").read_text(encoding="utf-8"))["kata"]
    else:
        kata = (tts_fn or NF.tts)(teks, mentah, suara=suara)
        jejak.write_text(kunci, encoding="utf-8")
    w = NF.susun_waktu(NF.potong(kata, jumlah), jeda)
    NF.rakit_audio(mentah, w["potongan"], jeda, folder / "narasi.mp3")
    (folder / "narasi.waktu.json").write_text(json.dumps({"kata": w["kata"]}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    # waktu shot: shot bernarasi mulai di segmennya; shot diam mulai setelah segmen sebelumnya selesai bicara
    shot, akhir = spek["cerita"]["shot"], dict(zip(idx, (a1 - a0 + m for (a0, a1), m in zip(w["potongan"], w["waktu_adegan"]))))
    terakhir = 0.0
    for i, sh in enumerate(shot):
        if i in idx:
            mulai = w["waktu_adegan"][idx.index(i)]
            terakhir = akhir[i]
        else:
            mulai, terakhir = terakhir, terakhir + float(sh["durasi"])
        if not isinstance(sh.get("at"), str):  # "@kata" tetap diselesaikan oleh papan_buat
            sh["at"] = round(mulai, 2)
        if sh.get("narasi"):
            sh["_narasi"] = sh["narasi"]  # penjaga adab membaca narasi shot (mis. figuran berwajah di shot yang menyebut nabi)
        for k in ("narasi", "intonasi", "jeda"):
            sh.pop(k, None)
        if i not in idx:
            sh.pop("durasi", None)
    return w


def _env() -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join([str(AKAR), str(MV), env.get("PYTHONPATH", "")]).rstrip(os.pathsep)
    return env


def siapkan_pratinjau_visual(p: Path, durasi_per_shot: float = 4.0) -> Path:
    """Buat salinan papan untuk pratinjau visual tanpa TTS, narasi, musik, atau efek audio."""
    if durasi_per_shot <= 0:
        raise ValueError("durasi pratinjau tiap shot harus lebih dari 0 detik")
    spek = baca_spek(p)
    cerita = spek.get("cerita")
    if not isinstance(cerita, dict) or not isinstance(cerita.get("shot"), list):
        raise ValueError("Pratinjau visual saat ini memerlukan cerita.shot.")
    shot = cerita["shot"]
    if not shot:
        raise ValueError("Tidak ada shot untuk dipratinjau.")
    for i, sh in enumerate(shot):
        if not isinstance(sh, dict):
            raise ValueError(f"shot {i + 1} harus berupa objek.")
        sh["at"] = round(i * durasi_per_shot, 2)
        for k in ("narasi", "intonasi", "jeda", "_narasi", "durasi"):
            sh.pop(k, None)
    spek["durasi"] = round(len(shot) * durasi_per_shot, 2)
    for k in ("suara", "waktu", "subtitle", "rekaman", "musik", "musik_seed"):
        spek.pop(k, None)
    spek["musik"] = False
    tujuan = p.parent / f".pratinjau-{p.stem}.json"
    tujuan.write_text(json.dumps(spek, ensure_ascii=False, indent=2) + "\\n", encoding="utf-8")
    return tujuan


def jalankan(p: Path, video: Path, *, tts_fn=None) -> dict:
    """Render + periksa. Mengembalikan ringkasan; 'lulus' False bila ada GAGAL teknis/batas wajib."""
    kerja = video.parent / (video.stem + "_periksa")
    kerja.mkdir(parents=True, exist_ok=True)
    papan, ada_narasi = siapkan(p, tts_fn=tts_fn)
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
def _kirim_berkas(metode: str, medan: str, berkas: Path, nama: str, jenis: str, keterangan: str, tombol: dict | None = None) -> None:
    token = (os.environ.get("TELEGRAM_BOT_TOKEN") or "").strip()
    chat = (os.environ.get("TELEGRAM_CHAT_ID") or "").strip()
    if not token or not chat:
        raise RuntimeError("TELEGRAM_BOT_TOKEN atau TELEGRAM_CHAT_ID belum tersedia.")
    batas = "----NewMotionManual"
    tubuh = bytearray()
    medan_teks = [("chat_id", chat), ("caption", keterangan[:1000])] + ([("reply_markup", json.dumps(tombol, ensure_ascii=False))] if tombol else [])
    for k, v in medan_teks:
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


def kirim(nama: str, video: Path, hasil: dict, id_antrean: str | None = None) -> None:
    lembar = Path(hasil["periksa"]) / "lembar.jpg"
    if lembar.is_file():
        _kirim_berkas("sendPhoto", "photo", lembar, "lembar.jpg", "image/jpeg", f"Lembar kontak — {nama}")
    if video.stat().st_size > 49 * 1024 * 1024:
        kirim_pesan(f"🎞️ {nama}: video >49 MB, ambil dari artefak GitHub Actions.\n\n{hasil['laporan']}")
        return
    tanda = "🎞️" if hasil["lulus"] else "⚠️ ADA GAGAL TEKNIS —"
    suara = "dengan narasi dari JSON" if hasil.get("ada_narasi") else "tanpa narasi (JSON tidak merujuk berkas suara)"
    tombol = {"inline_keyboard": [[{"text": "📊 Catat hasil", "callback_data": f"sh:{id_antrean}"}]]} if id_antrean else None
    _kirim_berkas("sendVideo", "video", video, f"{nama}.mp4", "video/mp4",
                  f"{tanda} Jalur manual (tanpa LLM) — {nama}, {suara}.\nPeriksa:\n{hasil['laporan']}\nLabel AI tetap wajib aktif saat unggah.", tombol)


def bekal() -> str:
    """Dokumen format + katalog renderer, tokoh, dan suara terbaru (selalu sesuai kode saat ini)."""
    from newmotion.application.katalog_renderer import teks_katalog
    from newmotion.application.katalog_suara import teks_katalog_suara
    from newmotion.application.kemampuan_tokoh import teks_kemampuan_tokoh

    return "\n\n".join([(AKAR / "docs" / "FORMAT_PAPAN_MANUAL.md").read_text(encoding="utf-8"),
                        "## Katalog benda (shot.benda[].jenis)\n" + teks_katalog(),
                        "## Kemampuan tokoh (shot.boneka[])\n" + teks_kemampuan_tokoh(),
                        "## Katalog efek suara (rekaman[].berkas = ../../aset/suara/<nama>.mp3)\n" + teks_katalog_suara()])


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("spek", nargs="?", help="jalur papan di repo, mis. mesin-video/papan/kisah/mahsyar1.json")
    ap.add_argument("--bekal", action="store_true", help="cetak format + katalog terbaru untuk sesi chat penulis JSON")
    ap.add_argument("-o", help="berkas MP4 keluaran")
    ap.add_argument("--kirim", action="store_true", help="kirim hasil ke Telegram")
    ap.add_argument("--pratinjau-visual", action="store_true", help="render visual tanpa TTS, narasi, musik, atau efek audio")
    a = ap.parse_args()
    if a.bekal:
        print(bekal())
        return
    if not a.spek:
        ap.error("spek wajib (atau --bekal)")
    nama = Path(a.spek).stem if Path(a.spek).stem != "papan_manual" else Path(a.spek).parent.name
    try:
        p = jalur_spek(a.spek)
        video = Path(a.o or Path(os.environ.get("RUNNER_TEMP", "/tmp")) / f"manual-{nama}.mp4")
        if a.pratinjau_visual and a.kirim:
            raise ValueError("Mode pratinjau visual tidak boleh dikirim; setujui visual dahulu.")
        hasil = jalankan(p, video, pratinjau_visual=a.pratinjau_visual)
    except Exception as e:  # noqa: BLE001 - semua kegagalan dilaporkan ke pemilik lewat Telegram
        if a.kirim:
            kirim_pesan(f"❌ Jalur manual {nama}: {e}")
        print(f"GAGAL: {e}", file=sys.stderr)
        sys.exit(1)
    print(json.dumps(hasil, ensure_ascii=False, indent=1))
    if a.kirim:
        id_antrean = Path(a.spek).parent.name if a.spek.startswith("antrean/") else None
        if id_antrean and hasil["lulus"]:
            try:
                from newmotion.application.statistik_video import simpan_ciri

                simpan_ciri(AKAR / "antrean" / id_antrean)
            except Exception as e:  # noqa: BLE001
                print(f"ciri video tidak tersimpan: {e}")
        if video.is_file():
            kirim(nama, video, hasil, id_antrean)
        else:
            kirim_pesan(f"❌ Jalur manual {nama} gagal di tahap {hasil['tahap']}:\n{hasil['laporan']}")
    sys.exit(0 if hasil["lulus"] else 1)


if __name__ == "__main__":
    main()
