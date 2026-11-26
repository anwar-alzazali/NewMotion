"""Katalog suara rekaman (mesin-video/aset/suara/*.mp3) untuk rencana sutradara.

Dibaca dari folder aset agar katalog selalu sama dengan berkas yang benar-benar ada.
Suasana = rekaman panjang yang boleh diulang di bawah narasi; efek = sekali bunyi.
Efek bernada komedi/notifikasi tidak ditawarkan ke genre kisah.
"""
from __future__ import annotations

from pathlib import Path

FOLDER = Path(__file__).resolve().parents[2] / "mesin-video" / "aset" / "suara"
JALUR_SPEK = "aset/suara"  # papan_buat.cari() mencari relatif ke folder mesin-video

SUASANA = {
    "air_mengalir": "aliran air", "angin_gurun": "angin padang tandus", "angin_sejuk": "angin lembut",
    "bawah_laut": "dalam air, teredam", "detak_jantung": "detak jantung, cemas", "dengung_haru": "dengung lembut, haru",
    "didih": "air mendidih", "drone_gelap": "dengung gelap, mencekam", "gemuruh_api": "api besar menyala",
    "guntur_hujan": "hujan badai dan guntur", "jam_dinding": "detik jam, waktu berjalan", "jangkrik": "malam di desa",
    "kerumunan_cemas": "kerumunan orang gelisah", "laut_malam": "ombak laut malam", "malam_hening": "malam sunyi",
    "napas_berat": "napas berat, lelah/takut", "panas_naik": "panas menyengat", "ratapan_jauh": "ratapan dari jauh",
    "rumah_sore": "suasana rumah sore", "senandung_gelap": "senandung muram", "senandung_haru": "senandung haru",
}
EFEK = {
    "braam": "hantaman sinematik berat (pembuka/kejutan besar)", "dentum_jauh": "dentuman dari jauh",
    "halaman_buku": "halaman dibalik", "hentak_serius": "hentakan tegas", "isak_lembut": "isak tangis pelan",
    "kertas_amplop": "kertas/surat", "kilau_cahaya": "cahaya muncul, berkilau", "koin_jatuh": "koin/harta jatuh",
    "langkah_lari": "langkah berlari", "langkah_pelan": "langkah pelan", "palu_kayu": "palu/ketukan kayu",
    "pintu_besi": "pintu besi berat", "rantai_seret": "rantai diseret", "stempel": "cap/ketetapan",
    "tanah_retak": "tanah/dinding retak, runtuh", "tetes": "tetesan", "timbangan_denting": "denting timbangan/logam",
    "whoosh": "sapuan cepat, perpindahan",
}
KERAS = {"lemah": 0.3, "sedang": 0.5, "kuat": 0.8}
VOL_SUASANA = 0.35
INTONASI = ("tenang", "berat", "tegang", "bisik", "tegas", "haru", "lega")


def _ada(daftar: dict) -> dict:
    return {k: v for k, v in daftar.items() if (FOLDER / f"{k}.mp3").exists()}


def katalog_suara() -> dict:
    return {"suasana": _ada(SUASANA), "efek": _ada(EFEK)}


def berkas(nama: str) -> str:
    return f"{JALUR_SPEK}/{nama}.mp3"


def teks_katalog_suara() -> str:
    k = katalog_suara()
    baris = ["Suasana (diulang di bawah narasi):"] + [f"- {n}: {d}" for n, d in k["suasana"].items()]
    baris += ["Efek (sekali bunyi):"] + [f"- {n}: {d}" for n, d in k["efek"].items()]
    baris += [f"Intonasi narasi: {', '.join(INTONASI)}"]
    return "\n".join(baris)
