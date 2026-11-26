"""Orkestrator sutradara inti: memilih paket dan menegakkan kontrak arahan.

Modul ini netral genre. Ia tidak menentukan estetika atau isi shot; kebijakan
pengarahan spesifik tetap disediakan oleh paket genre.
"""

import copy
from collections.abc import Mapping
from typing import Any

from newmotion.penataan_panggung import susun_rencana_blocking
from newmotion.adapter_visual_tokoh import terapkan_rencana_visual_tokoh

from newmotion.domain.genre import (
    ambil,
    konteks_konten_untuk_naskah,
    nama_genre_untuk_naskah,
)


class GalatPengarahan(ValueError):
    """Naskah atau hasil paket tidak memenuhi kontrak sutradara."""


def _rencana_cerita(naskah: Mapping[str, Any], shot: list[dict]) -> dict[str, Any]:
    """Pisahkan data cerita semantik dari instruksi visual yang dikonsumsi renderer."""
    tokoh = naskah.get("tokoh", [])
    if not isinstance(tokoh, list):
        raise GalatPengarahan("Daftar tokoh pada rencana cerita harus berupa daftar")
    id_tokoh = set()
    tokoh_berdasarkan_nama: dict[str, list[str]] = {}
    for nomor, item in enumerate(tokoh, start=1):
        if not isinstance(item, Mapping):
            raise GalatPengarahan(f"Tokoh ke-{nomor} harus berupa objek")
        identitas, nama = item.get("id"), item.get("nama")
        if not isinstance(identitas, str) or not identitas.strip():
            raise GalatPengarahan(f"Tokoh ke-{nomor} tidak memiliki ID stabil")
        if not isinstance(nama, str) or not nama.strip():
            raise GalatPengarahan(f"Tokoh ke-{nomor} tidak memiliki nama")
        if identitas in id_tokoh:
            raise GalatPengarahan(f"ID tokoh {identitas!r} digunakan lebih dari sekali")
        id_tokoh.add(identitas)
        kunci_nama = " ".join(nama.split()).casefold()
        tokoh_berdasarkan_nama.setdefault(kunci_nama, []).append(identitas)

    def cari_id_tokoh(nilai):
        if not isinstance(nilai, str):
            return None
        if nilai in id_tokoh:
            return nilai
        kunci = " ".join(nilai.split()).casefold()
        cocok = tokoh_berdasarkan_nama.get(kunci, [])
        return cocok[0] if len(cocok) == 1 else None

    diagnostik = []
    daftar_adegan = []
    id_adegan = set()
    id_peristiwa_global = set()
    daftar_benda = naskah.get("benda", [])
    if not isinstance(daftar_benda, list):
        raise GalatPengarahan("Daftar benda naskah harus berupa daftar")
    id_benda = set()
    for nomor_benda, benda in enumerate(daftar_benda, start=1):
        if not isinstance(benda, Mapping):
            raise GalatPengarahan(f"Benda ke-{nomor_benda} harus berupa objek")
        identitas_benda = benda.get("id")
        jenis_benda = benda.get("jenis_renderer")
        if not isinstance(identitas_benda, str) or not identitas_benda.strip():
            raise GalatPengarahan(f"Benda ke-{nomor_benda} wajib memiliki ID")
        if identitas_benda in id_benda:
            raise GalatPengarahan(f"ID benda {identitas_benda!r} digunakan lebih dari sekali")
        if not isinstance(jenis_benda, str) or not jenis_benda.strip():
            raise GalatPengarahan(f"Benda {identitas_benda!r} wajib memiliki jenis_renderer")
        id_benda.add(identitas_benda)
    for nomor, adegan in enumerate(naskah["adegan"], start=1):
        identitas = adegan.get("id") or f"beat-{nomor:03d}"
        if not isinstance(identitas, str) or not identitas.strip():
            raise GalatPengarahan(f"ID beat ke-{nomor} tidak valid")
        if identitas in id_adegan:
            raise GalatPengarahan(f"ID beat {identitas!r} digunakan lebih dari sekali")
        id_adegan.add(identitas)

        tokoh_ids = adegan.get("tokoh_ids", [])
        if not isinstance(tokoh_ids, list) or any(
            not isinstance(x, str) or x not in id_tokoh for x in tokoh_ids
        ):
            raise GalatPengarahan(
                f"Beat {identitas!r} merujuk ID tokoh yang tidak terdaftar"
            )
        butir = {
            "id": identitas,
            "nama": str(adegan.get("nama") or f"adegan_{nomor}"),
            "teks": adegan["teks"],
            "peran": copy.deepcopy(adegan.get("peran", [])),
            "tokoh_ids": list(tokoh_ids),
            "dialog": copy.deepcopy(adegan.get("dialog", [])),
            "benda_ids": copy.deepcopy(adegan.get("benda_ids", [])),
        }
        if not isinstance(butir["benda_ids"], list):
            raise GalatPengarahan(f"Beat {identitas!r} benda_ids harus berupa daftar")
        for benda_id in butir["benda_ids"]:
            if not isinstance(benda_id, str) or benda_id not in id_benda:
                diagnostik.append({
                    "kode": "benda_id_tidak_terdaftar",
                    "beat_id": identitas,
                    "benda_id": benda_id,
                })
        for kunci in ("peristiwa", "aksi", "sasaran", "tujuan", "perubahan_keadaan"):
            if kunci in adegan:
                butir[kunci] = copy.deepcopy(adegan[kunci])

        # Hubungkan nama aktor/sasaran dengan roster hanya jika cocokannya tunggal.
        # Sasaran yang tidak cocok dengan tokoh bisa berupa benda/lingkungan.
        peristiwa = butir.get("peristiwa")
        if isinstance(peristiwa, list):
            peristiwa_tertaut = []
            for nomor_peristiwa, data_peristiwa in enumerate(peristiwa, start=1):
                if not isinstance(data_peristiwa, Mapping):
                    raise GalatPengarahan(
                        f"Peristiwa ke-{nomor_peristiwa} pada beat {identitas!r} harus berupa objek"
                    )
                item_peristiwa = copy.deepcopy(dict(data_peristiwa))
                id_peristiwa = item_peristiwa.get("id")
                if id_peristiwa is None:
                    id_peristiwa = f"{identitas}-peristiwa-{nomor_peristiwa:03d}"
                if not isinstance(id_peristiwa, str) or not id_peristiwa.strip():
                    raise GalatPengarahan(
                        f"ID peristiwa ke-{nomor_peristiwa} pada beat {identitas!r} tidak valid"
                    )
                if id_peristiwa in id_peristiwa_global:
                    raise GalatPengarahan(
                        f"ID peristiwa {id_peristiwa!r} digunakan lebih dari sekali"
                    )
                id_peristiwa_global.add(id_peristiwa)
                item_peristiwa["id"] = id_peristiwa
                item_peristiwa["beat_id"] = identitas
                sasaran_benda_id = item_peristiwa.get("sasaran_benda_id")
                if sasaran_benda_id is not None and (
                    not isinstance(sasaran_benda_id, str) or sasaran_benda_id not in id_benda
                ):
                    diagnostik.append({
                        "kode": "sasaran_benda_id_tidak_terdaftar",
                        "beat_id": identitas,
                        "peristiwa_id": id_peristiwa,
                        "sasaran_benda_id": sasaran_benda_id,
                    })

                aktor = item_peristiwa.get("aktor")
                aktor_id = item_peristiwa.get("aktor_id")
                if aktor_id is None and isinstance(aktor, str):
                    aktor_id = cari_id_tokoh(aktor)
                if aktor_id is not None:
                    if not isinstance(aktor_id, str) or aktor_id not in id_tokoh:
                        diagnostik.append({
                            "kode": "aktor_id_tidak_terdaftar",
                            "beat_id": identitas,
                            "peristiwa_id": id_peristiwa,
                            "nilai": aktor_id,
                        })
                        item_peristiwa.pop("aktor_id", None)
                    else:
                        item_peristiwa["aktor_id"] = aktor_id
                        if tokoh_ids and aktor_id not in tokoh_ids:
                            diagnostik.append({
                                "kode": "aktor_tidak_tercantum_di_beat",
                                "beat_id": identitas,
                                "peristiwa_id": id_peristiwa,
                                "aktor_id": aktor_id,
                            })
                else:
                    diagnostik.append({
                        "kode": "aktor_belum_terpetakan",
                        "beat_id": identitas,
                        "peristiwa_id": id_peristiwa,
                        "nilai": aktor,
                    })

                sasaran = item_peristiwa.get("sasaran")
                sasaran_id = item_peristiwa.get("sasaran_tokoh_id")
                if sasaran_id is None:
                    sasaran_id = cari_id_tokoh(sasaran)
                if sasaran_id is not None:
                    if not isinstance(sasaran_id, str) or sasaran_id not in id_tokoh:
                        diagnostik.append({
                            "kode": "sasaran_tokoh_id_tidak_terdaftar",
                            "beat_id": identitas,
                            "peristiwa_id": id_peristiwa,
                            "nilai": sasaran_id,
                        })
                        item_peristiwa.pop("sasaran_tokoh_id", None)
                    else:
                        item_peristiwa["sasaran_tokoh_id"] = sasaran_id
                        if tokoh_ids and sasaran_id not in tokoh_ids:
                            diagnostik.append({
                                "kode": "sasaran_tokoh_tidak_tercantum_di_beat",
                                "beat_id": identitas,
                                "peristiwa_id": id_peristiwa,
                                "sasaran_tokoh_id": sasaran_id,
                            })

                bukti = item_peristiwa.get("bukti_teks")
                if isinstance(bukti, str) and bukti.strip():
                    teks_sumber = " ".join(str(adegan["teks"]).split()).casefold()
                    teks_bukti = " ".join(bukti.split()).casefold()
                    if teks_bukti not in teks_sumber:
                        diagnostik.append({
                            "kode": "bukti_teks_tidak_ditemukan_di_beat",
                            "beat_id": identitas,
                            "peristiwa_id": id_peristiwa,
                            "bukti_teks": bukti,
                        })
                else:
                    diagnostik.append({
                        "kode": "bukti_teks_belum_dicantumkan",
                        "beat_id": identitas,
                        "peristiwa_id": id_peristiwa,
                    })
                peristiwa_tertaut.append(item_peristiwa)
            butir["peristiwa"] = peristiwa_tertaut
        daftar_adegan.append(butir)

    # Kaitkan shot ke ID beat stabil; indeks _adegan tetap dipakai untuk kompatibilitas lama.
    for nomor, item_shot in enumerate(shot, start=1):
        indeks = item_shot.get("_adegan")
        if indeks is None:
            continue
        if type(indeks) is not int or not 0 <= indeks < len(daftar_adegan):
            raise GalatPengarahan(
                f"Shot ke-{nomor} memiliki indeks _adegan di luar daftar beat"
            )
        item_shot["_beat_id"] = daftar_adegan[indeks]["id"]

    return {
        "tokoh": copy.deepcopy(tokoh),
        "benda": copy.deepcopy(daftar_benda),
        "adegan": daftar_adegan,
        "diagnostik": diagnostik,
    }




