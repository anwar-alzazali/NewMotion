"""Antrean naskah NewMotion: ide/naskah dari bot Telegram -> naskah terstruktur -> verifikasi dalil -> tinjauan pemilik.

Bot NewMotion (bot/worker.js) menyimpan masukan ke `antrean/<id>/` lalu memicu workflow `naskah` (workflow_dispatch).
Pekerjaan berat ada di sini (Python, teruji):
- `ide`    : topik -> naskah melalui LLM bersama (aturan Kisah Islami; dalil HANYA rujukan);
- `tempel` : naskah jadi dari pemilik -> dirapikan ke format (narasi TIDAK diubah; dicek otomatis);
- `revisi` : naskah + catatan pemilik -> naskah baru melalui LLM bersama;
lalu: validasi format, tolak huruf Arab di narasi, verifikasi dalil (Quran Foundation + dataset hadis),
tulis `naskah.json` + `status.json`, perbarui kartu status di Telegram, kirim naskah untuk ditinjau.

FORMAT NASKAH (dipakai bot NewMotion; setelah pemilik menyetujui naskah, `pratinjau_visual.py` mengubah beat menjadi kontrak adegan, menjalankan pengarah Kisah Islami, dan membuat MP4 storyboard tanpa TTS):
{
  "judul": "Nabi Hud dan Kaum 'Ad",
  "inti": "satu kalimat inti cerita",
  "dalil": [{"id": "hud50", "jenis": "quran", "label": "QS HUD 50", "surah": 11, "ayat": "50"},
            {"id": "b3343", "jenis": "hadis", "label": "HR. BUKHARI 3343", "kitab": "bukhari", "nomor": "3343"}],
  "beat": [{"narasi": "…", "dalil": ["hud50"], "suasana": "senja", "kata_kunci": ["kaum", "angin"]}]
}
Status: antrean/<id>/status.json -> kartu status (sama persis dengan bot/worker.js `kartuStatus`, diuji dengan fixture).
"""
from __future__ import annotations

import copy
import datetime as _dt
import json
import os
import re
import sys
import unicodedata
import urllib.error
import urllib.request
from pathlib import Path

AKAR = Path(__file__).resolve().parents[2]
ANTREAN = AKAR / "antrean"
SUASANA = ["senja", "dhuha", "malam", "malam_merah", "fajar"]
KITAB = ["bukhari", "muslim", "abudawud", "tirmidhi", "nasai", "ibnmajah"]
TAHAP = [("diterima", "Naskah diterima"), ("dalil", "Dalil diverifikasi"), ("tinjau", "Tinjauan naskah"),
         ("sutradara", "Pratinjau visual"), ("tinjau_visual", "Tinjauan visual"),
         ("narasi", "TTS/Narasi"), ("render", "Render final"), ("periksa", "Pemeriksaan"),
         ("kirim", "Dikirim untuk persetujuan")]
IKON = {"selesai": "✅", "jalan": "⏳", "gagal": "❌", "tunggu": "⏸", "belum": "▫️"}
_ARAB = re.compile(r"[؀-ۿݐ-ݿࢠ-ࣿﭐ-﷿ﹰ-﻿]")


# ---------------- status & kartu ----------------
def status_baru(
    id_: str, judul: str, sumber: str, *,
    genre: str = "kisah_islami", konteks_konten: str = "islami",
) -> dict:
    """Buat status antrean dengan metadata produksi eksplisit.

    Nilai bawaan mempertahankan alur Telegram lama; genre lain tidak diaktifkan
    sebelum paket pengarah, validator, dan kebijakan genre tersebut tersedia.
    """
    return {
        "id": id_, "judul": judul, "sumber": sumber,
        "genre": genre, "konteks_konten": konteks_konten,
        "tahap": {k: "belum" for k, _ in TAHAP}, "ket": {},
        "dibuat": _sekarang(), "diperbarui": _sekarang(),
    }


def kebijakan_naskah(status: dict, naskah: dict | None = None) -> dict:
    """Pastikan jalur antrean hanya memakai kebijakan yang benar-benar tersedia.

    Metadata status adalah sumber otoritatif; metadata naskah hanya menjadi
    cadangan untuk antrean lama. Paket genre selain Kisah Islami belum aktif.
    """
    from newmotion.application.pengklasifikasi_konten import klasifikasikan_konten

    data_lama = naskah or {}
    genre = status.get("genre") if status.get("genre") is not None else data_lama.get("genre")
    konteks = (
        status.get("konteks_konten")
        if status.get("konteks_konten") is not None
        else data_lama.get("konteks_konten")
    )
    genre = "kisah_islami" if genre is None else genre
    if not isinstance(genre, str) or not genre.strip():
        raise ValueError("Metadata genre kosong/tidak sah; antrean tidak boleh diproses.")
    if konteks is None and genre == "kisah_islami":
        konteks = "islami"
    if not isinstance(konteks, str) or not konteks.strip():
        raise ValueError("Metadata konteks_konten kosong/tidak sah; antrean tidak boleh diproses.")

    sumber = dict(naskah or {})
    sumber["genre"] = genre
    if konteks is not None:
        sumber["konteks_konten"] = konteks
    hasil = klasifikasikan_konten(sumber)
    if hasil["perlu_klarifikasi"]:
        raise ValueError(
            "Genre/konteks naskah perlu diklarifikasi sebelum dibuat: "
            + hasil["keputusan"]
        )
    if genre != "kisah_islami":
        raise ValueError(
            f"Paket genre '{genre}' belum tersedia pada jalur antrean naskah; "
            "untuk saat ini hanya Kisah Islami yang dapat diproses."
        )
    if not hasil["kebijakan"]["aktifkan_kebijakan_islami"]:
        raise ValueError("Jalur Kisah Islami wajib mengaktifkan kebijakan konten Islami.")
    return {
        "genre": hasil["genre"],
        "konteks_konten": hasil["konteks_konten"],
        "kebijakan": hasil["kebijakan"],
    }


