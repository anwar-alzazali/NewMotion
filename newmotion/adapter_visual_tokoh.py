"""Adapter rencana visual tokoh ke kontrak boneka renderer mesin-video.

Modul ini hanya menerjemahkan instruksi eksplisit dari paket genre. Ia tidak
menebak posisi, profil karakter, pose, kendaraan, atau sasaran cerita.
"""
from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from math import hypot


class GalatAdapterVisualTokoh(ValueError):
    """Rencana visual tokoh tidak cocok dengan kontrak renderer."""


def _lintasan(nilai):
    """Ambil titik dari keyframe posisi renderer [[detik, nilai], ...]."""
    if not isinstance(nilai, list) or len(nilai) < 2:
        return []
    if all(
        isinstance(item, (list, tuple)) and len(item) == 2
        and isinstance(item[0], (int, float))
        and isinstance(item[1], (int, float))
        for item in nilai
    ):
        return [(float(item[0]), float(item[1])) for item in nilai]
    if all(isinstance(item, (int, float)) for item in nilai) and len(nilai) == 2:
        return [(0.0, float(nilai[0])), (1.0, float(nilai[1]))]
    return []


def _berpindah(x, y):
    """Pastikan aksi jalan/lari memiliki perpindahan posisi yang terlihat."""
    kx, ky = _lintasan(x), _lintasan(y)
    if not kx or not ky:
        return False
    waktu = sorted({t for t, _ in kx + ky})
    if len(waktu) < 2:
        return False

    def nilai(kunci, t):
        if t <= kunci[0][0]:
            return kunci[0][1]
        for (t0, v0), (t1, v1) in zip(kunci, kunci[1:]):
            if t <= t1:
                if t1 == t0:
                    return v1
                return v0 + (v1 - v0) * ((t - t0) / (t1 - t0))
        return kunci[-1][1]

    awal = (nilai(kx, waktu[0]), nilai(ky, waktu[0]))
    akhir = (nilai(kx, waktu[-1]), nilai(ky, waktu[-1]))
    return hypot(akhir[0] - awal[0], akhir[1] - awal[1]) >= 12


