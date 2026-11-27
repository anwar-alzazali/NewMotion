"""Pemeriksa independen naskah terhadap teks dalil yang telah diverifikasi."""
from __future__ import annotations

import json
from pathlib import Path

AKAR = Path(__file__).resolve().parents[2]
_PATH_SKILL = AKAR / "newmotion" / "paket_genre" / "kisah_islami" / "skill" / "periksa_naskah.md"

KATEGORI = {
    "detail_tanpa_dalil",
    "hook_lemah",
    "fakta_kuat_terlewat",
    "janji_tidak_dijawab",
    "kalimat_mengulang",
}
BERAT = {"berat", "sedang", "ringan"}


def validasi_hasil(data: dict, naskah: dict) -> list[str]:
    if not isinstance(data, dict):
        return ["hasil pemeriksa harus berupa objek JSON"]
    galat = []
    temuan = data.get("temuan")
    if not isinstance(temuan, list):
        return ["temuan harus berupa daftar"]
    jumlah = len(naskah.get("beat", []))
    for i, t in enumerate(temuan, 1):
        if not isinstance(t, dict):
            galat.append(f"temuan {i} harus berupa objek")
            continue
        if t.get("kategori") not in KATEGORI:
            galat.append(f"temuan {i}: kategori tidak dikenal")
        if t.get("tingkat") not in BERAT:
            galat.append(f"temuan {i}: tingkat harus berat/sedang/ringan")
        beat = t.get("beat")
        if not isinstance(beat, int) or isinstance(beat, bool) or not 1 <= beat <= jumlah:
            galat.append(f"temuan {i}: nomor beat di luar rentang")
        for k in ("bukti", "alasan", "saran"):
            if not isinstance(t.get(k), str) or not t[k].strip():
                galat.append(f"temuan {i}: {k} wajib berupa teks")
    usulan = data.get("usulan_dalil", [])
    if not isinstance(usulan, list):
        galat.append("usulan_dalil harus berupa daftar")
    else:
        ids = {d.get("id") for d in naskah.get("dalil", []) if isinstance(d, dict)}
        for i, d in enumerate(usulan, 1):
            if not isinstance(d, dict):
                galat.append(f"usulan dalil {i} harus berupa objek")
                continue
            if d.get("id") in ids:
                galat.append(f"usulan dalil {i}: id sudah dipakai")
            if (d.get("jenis") != "quran" or not isinstance(d.get("surah"), int)
                    or isinstance(d.get("surah"), bool) or not isinstance(d.get("ayat"), str)):
                galat.append(f"usulan dalil {i}: hanya rujukan Quran dengan surah/ayat eksplisit yang boleh diusulkan")
            if not isinstance(d.get("alasan"), str) or not d["alasan"].strip():
                galat.append(f"usulan dalil {i}: alasan wajib diisi")
    return galat


def periksa(naskah: dict, *, panggil=None):
    """Periksa naskah. Dalil yang disajikan ke model hanya teks resmi hasil verifikasi."""
    from newmotion.infrastructure import llm

    if not _PATH_SKILL.is_file():
        raise RuntimeError("Skill pemeriksa naskah tidak ditemukan")
    dalil = []
    for d in naskah.get("dalil", []):
        dalil.append({
            "id": d.get("id"), "label": d.get("label"), "status": d.get("status"),
            "derajat": d.get("derajat"), "terjemah_resmi": d.get("terjemah"),
            "sumber_teks": d.get("sumber_teks"),
        })
    isi = json.dumps({
        "judul": naskah.get("judul"), "inti": naskah.get("inti"),
        "beat": naskah.get("beat"), "dalil_terverifikasi": dalil,
    }, ensure_ascii=False, indent=2)
    sistem = _PATH_SKILL.read_text(encoding="utf-8").strip() + (
        "\n\nPeriksa naskah Kisah Islami secara independen terhadap teks dalil resmi yang disertakan. "
        "Jangan menganggap fakta benar hanya karena narasi menyebutnya. Setiap temuan harus menunjuk "
        "nomor beat dan bukti frasa. Kategori wajib: detail_tanpa_dalil, hook_lemah, fakta_kuat_terlewat, "
        "janji_tidak_dijawab, kalimat_mengulang. Tingkat: berat, sedang, ringan. "
        "Usulan ayat baru hanya boleh berupa rujukan Quran (id, jenis=quran, label, surah integer, "
        "ayat string, alasan); jangan menulis teks/terjemah ayat dan jangan memasukkannya ke dalil. "
        "Usulan belum boleh dipakai sampai mesin memverifikasi dari sumber resmi. "
        "Keluarkan JSON: {temuan:[{beat,kategori,tingkat,bukti,alasan,saran}],usulan_dalil:[]}."
    )
    def pemeriksa(hasil):
        return validasi_hasil(hasil, naskah)
    if panggil is None:
        hasil = llm.panggil(
            "periksa_naskah", sistem, isi, json=True,
            validasi=pemeriksa, maks_token=5000, ulang_validasi=1,
        )
    else:
        hasil = panggil("periksa_naskah", sistem, isi, json=True, validasi=pemeriksa)
    return hasil.data, hasil