def kartu(st: dict) -> str:
    """Teks kartu status. HARUS identik dengan kartuStatus() di bot/worker.js (tests/data/kartu_status.json)."""
    baris = [f"🎬 {st.get('judul') or st['id']}"]
    for k, label in TAHAP:
        keadaan = st["tahap"].get(k, "belum")
        ket = (st.get("ket") or {}).get(k)
        baris.append(f"{IKON[keadaan]} {label}" + (f" — {ket}" if ket else ""))
    if st.get("uji_cerita_ringkas"):
        baris.append("🧪 Uji cerita: " + st["uji_cerita_ringkas"])
    if st.get("pemeriksaan_naskah_ringkas"):
        baris.append("🔎 Pemeriksa naskah: " + st["pemeriksaan_naskah_ringkas"])
    return "\n".join(baris)


def atur(st: dict, tahap: str, keadaan: str, ket: str | None = None) -> dict:
    st["tahap"][tahap] = keadaan
    if ket:
        st.setdefault("ket", {})[tahap] = ket
    else:
        st.setdefault("ket", {}).pop(tahap, None)
    st["diperbarui"] = _sekarang()
    return st


def _sekarang() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


# ---------------- normalisasi & validasi naskah ----------------
_JENIS = {"quran": "quran", "qs": "quran", "ayat": "quran", "al-quran": "quran", "alquran": "quran", "al quran": "quran",
          "hadis": "hadis", "hadits": "hadis", "hadith": "hadis", "hr": "hadis"}


def normalisasi(n: dict) -> dict:
    """Rapikan salah ketik yang aman tanpa menutupi kesalahan struktur untuk validator."""
    if not isinstance(n, dict):
        return n
    daftar_dalil = n.get("dalil")
    if not isinstance(daftar_dalil, list):
        return n
    for d in daftar_dalil:
        if not isinstance(d, dict):
            continue
        j = _JENIS.get(str(d.get("jenis", "")).strip().lower())
        if j:
            d["jenis"] = j
        if d.get("jenis") == "quran" and str(d.get("surah", "")).strip().isdigit():
            d["surah"] = int(str(d["surah"]).strip())
        if "ayat" in d:
            d["ayat"] = str(d["ayat"]).replace(" ", "")
        if "nomor" in d:
            d["nomor"] = str(d["nomor"]).strip().lower()
        if "kitab" in d:
            d["kitab"] = re.sub(r"[^a-z]", "", str(d["kitab"]).lower()).replace("sahih", "").replace("sunan", "")
        d.setdefault("label", d.get("id", "dalil"))
    daftar_beat = n.get("beat")
    if not isinstance(daftar_beat, list):
        return n
    ada = {d.get("id") for d in daftar_dalil if isinstance(d, dict) and isinstance(d.get("id"), str)}
    for i, b in enumerate(daftar_beat, 1):
        if not isinstance(b, dict):
            continue
        rujukan = b.get("dalil")
        if isinstance(rujukan, list):
            hilang = [r for r in rujukan if isinstance(r, str) and r not in ada]
            if hilang:
                # Jangan menghapus rujukan yang tidak dikenal: validator harus melihatnya
                # agar beat faktual tidak lolos setelah kehilangan satu-satunya dalil.
                peringatan = n.get("peringatan")
                if not isinstance(peringatan, list):
                    peringatan = []
                    n["peringatan"] = peringatan
                peringatan.append(
                    f"beat {i}: rujukan {', '.join(map(str, hilang))} tidak ditemukan di daftar dalil")
        if b.get("suasana") not in SUASANA:
            b.pop("suasana", None)
    return n