def _tahapan_peristiwa(peristiwa: list[Mapping]) -> list[dict]:
    """Kelompokkan aksi simultan; pisahkan hanya jika urutan temporal dinyatakan."""
    tahapan = []
    tahap_aktif = None
    keadaan_terakhir = {}
    for nomor, item in enumerate(peristiwa, start=1):
        id_event = item.get("id")
        ketergantungan = (
            item.get("setelah_peristiwa_id")
            or item.get("peristiwa_sebelumnya_id")
        )
        relasi = str(item.get("hubungan_temporal") or "").strip().casefold()
        perubahan = item.get("perubahan_keadaan")
        transisi_berurutan = False
        if isinstance(perubahan, Mapping):
            entitas = perubahan.get("entitas_id")
            if isinstance(entitas, str) and entitas in keadaan_terakhir:
                transisi_berurutan = (
                    perubahan.get("dari") == keadaan_terakhir[entitas]
                )
            if isinstance(entitas, str) and perubahan.get("menjadi") is not None:
                keadaan_terakhir[entitas] = perubahan["menjadi"]

        eksplisit_setelah = (
            isinstance(ketergantungan, str) and bool(ketergantungan.strip())
        ) or relasi in {"setelah", "sesudah", "kemudian", "berikutnya"}
        perlu_tahap_baru = tahap_aktif is None or (
            eksplisit_setelah or transisi_berurutan
        )
        if perlu_tahap_baru:
            tahap_aktif = {
                "id": f"tahap-aksi-{len(tahapan) + 1:03d}",
                "urutan": len(tahapan) + 1,
                "peristiwa_ids": [],
                "dasar_pemisahan": (
                    "relasi_temporal_eksplisit" if eksplisit_setelah
                    else "transisi_keadaan_berurutan" if transisi_berurutan
                    else "tahap_awal"
                ),
                "bergantung_pada_peristiwa_id": ketergantungan,
            }
            tahapan.append(tahap_aktif)
        if isinstance(id_event, str):
            tahap_aktif["peristiwa_ids"].append(id_event)
    return tahapan


