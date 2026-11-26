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
    if isinstance(nilai, (int, float)):
        return [(0.0, float(nilai)), (1.0, float(nilai))]
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
    # Pengarahan memanggil adapter saat JSON disusun; renderer dapat memanggilnya lagi.
    # Penanda ini mencegah tokoh dan benda digandakan.
    if spec.get("_rencana_visual_tokoh_diterapkan") is True:
        return []
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
    # Perluas satu shot sumber menjadi beberapa shot renderer bila pengarah
    # menghasilkan lebih dari satu tahap temporal. Salinan mempertahankan
    # metadata kamera/komposisi, sedangkan ID shot dan tahap dibuat eksplisit.
    rencana_per_indeks = {}
    for item in daftar_rencana:
        if not isinstance(item, Mapping):
            raise GalatAdapterVisualTokoh("Rencana shot harus berupa objek")
        indeks_asal = item.get("indeks")
        if type(indeks_asal) is not int or not 0 <= indeks_asal < len(daftar_shot):
            raise GalatAdapterVisualTokoh("Indeks shot sumber tidak valid")
        rencana_per_indeks.setdefault(indeks_asal, []).append(item)

    shot_renderer_baru = []
    rencana_renderer_baru = []
    for indeks_asal, shot_asal in enumerate(daftar_shot):
        rencana_tahap = rencana_per_indeks.get(indeks_asal, [])
        if not rencana_tahap:
            shot_renderer_baru.append(shot_asal)
            continue
        for nomor_tahap, item in enumerate(rencana_tahap, start=1):
            shot_turunan = deepcopy(shot_asal)
            tahap_id = item.get("tahap_id")
            if tahap_id:
                pengarahan_asal = shot_turunan.get("pengarahan")
                if isinstance(pengarahan_asal, dict):
                    pengarahan_asal["id"] = f"{pengarahan_asal.get('id', f'shot-{indeks_asal + 1:03d}')}-{tahap_id}"
                    pengarahan_asal["tahap_id"] = tahap_id
                    pengarahan_asal["tahap_urutan"] = item.get("tahap_urutan", nomor_tahap)
                    pengarahan_asal["peristiwa_ids"] = list(item.get("peristiwa_ids", []))
                    pengarahan_asal["status_segmentasi"] = (
                        "shot_renderer_dibagi_dari_tahap_semantik"
                        if len(rencana_tahap) > 1
                        else "shot_renderer_satu_tahap_semantik"
                    )
            if len(rencana_tahap) > 1:
                durasi_asal = float(shot_asal.get("durasi", 3.0) or 3.0)
                durasi_tahap = round(durasi_asal / len(rencana_tahap), 2)
                shot_turunan["at"] = round(
                    float(shot_asal.get("at", 0) or 0) + (nomor_tahap - 1) * durasi_tahap, 2
                )
                shot_turunan["durasi"] = durasi_tahap
            indeks_baru = len(shot_renderer_baru)
            shot_renderer_baru.append(shot_turunan)
            item_baru = deepcopy(dict(item))
            item_baru["indeks_asal"] = indeks_asal
            item_baru["indeks"] = indeks_baru
            rencana_renderer_baru.append(item_baru)

    daftar_shot[:] = shot_renderer_baru
    daftar_rencana = rencana_renderer_baru
    indeks_dipakai = set()
    hasil = []

    for nomor_shot, rencana_shot in enumerate(daftar_rencana, start=1):
        if not isinstance(rencana_shot, Mapping):
            raise GalatAdapterVisualTokoh(f"Rencana shot ke-{nomor_shot} harus berupa objek")
        indeks = rencana_shot.get("indeks")
        if type(indeks) is not int or not 0 <= indeks < len(daftar_shot):
            raise GalatAdapterVisualTokoh(f"Indeks shot ke-{nomor_shot} tidak valid")
        if indeks in indeks_dipakai:
            raise GalatAdapterVisualTokoh(f"Shot renderer {indeks} memiliki rencana visual ganda")
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

        # Benda renderer hanya ditambahkan bila paket genre menyatakannya secara eksplisit.
        daftar_benda = rencana_shot.get("benda", [])
        if not isinstance(daftar_benda, list):
            raise GalatAdapterVisualTokoh(f"Daftar benda shot {indeks} harus berupa daftar")
        benda_lama = shot.setdefault("benda", [])
        if not isinstance(benda_lama, list):
            raise GalatAdapterVisualTokoh(f"benda shot {indeks} harus berupa daftar")
        id_benda = {
            str(item.get("id")) for item in benda_lama
            if isinstance(item, Mapping) and item.get("id") is not None
        }
        for benda in daftar_benda:
            if not isinstance(benda, Mapping):
                raise GalatAdapterVisualTokoh(f"Benda shot {indeks} harus berupa objek")
            identitas_benda = benda.get("id")
            jenis_benda = benda.get("jenis")
            if not isinstance(identitas_benda, str) or not identitas_benda.strip():
                raise GalatAdapterVisualTokoh(f"Benda shot {indeks} wajib memiliki ID")
            if not isinstance(jenis_benda, str) or not jenis_benda.strip():
                raise GalatAdapterVisualTokoh(f"Benda {identitas_benda!r} wajib memiliki jenis")
            if identitas_benda in id_benda:
                raise GalatAdapterVisualTokoh(f"Benda {identitas_benda!r} digandakan pada shot {indeks}")
            benda_lama.append(deepcopy(dict(benda)))
            id_benda.add(identitas_benda)

        indeks_aktor = {}
        for nomor_lama, boneka_lama_item in enumerate(boneka_lama):
            if isinstance(boneka_lama_item, Mapping):
                aktor_lama = boneka_lama_item.get("aktor_id")
                if isinstance(aktor_lama, str):
                    if aktor_lama in indeks_aktor:
                        raise GalatAdapterVisualTokoh(
                            f"Tokoh {aktor_lama!r} sudah digandakan pada shot {indeks}"
                        )
                    indeks_aktor[aktor_lama] = nomor_lama
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
            karakter = arahan.get("karakter", {})
            if not isinstance(karakter, Mapping):
                raise GalatAdapterVisualTokoh(f"karakter tokoh {aktor_id!r} harus berupa objek")
            karakter = deepcopy(dict(karakter))

            # integrasi mesin-video membangun pose dari karakter.gerak dan
            # mengganti boneka.pose; karena itu jadwal pose diteruskan lewat
            # kontrak karakter, bukan ditaruh pada field renderer sebelum integrasi.
            if "pose" in arahan:
                karakter["gerak"] = deepcopy(arahan["pose"])

            # Aksi lokomosi diterjemahkan ke kanal jalan dan jadwal gerak renderer.
            if aksi in {"jalan", "lari"}:
                if not _berpindah(arahan["x"], arahan["y"]):
                    raise GalatAdapterVisualTokoh(
                        f"Aksi {aksi} tokoh {aktor_id!r} tidak memiliki lintasan posisi yang nyata"
                    )
                boneka["jalan"] = 1.0 if aksi == "jalan" else 1.35
                karakter.setdefault("gerak", aksi)
            elif aksi is not None:
                if not isinstance(aksi, str) or not aksi.strip():
                    raise GalatAdapterVisualTokoh(f"aksi tokoh {aktor_id!r} tidak valid")
                boneka["aksi_cerita"] = aksi

            if karakter or aksi in {"jalan", "lari"} or "pose" in arahan:
                boneka["karakter"] = karakter

            for kunci in (
                "s", "naik", "arah", "wajah", "mata", "lengan", "keringat",
                "profil", "gaya", "baju", "kendaraan_id",
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
            "shot_asal": rencana_shot.get("indeks_asal", indeks),
            "tahap_id": rencana_shot.get("tahap_id"),
            "jumlah_tokoh_ditambahkan": len(boneka_baru),
            "aktor_ids": [b["aktor_id"] for b in boneka_baru],
        })
    spec["_rencana_visual_tokoh_diterapkan"] = True
    return hasil
