"""Terjemahkan peristiwa eksplisit menjadi blocking dan gerak tokoh umum.

Tidak menebak tokoh, profil, kendaraan, atau sasaran. Motor hanya dibuat bila
peristiwa secara eksplisit menyebut sasaran/objek motor.
"""
from __future__ import annotations

from collections.abc import Mapping

AKSI_JALAN = {"jalan", "berjalan", "berjalan_menolong", "mendekati", "menolong"}
AKSI_LARI = {"lari", "berlari"}
AKSI_MOTOR = {"naik_motor", "mengendarai_motor", "mengendarai"}
AKSI_DIAM = {"tergelincir", "jatuh", "berhenti", "menunggu", "duduk"}


def _posisi_awal(nomor: int) -> int:
    return max(150, min(930, 220 + nomor * 150))


def arahkan_tokoh_visual(rencana_cerita, rencana_blocking, cerita):
    roster = rencana_cerita.get("tokoh", []) if isinstance(rencana_cerita, Mapping) else []
    tokoh_valid = {
        item.get("id"): item for item in roster
        if isinstance(item, Mapping) and isinstance(item.get("id"), str)
    }
    peristiwa = {
        item.get("id"): item for item in (rencana_blocking or {}).get("peristiwa", [])
        if isinstance(item, Mapping)
    }
    shot_plan = []
    diagnostik = []
    for tautan in (rencana_blocking or {}).get("shot", []):
        indeks = tautan.get("indeks")
        if type(indeks) is not int or indeks >= len(cerita.get("shot", [])):
            continue
        arahan_tokoh = []
        sudah = set()
        motor_dibutuhkan = False
        for id_peristiwa in tautan.get("peristiwa_ids", []):
            event = peristiwa.get(id_peristiwa)
            if not event:
                continue
            aktor_id = event.get("aktor_id")
            aksi_asli = event.get("aksi")
            if aktor_id not in tokoh_valid or not isinstance(aksi_asli, str):
                diagnostik.append({"kode": "peristiwa_tidak_cukup_untuk_visual", "peristiwa_id": id_peristiwa})
                continue
            aksi = aksi_asli.strip().casefold().replace(" ", "_")
            sasaran_objek = str(event.get("sasaran") or "").casefold()
            if sasaran_objek in {"motor", "sepeda_motor"}:
                motor_dibutuhkan = True
            if aktor_id in sudah:
                diagnostik.append({"kode": "aktor_memiliki_beberapa_aksi_dalam_satu_shot", "aktor_id": aktor_id})
                continue
            sudah.add(aktor_id)
            nomor = list(tokoh_valid).index(aktor_id)
            x_tetap = _posisi_awal(nomor)
            butir = {"tokoh_id": aktor_id, "x": x_tetap, "y": 1510}
            if aksi in AKSI_JALAN or aksi in AKSI_LARI:
                sasaran_id = event.get("sasaran_tokoh_id")
                x_tujuan = _posisi_awal(list(tokoh_valid).index(sasaran_id)) if sasaran_id in tokoh_valid else 540
                x_mulai = 900 if x_tujuan < x_tetap else 150
                butir.update({
                    "aksi": "lari" if aksi in AKSI_LARI else "jalan",
                    "x": [[0, x_mulai], [2.5, x_tujuan]],
                    "sasaran_tokoh_id": sasaran_id,
                    "pose": [[0, "berdiri"], [2.2, "berdiri"]],
                })
            elif aksi in AKSI_MOTOR:
                sasaran = sasaran_objek
                if sasaran not in {"motor", "sepeda_motor"}:
                    diagnostik.append({"kode": "kendaraan_tidak_dinyatakan_eksplisit", "peristiwa_id": id_peristiwa})
                    continue
                motor_dibutuhkan = True
                butir.update({"x": 500, "y": 1510, "kendaraan_id": f"motor-{tautan.get('beat_id')}"})
            elif aksi in AKSI_DIAM:
                butir["aksi"] = aksi
            else:
                diagnostik.append({"kode": "aksi_visual_belum_didukung", "peristiwa_id": id_peristiwa, "aksi": aksi_asli})
                continue
            if aksi in AKSI_JALAN or aksi in AKSI_LARI:
                arahan_tokoh.insert(0, butir)
            else:
                arahan_tokoh.append(butir)
        if arahan_tokoh:
            shot_plan.append({"indeks": indeks, "tokoh": arahan_tokoh})
            if motor_dibutuhkan:
                cerita["shot"][indeks].setdefault("benda", []).append({
                    "id": f"motor-{tautan.get('beat_id')}", "jenis": "motor",
                    "x": 500, "y": 1550, "s": 0.8,
                })
    return {"status": "siap_diterjemahkan" if shot_plan else "tidak_ada_aksi_visual_eksplisit",
            "shot": shot_plan, "diagnostik": diagnostik}