def validasi(n: dict) -> list[str]:
    """Validasi format naskah dan beri petunjuk berbahasa Indonesia yang bisa ditindaklanjuti."""
    if not isinstance(n, dict):
        return ["naskah harus berupa objek JSON, bukan teks atau daftar"]
    g: list[str] = []
    if not isinstance(n.get("judul"), str) or not n["judul"].strip():
        g.append("judul kosong; isi dengan judul cerita")
    if not isinstance(n.get("inti"), str) or not n["inti"].strip():
        g.append("inti kosong; tulis satu kalimat tentang pesan/peristiwa utama cerita")

    daftar = n.get("dalil", [])
    if not isinstance(daftar, list):
        g.append("dalil harus berupa daftar rujukan; gunakan [] bila tidak ada")
        daftar = []
    ids: set[str] = set()
    for i, d in enumerate(daftar, 1):
        if not isinstance(d, dict):
            g.append(f"dalil ke-{i} harus berupa objek dengan id, jenis, label, dan rujukan")
            continue
        id_ = d.get("id")
        if not isinstance(id_, str) or not id_.strip():
            g.append(f"dalil ke-{i} tanpa id; beri id singkat yang unik")
        elif id_ in ids:
            g.append(f"id dalil '{id_}' dipakai lebih dari sekali; satukan rujukan yang sama")
        else:
            ids.add(id_)
        if not isinstance(d.get("label"), str) or not d["label"].strip():
            g.append(f"dalil ke-{i}: label kosong; tulis label rujukan yang mudah dibaca")
        if d.get("jenis") == "quran":
            if (not isinstance(d.get("surah"), int) or isinstance(d.get("surah"), bool)
                    or not (1 <= d["surah"] <= 114)
                    or not re.fullmatch(r"\d+(-\d+)?", str(d.get("ayat", "")))):
                g.append(f"dalil {id_ or i}: nomor surah/ayat tidak sah; gunakan surah 1–114 dan ayat angka atau rentang, misalnya '37-38'")
        elif d.get("jenis") == "hadis":
            if d.get("kitab") not in KITAB:
                g.append(f"dalil {id_ or i}: kitab '{d.get('kitab')}' belum didukung; pilih {', '.join(KITAB)}")
            if not re.fullmatch(r"\d+[a-z]?", str(d.get("nomor", ""))):
                g.append(f"dalil {id_ or i}: nomor hadis tidak sah; gunakan nomor dari sumber rujukan")
        else:
            g.append(f"dalil {id_ or i}: jenis harus 'quran' atau 'hadis'")

    beat = n.get("beat")
    if not isinstance(beat, list) or not beat:
        return g + ["beat kosong; pecah cerita menjadi satu atau beberapa bagian (beat)"]
    for i, b in enumerate(beat, 1):
        if not isinstance(b, dict):
            g.append(f"beat {i} harus berupa objek JSON")
            continue
        narasi = b.get("narasi")
        if not isinstance(narasi, str) or not narasi.strip():
            g.append(f"beat {i}: narasi kosong; tulis kalimat bahasa Indonesia")
        elif _ARAB.search(narasi):
            g.append(f"beat {i}: ada huruf Arab di narasi; bacaan Arab tidak disuarakan AI, tampilkan melalui sumber/kartu dalil")
        kata = b.get("kata_kunci")
        if not isinstance(kata, list) or any(not isinstance(x, str) or not x.strip() for x in kata):
            g.append(f"beat {i}: kata_kunci harus berupa daftar kata/frasa singkat; gunakan [] bila tidak ada")
        peran = b.get("peran")
        if not isinstance(peran, list) or any(not isinstance(x, str) or not x.strip() for x in peran):
            g.append(f"beat {i}: peran harus berupa daftar nama tokoh/pihak yang hadir atau dibahas; gunakan [] bila tidak ada")
        if isinstance(peran, list) and any(
            isinstance(x, str) and _polos(x).split(" ", 1)[0] in {"allah", "tuhan"} for x in peran
        ):
            g.append(f"beat {i}: Allah/Tuhan tidak boleh menjadi peran visual; pindahkan ke narasi atau tampilkan firman sebagai teks dan cahaya tanpa sosok")
        dialog = b.get("dialog", [])
        if not isinstance(dialog, list):
            g.append(f"beat {i}: dialog harus berupa daftar giliran bicara; gunakan [] bila tidak ada")
        else:
            nama_peran = {x for x in peran if isinstance(x, str)} if isinstance(peran, list) else set()
            for j, giliran in enumerate(dialog, 1):
                if not isinstance(giliran, dict):
                    g.append(f"beat {i} dialog {j}: harus berupa objek dengan pembicara dan ucapan")
                    continue
                for kunci in ("pembicara", "ucapan"):
                    if not isinstance(giliran.get(kunci), str) or not giliran[kunci].strip():
                        g.append(f"beat {i} dialog {j}: {kunci} kosong; isi nama peran/ucapan")
                if giliran.get("penjawab") is not None and not isinstance(giliran.get("penjawab"), str):
                    g.append(f"beat {i} dialog {j}: penjawab harus berupa nama peran atau null")
                for sisi in ("pembicara", "penjawab"):
                    nama = giliran.get(sisi)
                    if isinstance(nama, str) and nama.strip() and nama not in nama_peran:
                        g.append(f"beat {i} dialog {j}: {sisi} '{nama}' belum tercantum di peran; tambahkan agar bisa ditata dan digambar dengan aman")
                    if isinstance(nama, str) and _polos(nama) in {"allah", "tuhan"}:
                        g.append(f"beat {i} dialog {j}: Allah tidak digambarkan sebagai tokoh; gunakan narasi atau cahaya tanpa sosok")
        rujukan = b.get("dalil")
        if not isinstance(rujukan, list) or any(not isinstance(x, str) for x in rujukan):
            g.append(f"beat {i}: dalil harus berupa daftar id rujukan; gunakan [] bila beat bukan pernyataan fakta")
        else:
            for r in rujukan:
                if isinstance(r, str) and r not in ids:
                    g.append(f"beat {i}: id dalil '{r}' tidak ditemukan; periksa ejaan atau tambahkan rujukannya")
        suasana = b.get("suasana")
        if suasana is not None and suasana not in SUASANA:
            g.append(f"beat {i}: suasana '{suasana}' tidak dikenal; pilih {', '.join(SUASANA)}")
    return g

