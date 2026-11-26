"""Penataan panggung netral genre; adaptasi geometri panggung dari Sutradara AI Studio."""
from __future__ import annotations

from math import hypot


def _angka(nilai, bawaan=0.0):
    try:
        return float(nilai)
    except (TypeError, ValueError):
        return bawaan


def _nilai_posisi_kunci(nilai):
    """Ubah format keyframe renderer menjadi pasangan waktu-nilai."""
    if not isinstance(nilai, list) or not nilai:
        return []
    if isinstance(nilai[0], (list, tuple)) and len(nilai[0]) >= 2:
        hasil = []
        for pasangan in nilai:
            if len(pasangan) >= 2:
                try:
                    hasil.append((float(pasangan[0]), float(pasangan[1])))
                except (TypeError, ValueError):
                    continue
        return hasil
    if len(nilai) >= 2:
        return [(0.0, _angka(nilai[0])), (1.0, _angka(nilai[1]))]
    return []


def _nilai_pada(kunci, waktu, bawaan):
    if not kunci:
        return bawaan
    if waktu <= kunci[0][0]:
        return kunci[0][1]
    for i in range(1, len(kunci)):
        t1, v1 = kunci[i]
        t0, v0 = kunci[i - 1]
        if waktu <= t1:
            if t1 == t0:
                return v1
            p = (waktu - t0) / (t1 - t0)
            return v0 + (v1 - v0) * p
    return kunci[-1][1]


def _titik_lintasan(tokoh):
    """Baca lintasan eksplisit atau keyframe x/y yang dipakai cerita.js."""
    lintasan = tokoh.get("lintasan") or tokoh.get("tujuan")
    if isinstance(lintasan, list):
        hasil = []
        for titik in lintasan:
            if isinstance(titik, dict) and "x" in titik and "y" in titik:
                hasil.append((_angka(titik["x"]), _angka(titik["y"])))
            elif isinstance(titik, (list, tuple)) and len(titik) >= 2:
                # Bentuk [detik, x, y] atau [x, y].
                if len(titik) >= 3:
                    hasil.append((_angka(titik[1]), _angka(titik[2])))
                else:
                    hasil.append((_angka(titik[0]), _angka(titik[1])))
        if hasil:
            return hasil

    # cerita.js menerima x/y sebagai [awal, akhir] atau [[detik, nilai], ...].
    kunci_x = _nilai_posisi_kunci(tokoh.get("x"))
    kunci_y = _nilai_posisi_kunci(tokoh.get("y"))
    waktu = sorted({t for t, _ in kunci_x + kunci_y})
    if len(waktu) < 2:
        return []
    x_awal = _angka(tokoh.get("x")) if not kunci_x else kunci_x[0][1]
    y_awal = _angka(tokoh.get("y")) if not kunci_y else kunci_y[0][1]
    return [(_nilai_pada(kunci_x, t, x_awal),
             _nilai_pada(kunci_y, t, y_awal)) for t in waktu]


def _komponen_posisi(nilai, awal=False):
    """Ambil posisi awal/akhir dari angka, rentang, atau keyframe renderer."""
    if not isinstance(nilai, list) or not nilai:
        return _angka(nilai)
    butir = nilai[0] if awal else nilai[-1]
    if isinstance(butir, (list, tuple)):
        if len(butir) >= 2:
            return _angka(butir[1] if len(butir) >= 2 else butir[0])
        return _angka(butir[0]) if butir else 0.0
    return _angka(butir)


def _posisi(tokoh, awal=False):
    """Posisi ujung lintasan; kontinuitas membandingkan awal shot dengan akhir shot sebelumnya."""
    return (_komponen_posisi(tokoh.get("x", 0), awal),
            _komponen_posisi(tokoh.get("y", 0), awal))


