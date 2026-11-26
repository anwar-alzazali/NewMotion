# Penataan panggung NewMotion

Modul `newmotion.penataan_panggung` menyediakan pemeriksaan penataan panggung yang netral genre dan tidak mengubah renderer JavaScript/SVG.

## Kontrak dasar

- `boneka[].lintasan`: minimal dua titik perpindahan, berupa `[{"x": 100, "y": 200}, {"x": 300, "y": 200}]` atau pasangan koordinat.
- `boneka[].gerak`: `jalan` atau `lari` menyatakan siklus anggota badan, bukan perpindahan dunia. Karena itu gerak tersebut wajib disertai lintasan.
- `boneka[].di_tempat` hanya boleh dipakai bila ada `alasan_di_tempat`.
- `boneka[].aksi` bersama `sasaran_id` atau `target_id` menyatakan interaksi; pemeriksa memastikan sasaran hadir dan cukup dekat.
- Identitas `boneka[].id` dipakai untuk memeriksa kontinuitas posisi antarsyot.

## Pemakaian

```python
from newmotion.penataan_panggung import periksa_penataan_panggung, wajib_lolos_penataan_panggung

temuan = periksa_penataan_panggung(spec.get("cerita", {}))
wajib_lolos_penataan_panggung(spec.get("cerita", {}))
```

Temuan `gagal` menunjukkan kontrak penataan panggung yang wajib diperbaiki. Temuan `peringatan` membantu audit visual, tetapi tidak otomatis menghentikan render. Pemeriksaan tumpang-tindih adalah heuristik berbasis posisi dan skala, bukan deteksi siluet piksel.
## Kontrak blocking dari rencana cerita

`newmotion.penataan_panggung.susun_rencana_blocking` menyusun `rencana_blocking`
dari `rencana_cerita` dan `cerita.shot`. Sutradara inti menjalankannya
setelah setiap shot ditautkan ke ID beat.

Kontrak ini:
- Mengikat peristiwa ke shot melalui `_beat_id`, tanpa menyalin atau menebak isi narasi.
- Membawa `aktor_id`, aksi, sasaran tokoh/benda, tujuan, dan perubahan keadaan.
- Mencatat peristiwa yang belum memiliki aktor atau aksi terpetakan, serta beat yang belum memiliki shot.
- Tidak membuat `boneka`, koordinat, lintasan, pose, kendaraan, atau keyframe. Semua itu tetap tanggung jawab pengarah visual/paket genre.

Dengan demikian, `rencana_blocking` adalah kontrak semantik untuk tahap blocking berikutnya, bukan bukti bahwa gerakan sudah terbentuk atau siap dirender.
## Metadata roster tokoh

Naskah dapat menyediakan `tokoh[]` sebagai roster eksplisit. Setiap entri wajib memiliki `nama`; `id` boleh disediakan atau dibentuk deterministik dari nama. Field metadata lain disalin utuh ke `rencana_cerita.tokoh`, misalnya kategori dan deskripsi visual.

Beat yang menyebut nama pada `peran[]` akan ditautkan ke entri roster berdasarkan nama yang dinormalisasi. Nama yang bertabrakan setelah normalisasi dan ID ganda ditolak agar rujukan tidak ambigu.

Metadata ini belum menghasilkan `boneka[]` dan tidak memberi izin visual dengan sendirinya. Paket genre tetap harus menentukan cara tokoh boleh ditampilkan, lalu pengarah visual memetakan profil yang sah ke kontrak renderer.
