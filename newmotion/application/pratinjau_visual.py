"""Pratinjau visual storyboard NewMotion sebelum produksi narasi/TTS.

Alur: naskah terverifikasi -> sutradara (hibrida LLM + mesin, atau aturan) -> papan JSON -> MP4 tanpa audio.
Tidak ada pemanggilan TTS pada modul ini.
"""
from __future__ import annotations

import copy
import hashlib
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


def naskah_untuk_pengarah(
    naskah: dict, *, genre: str | None = None, konteks_konten: str | None = None
) -> dict:
    """Ubah beat menjadi kontrak adegan; genre dan konteks mengikuti metadata antrean."""
    beat = naskah.get("beat")
    if not isinstance(beat, list) or not beat:
        raise ValueError("Naskah tidak memiliki beat untuk diarahkan.")
    adegan = []
    tokoh_berdasarkan_nama: dict[str, dict] = {}
    ids_tokoh: set[str] = set()
    sumber_tokoh = naskah.get("tokoh", [])
    if not isinstance(sumber_tokoh, list):
        raise ValueError("Daftar tokoh pada naskah harus berupa daftar objek.")
    for nomor_tokoh, sumber in enumerate(sumber_tokoh, 1):
        if not isinstance(sumber, dict):
            raise ValueError(f"Tokoh ke-{nomor_tokoh} harus berupa objek.")
        nama_tokoh = sumber.get("nama")
        if not isinstance(nama_tokoh, str) or not nama_tokoh.strip():
            raise ValueError(f"Tokoh ke-{nomor_tokoh} harus memiliki nama.")
        label = " ".join(nama_tokoh.split())
        kunci = label.casefold()
        if kunci in tokoh_berdasarkan_nama:
            raise ValueError(f"Nama tokoh {label!r} ambigu karena terdaftar lebih dari sekali.")
        identitas = sumber.get("id")
        if not isinstance(identitas, str) or not identitas.strip():
            sidik = hashlib.sha256(kunci.encode("utf-8")).hexdigest()[:12]
            identitas = f"tokoh-{sidik}"
        else:
            identitas = identitas.strip()
        if identitas in ids_tokoh:
            raise ValueError(f"ID tokoh {identitas!r} digunakan lebih dari sekali.")
        data_tokoh = copy.deepcopy(sumber)
        data_tokoh["id"] = identitas
        data_tokoh["nama"] = label
        tokoh_berdasarkan_nama[kunci] = data_tokoh
        ids_tokoh.add(identitas)
    ids_beat: set[str] = set()
    ids_quran = {
        d.get("id"): d for d in naskah.get("dalil", [])
        if isinstance(d, dict) and d.get("jenis") == "quran"
        and isinstance(d.get("surah"), int)
        and re.fullmatch(r"\d+(-\d+)?", str(d.get("ayat", "")).replace(" ", ""))
        and d.get("status") == "terverifikasi"
    }
    dalil_dipakai = []
    genre_efektif = genre or naskah.get("genre") or "kisah_islami"
    for i, b in enumerate(beat, 1):
        if not isinstance(b, dict):
            raise ValueError(f"Beat {i} tidak valid.")
        narasi = b.get("narasi")
        if not isinstance(narasi, str) or not narasi.strip():
            raise ValueError(f"Beat {i} tidak memiliki narasi.")
        nama = str(b.get("nama") or f"adegan_{i}")
        id_beat = b.get("id")
        if not isinstance(id_beat, str) or not id_beat.strip():
            id_beat = f"beat-{i:03d}"
        else:
            id_beat = id_beat.strip()
        if id_beat in ids_beat:
            raise ValueError(f"ID beat {id_beat!r} digunakan lebih dari sekali.")
        ids_beat.add(id_beat)

        peran = b.get("peran", [])
        if not isinstance(peran, list) or any(not isinstance(x, str) or not x.strip() for x in peran):
            raise ValueError(f"Peran pada beat {i} harus berupa daftar nama yang tidak kosong.")
        peran_ids = []
        for nama_peran in peran:
            label = " ".join(nama_peran.split())
            kunci_peran = label.casefold()
            if kunci_peran not in tokoh_berdasarkan_nama:
                sidik = hashlib.sha256(kunci_peran.encode("utf-8")).hexdigest()[:12]
                identitas = f"tokoh-{sidik}"
                if identitas in ids_tokoh:
                    raise ValueError(
                        f"ID tokoh hasil pembentukan untuk {label!r} bertabrakan dengan ID lain."
                    )
                tokoh_berdasarkan_nama[kunci_peran] = {
                    "id": identitas, "nama": label,
                }
                ids_tokoh.add(identitas)
            peran_ids.append(tokoh_berdasarkan_nama[kunci_peran]["id"])

        dialog = b.get("dialog", [])
        if not isinstance(dialog, list) or any(not isinstance(x, dict) for x in dialog):
            raise ValueError(f"Dialog pada beat {i} harus berupa daftar objek.")
        adegan_item = {
            "id": id_beat,
            "nama": nama,
            "teks": narasi.strip(),
            "kunci": [str(x) for x in b.get("kata_kunci", []) if isinstance(x, str)],
            "peran": list(peran),
            "tokoh_ids": peran_ids,
            "dialog": copy.deepcopy(dialog),
        }
        # Peristiwa eksplisit dari sumber selalu menjadi otoritas.
        # Cerita umum boleh memakai pengurai deterministik jika field peristiwa belum ada.
        if "peristiwa" in b:
            for kunci in ("peristiwa", "aksi", "sasaran", "tujuan", "perubahan_keadaan"):
                if kunci in b:
                    adegan_item[kunci] = copy.deepcopy(b[kunci])
        elif genre_efektif == "cerita_umum":
            from newmotion.paket_genre.cerita_umum.pemahaman_peristiwa import uraikan_peristiwa

            daftar_benda = naskah.get("benda", [])
            hasil_pemahaman = uraikan_peristiwa(
                narasi.strip(),
                peran,
                benda=daftar_benda if isinstance(daftar_benda, list) else [],
            )
            daftar_peristiwa = hasil_pemahaman["peristiwa"]
            pemetaan_id = {
                item["id"]: f"{id_beat}-{item['id']}"
                for item in daftar_peristiwa
                if isinstance(item.get("id"), str)
            }
            diagnostik_pemahaman = list(hasil_pemahaman["diagnostik"])
            for peristiwa in daftar_peristiwa:
                id_lokal = peristiwa.get("id")
                if id_lokal in pemetaan_id:
                    peristiwa["id"] = pemetaan_id[id_lokal]
                relasi = peristiwa.get("hubungan_sebab_akibat")
                if isinstance(relasi, dict):
                    id_sebab_lokal = relasi.get("peristiwa_id")
                    if id_sebab_lokal in pemetaan_id:
                        relasi["peristiwa_id"] = pemetaan_id[id_sebab_lokal]
                    else:
                        peristiwa.pop("hubungan_sebab_akibat", None)
                        diagnostik_pemahaman.append({
                            "kode": "referensi_sebab_akibat_tidak_ditemukan",
                            "bukti_teks": peristiwa.get("bukti_teks", ""),
                        })
            adegan_item["peristiwa"] = daftar_peristiwa
            adegan_item["diagnostik_pemahaman"] = {
                "status": hasil_pemahaman["status"],
                "metode": hasil_pemahaman["metode"],
                "diagnostik": diagnostik_pemahaman,
            }
        adegan.append(adegan_item)
        for id_dalil in b.get("dalil", []):
            d = ids_quran.get(id_dalil)
            if d:
                dalil_dipakai.append({
                    "surah": d["surah"], "ayat": str(d["ayat"]).replace(" ", ""), "di_adegan": nama,
                    **({"label": d["label"]} if d.get("label") else {}),
                })
    from newmotion.application.pengklasifikasi_konten import klasifikasikan_konten

    metadata = dict(naskah)
    if genre is not None:
        metadata["genre"] = genre
    if konteks_konten is not None:
        metadata["konteks_konten"] = konteks_konten
    # Kompatibilitas antrean lama: sebelum metadata genre tersedia, seluruh
    # antrean dibuat melalui jalur Kisah Islami.
    if "genre" not in metadata:
        metadata["genre"] = "kisah_islami"
    if metadata["genre"] == "kisah_islami" and "konteks_konten" not in metadata:
        metadata["konteks_konten"] = "islami"
    hasil_klasifikasi = klasifikasikan_konten(metadata)
    if hasil_klasifikasi["perlu_klarifikasi"]:
        raise ValueError(
            "Genre/konteks konten belum cukup jelas untuk pratinjau: "
            + hasil_klasifikasi["keputusan"]
        )
    return {
        "judul": str(naskah.get("judul") or "Pratinjau NewMotion"),
        "genre": hasil_klasifikasi["genre"],
        "konteks_konten": hasil_klasifikasi["konteks_konten"],
        "adegan": adegan,
        "tokoh": list(tokoh_berdasarkan_nama.values()),
        "benda": copy.deepcopy(naskah.get("benda", [])),
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
    tahap_visual = status.get("tahap", {}).get("tinjau_visual", "belum")
    if tahap_visual in ("jalan", "selesai"):
        raise ValueError("Pratinjau visual sudah dibuat dan sedang/selesai ditinjau; cegah render ganda.")
    if status.get("tahap", {}).get("tinjau") != "selesai":
        raise ValueError("Pratinjau visual hanya boleh dibuat setelah naskah disetujui.")
    if status.get("tahap", {}).get("dalil") != "selesai":
        raise ValueError("Pratinjau visual diblokir: dalil naskah belum lolos verifikasi semua.")
    naskah = json.loads(naskah_path.read_text(encoding="utf-8"))
    from newmotion.application.pengarah_inti import arahkan_naskah

    genre = status.get("genre") or naskah.get("genre")
    konteks_konten = status.get("konteks_konten") or naskah.get("konteks_konten")
    sumber = naskah_untuk_pengarah(
        naskah, genre=genre, konteks_konten=konteks_konten
    )
    info_sutradara: dict = {"mode": "aturan"}
    if sumber["genre"] == "kisah_islami":  # sutradara hibrida (rencana LLM + periksa visual), jatuh ke aturan
        from newmotion.paket_genre.kisah_islami.sutradara_hibrida import arahkan_hibrida

        spek, info_sutradara = arahkan_hibrida(sumber, d, genre=sumber["genre"])
        nama_paket, jumlah_shot = sumber["genre"], len(spek["cerita"]["shot"])
    else:
        spek, nama_paket, jumlah_shot = arahkan_naskah(
            sumber, genre_pilihan=sumber["genre"]
        )
    spek["judul"] = sumber["judul"]
    spek["genre"] = nama_paket
    spek["konteks_konten"] = sumber["konteks_konten"]
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
    ringkas = (f"sutradara LLM {info_sutradara.get('model')}, biaya ${info_sutradara.get('biaya_usd', 0):.2f}"
               if info_sutradara.get("mode") == "llm" else "sutradara aturan")
    if info_sutradara.get("catatan"):
        ringkas += f" ({info_sutradara['catatan']})"
    status.setdefault("ket", {})["sutradara"] = f"{jumlah_shot} shot disusun oleh {nama_paket}; {ringkas}"
    status["sutradara"] = info_sutradara
    status["ket"]["tinjau_visual"] = "menunggu tinjauan visual pemilik; TTS belum dibuat"
    status["pratinjau_visual"] = str(papan.relative_to(AKAR))
    status_path.write_text(json.dumps(status, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return papan, video


def kirim_ke_telegram(id_: str, video: Path, *, caption: str | None = None, tombol: dict | None = None,
                      nama_berkas: str = "pratinjau-visual.mp4") -> None:
    status = json.loads((ANTREAN / id_ / "status.json").read_text(encoding="utf-8"))
    token = (os.environ.get("TELEGRAM_BOT_TOKEN") or "").strip()
    chat = str(status.get("chat") or os.environ.get("TELEGRAM_CHAT_ID") or "").strip()
    if not token or not chat:
        raise RuntimeError("TELEGRAM_BOT_TOKEN atau TELEGRAM_CHAT_ID belum tersedia.")
    if video.stat().st_size > 49 * 1024 * 1024:
        raise RuntimeError("Video melebihi batas unggah Telegram 49 MB; gunakan artefak GitHub Actions.")
    boundary = "----NewMotionVisualPreview"
    if tombol is None:
        tombol = {"inline_keyboard": [[
            {"text": "✅ Setujui visual", "callback_data": f"va:{id_}"},
            {"text": "❌ Tolak visual", "callback_data": f"vr:{id_}"},
        ]]}
    if caption is None:
        caption = (
            f"🎬 Pratinjau visual — {status.get('judul') or id_}\n"
            "Video ini tanpa TTS. Tinjau urutan adegan, tokoh, aksi, latar, blocking, dan kamera.\n"
            "TTS dan render final belum dimulai."
        )
    fields = [
        ("chat_id", chat.encode()),
        ("caption", caption.encode()),
        ("supports_streaming", b"true"),
    ] + ([("reply_markup", json.dumps(tombol, ensure_ascii=False).encode())] if tombol else [])
    body = bytearray()
    for name, value in fields:
        body.extend(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"\r\n\r\n".encode())
        body.extend(value + b"\r\n")
    body.extend(
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"video\"; filename=\"{nama_berkas}\"\r\nContent-Type: video/mp4\r\n\r\n".encode()
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


def tandai_gagal(id_: str, e: BaseException, *, folder: Path = ANTREAN) -> None:
    """Pratinjau gagal: status gagal + alasan singkat, kartu Telegram diperbarui (tombol Ulangi pratinjau)."""
    p = folder / id_ / "status.json"
    if not re.fullmatch(r"[a-z0-9_-]{1,60}", id_) or not p.is_file():
        return
    st = json.loads(p.read_text(encoding="utf-8"))
    tahap = st.setdefault("tahap", {})
    if tahap.get("tinjau_visual") in ("jalan", "selesai"):
        return  # galat 'cegah render ganda': status yang ada tetap
    tahap["sutradara"] = "gagal"
    tahap["tinjau_visual"] = "belum"
    st.setdefault("ket", {})["sutradara"] = f"pratinjau gagal: {str(e)[:220]}"
    p.write_text(json.dumps(st, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    try:
        from newmotion.application.antrean_naskah import perbarui_kartu

        perbarui_kartu(st)
        p.write_text(json.dumps(st, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    except Exception as kirim_galat:  # noqa: BLE001 - kartu gagal terkirim tidak boleh menutupi galat asli
        print(f"kartu tidak terkirim: {kirim_galat}")


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
    try:
        _, video = buat_pratinjau(args.id, keluaran=video)
    except Exception as e:
        tandai_gagal(args.id, e)
        raise
    if args.kirim:
        kirim_ke_telegram(args.id, video)
    print(f"Pratinjau visual selesai: {video}")


if __name__ == "__main__":
    main()
