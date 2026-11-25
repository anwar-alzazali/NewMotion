"""Pemeriksaan blocking panggung yang tidak bergantung pada genre atau renderer."""
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


def _posisi(tokoh):
    x, y = tokoh.get("x", 0), tokoh.get("y", 0)
    if isinstance(x, list) and x:
        x = x[-1][-1] if isinstance(x[-1], (list, tuple)) else x[-1]
    if isinstance(y, list) and y:
        y = y[-1][-1] if isinstance(y[-1], (list, tuple)) else y[-1]
    return _angka(x), _angka(y)


def periksa_blocking(cerita, jarak_interaksi=190.0, loncatan_maksimum=300.0):
    """Periksa perpindahan, interaksi, tumpang-tindih, dan kontinuitas antarsyot.

    Hasil berupa daftar temuan {tingkat, kode, shot, tokoh, pesan}.
    Pemeriksaan bersifat non-mutasi: spesifikasi tidak diubah.
    """
    temuan = []
    daftar_shot = (cerita or {}).get("shot") or []
    posisi_lalu = {}

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
            berjalan = (isinstance(gerak, str) and gerak in {"jalan", "lari"}) or (
                isinstance(nilai_jalan, (int, float)) and nilai_jalan > 0
            )
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
                if hypot(x - px, y - py) > loncatan_maksimum and not tokoh.get("perubahan_posisi_dijelaskan"):
                    lapor("peringatan", "loncatan_posisi", indeks, identitas,
                          "Posisi tokoh berubah jauh dari shot sebelumnya tanpa penjelasan.")

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

        # Tumpang-tindih kasar pada kedalaman serupa; hanya peringatan agar blocking artistik tetap mungkin.
        for i, kiri in enumerate(boneka):
            for kanan in boneka[i + 1:]:
                ix, iy = _posisi(kiri)
                jx, jy = _posisi(kanan)
                skala = max(_angka(kiri.get("s"), 1), _angka(kanan.get("s"), 1), 0.1)
                if abs(iy - jy) < 75 and abs(ix - jx) < 70 * skala:
                    lapor("peringatan", "tokoh_bertumpuk", indeks,
                          str(kiri.get("id", "")),
                          f"Tokoh {kiri.get('id')} dan {kanan.get('id')} berpotensi bertumpuk.")

        posisi_lalu = posisi_kini

    return temuan


def wajib_lolos_blocking(cerita):
    """Gagalkan validasi hanya untuk temuan tingkat gagal."""
    temuan = periksa_blocking(cerita)
    gagal = [item for item in temuan if item["tingkat"] == "gagal"]
    if gagal:
        ringkasan = "; ".join(f'{item["kode"]} (shot {item["shot"]}, tokoh {item["tokoh"]})'
                              for item in gagal)
        raise ValueError("Blocking tidak valid: " + ringkasan)
    return temuan