def periksa_penataan_panggung(cerita, jarak_interaksi=190.0, loncatan_maksimum=300.0):
    """Periksa perpindahan, interaksi, tumpang-tindih, dan kontinuitas antarsyot.

    Hasil berupa daftar temuan {tingkat, kode, shot, tokoh, pesan}.
    Pemeriksaan bersifat non-mutasi: spesifikasi tidak diubah.
    """
    temuan = []
    daftar_shot = (cerita or {}).get("shot") or []
    posisi_lalu = {}
    arah_lalu = {}

    def lapor(tingkat, kode, indeks, identitas, pesan):
        temuan.append({"tingkat": tingkat, "kode": kode, "shot": indeks,
                       "tokoh": identitas, "pesan": pesan})

    for indeks, shot in enumerate(daftar_shot):
        boneka = shot.get("boneka") or []
        menurut_id = {str(b.get("id", i)): b for i, b in enumerate(boneka)}
        posisi_kini = {}

        for nomor, tokoh in enumerate(boneka):
            identitas = str(tokoh.get("id", nomor))
            x, y = _posisi(tokoh)
            posisi_kini[identitas] = (x, y)
            gerak = tokoh.get("gerak", "")
            nilai_jalan = tokoh.get("jalan", 0)
            jalan_aktif = isinstance(nilai_jalan, (int, float)) and nilai_jalan > 0
            if isinstance(nilai_jalan, list):
                jalan_aktif = any(
                    isinstance(kunci, (list, tuple))
                    and len(kunci) >= 2
                    and isinstance(kunci[-1], (int, float))
                    and kunci[-1] > 0
                    for kunci in nilai_jalan
                )
            berjalan = (isinstance(gerak, str) and gerak in {"jalan", "lari"}) or jalan_aktif
            lintasan = _titik_lintasan(tokoh)
            bergerak_nyata = len(lintasan) >= 2 and hypot(
                lintasan[-1][0] - lintasan[0][0],
                lintasan[-1][1] - lintasan[0][1]) >= 12
            if berjalan and not bergerak_nyata and not tokoh.get("di_tempat"):
                lapor("gagal", "jalan_tanpa_lintasan", indeks, identitas,
                      "Gerak jalan/lari hanya mengayun anggota badan; tambahkan lintasan dengan perpindahan posisi.")
            if tokoh.get("di_tempat") and not tokoh.get("alasan_di_tempat"):
                lapor("peringatan", "alasan_di_tempat_kosong", indeks, identitas,
                      "Tokoh ditandai bergerak di tempat tanpa alasan cerita.")

            if lintasan and len(lintasan) == 1:
                lapor("peringatan", "lintasan_tidak_lengkap", indeks, identitas,
                      "Lintasan perlu minimal dua titik agar perpindahan dapat diperiksa.")

            if identitas in posisi_lalu:
                px, py = posisi_lalu[identitas]
                x_awal, y_awal = _posisi(tokoh, awal=True)
                if hypot(x_awal - px, y_awal - py) > loncatan_maksimum and not tokoh.get("perubahan_posisi_dijelaskan"):
                    lapor("peringatan", "loncatan_posisi", indeks, identitas,
                          "Awal posisi tokoh pada shot ini meloncat dari akhir shot sebelumnya tanpa penjelasan.")

            sasaran = tokoh.get("sasaran_id", tokoh.get("target_id"))
            aksi = tokoh.get("aksi")
            if sasaran is not None and aksi:
                target = menurut_id.get(str(sasaran))
                if target is None:
                    lapor("gagal", "sasaran_tidak_ditemukan", indeks, identitas,
                          f"Sasaran interaksi {sasaran} tidak ada pada shot ini.")
                else:
                    tx, ty = _posisi(target)
                    if hypot(x - tx, y - ty) > jarak_interaksi:
                        lapor("peringatan", "sasaran_terlalu_jauh", indeks, identitas,
                              "Pelaku aksi masih terlalu jauh dari sasaran untuk interaksi yang dinyatakan.")

        # Tumpang-tindih kasar pada kedalaman serupa; hanya peringatan agar penataan panggung artistik tetap mungkin.
        for i, kiri in enumerate(boneka):
            for kanan in boneka[i + 1:]:
                ix, iy = _posisi(kiri)
                jx, jy = _posisi(kanan)
                skala = max(_angka(kiri.get("s"), 1), _angka(kanan.get("s"), 1), 0.1)
                if abs(iy - jy) < 75 and abs(ix - jx) < 70 * skala:
                    lapor("peringatan", "tokoh_bertumpuk", indeks,
                          str(kiri.get("id", "")),
                          f"Tokoh {kiri.get('id')} dan {kanan.get('id')} berpotensi bertumpuk.")


        # Pemeriksaan kedekatan pelaku ke visual inti, mengikuti pemeriksaan
        # geometri netral-genre pada Sutradara AI Studio.
        aturan = shot.get("penataan_panggung") or {}
        if isinstance(aturan, dict) and aturan.get("otomatis") is True:
            visual_id = aturan.get("visual_id")
            visual = next((o for o in (shot.get("benda") or [])
                           if str(o.get("id")) == str(visual_id)), None)
            pelaku_ids = {str(x) for x in aturan.get("pelaku", [])}
            if visual is None:
                lapor("peringatan", "visual_penataan_panggung_tidak_ditemukan", indeks, "",
                      f"Visual inti {visual_id!r} tidak ditemukan; penataan panggung otomatis tidak dapat diperiksa.")
            else:
                vx, vy = _posisi(visual)
                ambang = _angka(aturan.get("jarak_maks_visual"), 180.0)
                jauh = []
                for tokoh in boneka:
                    if str(tokoh.get("id")) not in pelaku_ids:
                        continue
                    tx, ty = _posisi(tokoh)
                    jarak = hypot(tx - vx, ty - vy)
                    if jarak > ambang:
                        jauh.append(str(tokoh.get("id", "")))
                if jauh:
                    lapor("peringatan", "pelaku_jauh_dari_visual", indeks, ",".join(jauh),
                          "Pelaku aksi terlalu jauh dari visual inti; tinjau posisi panggung.")

        # Arah lintasan yang berubah antarsyot perlu putar balik yang diceritakan.
        for tokoh in boneka:
            identitas = str(tokoh.get("id", ""))
            arah = _arah_lintasan(tokoh)
            if arah and identitas in arah_lalu and arah_lalu[identitas] != arah:
                if not tokoh.get("berbalik_sesuai_cerita"):
                    lapor("peringatan", "arah_lintasan_berubah", indeks, identitas,
                          "Arah perjalanan berubah dari shot sebelumnya tanpa penanda putar balik cerita.")
            if arah:
                arah_lalu[identitas] = arah

        # Dalam interaksi, dua tokoh tidak semestinya sama-sama memakai profil depan
        # kecuali pilihan itu dijelaskan secara artistik.
        for tokoh in boneka:
            sasaran = tokoh.get("sasaran_id", tokoh.get("target_id"))
            if sasaran is None or not tokoh.get("aksi"):
                continue
            target = menurut_id.get(str(sasaran))
            if target and tokoh.get("profil") == "depan" and target.get("profil") == "depan":
                alasan = tokoh.get("alasan_arah") or target.get("alasan_arah")
                if not (isinstance(alasan, str) and alasan.strip()):
                    lapor("peringatan", "interaksi_menghadap_kamera", indeks, str(tokoh.get("id", "")),
                          "Pelaku dan sasaran sama-sama menghadap kamera; arahkan profil ke lawan atau jelaskan alasannya.")

        posisi_lalu = posisi_kini

    return temuan