def _lengkapi_metadata_pengarah(shot: list[dict], rencana_cerita: dict) -> None:
    """Tautkan metadata shot ke hasil resolusi ID aktor/sasaran yang otoritatif."""
    adegan = {
        item["id"]: item
        for item in rencana_cerita.get("adegan", [])
        if isinstance(item, Mapping) and isinstance(item.get("id"), str)
    }
    for item_shot in shot:
        if not isinstance(item_shot, dict):
            continue
        identitas_beat = item_shot.get("_beat_id")
        sumber = adegan.get(identitas_beat)
        pengarahan = item_shot.get("pengarahan")
        if not isinstance(sumber, Mapping) or not isinstance(pengarahan, dict):
            continue
        peristiwa = sumber.get("peristiwa") or []
        urutan = []
        fokus = list(pengarahan.get("fokus_tokoh_ids") or [])
        for nomor, item in enumerate(peristiwa, start=1):
            if not isinstance(item, Mapping):
                continue
            aktor_id = item.get("aktor_id")
            sasaran_tokoh_id = item.get("sasaran_tokoh_id")
            for tokoh_id in (aktor_id, sasaran_tokoh_id):
                if isinstance(tokoh_id, str) and tokoh_id not in fokus:
                    fokus.append(tokoh_id)
            urutan.append({
                "urutan": nomor,
                "peristiwa_id": item.get("id"),
                "aktor_id": aktor_id,
                "aktor": item.get("aktor"),
                "aksi": item.get("aksi"),
                "sasaran": item.get("sasaran"),
                "sasaran_tokoh_id": sasaran_tokoh_id,
                "sasaran_benda_id": item.get("sasaran_benda_id"),
            })
        pengarahan["fokus_tokoh_ids"] = fokus
        pengarahan["tahapan_peristiwa"] = _tahapan_peristiwa(peristiwa)
        pengarahan["status_segmentasi"] = "rencana_semantik_belum_memecah_shot_renderer"
        pengarahan["peristiwa_ids"] = [
            item["peristiwa_id"] for item in urutan if item.get("peristiwa_id")
        ]
        pengarahan["urutan_peristiwa"] = urutan


