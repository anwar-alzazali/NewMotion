"""Kemampuan tokoh renderer, dibaca langsung dari mesin-video/papan/cerita.js.

Sutradara hanya boleh meminta yang benar-benar bisa digambar: pose diam (POSE), aksi
berulang (poseGerak), benda yang bisa dinaiki/diduduki (KAIT), arah hadap, dan suku
figuran. Dibaca dari kode agar daftar di skill tidak pernah tertinggal dari renderer.
"""
from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

from newmotion.application.katalog_renderer import CERITA_JS

HADAP = ("depan", "kanan", "kiri")
SUKU = ("umum", "arab")


@lru_cache(maxsize=2)
def _baca(jalur: str) -> dict:
    s = Path(jalur).read_text(encoding="utf-8")
    a = s.index("const POSE = {")
    pose = list(dict.fromkeys(re.findall(r"^\s{4}(\w+): \{", s[a:s.index("\n  };", a)], re.MULTILINE)))
    a = s.index("function poseGerak")
    aksi = sorted(set(re.findall(r'nama === "(\w+)"', s[a:s.index("\n  }\n", a)])))
    a = s.index("const KAIT = {")
    blok = s[a:s.index("\n  };", a)]
    kait = {m.group(1): m.group(2) for m in re.finditer(r'^\s{4}(\w+): \{ sudut: "(\w+)"', blok, re.MULTILINE)}
    return {"pose": pose, "aksi": aksi, "kait": kait}


def kemampuan(jalur: Path = CERITA_JS) -> dict:
    return _baca(str(jalur))


def gerak_sah(jalur: Path = CERITA_JS) -> set[str]:
    k = kemampuan(jalur)
    return set(k["pose"]) | set(k["aksi"])


def teks_kemampuan_tokoh(jalur: Path = CERITA_JS) -> str:
    k = kemampuan(jalur)
    kait = ", ".join(f"{j} ({s})" for j, s in k["kait"].items())
    return "\n".join([
        f"- pose diam: {', '.join(k['pose'])}",
        f"- aksi berulang: {', '.join(k['aksi'])}",
        f"- hadap: {', '.join(HADAP)} (kanan/kiri = tampak samping utuh, badan dan kaki ikut menyamping)",
        f"- bisa dinaiki/diduduki (kait): {kait}. Tokoh menempel otomatis: duduk di jok, tangan di setang, kaki di pijakan",
        (f"- suku figuran: {', '.join(SUKU)}. arab = laki-laki berjubah dengan imamah/ghutrah/peci (sebagian berbisht), "
         "perempuan berkerudung dan abaya gelap"),
    ])
