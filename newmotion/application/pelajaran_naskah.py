"""Pengumpulan revisi, contoh naskah, dan usulan pedoman yang disetujui pemilik."""
from __future__ import annotations

import json
import re
from pathlib import Path

from newmotion.application.antrean_naskah import AKAR


DATA = AKAR / "newmotion" / "application" / "data"
PEDOMAN = DATA / "pedoman_naskah_pemilik.md"


def _kata(teks: str) -> set[str]:
    return {x for x in re.findall(r"[a-zA-ZÀ-ÿ0-9']+", teks.lower()) if len(x) > 2}


def pilih_contoh(ide: str, *, batas: int = 2) -> list[dict]:
    """Ambil contoh final paling mirip berdasarkan irisan kata topik dan peran."""
    folder = DATA / "contoh_naskah"
    if not folder.is_dir():
        return []
    kunci = _kata(ide)
    calon = []
    for path in folder.glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        naskah = data.get("naskah") or {}
        teks = " ".join([str(data.get("judul", "")), str(data.get("inti", ""))]
                        + [str(b.get("narasi", "")) + " " + " ".join(map(str, b.get("peran", [])))
                           for b in naskah.get("beat", [])])
        kata = _kata(teks)
        skor = len(kunci & kata) / max(1, len(kunci | kata))
        if skor > 0:
            calon.append((skor, data))
    calon.sort(key=lambda x: x[0], reverse=True)
    return [x[1] for x in calon[:max(0, batas)]]


def pedoman_disetujui() -> str:
    """Hanya pedoman yang dipindahkan pemilik ke berkas persetujuan yang dibaca penulis."""
    if not PEDOMAN.is_file():
        return ""
    return PEDOMAN.read_text(encoding="utf-8").strip()


def ringkas(*, tanya=None) -> dict:
    """Rangkum pola revisi menjadi usulan; tidak pernah mengaktifkannya otomatis."""
    sumber = DATA / "pelajaran_naskah.jsonl"
    if not sumber.is_file():
        return {"jumlah_revisi": 0, "usulan": []}
    baris = []
    for teks in sumber.read_text(encoding="utf-8").splitlines():
        try:
            baris.append(json.loads(teks))
        except json.JSONDecodeError:
            continue
    if not baris:
        return {"jumlah_revisi": 0, "usulan": []}
    from newmotion.infrastructure import llm

    prompt = json.dumps(baris, ensure_ascii=False)
    sistem = (
        "Analisis kumpulan revisi pemilik naskah. Temukan hanya pola yang berulang dan didukung bukti. "
        "Jangan mengubah temuan menjadi aturan wajib. Keluarkan JSON {usulan:[{pola,alasan,jumlah_revisi,contoh_sebelum,contoh_sesudah}]}. "
        "Jumlah revisi harus dihitung dari bukti; contoh kalimat harus verbatim dari data."
    )
    def kalimat_naskah(sisi):
        hasil = set()
        for revisi in baris:
            naskah = revisi.get(sisi) or {}
            beat = naskah.get("beat", []) if isinstance(naskah, dict) else []
            if isinstance(beat, list):
                for bagian in beat:
                    if isinstance(bagian, dict):
                        narasi = bagian.get("narasi")
                        if isinstance(narasi, str) and narasi.strip():
                            hasil.add(narasi.strip())
        return hasil

    sebelum_tersedia = kalimat_naskah("sebelum")
    sesudah_tersedia = kalimat_naskah("sesudah")

    def validasi(data):
        if not isinstance(data, dict) or not isinstance(data.get("usulan"), list):
            return ["usulan harus berupa daftar"]
        galat = []
        for i, u in enumerate(data["usulan"]):
            if not isinstance(u, dict) or not all(isinstance(u.get(k), str) and u[k].strip()
                                                  for k in ("pola", "alasan", "contoh_sebelum", "contoh_sesudah")):
                galat.append(f"usulan {i + 1}: isi pola, alasan, dan contoh sebelum/sesudah")
                continue
            jumlah = u.get("jumlah_revisi")
            if not isinstance(jumlah, int) or isinstance(jumlah, bool) or not 2 <= jumlah <= len(baris):
                galat.append(f"usulan {i + 1}: jumlah revisi harus antara 2 dan {len(baris)}")
            if u["contoh_sebelum"] not in sebelum_tersedia:
                galat.append(f"usulan {i + 1}: contoh_sebelum tidak ditemukan persis pada arsip revisi")
            if u["contoh_sesudah"] not in sesudah_tersedia:
                galat.append(f"usulan {i + 1}: contoh_sesudah tidak ditemukan persis pada arsip revisi")
        return galat
    if tanya is None:
        hasil = llm.panggil("ringkas_pelajaran", sistem, prompt, json=True, validasi=validasi, maks_token=4000)
        data = hasil.data
    else:
        teks, _ = tanya(sistem, prompt)
        data = llm.baca_json(teks)
        galat = validasi(data)
        if galat:
            raise ValueError("; ".join(galat))
    tujuan = DATA / "usulan_pedoman_naskah.json"
    tujuan.parent.mkdir(parents=True, exist_ok=True)
    hasil = {"jumlah_revisi": len(baris), "usulan": data["usulan"]}
    tujuan.write_text(json.dumps(hasil, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return hasil


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Ringkas pelajaran revisi menjadi usulan pedoman.")
    ap.add_argument("--ringkas", action="store_true")
    a = ap.parse_args()
    if a.ringkas:
        print(json.dumps(ringkas(), ensure_ascii=False, indent=2))