def _polos(s: str) -> str:
    s = "".join(c for c in unicodedata.normalize("NFKD", s.lower()) if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def narasi_utuh(n: dict, sumber: str) -> list[str]:
    """Naskah tempelan: setiap narasi harus ada di teks asli (narasi pemilik tidak boleh diubah AI). Pengaman kedua;
    jalur tempel mengambil narasi langsung dari teks pemilik."""
    asal = _polos(" ".join(paragraf(sumber)[1]))
    return [f"beat {i}: narasi tidak sama dengan naskah asli (\"{b['narasi'][:60]}…\")"
            for i, b in enumerate(n["beat"], 1) if _polos(b["narasi"]) not in asal]


_RUJUKAN = re.compile(r"\s*[\(\[]\s*(?:QS|Q\.S\.|HR|H\.R\.|Hadis|Hadits)[^\)\]]*[\)\]]", re.I)


def paragraf(teks: str) -> tuple[str | None, list[str]]:
    """Naskah tempelan -> judul dan paragraf narasi tanpa catatan rujukan dalam kurung."""
    judul, isi = None, []
    for p in re.split(r"\n\s*\n", teks.strip()):
        p = " ".join(p.split())
        m = re.match(r"(?i)^judul\s*:\s*(.+)$", p)
        if m and judul is None and not isi:
            judul = m.group(1).strip()
            continue
        p = _RUJUKAN.sub("", p).strip()
        if p:
            isi.append(p)
    return judul, isi


# ---------------- Jalur LLM bersama untuk penulisan naskah ----------------
_PATH_SKILL = AKAR / "newmotion" / "paket_genre" / "kisah_islami" / "skill" / "naskah.md"


def validasi_uji_cerita(data):
    uji = data.get("uji_cerita")
    if not isinstance(uji, dict):
        return ["uji_cerita harus berupa objek"]
    wajib = ("kalimat_inti", "fakta_terkuat_detik_0", "jawaban_hook",
             "momen_emosi_kejutan", "alasan_interaksi", "kalimat_dibuang")
    galat = []
    for k in wajib:
        v = uji.get(k)
        if k == "kalimat_dibuang":
            if not isinstance(v, list) or any(not isinstance(x, str) for x in v):
                galat.append("uji_cerita.kalimat_dibuang harus berupa daftar teks")
        elif not isinstance(v, str) or not v.strip():
            galat.append(f"uji_cerita.{k} wajib diisi")
    return galat


def validasi_peta_tempel(data, jumlah_paragraf=None, rujukan_asli=()):
    """Pastikan pemetaan mencakup naskah asli tanpa paragraf hilang/terduplikasi."""
    if not isinstance(data, dict):
        return ["pemetaan tempel harus berupa objek JSON"]
    galat = []
    for k in ("judul", "inti"):
        if not isinstance(data.get(k), str) or not data[k].strip():
            galat.append(f"{k} pemetaan tempel wajib diisi")
    daftar_dalil = data.get("dalil", [])
    if not isinstance(daftar_dalil, list):
        galat.append("dalil pemetaan tempel harus berupa daftar")
        daftar_dalil = []
    else:
        label_ai = {
            _polos(d.get("label", "")) for d in daftar_dalil if isinstance(d, dict)
        }
        label_asli = {
            _polos(str(r).strip("()[] ")) for r in rujukan_asli
        }
        if label_ai != label_asli:
            galat.append(
                "dalil tempel harus sama persis dengan rujukan yang ditulis pemilik; "
                "AI tidak boleh menambah, mengubah, atau menghilangkan rujukan"
            )
    if not isinstance(data.get("beat"), list) or not data["beat"]:
        return galat + ["pemetaan tempel harus memiliki daftar beat"]

    sudah = set()
    for i, b in enumerate(data["beat"], 1):
        if not isinstance(b, dict):
            galat.append(f"beat {i} harus berupa objek")
            continue
        p = b.get("paragraf")
        if not isinstance(p, list) or not p or any(
            not isinstance(x, int) or isinstance(x, bool) or x < 1 for x in p
        ):
            galat.append(f"beat {i}: paragraf harus berupa daftar nomor positif")
            continue
        if p != sorted(p):
            galat.append(f"beat {i}: urutan paragraf harus menaik agar narasi tidak terbalik")
        for nomor in p:
            if nomor in sudah:
                galat.append(f"paragraf {nomor} dipetakan lebih dari sekali")
            sudah.add(nomor)
            if jumlah_paragraf is not None and nomor > jumlah_paragraf:
                galat.append(f"paragraf {nomor} tidak ada dalam naskah asli")
    if jumlah_paragraf is not None:
        hilang = sorted(set(range(1, jumlah_paragraf + 1)) - sudah)
        if hilang:
            galat.append("paragraf belum dipetakan: " + ", ".join(map(str, hilang)))
    return galat


def ringkasan_uji_cerita(u):
    kunci = ("kalimat_inti", "fakta_terkuat_detik_0", "jawaban_hook",
             "momen_emosi_kejutan", "alasan_interaksi")
    return " | ".join(str(u.get(k, "")) for k in kunci)[:900]


def buat_naskah(mode, masukan, naskah_lama=None, *, tanya=None):
    """Jalur produksi memakai llm.panggil; tanya hanya seam injeksi unit test."""
    from newmotion.infrastructure import llm

    if not _PATH_SKILL.is_file():
        raise RuntimeError("Skill penulisan naskah tidak ditemukan")
    skill = _PATH_SKILL.read_text(encoding="utf-8").strip()
    if mode == "tempel":
        judul, par = paragraf(masukan)
        isi = "Naskah bernomor:\n" + "\n".join(f"[{i}] {p}" for i, p in enumerate(par, 1))
        isi += "\nRujukan asli pemilik:\n" + "\n".join(m.group(0) for m in _RUJUKAN.finditer(masukan))
        sistem = skill + "\nMODE TEMPEL: petakan paragraf; jangan mengubah satu kata pun narasi. Jangan menambah dalil. JSON: {judul, inti, dalil, beat:[{paragraf:[1], dalil:[], suasana, kata_kunci:[], peran:[], dialog:[]}]}"
        tahap = "rapikan"

        def pemeriksa(data):
            galat = validasi_peta_tempel(data, len(par), [m.group(0) for m in _RUJUKAN.finditer(masukan)])
            if galat:
                return galat
            beat_uji = []
            for b in data["beat"]:
                narasi = " ".join(par[i - 1] for i in b["paragraf"] if i <= len(par))
                beat_uji.append({
                    "narasi": narasi, "dalil": b.get("dalil", []),
                    "kata_kunci": b.get("kata_kunci", []), "peran": b.get("peran", []),
                    "dialog": b.get("dialog", []), "suasana": b.get("suasana"),
                })
            sementara = {"judul": data["judul"], "inti": data["inti"],
                         "dalil": data.get("dalil", []), "beat": beat_uji}
            return validasi(sementara)
    elif mode == "ide":
        isi = "Ide pemilik:\n" + masukan
        sistem = skill + "\nMODE IDE: tulis cerita utuh. Sertakan uji_cerita dengan kalimat_inti, fakta_terkuat_detik_0, jawaban_hook, momen_emosi_kejutan, alasan_interaksi, kalimat_dibuang (daftar). Keluarkan JSON naskah."
        tahap = "naskah"
        def pemeriksa(d):
            return validasi(d) + validasi_uji_cerita(d)
    elif mode == "revisi":
        isi = f"NASKAH SAAT INI:\n{json.dumps(naskah_lama, ensure_ascii=False)}\nCATATAN PEMILIK:\n{masukan}"
        sistem = skill + "\nMODE REVISI: ubah hanya bagian yang diminta pemilik; bagian lain kata demi kata. Sertakan uji_cerita lengkap. Keluarkan JSON naskah."
        tahap = "naskah"
        def pemeriksa(d):
            return validasi(d) + validasi_uji_cerita(d)
    else:
        raise ValueError(f"mode tidak dikenal: {mode}")

    if tanya is None:
        hasil_ai = llm.panggil(tahap, sistem, isi, json=True, validasi=pemeriksa,
                               maks_token=8000, ulang_validasi=1)
        data = hasil_ai.data
    else:
        teks, token = tanya(sistem, isi)
        data = llm.baca_json(teks)
        galat = pemeriksa(data)
        if galat:
            raise ValueError("keluaran ditolak validator: " + "; ".join(galat[:8]))
        hasil_ai = llm.Jawaban(teks, "uji", "palsu", token_masuk=token)

    if mode != "tempel":
        return data, hasil_ai

    dipakai, terurut = set(), []
    for b in data["beat"]:
        nomor = [x for x in b.get("paragraf", []) if isinstance(x, int) and not isinstance(x, bool)
                 and 1 <= x <= len(par) and x not in dipakai]
        if not nomor:
            continue
        dipakai.update(nomor)
        terurut.append((min(nomor), {"narasi": " ".join(par[x - 1] for x in nomor),
            "dalil": b.get("dalil", []), "suasana": b.get("suasana"),
            "kata_kunci": b.get("kata_kunci", []), "peran": b.get("peran", []),
            "dialog": b.get("dialog", [])}))
    for i, p in enumerate(par, 1):
        if i not in dipakai:
            terurut.append((i, {"narasi": p, "dalil": [], "kata_kunci": [], "peran": [], "dialog": []}))
    beat = [b for _, b in sorted(terurut, key=lambda x: x[0])]
    for b in beat:
        if not b.get("suasana"):
            b.pop("suasana", None)
    return {"judul": judul or data.get("judul") or (par[0][:60] if par else "Naskah"),
            "inti": data.get("inti", ""), "dalil": data.get("dalil", []), "beat": beat}, hasil_ai


# ---------------- Telegram ----------------
def tg(metode: str, badan: dict) -> dict:
    token = (os.environ.get("TELEGRAM_BOT_TOKEN") or "").strip()
    if not token:
        return {"ok": False}
    req = urllib.request.Request(f"https://api.telegram.org/bot{token}/{metode}", data=json.dumps(badan).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        return json.load(urllib.request.urlopen(req, timeout=30))
    except urllib.error.HTTPError as e:
        return {"ok": False, "kode": e.code}


def tombol_kartu(st: dict) -> list:
    i = st["id"]
    if st["tahap"]["tinjau"] in ("belum", "jalan") and st["tahap"]["dalil"] == "selesai":
        return [[{"text": "✅ Lanjut", "callback_data": f"nl:{i}"}, {"text": "✏️ Revisi", "callback_data": f"nr:{i}"}],
                [{"text": "❌ Batal", "callback_data": f"nb:{i}"}, {"text": "🏠 Menu", "callback_data": "menu"}]]
    # Dalil gagal: naskah tidak boleh lanjut ke visual (sama dengan tombolKartu di bot/worker.js).
    if st["tahap"]["tinjau"] in ("belum", "jalan") and st["tahap"]["dalil"] == "gagal":
        return [[{"text": "✏️ Revisi dalil", "callback_data": f"nr:{i}"}, {"text": "❌ Batal", "callback_data": f"nb:{i}"}],
                [{"text": "🏠 Menu", "callback_data": "menu"}]]
    return [[{"text": "🏠 Menu", "callback_data": "menu"}]]


def perbarui_kartu(st: dict) -> None:
    chat = st.get("chat") or (os.environ.get("TELEGRAM_CHAT_ID") or "").strip()
    if not chat:
        return
    badan = {"chat_id": chat, "text": kartu(st), "reply_markup": {"inline_keyboard": tombol_kartu(st)}}
    if st.get("pesan_kartu"):
        r = tg("editMessageText", {**badan, "message_id": st["pesan_kartu"]})
        if r.get("ok") or "not modified" in str(r):
            return
    r = tg("sendMessage", badan)
    if r.get("ok"):
        st["pesan_kartu"] = r["result"]["message_id"]


def teks_tinjauan(n: dict) -> list[str]:
    """Naskah untuk dibaca pemilik: per beat + status dalil + terjemah resmi (agar makna bisa dinilai)."""
    dl = {d["id"]: d for d in n.get("dalil", [])}
    out = [f"📝 {n['judul']}" + (f"\nInti: {n['inti']}" if n.get("inti") else "")
           + "".join(f"\n⚠️ {p}" for p in n.get("peringatan", []))]
    sudah = set()  # terjemah dalil yang sama cukup ditampilkan sekali
    for i, b in enumerate(n["beat"], 1):
        s = f"\n{i}. {b['narasi']}"
        if not b.get("dalil"):
            s += "\n   ▫️ tanpa dalil: pastikan bukan klaim karangan"
        for r in b.get("dalil") or []:
            d = dl.get(r, {})
            tanda = "✅" if d.get("status") == "terverifikasi" and d.get("derajat", "sahih") in ("sahih", "hasan") else "⚠️"
            s += f"\n   {tanda} {d.get('label', r)}" + (f" ({d['derajat']})" if d.get("derajat") else "")
            if d.get("alasan"):
                s += f": {d['alasan']}"
            elif r in sudah:
                s += " (terjemah di atas)"
            elif d.get("terjemah"):
                s += f": “{d['terjemah'][:220]}{'…' if len(d['terjemah']) > 220 else ''}”"
            sudah.add(r)
        out.append(s)
    gagal = [d.get("label", d.get("id")) for d in n.get("dalil", [])
             if not (d.get("status") == "terverifikasi" and d.get("derajat", "sahih") in ("sahih", "hasan"))]
    if gagal:
        out.append(f"\n⛔ {len(gagal)} dalil belum lolos ({', '.join(map(str, gagal))}). Naskah tidak bisa lanjut ke visual; "
                   "ketuk ✏️ Revisi dalil untuk mengganti/membuang dalil itu, atau ❌ Batal.")
    else:
        out.append("\nCek: apakah setiap kalimat sesuai makna dalilnya? Lalu ketuk ✅ Lanjut / ✏️ Revisi / ❌ Batal di kartu status.")
    potong, buf = [], ""
    for bagian in out:  # batas pesan Telegram 4096
        if len(buf) + len(bagian) > 3800:
            potong.append(buf)
            buf = ""
        buf += bagian + "\n"
    return potong + [buf]


# ---------------- proses satu antrean ----------------
def proses(id_: str, mode: str, *, folder: Path = ANTREAN, tanya=None, quran=None, kirim_tg: bool = True) -> dict:
    d = folder / id_
    st = json.loads((d / "status.json").read_text(encoding="utf-8"))
    masukan = (d / ("catatan.txt" if mode == "revisi" else "masukan.txt")).read_text(encoding="utf-8")
    lama = json.loads((d / "naskah.json").read_text(encoding="utf-8")) if mode == "revisi" else None
    atur(st, "diterima", "jalan", "naskah sedang disusun AI" if mode != "tempel" else "naskah sedang dirapikan")
    for k in ("dalil", "tinjau"):
        atur(st, k, "belum")
    _tulis(d, st, None, kirim_tg)
    try:
        metadata = kebijakan_naskah(st, lama)
        n, hasil_ai = buat_naskah(mode, masukan, lama, tanya=tanya)
        n = normalisasi(n)
        n["genre"] = metadata["genre"]
        n["konteks_konten"] = metadata["konteks_konten"]
        galat = validasi(n)
        if mode in ("ide", "revisi"):
            galat += validasi_uji_cerita(n)
        if mode == "tempel" and not galat:
            galat = narasi_utuh(n, masukan)
    except Exception as e:  # noqa: BLE001 - pesan untuk pemilik
        atur(st, "diterima", "gagal", f"gagal menyusun naskah: {str(e)[:150]}")
        _tulis(d, st, None, kirim_tg)
        return st
    st["judul"] = n.get("judul") or st.get("judul")
    token = hasil_ai.token_masuk + hasil_ai.token_keluar
    st["token_ai"] = st.get("token_ai", 0) + token
    st["biaya_ai_usd"] = round(st.get("biaya_ai_usd", 0.0) + hasil_ai.biaya_usd, 6)
    # Harga Gemini belum dipatok di config; jangan menyajikan nol sebagai biaya aktual.
    biaya_status = (
        "belum_terverifikasi"
        if hasil_ai.penyedia == "google" and hasil_ai.biaya_usd == 0
        else "tercatat"
    )
    st["biaya_ai_status"] = biaya_status
    st["naskah_ai"] = {"tahap": "rapikan" if mode == "tempel" else "naskah",
        "model": hasil_ai.model, "penyedia": hasil_ai.penyedia,
        "token_masuk": hasil_ai.token_masuk, "token_keluar": hasil_ai.token_keluar,
        "biaya_usd": hasil_ai.biaya_usd, "biaya_status": biaya_status,
        "percobaan": hasil_ai.percobaan}
    if isinstance(n.get("uji_cerita"), dict):
        st["uji_cerita_ringkas"] = ringkasan_uji_cerita(n["uji_cerita"])
    if galat:
        atur(st, "diterima", "gagal", "; ".join(galat)[:300])
        _tulis(d, st, n, kirim_tg)
        return st
    atur(st, "diterima", "selesai", f"{len(n['beat'])} beat, {len(n.get('dalil', []))} dalil · {hasil_ai.model}")
    atur(st, "dalil", "jalan")
    _tulis(d, st, n, kirim_tg)
    from newmotion.paket_genre.kisah_islami.dalil.verifikasi import verifikasi
    n, laporan = verifikasi(n, quran=quran)

    # Pemeriksa independen hanya dijalankan pada jalur produksi; seam tanya dipakai tes tanpa biaya.
    if tanya is None:
        from newmotion.application import pemeriksa_naskah
        temuan, meta_periksa = pemeriksa_naskah.periksa(n)
        token_periksa = meta_periksa.token_masuk + meta_periksa.token_keluar
        st["token_ai"] = st.get("token_ai", 0) + token_periksa
        st["biaya_ai_usd"] = round(st.get("biaya_ai_usd", 0.0) + meta_periksa.biaya_usd, 6)
        st["pemeriksaan_naskah_ai"] = {
            "tahap": "periksa_naskah", "model": meta_periksa.model, "penyedia": meta_periksa.penyedia,
            "token_masuk": meta_periksa.token_masuk, "token_keluar": meta_periksa.token_keluar,
            "biaya_usd": meta_periksa.biaya_usd, "percobaan": meta_periksa.percobaan,
        }
        usulan_terverifikasi = []
        usulan = temuan.get("usulan_dalil", [])
        if usulan:
            calon, _ = verifikasi({"dalil": usulan}, quran=quran)
            usulan_terverifikasi = [
                d for d in calon.get("dalil", [])
                if d.get("status") == "terverifikasi"
                and d.get("diverifikasi_oleh")
                and (d.get("derajat", "sahih") in ("sahih", "hasan"))
            ]
        berat = [x for x in temuan.get("temuan", []) if x.get("tingkat") == "berat"]
        if berat and mode != "tempel":
            arahan = {
                "temuan_pemeriksa": temuan.get("temuan", []),
                "dalil_baru_terverifikasi": usulan_terverifikasi,
                "aturan": [
                    "Perbaiki temuan berat tanpa menambah fakta di luar teks dalil.",
                    "Gunakan dalil baru hanya jika ada di daftar dalil_baru_terverifikasi.",
                    "Jangan membuat nomor/teks/terjemah dalil baru.",
                    "Pertahankan genre, adab, dan struktur beat.",
                    "Sertakan uji_cerita lengkap.",
                ],
            }
            lama_naskah = json.dumps(n, ensure_ascii=False)
            revisi, meta_penulis = buat_naskah(
                "revisi", "PERBAIKAN WAJIB BERDASARKAN PEMERIKSA INDEPENDEN:\\n"
                + json.dumps(arahan, ensure_ascii=False), n
            )
            daftar_diizinkan = {d["id"]: d for d in n.get("dalil", []) if isinstance(d, dict)}
            daftar_diizinkan.update({d["id"]: d for d in usulan_terverifikasi if d.get("id")})
            revisi["dalil"] = [
                copy.deepcopy(daftar_diizinkan[d["id"]])
                for d in revisi.get("dalil", [])
                if isinstance(d, dict) and d.get("id") in daftar_diizinkan
            ]
            galat_revisi = validasi(revisi) + validasi_uji_cerita(revisi)
            if not galat_revisi:
                berubah = json.dumps(revisi, ensure_ascii=False, sort_keys=True) != json.dumps(n, ensure_ascii=False, sort_keys=True)
                if berubah:
                    n = normalisasi(revisi)
                    n, laporan = verifikasi(n, quran=quran)
                    # Verifikasi ulang setelah perbaikan memastikan dalil yang berubah tidak lolos dari cache lama.
                    temuan, meta_periksa_ulang = pemeriksa_naskah.periksa(n)
                    st["token_ai"] += meta_penulis.token_masuk + meta_penulis.token_keluar + meta_periksa_ulang.token_masuk + meta_periksa_ulang.token_keluar
                    st["biaya_ai_usd"] = round(st["biaya_ai_usd"] + meta_penulis.biaya_usd + meta_periksa_ulang.biaya_usd, 6)
                    st["pemeriksaan_naskah_ai"]["perbaikan"] = {
                        "model_penulis": meta_penulis.model,
                        "model_verifikasi_ulang": meta_periksa_ulang.model,
                        "token": meta_penulis.token_masuk + meta_penulis.token_keluar + meta_periksa_ulang.token_masuk + meta_periksa_ulang.token_keluar,
                        "biaya_usd": round(meta_penulis.biaya_usd + meta_periksa_ulang.biaya_usd, 6),
                    }
            else:
                temuan.setdefault("temuan", []).append({
                    "beat": 1, "kategori": "detail_tanpa_dalil", "tingkat": "berat",
                    "bukti": "Keluaran perbaikan penulis tidak lolos validator.",
                    "alasan": "; ".join(galat_revisi[:4]), "saran": "Perlu revisi manual pemilik.",
                })
        st["pemeriksaan_naskah"] = temuan
        jumlah_t = len(temuan.get("temuan", []))
        jumlah_perbaikan = len(berat) if berat and mode != "tempel" else 0
        st["pemeriksaan_naskah_ringkas"] = (
            f"{jumlah_t} temuan; {jumlah_perbaikan} putaran perbaikan otomatis"
            if jumlah_t else "tidak ada temuan"
        )
    lolos = [x for x in n.get("dalil", []) if x.get("status") == "terverifikasi" and x.get("derajat", "sahih") in ("sahih", "hasan")]
    total = len(n.get("dalil", []))
    if total and len(lolos) < total:
        atur(st, "dalil", "gagal", f"{len(lolos)}/{total} lolos; yang ⚠️ harus diganti atau dibuang")
    else:
        atur(st, "dalil", "selesai", f"{len(lolos)}/{total}" if total else "tanpa dalil")
    atur(st, "tinjau", "jalan", "menunggu Anda membaca naskah")
    st["laporan_dalil"] = laporan
    _tulis(d, st, n, kirim_tg)
    if kirim_tg:
        chat = st.get("chat") or os.environ.get("TELEGRAM_CHAT_ID", "").strip()
        for t in teks_tinjauan(n):
            tg("sendMessage", {"chat_id": chat, "text": t})
        if st.get("pesan_kartu"):  # kartu dipindah ke bawah naskah supaya tombolnya dekat dengan yang dibaca
            tg("deleteMessage", {"chat_id": chat, "message_id": st.pop("pesan_kartu")})
        perbarui_kartu(st)
        _tulis(d, st, n, False)
    return st


def _tulis(d: Path, st: dict, naskah: dict | None, kirim_tg: bool) -> None:
    if kirim_tg:
        perbarui_kartu(st)
    if naskah is not None:
        (d / "naskah.json").write_text(json.dumps(naskah, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (d / "status.json").write_text(json.dumps(st, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":  # python -m newmotion.application.antrean_naskah <id> <ide|tempel|revisi>
    from newmotion.paket_genre.kisah_islami.dalil.quran import QuranBertingkat, QuranComPublik, QuranFoundation
    q = QuranBertingkat(QuranFoundation() if os.environ.get("QURAN_FOUNDATION_CLIENT_ID") else None, QuranComPublik())
    hasil = proses(sys.argv[1], sys.argv[2], quran=q)
    print(kartu(hasil))
    print("penyedia AI:", (hasil.get("naskah_ai") or {}).get("penyedia", "-"))
    sys.exit(1 if "gagal" in hasil["tahap"]["diterima"] else 0)