def wajib_lolos_penataan_panggung(cerita):
    """Gagalkan validasi hanya untuk temuan tingkat gagal."""
    temuan = periksa_penataan_panggung(cerita)
    gagal = [item for item in temuan if item["tingkat"] == "gagal"]
    if gagal:
        ringkasan = "; ".join(f'{item["kode"]} (shot {item["shot"]}, tokoh {item["tokoh"]})'
                              for item in gagal)
        raise ValueError("Penataan panggung tidak valid: " + ringkasan)
    return temuan


def rencanakan_penataan_panggung(cerita):
    """Tempatkan pelaku dekat visual inti dan susun pihak lawan secara deterministik.

    Meniru prinsip penataan panggung Sutradara AI Studio: pelaku berada di sisi
    kerja objek, pihak lawan di sisi seberang. Koordinat eksplisit tidak ditimpa
    kecuali aturan shot menyatakan paksa=True.
    Format shot.penataan_panggung:
      {"otomatis": true, "visual_id": "objek", "pelaku": [1],
       "sisi_pelaku": 1, "jarak_pelaku": 70, "jarak_lawan": 260,
       "paksa": false}
    """
    perubahan = []
    for indeks, shot in enumerate((cerita or {}).get("shot") or []):
        aturan = shot.get("penataan_panggung")
        if not isinstance(aturan, dict) or aturan.get("otomatis") is not True:
            continue
        boneka = shot.setdefault("boneka", [])
        benda = shot.get("benda") or []
        visual_id = aturan.get("visual_id")
        visual = next((o for o in benda if str(o.get("id")) == str(visual_id)), None) if visual_id is not None else None
        if visual is None:
            perubahan.append({"shot": indeks, "status": "lewati",
                              "alasan": "visual_id tidak ditemukan"})
            continue

        cx, cy = _posisi(visual)
        pelaku_ids = {str(x) for x in aturan.get("pelaku", [])}
        paksa = aturan.get("paksa") is True
        sisi = -1 if _angka(aturan.get("sisi_pelaku"), 1.0) < 0 else 1
        jarak_pelaku = max(35.0, _angka(aturan.get("jarak_pelaku"), 70.0))
        jarak_lawan = max(jarak_pelaku + 40.0, _angka(aturan.get("jarak_lawan"), 260.0))
        jumlah_diatur = 0

        for nomor, aktor in enumerate(boneka):
            identitas = str(aktor.get("id", nomor))
            if identitas in pelaku_ids:
                target_x = max(80.0, min(1000.0, cx + sisi * jarak_pelaku))
            else:
                target_x = max(80.0, min(1000.0, cx - sisi * jarak_lawan))
            if paksa or "x" not in aktor:
                aktor["x"] = target_x
                jumlah_diatur += 1
            if paksa or "y" not in aktor:
                aktor["y"] = cy + _angka(aturan.get("offset_y"), 0.0)

        perubahan.append({"shot": indeks, "status": "diterapkan",
                          "jumlah_tokoh_diatur": jumlah_diatur,
                          "visual_id": visual_id})
    return perubahan


