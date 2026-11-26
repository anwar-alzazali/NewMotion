"""Referensi papan Kisah Islami (Nuh 1, Mahsyar 1, Ya'juj 1, Ya'juj 2) harus utuh di repo ini.

Keempat JSON ini menjadi patokan kedalaman bagi pengarah otomatis. Sumber aslinya repo
mesin-video (disalin 26 Nov 2026), yang direncanakan dihapus; uji ini menjaga agar berkas
dan semua audio/aset yang dirujuknya tidak hilang tanpa disadari.
"""
import json
import re
from pathlib import Path

import pytest

AKAR = Path(__file__).resolve().parents[1]
KISAH = AKAR / "mesin-video" / "papan" / "kisah"
REFERENSI = ["nuh1", "mahsyar1", "yajuj1", "yajuj2"]


@pytest.mark.parametrize("nama", REFERENSI)
def test_referensi_ada_dan_punya_shot(nama):
    spek = json.loads((KISAH / f"{nama}.json").read_text(encoding="utf-8"))
    assert spek["cerita"]["shot"], f"{nama}: daftar shot kosong"


@pytest.mark.parametrize("nama", REFERENSI)
def test_semua_rujukan_berkas_referensi_tersedia(nama):
    berkas = KISAH / f"{nama}.json"
    rujukan = set(re.findall(r'"(\.\./\.\./[^"]+)"', berkas.read_text(encoding="utf-8")))
    assert rujukan, f"{nama}: tidak ada rujukan audio/aset"
    hilang = sorted(r for r in rujukan if not (berkas.parent / r).resolve().is_file())
    assert not hilang, f"{nama}: berkas rujukan hilang: {hilang}"


def test_naskah_mahsyar1_tersedia():
    assert (AKAR / "mesin-video" / "naskah" / "mahsyar1.txt").read_text(encoding="utf-8").strip()
