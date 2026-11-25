"""Kamus aksi karakter untuk kontrak Python -> renderer JavaScript.

Modul ini sengaja tidak menghitung pose, sudut sendi, IK, atau keyframe visual.
Evaluasi gerak dan seluruh geometri rangka menjadi tanggung jawab cerita.js.
"""
from __future__ import annotations

GERAK_STATIS = {
    "berdiri", "tunjuk", "ulurkan", "angkat", "silang", "kaget", "mundur",
    "tutup", "tutup_telinga", "tutup_wajah", "berdoa", "menengadah",
    "lemas", "pinggang", "dagu", "kepala",
}
GERAK_BERULANG = {
    "jalan", "lari", "joget", "lompat", "duduk", "melambai", "palu",
    "gali", "menggeleng", "mengangguk", "tertawa",
}
SEMUA = frozenset(GERAK_STATIS | GERAK_BERULANG)


def jadwal_gerak(spec) -> list[list[float | str]]:
    """Validasi dan normalkan nama aksi atau jadwal [[detik, nama], ...]."""
    if isinstance(spec, str):
        jadwal = [[0.0, spec]]
    elif isinstance(spec, list) and spec:
        jadwal = [[float(waktu), str(nama)] for waktu, nama in spec]
        jadwal.sort(key=lambda item: item[0])
    else:
        raise ValueError("karakter.gerak harus berupa nama aksi atau jadwal [[detik, nama], ...]")
    if jadwal[0][0] < 0:
        raise ValueError("waktu gerak tidak boleh negatif")
    for waktu, nama in jadwal:
        if waktu < 0:
            raise ValueError("waktu gerak tidak boleh negatif")
        if nama not in SEMUA:
            raise ValueError(f"gerak karakter tidak dikenal: {nama}")
    return jadwal