def arahkan_naskah(
    naskah: Mapping[str, Any], *, genre_pilihan: str | None = None
) -> tuple[dict[str, Any], str, int]:
    """Pilih paket secara eksplisit, panggil pengarahnya, lalu validasi papan."""
    if not isinstance(naskah, Mapping):
        raise GalatPengarahan("Naskah harus berupa objek")

    try:
        nama_genre = nama_genre_untuk_naskah(naskah, pilihan=genre_pilihan)
        konteks_konten = konteks_konten_untuk_naskah(
            naskah, genre=nama_genre, wajib_eksplisit=True
        )
        paket = ambil(nama_genre)
    except (TypeError, ValueError, ImportError) as galat:
        raise GalatPengarahan(str(galat)) from galat

    adegan = naskah.get("adegan")
    if not isinstance(adegan, list) or not adegan:
        raise GalatPengarahan("Naskah harus memiliki daftar 'adegan' yang tidak kosong")
    for nomor, adegan_item in enumerate(adegan, start=1):
        if (
            not isinstance(adegan_item, Mapping)
            or not isinstance(adegan_item.get("teks"), str)
            or not adegan_item["teks"].strip()
        ):
            raise GalatPengarahan(
                f"Adegan ke-{nomor} harus berupa objek dengan teks yang tidak kosong"
            )

    if not callable(paket.pengarah_naskah):
        raise GalatPengarahan(
            f"Paket genre {paket.nama!r} belum menyediakan pengarah naskah"
        )

    spesifikasi = paket.pengarah_naskah(naskah)
    if not isinstance(spesifikasi, dict):
        raise GalatPengarahan("Pengarah genre harus menghasilkan objek spesifikasi")
    cerita = spesifikasi.get("cerita")
    shot = cerita.get("shot") if isinstance(cerita, dict) else None
    if not isinstance(shot, list) or not shot:
        raise GalatPengarahan("Pengarah genre tidak menghasilkan daftar shot yang dapat dirender")

    # Rencana semantik disimpan terpisah dari instruksi visual renderer.
    # Renderer tetap menerima cerita.shot; lapisan blocking berikutnya memakai rencana_cerita.
    spesifikasi["rencana_cerita"] = _rencana_cerita(naskah, shot)
    _lengkapi_metadata_pengarah(shot, spesifikasi["rencana_cerita"])
    spesifikasi["rencana_blocking"] = susun_rencana_blocking(
        spesifikasi["rencana_cerita"], cerita
    )

    # Visualisasi pemeran bersifat opt-in per paket genre. Tanpa kait eksplisit,
    # roster tetap semantik dan tidak disisipkan ke cerita.shot.boneka.
    if paket.pengarah_tokoh_visual is None:
        spesifikasi["rencana_visual_tokoh"] = {
            "status": "belum_didukung_paket",
            "shot": [],
            "diagnostik": [{
                "kode": "paket_belum_menyediakan_pengarah_tokoh_visual",
                "pesan": (
                    "Roster tokoh dipertahankan sebagai data cerita; "
                    "paket genre belum mengizinkan pemetaan ke visual renderer."
                ),
            }],
        }
    else:
        hasil_visual_tokoh = paket.pengarah_tokoh_visual(
            copy.deepcopy(spesifikasi["rencana_cerita"]),
            copy.deepcopy(spesifikasi["rencana_blocking"]),
            copy.deepcopy(cerita),
        )
        if not isinstance(hasil_visual_tokoh, Mapping):
            raise GalatPengarahan(
                "Pengarah visual tokoh harus menghasilkan objek rencana"
            )
        status_visual = hasil_visual_tokoh.get("status")
        shot_visual = hasil_visual_tokoh.get("shot")
        diagnostik_visual = hasil_visual_tokoh.get("diagnostik", [])
        if not isinstance(status_visual, str) or not status_visual.strip():
            raise GalatPengarahan(
                "Rencana visual tokoh harus memiliki status yang tidak kosong"
            )
        if not isinstance(shot_visual, list) or not isinstance(diagnostik_visual, list):
            raise GalatPengarahan(
                "Rencana visual tokoh harus memiliki daftar shot dan diagnostik"
            )
        spesifikasi["rencana_visual_tokoh"] = copy.deepcopy(dict(hasil_visual_tokoh))

        # Benda lingkungan/props memiliki pengarah terpisah dari blocking tokoh.
        # Kedua rencana digabung sebelum adapter tunggal menerapkan kontrak renderer.
        if paket.pengarah_benda_visual is not None:
            try:
                hasil_visual_benda = paket.pengarah_benda_visual(
                    copy.deepcopy(spesifikasi["rencana_cerita"]),
                    copy.deepcopy(spesifikasi["rencana_blocking"]),
                    copy.deepcopy(cerita),
                )
            except (TypeError, ValueError) as galat:
                raise GalatPengarahan(
                    f"Pengarah benda tidak dapat menyusun objek renderer: {galat}"
                ) from galat
            if not isinstance(hasil_visual_benda, Mapping):
                raise GalatPengarahan("Pengarah benda harus menghasilkan objek rencana")
            daftar_shot_benda = hasil_visual_benda.get("shot")
            diagnostik_benda = hasil_visual_benda.get("diagnostik", [])
            if not isinstance(daftar_shot_benda, list) or not isinstance(diagnostik_benda, list):
                raise GalatPengarahan(
                    "Rencana visual benda harus memiliki daftar shot dan diagnostik"
                )
            spesifikasi["rencana_visual_benda"] = copy.deepcopy(dict(hasil_visual_benda))
            visual_by_index = {
                item.get("indeks"): item
                for item in shot_visual
                if isinstance(item, dict) and type(item.get("indeks")) is int
            }
            for item_benda in daftar_shot_benda:
                if not isinstance(item_benda, Mapping):
                    raise GalatPengarahan("Entri shot pada rencana visual benda harus berupa objek")
                indeks_benda = item_benda.get("indeks")
                if type(indeks_benda) is not int or not 0 <= indeks_benda < len(shot):
                    raise GalatPengarahan("Indeks shot pada rencana visual benda tidak valid")
                target_visual = visual_by_index.get(indeks_benda)
                if target_visual is None:
                    target_visual = {"indeks": indeks_benda, "tokoh": [], "benda": []}
                    shot_visual.append(target_visual)
                    visual_by_index[indeks_benda] = target_visual
                target_visual.setdefault("benda", []).extend(
                    copy.deepcopy(item_benda.get("benda", []))
                )
            # Sinkronkan hasil gabungan; sebelumnya spesifikasi sudah menyalin rencana
            # tokoh sehingga perubahan pada daftar lokal tidak ikut terbawa.
            spesifikasi["rencana_visual_tokoh"]["shot"] = copy.deepcopy(shot_visual)

        # JSON keluaran sutradara sudah memuat instruksi renderer, bukan hanya rencana terpisah.
        try:
            terapkan_rencana_visual_tokoh(spesifikasi)
        except ValueError as galat:
            raise GalatPengarahan(
                f"Rencana visual tidak dapat diterapkan ke JSON renderer: {galat}"
            ) from galat

    # Kamera dihitung setelah posisi tokoh diterjemahkan agar dapat mengikuti panggung nyata.
    if paket.pengarah_kamera is not None:
        try:
            hasil_kamera = paket.pengarah_kamera(
                copy.deepcopy(spesifikasi["rencana_cerita"]),
                copy.deepcopy(spesifikasi["rencana_blocking"]),
                spesifikasi["cerita"],
            )
        except (TypeError, ValueError) as galat:
            raise GalatPengarahan(
                f"Pengarah kamera tidak dapat menyusun keyframe: {galat}"
            ) from galat
        if not isinstance(hasil_kamera, Mapping):
            raise GalatPengarahan("Pengarah kamera harus menghasilkan objek rencana")
        spesifikasi["rencana_kamera"] = copy.deepcopy(dict(hasil_kamera))

    # Genre menjadi metadata otoritatif untuk gerbang penjaga pada renderer.
    spesifikasi["genre"] = paket.nama
    spesifikasi["konteks_konten"] = konteks_konten
    return spesifikasi, paket.nama, len(shot)