def _arah_lintasan(tokoh):
    """Arah mendatar lintasan, 1 ke kanan, -1 ke kiri, 0 tidak bergerak."""
    lintasan = _titik_lintasan(tokoh)
    if len(lintasan) < 2:
        return 0
    dx = lintasan[-1][0] - lintasan[0][0]
    return (dx > 0) - (dx < 0)

def susun_rencana_blocking(rencana_cerita, cerita):
    """Bangun kontrak aksi panggung dari peristiwa semantik tanpa mengarang geometri.

    Rencana ini menjembatani ID tokoh/peristiwa ke shot. Posisi, lintasan,
    pose, kendaraan, dan gerak tetap harus ditentukan oleh pengarah visual.
    """
    rencana_cerita = rencana_cerita if isinstance(rencana_cerita, dict) else {}
    cerita = cerita if isinstance(cerita, dict) else {}
    adegan = rencana_cerita.get("adegan") or []
    daftar_shot = cerita.get("shot") or []

    peristiwa_berdasarkan_beat = {}
    daftar_peristiwa = []
    transisi_keadaan = []
    keadaan_terakhir = {}
    diagnostik = []
    for nomor_adegan, beat in enumerate(adegan, start=1):
        if not isinstance(beat, dict):
            continue
        beat_id = beat.get("id")
        peristiwa = beat.get("peristiwa") or []
        if not isinstance(peristiwa, list):
            diagnostik.append({
                "kode": "daftar_peristiwa_tidak_valid",
                "beat_id": beat_id,
            })
            continue
        ids = []
        for nomor, item in enumerate(peristiwa, start=1):
            if not isinstance(item, dict):
                continue
            id_peristiwa = item.get("id")
            if not isinstance(id_peristiwa, str) or not id_peristiwa.strip():
                id_peristiwa = f"{beat_id or f'beat-{nomor_adegan:03d}'}-peristiwa-{nomor:03d}"
            aktor_id = item.get("aktor_id")
            aksi = item.get("aksi")
            sasaran_tokoh_id = item.get("sasaran_tokoh_id")
            siap_dipetakan = (
                isinstance(aktor_id, str) and bool(aktor_id.strip())
                and isinstance(aksi, str) and bool(aksi.strip())
            )
            butir = {
                "id": id_peristiwa,
                "beat_id": beat_id,
                "aktor_id": aktor_id,
                "aksi": aksi,
                "sasaran": item.get("sasaran"),
                "sasaran_tokoh_id": sasaran_tokoh_id,
                "sasaran_benda": item.get("sasaran_benda"),
                "sasaran_benda_id": item.get("sasaran_benda_id"),
                "tujuan": item.get("tujuan"),
                "perubahan_keadaan": item.get("perubahan_keadaan"),
                "status": "siap_dipetakan_ke_visual" if siap_dipetakan else "perlu_pelengkapan_semantik",
            }
            perubahan = item.get("perubahan_keadaan")
            if perubahan is not None:
                if not isinstance(perubahan, dict):
                    diagnostik.append({
                        "kode": "perubahan_keadaan_tidak_valid",
                        "beat_id": beat_id,
                        "peristiwa_id": id_peristiwa,
                    })
                else:
                    entitas_id = perubahan.get("entitas_id")
                    dari = perubahan.get("dari")
                    menjadi = perubahan.get("menjadi")
                    if not isinstance(entitas_id, str) or not entitas_id.strip() or menjadi is None:
                        diagnostik.append({
                            "kode": "transisi_keadaan_belum_lengkap",
                            "beat_id": beat_id,
                            "peristiwa_id": id_peristiwa,
                        })
                    else:
                        sebelumnya = keadaan_terakhir.get(entitas_id)
                        if "dari" in perubahan and sebelumnya is not None and dari != sebelumnya:
                            diagnostik.append({
                                "kode": "asal_transisi_tidak_cocok_dengan_keadaan_terakhir",
                                "beat_id": beat_id,
                                "peristiwa_id": id_peristiwa,
                                "entitas_id": entitas_id,
                                "keadaan_terakhir": sebelumnya,
                                "keadaan_dari": dari,
                            })
                        transisi_keadaan.append({
                            "entitas_id": entitas_id,
                            "dari": dari,
                            "menjadi": menjadi,
                            "beat_id": beat_id,
                            "peristiwa_id": id_peristiwa,
                            "urutan": len(transisi_keadaan) + 1,
                        })
                        keadaan_terakhir[entitas_id] = menjadi
            daftar_peristiwa.append(butir)
            ids.append(id_peristiwa)
            if not siap_dipetakan:
                diagnostik.append({
                    "kode": "peristiwa_belum_lengkap_untuk_blocking",
                    "beat_id": beat_id,
                    "peristiwa_id": id_peristiwa,
                    "aktor_id": aktor_id,
                    "aksi": aksi,
                })
        if beat_id is not None:
            peristiwa_berdasarkan_beat[str(beat_id)] = ids

    tautan_shot = []
    beat_terpakai = set()
    for indeks, shot in enumerate(daftar_shot):
        if not isinstance(shot, dict):
            continue
        beat_id = shot.get("_beat_id")
        ids = peristiwa_berdasarkan_beat.get(str(beat_id), []) if beat_id is not None else []
        if beat_id is not None:
            beat_terpakai.add(str(beat_id))
        tautan_shot.append({
            "indeks": indeks,
            "beat_id": beat_id,
            "peristiwa_ids": list(ids),
        })

    for beat_id, ids in peristiwa_berdasarkan_beat.items():
        if ids and beat_id not in beat_terpakai:
            diagnostik.append({
                "kode": "beat_peristiwa_tidak_memiliki_shot",
                "beat_id": beat_id,
                "peristiwa_ids": list(ids),
            })

    return {
        "versi": 1,
        "tahap": "kontrak_semantik",
        "catatan": (
            "Belum berisi koordinat, lintasan, pose, atau gerak. "
            "Pengarah visual harus memetakannya ke boneka dan benda renderer."
        ),
        "peristiwa": daftar_peristiwa,
        "transisi_keadaan": transisi_keadaan,
        "keadaan_akhir": dict(keadaan_terakhir),
        "shot": tautan_shot,
        "diagnostik": diagnostik,
    }

