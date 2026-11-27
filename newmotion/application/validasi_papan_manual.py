"""Validator papan manual: menangkap kesalahan JSON tulisan AI chat SEBELUM narasi dibuat (hemat kredit).

Kesalahan yang ditemukan di uji Meta/Gemini/ChatGPT (27 Nov 2026) dan sebabnya:
- parameter benda dibungkus "o": {...}  -> renderer mengabaikan semuanya (matahari/kerumunan/kartu hilang);
- benda ditulis sebagai kunci shot ("surya": {...}) -> tidak tergambar;
- "@kata" yang tidak ada di narasi (mis. "@sekali" untuk "sekali-kali") -> render gagal;
- kartu_dalil tanpa kitab/terjemahan, atau teks Arab di kolom "teks" -> kartu kosong/hancur;
- judul satu baris terlalu lebar -> terpotong di tepi layar;
- berkas efek suara yang tidak ada.

`periksa(spek)` mengembalikan (galat, peringatan). Galat menghentikan jalur manual dengan daftar yang bisa
disalin balik ke sesi chat; peringatan hanya dilaporkan.
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

from newmotion.application.katalog_renderer import CERITA_JS, UMUM, katalog
from newmotion.application.kemampuan_tokoh import HADAP, kemampuan

AKAR = Path(__file__).resolve().parents[2]
DASAR_KISAH = AKAR / "mesin-video" / "papan" / "kisah"
ARAB = re.compile(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]")
FONT = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
LEBAR_AMAN = 1060  # px dari 1080 (termasuk garis tepi teks 16 px): sisa ±10 px di tiap sisi
KUNCI_SHOT_MANUAL = {"narasi", "intonasi", "jeda", "durasi", "at", "_narasi", "id", "catatan"}
INTONASI = {"tenang", "berat", "tegang", "bisik", "tegas", "haru", "lega"}
# benda yang khusus untuk satu kisah: dipakai di luar konteksnya hampir selalu salah tafsir
KHUSUS = {"genangan_tubuh": ("mahsyar", "keringat", "kiamat", "hari pembalasan")}


@lru_cache(maxsize=1)
def _kunci_shot() -> frozenset[str]:
    s = CERITA_JS.read_text(encoding="utf-8")
    return frozenset(re.findall(r"\bS\.([a-z_][a-z_0-9]*)", s)) | KUNCI_SHOT_MANUAL


@lru_cache(maxsize=1)
def _font():
    try:
        from PIL import ImageFont

        return ImageFont.truetype(str(FONT), 100) if FONT.is_file() else None
    except Exception:  # noqa: BLE001 - tanpa Pillow/huruf: pakai perkiraan
        return None


def lebar_teks(teks: str, ukuran: float) -> float:
    """Lebar teks tebal DejaVu Sans dalam px (perkiraan 0,68 em per huruf bila huruf tidak tersedia)."""
    f = _font()
    if f is not None:
        return f.getlength(teks) * ukuran / 100
    return len(teks) * ukuran * 0.68


def _token(x: str) -> str:
    return re.sub(r"[^\w]", "", x.lower())


def _anchor(v: str) -> tuple[str, int] | None:
    m = re.match(r"@([^#+\-]+)(?:#(\d+))?([+\-][\d.]+)?$", v)
    return (_token(m.group(1)), int(m.group(2) or 1)) if m else None


def _semua_anchor(v, jalur: str):
    if isinstance(v, str) and v.startswith("@"):
        yield jalur, v
    elif isinstance(v, list):
        for i, x in enumerate(v):
            yield from _semua_anchor(x, f"{jalur}[{i}]")
    elif isinstance(v, dict):
        for k, x in v.items():
            yield from _semua_anchor(x, f"{jalur}.{k}")


def periksa(spek: dict, dasar: Path = DASAR_KISAH) -> tuple[list[str], list[str]]:
    galat: list[str] = []
    awas: list[str] = []
    C = spek.get("cerita")
    shot = C.get("shot") if isinstance(C, dict) else None
    if not isinstance(shot, list) or not shot:
        return ["papan harus punya \"cerita\": {\"shot\": [...]} (bukan \"shots\" atau kunci lain)"], awas
    kat, kem = katalog(), kemampuan()
    pose_sah = set(kem["pose"]) | set(kem["aksi"])
    kunci_shot = _kunci_shot()
    kelompok: dict[tuple[str, str], list] = {}  # kesalahan berulang digabung jadi satu butir
    contoh_o: dict[str, str] = {}

    # token narasi per shot, untuk memeriksa "@kata"
    token_shot = [[_token(w) for w in str(sh.get("narasi") or "").split()] if isinstance(sh, dict) else [] for sh in shot]
    semua_token = [t for ts in token_shot for t in ts]
    teks_semua = " ".join(str(sh.get("narasi") or "") for sh in shot if isinstance(sh, dict)).lower()

    if isinstance(shot[0], dict) and not str(shot[0].get("narasi") or "").strip() and not spek.get("suara"):
        galat.append("shot 1 harus bernarasi")

    for i, sh in enumerate(shot):
        n = i + 1
        if not isinstance(sh, dict):
            galat.append(f"shot {n}: harus berupa objek")
            continue
        nar = str(sh.get("narasi") or "")
        if ARAB.search(nar):
            galat.append(f"shot {n}: narasi berisi huruf Arab (bacaan Arab tidak disuarakan AI; taruh di kartu_dalil.arab)")
        if not nar.strip() and "durasi" not in sh and not spek.get("suara"):
            galat.append(f"shot {n}: shot tanpa narasi wajib punya \"durasi\" (detik)")
        if sh.get("intonasi") and sh["intonasi"] not in INTONASI:
            awas.append(f"shot {n}: intonasi \"{sh['intonasi']}\" tidak dikenal ({', '.join(sorted(INTONASI))})")
        for k in sh:
            if k in kunci_shot:
                continue
            if k in kat:
                kelompok.setdefault(("kunci_benda", k), []).append(n)
            else:
                awas.append(f"shot {n}: kunci shot \"{k}\" tidak dibaca renderer (diabaikan)")

        for j, b in enumerate(sh.get("benda") or []):
            tempat = f"shot {n} benda {j + 1}"
            if not isinstance(b, dict) or "jenis" not in b:
                galat.append(f"{tempat}: harus objek dengan \"jenis\"")
                continue
            jenis = b["jenis"]
            if jenis not in kat:
                galat.append(f"{tempat}: jenis \"{jenis}\" tidak ada di katalog benda")
                continue
            if "o" in b and isinstance(b["o"], dict):
                if "o" not in contoh_o:
                    contoh_o["o"] = json.dumps({"jenis": jenis, **{k: v for k, v in list(b["o"].items())[:3]}}, ensure_ascii=False)
                kelompok.setdefault(("o", ""), []).append(f"{n}.{j + 1}")
            dikenal = set(kat[jenis]["parameter"]) | UMUM | {"o"}
            asing = [x for x in b if x not in dikenal]
            if asing and jenis != "kartu_dalil":
                awas.append(f"{tempat} ({jenis}): parameter {', '.join(asing)} tidak dibaca renderer")
            if jenis in KHUSUS and not any(x in teks_semua for x in KHUSUS[jenis]):
                galat.append(f"{tempat}: \"{jenis}\" khusus kisah {KHUSUS[jenis][0]} (menggambar label tubuh "
                             "mata kaki-mulut); untuk orang tenggelam pakai air yang menutup (ombak/laut_terbelah depan)")
            if jenis == "kartu_dalil":
                galat += _periksa_kartu(b, tempat)

        for j, bo in enumerate(sh.get("boneka") or []):
            if not isinstance(bo, dict):
                continue
            pose = bo.get("pose")
            if isinstance(pose, str) and pose not in pose_sah:
                galat.append(f"shot {n} boneka {j + 1}: pose \"{pose}\" tidak ada (lihat Kemampuan tokoh)")
            if bo.get("hadap") and bo["hadap"] not in HADAP:
                galat.append(f"shot {n} boneka {j + 1}: hadap harus {', '.join(HADAP)}")

        for j, t in enumerate(sh.get("teks") or []):
            if not isinstance(t, dict):
                continue
            tempat = f"shot {n} teks {j + 1}"
            isi = str(t.get("teks") or "")
            if ARAB.search(isi):
                galat.append(f"{tempat}: teks Arab dalil hanya lewat kartu_dalil (kolom \"arab\", dicocokkan dengan sumber), bukan teks layar")
                continue
            if t.get("gaya") in ("sapuan", "neon"):
                continue
            uk = float(t.get("ukuran") or 82)
            for baris in isi.split("\n"):
                lb = lebar_teks(baris, uk) + 16
                if lb > LEBAR_AMAN:
                    muat = max(1, int(len(baris) * LEBAR_AMAN / lb))
                    galat.append(f"{tempat}: \"{baris}\" terlalu lebar ({lb:.0f} px > {LEBAR_AMAN}) dan akan terpotong; "
                                 f"pecah dengan \"\\n\" (maks ±{muat} huruf per baris di ukuran {uk:g}) atau kecilkan ukuran")
            sub = str(t.get("sub") or "")
            if sub and lebar_teks(sub, 40) + 40 > LEBAR_AMAN + 30:
                galat.append(f"{tempat}: sub \"{sub[:40]}...\" terlalu panjang untuk satu baris; ringkas jadi sumber saja "
                             "(mis. \"QS Yunus 10:92\")")

        # "@kata": isi shot memakai kemunculan kata secara global (kemunculan ke-n), lalu dikurangi awal shot
        sebelum = [t for ts in token_shot[:i] for t in ts]
        for jalur, v in _semua_anchor({k: x for k, x in sh.items() if k not in ("narasi", "_narasi")}, f"shot {n}"):
            a = _anchor(v)
            if not a:
                galat.append(f"{jalur}: format waktu \"{v}\" salah (pakai \"@kata\", \"@kata#2\", \"@kata-0.3\")")
                continue
            kata, ke = a
            total = semua_token.count(kata)
            if total < ke:
                saran = [w for w in dict.fromkeys(semua_token) if w.startswith(kata) or kata.startswith(w)][:3]
                galat.append(f"{jalur}: \"{v}\" tidak ada di narasi" + (f" (maksudnya @{saran[0]}?)" if saran else "")
                             + "; tanda baca/tanda hubung dibuang: \"sekali-kali\" = @sekalikali")
            elif ke <= sebelum.count(kata):
                galat.append(f"{jalur}: \"{v}\" menunjuk kata di shot sebelumnya; pakai @{kata}#{sebelum.count(kata) + 1}")

    for (jenis_g, k), lokasi in kelompok.items():
        if jenis_g == "kunci_benda":
            galat.insert(0, f"shot {', '.join(map(str, lokasi))}: \"{k}\" adalah benda; tulis di \"benda\": "
                            f"[{{\"jenis\": \"{k}\", \"x\": ..., \"y\": ...}}], bukan sebagai kunci shot")
        else:
            galat.insert(0, f"benda (shot.benda) {', '.join(lokasi[:12])}{' dst.' if len(lokasi) > 12 else ''}: parameter "
                            f"dibungkus \"o\": {{...}} sehingga diabaikan renderer. Tulis langsung di benda, mis. {contoh_o['o']}")
    for j, r in enumerate(spek.get("rekaman") or []):
        if not isinstance(r, dict):
            continue
        berkas = str(r.get("berkas") or "")
        if not berkas or not (dasar / berkas).resolve().is_file():
            galat.append(f"rekaman {j + 1}: berkas \"{berkas}\" tidak ada (lihat Katalog efek suara)")
        for jalur, v in _semua_anchor({"at": r.get("at"), "sampai": r.get("sampai")}, f"rekaman {j + 1}"):
            a = _anchor(v)
            if not a or semua_token.count(a[0]) < a[1]:
                galat.append(f"{jalur}: \"{v}\" tidak ada di narasi")
    return galat, awas


def _periksa_kartu(b: dict, tempat: str) -> list[str]:
    g = []
    contoh = ('{"jenis": "kartu_dalil", "label": "QUR\'AN", "kitab": "QS 26:62", "teks": "<terjemahan>", '
              '"arab": "<teks Arab persis>", "latar": 0.4}')
    if not str(b.get("kitab") or "").strip():
        g.append(f"{tempat} (kartu_dalil): \"kitab\" wajib, mis. \"QS 26:62\" atau \"HR. Tirmidzi\"; contoh: {contoh}")
    if not str(b.get("teks") or "").strip():
        g.append(f"{tempat} (kartu_dalil): \"teks\" (terjemahan) wajib")
    elif ARAB.search(str(b["teks"])):
        g.append(f"{tempat} (kartu_dalil): \"teks\" untuk terjemahan; teks Arab ditaruh di \"arab\"")
    if re.match(r"\s*H\.?R\b", str(b.get("kitab") or ""), re.IGNORECASE) and not b.get("no"):
        g.append(f"{tempat} (kartu_dalil): hadis wajib \"no\" (nomor hadis), mis. \"no\": \"3537\"")
    return g


def laporan(galat: list[str]) -> str:
    """Pesan siap salin ke sesi chat penulis JSON."""
    return ("Papan belum bisa dirender (narasi belum dibuat, kredit aman). Perbaiki lalu kirim ulang JSON lengkap:\n"
            + "\n".join(f"{i}. {x}" for i, x in enumerate(galat, 1)))
