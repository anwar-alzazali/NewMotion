"""Terjemahkan peristiwa eksplisit menjadi blocking dan gerak tokoh umum.

Tidak menebak tokoh, profil, kendaraan, atau sasaran. Motor hanya dibuat bila
peristiwa secara eksplisit menyebut sasaran/objek motor.
"""
from __future__ import annotations

from collections.abc import Mapping

AKSI_JALAN = {"jalan", "berjalan", "berjalan_menolong", "mendekati"}
AKSI_INTERAKSI = {"menolong"}
AKSI_LARI = {"lari", "berlari"}
AKSI_MOTOR = {"naik_motor", "menaiki", "mengendarai_motor", "mengendarai"}
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
    # Keadaan terakhir per ID tokoh dibawa antar-shot; identitas stabil menjadi kuncinya.
    posisi_terakhir = {}
    pose_terakhir = {}
    # Kendaraan mengikuti kontinuitas tokoh pemiliknya ke shot berikutnya.
    motor_terakhir = {}
    # Satu beat dapat memiliki beberapa tahap aksi. Peristiwa tanpa relasi
    # temporal tetap berada dalam satu tahap agar aksi simultan tidak terpecah.
    tautan_bertahap = []
    for tautan_asal in (rencana_blocking or {}).get("shot", []):
        indeks_asal = tautan_asal.get("indeks")
        shot_asal = (
            cerita.get("shot", [])[indeks_asal]
            if type(indeks_asal) is int and 0 <= indeks_asal < len(cerita.get("shot", []))
            else {}
        )
        pengarahan = shot_asal.get("pengarahan", {}) if isinstance(shot_asal, Mapping) else {}
        tahapan = pengarahan.get("tahapan_peristiwa") if isinstance(pengarahan, Mapping) else None
        if not isinstance(tahapan, list) or not tahapan:
            tautan_bertahap.append(dict(tautan_asal))
            continue
        for tahap in tahapan:
            if not isinstance(tahap, Mapping):
                continue
            ids_tahap = tahap.get("peristiwa_ids")
            if not isinstance(ids_tahap, list) or not ids_tahap:
                continue
            tautan_bertahap.append({
                **dict(tautan_asal),
                "peristiwa_ids": list(ids_tahap),
                "tahap_id": tahap.get("id"),
                "tahap_urutan": tahap.get("urutan"),
                "tahap_dasar": tahap.get("dasar_pemisahan"),
            })

    for tautan in tautan_bertahap:
        indeks = tautan.get("indeks")
        if type(indeks) is not int or indeks >= len(cerita.get("shot", [])):
            continue
        arahan_tokoh = []
        sudah = set()
        motor_dibutuhkan = False
        posisi_motor = None
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
            sasaran_objek = str(event.get("sasaran_benda") or event.get("sasaran") or "").casefold()
            if (
                sasaran_objek in {"motor", "sepeda_motor"}
                and not isinstance(event.get("sasaran_benda_id"), str)
            ):
                motor_dibutuhkan = True
            if aktor_id in sudah:
                diagnostik.append({"kode": "aktor_memiliki_beberapa_aksi_dalam_satu_shot", "aktor_id": aktor_id})
                continue
            sudah.add(aktor_id)
            nomor = list(tokoh_valid).index(aktor_id)
            x_tetap, y_tetap = posisi_terakhir.get(aktor_id, (_posisi_awal(nomor), 1510))
            sasaran_benda_id = event.get("sasaran_benda_id")
            motor_id_eksplisit = (
                sasaran_benda_id
                if isinstance(sasaran_benda_id, str) and sasaran_objek in {"motor", "sepeda_motor"}
                else None
            )
            if aksi == "tergelincir" and sasaran_objek in {"motor", "sepeda_motor"}:
                posisi_motor = x_tetap
            butir = {"tokoh_id": aktor_id, "x": x_tetap, "y": y_tetap}
            if aksi in AKSI_JALAN or aksi in AKSI_LARI:
                sasaran_id = event.get("sasaran_tokoh_id")
                x_sasaran, y_sasaran = (
                    posisi_terakhir.get(
                        sasaran_id,
                        (_posisi_awal(list(tokoh_valid).index(sasaran_id)), 1510),
                    )
                    if sasaran_id in tokoh_valid else (540, y_tetap)
                )
                y_tujuan = y_sasaran
                # Sasaran yang juga bergerak pada beat ini harus didekati pada
                # posisi akhirnya, bukan posisi awalnya. Ini membuat penolong
                # mengejar pengendara setelah motor tergelincir.
                event_sasaran = next((
                    peristiwa.get(id_event)
                    for id_event in tautan.get("peristiwa_ids", [])
                    if peristiwa.get(id_event, {}).get("aktor_id") == sasaran_id
                ), None)
                if event_sasaran and sasaran_id in tokoh_valid:
                    aksi_sasaran = str(event_sasaran.get("aksi") or "").strip().casefold().replace(" ", "_")
                    objek_sasaran = str(event_sasaran.get("sasaran") or "").casefold()
                    if aksi_sasaran == "tergelincir" and objek_sasaran in {"motor", "sepeda_motor"}:
                        # Jika sasaran belum diproses, hitung titik jatuhnya sekali.
                        if sasaran_id not in posisi_terakhir:
                            x_awal_sasaran, _ = posisi_terakhir.get(
                                sasaran_id,
                                (_posisi_awal(list(tokoh_valid).index(sasaran_id)), 1510),
                            )
                            x_sasaran, y_sasaran = min(1000, x_awal_sasaran + 280), 1700
                        # Penolong berhenti di bidang belakang korban, dengan jarak untuk menjangkau.
                        y_tujuan = y_sasaran - 80
                # Berhenti di sisi sasaran, bukan tepat menumpuk di titik yang sama.
                arah_ke_sasaran = 1 if x_sasaran >= x_tetap else -1
                x_tujuan = max(80, min(1000, x_sasaran - arah_ke_sasaran * 220))
                x_mulai = x_tetap if aktor_id in posisi_terakhir else (900 if x_tujuan < x_tetap else 100)
                butir.update({
                    "aksi": "lari" if aksi in AKSI_LARI else "jalan",
                    "x": [[0, x_mulai], [2.5, x_tujuan]],
                    "y": [[0, y_tetap], [2.5, y_tujuan]],
                    "sasaran_tokoh_id": sasaran_id,
                    "pose": (
                        [[0, "jalan"], [2.5, "menolong"]]
                        if aksi == "berjalan_menolong"
                        else [[0, "jalan" if aksi in AKSI_JALAN else "lari"], [2.5, "berdiri"]]
                    ),
                })
            elif aksi in AKSI_MOTOR:
                sasaran = sasaran_objek
                if sasaran not in {"motor", "sepeda_motor"}:
                    diagnostik.append({"kode": "kendaraan_tidak_dinyatakan_eksplisit", "peristiwa_id": id_peristiwa})
                    continue
                motor_dibutuhkan = motor_id_eksplisit is None
                posisi_motor = 500
                butir.update({
                    "x": 500, "y": 1510,
                    "kendaraan_id": motor_id_eksplisit or f"motor-{tautan.get('beat_id')}",
                })
            elif aksi in AKSI_INTERAKSI:
                # Interaksi harus membawa relasi sasaran sampai ke kontrak boneka renderer.
                # Sasaran yang tidak bergerak tetap ditambahkan sebagai pemeran pendukung di bawah.
                butir["aksi"] = aksi
                butir["sasaran_tokoh_id"] = event.get("sasaran_tokoh_id")
                butir["pose"] = [[0, "menolong"]]
            elif aksi in AKSI_DIAM:
                butir["aksi"] = aksi
                if aktor_id in pose_terakhir and aksi in {"menunggu", "berhenti", "duduk"}:
                    butir["pose"] = [[0, pose_terakhir[aktor_id]]]
                if aksi == "tergelincir" and sasaran_objek in {"motor", "sepeda_motor"}:
                    butir.update({
                        "kendaraan_id": motor_id_eksplisit or f"motor-{tautan.get('beat_id')}",
                        "lepas_kendaraan_at": 0.9,
                        "x": [[0, x_tetap], [1.2, min(1000, x_tetap + 280)]],
                        "y": [[0, 1504], [1.2, 1700]],
                        "pose": [[0, "mengendarai_motor"], [0.65, "tergelincir"]],
                    })
            else:
                diagnostik.append({"kode": "aksi_visual_belum_didukung", "peristiwa_id": id_peristiwa, "aksi": aksi_asli})
                continue
            if aksi in AKSI_JALAN or aksi in AKSI_LARI:
                arahan_tokoh.insert(0, butir)
            else:
                arahan_tokoh.append(butir)
            # Simpan posisi akhir lintasan untuk shot berikutnya.
            def _akhir(nilai):
                if isinstance(nilai, list) and nilai:
                    titik = nilai[-1]
                    return titik[1] if isinstance(titik, (list, tuple)) and len(titik) >= 2 else titik
                return nilai
            posisi_terakhir[aktor_id] = (_akhir(butir.get("x", x_tetap)), _akhir(butir.get("y", y_tetap)))
            jadwal_pose = butir.get("pose")
            if isinstance(jadwal_pose, list) and jadwal_pose:
                pose_terakhir[aktor_id] = jadwal_pose[-1][1] if isinstance(jadwal_pose[-1], (list, tuple)) else jadwal_pose[-1]
            elif aksi == "tergelincir":
                pose_terakhir[aktor_id] = "tergelincir"
        # Tokoh sasaran yang tidak memiliki aksi pada tahap ini tetap harus
        # hadir sebagai pemeran pendukung agar relasi interaksi renderer valid.
        for id_peristiwa in tautan.get("peristiwa_ids", []):
            event = peristiwa.get(id_peristiwa)
            sasaran_id = event.get("sasaran_tokoh_id") if isinstance(event, Mapping) else None
            if sasaran_id not in tokoh_valid or sasaran_id in sudah:
                continue
            nomor_sasaran = list(tokoh_valid).index(sasaran_id)
            x_sasaran, y_sasaran = posisi_terakhir.get(
                sasaran_id, (_posisi_awal(nomor_sasaran), 1510)
            )
            pendukung = {"tokoh_id": sasaran_id, "x": x_sasaran, "y": y_sasaran}
            if sasaran_id in pose_terakhir:
                pendukung["pose"] = [[0, pose_terakhir[sasaran_id]]]
            arahan_tokoh.append(pendukung)
            sudah.add(sasaran_id)

        if arahan_tokoh:
            butir_shot = {"indeks": indeks, "tokoh": arahan_tokoh}
            if tautan.get("tahap_id"):
                butir_shot.update({
                    "tahap_id": tautan["tahap_id"],
                    "tahap_urutan": tautan.get("tahap_urutan"),
                    "tahap_dasar": tautan.get("tahap_dasar"),
                    "peristiwa_ids": list(tautan.get("peristiwa_ids", [])),
                })
            benda_shot = []
            if motor_dibutuhkan:
                pemilik_motor = next(
                    (item["tokoh_id"] for item in arahan_tokoh if item.get("kendaraan_id")),
                    None,
                )
                id_motor = f"motor-{tautan.get('beat_id')}"
                x_awal_motor = posisi_motor if posisi_motor is not None else 540
                motor = {
                    "id": id_motor, "jenis": "motor",
                    "x": [[0, x_awal_motor], [0.9, min(1000, x_awal_motor + 55)]],
                    "y": [[0, 1550], [0.9, 1580]],
                    "miring": [[0, 0], [0.9, 28]], "s": 0.8,
                }
                benda_shot.append(motor)
                if pemilik_motor:
                    motor_terakhir[pemilik_motor] = {
                        "id": id_motor, "jenis": "motor",
                        "x": min(1000, x_awal_motor + 55), "y": 1580,
                        "miring": 28, "s": 0.8,
                    }

            # Jika pemilik masih tampil di shot berikutnya, motor yang sudah
            # terlepas tetap berada di panggung pada posisi akhir sebelumnya.
            aktor_shot = {item["tokoh_id"] for item in arahan_tokoh}
            for pemilik, motor in motor_terakhir.items():
                if pemilik in aktor_shot and not any(x["id"] == motor["id"] for x in benda_shot):
                    benda_shot.append(dict(motor))
            if benda_shot:
                butir_shot["benda"] = benda_shot
            shot_plan.append(butir_shot)
    return {"status": "siap_diterjemahkan" if shot_plan else "tidak_ada_aksi_visual_eksplisit",
            "shot": shot_plan, "diagnostik": diagnostik}