def terapkan_rencana_visual_tokoh(spec):
    """Terjemahkan rencana visual yang disetujui paket genre menjadi boneka.

    Format per shot:
      {"indeks": 0, "tokoh": [{
        "tokoh_id": "aktor-1", "x": [[0, 100], [2, 400]], "y": 1500,
        "aksi": "jalan", "pose": "berdiri", "karakter": {...},
        "sasaran_tokoh_id": "aktor-2", "kendaraan_id": "motor-1"
      }]}

    Referensi kendaraan harus menunjuk benda motor yang sudah ada pada shot.
    ID objek lain tetap menjadi metadata semantik dan tidak dipaksa menjadi ID
    boneka. Gerbang adab renderer harus dipanggil sebelum adapter ini.
    """
    if not isinstance(spec, dict):
        raise GalatAdapterVisualTokoh("Spesifikasi harus berupa objek")
    rencana = spec.get("rencana_visual_tokoh")
    if not isinstance(rencana, Mapping):
        return []
    if rencana.get("status") != "siap_diterjemahkan":
        return []
    daftar_rencana = rencana.get("shot")
    cerita = spec.get("cerita")
    daftar_shot = cerita.get("shot") if isinstance(cerita, Mapping) else None
    roster = (spec.get("rencana_cerita") or {}).get("tokoh", [])
    if not isinstance(daftar_rencana, list) or not isinstance(daftar_shot, list):
        raise GalatAdapterVisualTokoh("Daftar shot rencana dan cerita harus berupa daftar")
    if not isinstance(roster, list):
        raise GalatAdapterVisualTokoh("Roster rencana cerita harus berupa daftar")

    id_roster = {
        item.get("id") for item in roster
        if isinstance(item, Mapping) and isinstance(item.get("id"), str)
    }
    indeks_dipakai = set()
    hasil = []

    for nomor_shot, rencana_shot in enumerate(daftar_rencana, start=1):
        if not isinstance(rencana_shot, Mapping):
            raise GalatAdapterVisualTokoh(f"Rencana shot ke-{nomor_shot} harus berupa objek")
        indeks = rencana_shot.get("indeks")
        if type(indeks) is not int or not 0 <= indeks < len(daftar_shot):
            raise GalatAdapterVisualTokoh(f"Indeks shot ke-{nomor_shot} tidak valid")
        if indeks in indeks_dipakai:
            raise GalatAdapterVisualTokoh(f"Shot {indeks} memiliki rencana visual ganda")
        indeks_dipakai.add(indeks)
        shot = daftar_shot[indeks]
        if not isinstance(shot, dict):
            raise GalatAdapterVisualTokoh(f"Shot renderer {indeks} harus berupa objek")

        daftar_tokoh = rencana_shot.get("tokoh", [])
        if not isinstance(daftar_tokoh, list):
            raise GalatAdapterVisualTokoh(f"Daftar tokoh shot {indeks} harus berupa daftar")
        boneka_lama = shot.setdefault("boneka", [])
        if not isinstance(boneka_lama, list):
            raise GalatAdapterVisualTokoh(f"boneka shot {indeks} harus berupa daftar")

        indeks_aktor = {}
        boneka_baru = []
        for nomor, arahan in enumerate(daftar_tokoh):
            if not isinstance(arahan, Mapping):
                raise GalatAdapterVisualTokoh(f"Arahan tokoh ke-{nomor + 1} harus berupa objek")
            aktor_id = arahan.get("tokoh_id")
            if not isinstance(aktor_id, str) or aktor_id not in id_roster:
                raise GalatAdapterVisualTokoh(f"tokoh_id tidak terdaftar pada shot {indeks}: {aktor_id!r}")
            if aktor_id in indeks_aktor:
                raise GalatAdapterVisualTokoh(f"Tokoh {aktor_id!r} digandakan pada shot {indeks}")
            if "x" not in arahan or "y" not in arahan:
                raise GalatAdapterVisualTokoh(f"Tokoh {aktor_id!r} wajib memiliki posisi x dan y")

            aksi = arahan.get("aksi")
            boneka = {
                "aktor_id": aktor_id,
                "x": deepcopy(arahan["x"]),
                "y": deepcopy(arahan["y"]),
            }
            karakter = arahan.get("karakter")
            if karakter is not None:
                if not isinstance(karakter, Mapping):
                    raise GalatAdapterVisualTokoh(f"karakter tokoh {aktor_id!r} harus berupa objek")
                boneka["karakter"] = deepcopy(dict(karakter))

            # Aksi lokomosi diterjemahkan ke kanal jalan renderer yang memang ada.
            if aksi in {"jalan", "lari"}:
                if not _berpindah(arahan["x"], arahan["y"]):
                    raise GalatAdapterVisualTokoh(
                        f"Aksi {aksi} tokoh {aktor_id!r} tidak memiliki lintasan posisi yang nyata"
                    )
                boneka["jalan"] = 1.0 if aksi == "jalan" else 1.35
            elif aksi is not None:
                if not isinstance(aksi, str) or not aksi.strip():
                    raise GalatAdapterVisualTokoh(f"aksi tokoh {aktor_id!r} tidak valid")
                boneka["aksi_cerita"] = aksi

            for kunci in (
                "s", "naik", "arah", "wajah", "mata", "lengan", "keringat",
                "pose", "profil", "gaya", "baju", "kendaraan_id",
                "offset_kendaraan_x", "offset_kendaraan_y", "lepas_kendaraan_at",
            ):
                if kunci in arahan:
                    boneka[kunci] = deepcopy(arahan[kunci])

            indeks_aktor[aktor_id] = len(boneka_lama) + len(boneka_baru)
            boneka_baru.append(boneka)

        # Referensi sasaran aktor menjadi indeks boneka dalam shot ini; sasaran
        # benda dibiarkan eksplisit dan tidak disamakan dengan identitas tokoh.
        for arahan, boneka in zip(daftar_tokoh, boneka_baru):
            sasaran_id = arahan.get("sasaran_tokoh_id")
            if sasaran_id is not None:
                if sasaran_id not in indeks_aktor:
                    raise GalatAdapterVisualTokoh(
                        f"Sasaran tokoh {sasaran_id!r} tidak ada pada shot {indeks}"
                    )
                boneka["sasaran_id"] = indeks_aktor[sasaran_id]

            kendaraan_id = arahan.get("kendaraan_id")
            if kendaraan_id is not None:
                motor = next((
                    benda for benda in (shot.get("benda") or [])
                    if isinstance(benda, Mapping)
                    and str(benda.get("id")) == str(kendaraan_id)
                    and benda.get("jenis") == "motor"
                ), None)
                if motor is None:
                    raise GalatAdapterVisualTokoh(
                        f"Kendaraan {kendaraan_id!r} bukan benda motor pada shot {indeks}"
                    )

        shot["boneka"].extend(boneka_baru)
        hasil.append({
            "shot": indeks,
            "jumlah_tokoh_ditambahkan": len(boneka_baru),
            "aktor_ids": [b["aktor_id"] for b in boneka_baru],
        })
    return hasil
