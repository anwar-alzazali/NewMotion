# Blocking panggung NewMotion

Modul `newmotion.blocking` menyediakan pemeriksaan blocking yang netral genre dan tidak mengubah renderer JavaScript/SVG.

## Kontrak dasar

- `boneka[].lintasan`: minimal dua titik perpindahan, berupa `[{"x": 100, "y": 200}, {"x": 300, "y": 200}]` atau pasangan koordinat.
- `boneka[].gerak`: `jalan` atau `lari` menyatakan siklus anggota badan, bukan perpindahan dunia. Karena itu gerak tersebut wajib disertai lintasan.
- `boneka[].di_tempat` hanya boleh dipakai bila ada `alasan_di_tempat`.
- `boneka[].aksi` bersama `sasaran_id` atau `target_id` menyatakan interaksi; pemeriksa memastikan sasaran hadir dan cukup dekat.
- Identitas `boneka[].id` dipakai untuk memeriksa kontinuitas posisi antarsyot.

## Pemakaian

```python
from newmotion.blocking import periksa_blocking, wajib_lolos_blocking

temuan = periksa_blocking(spec.get("cerita", {}))
wajib_lolos_blocking(spec.get("cerita", {}))
```

Temuan `gagal` menunjukkan kontrak blocking yang wajib diperbaiki. Temuan `peringatan` membantu audit visual, tetapi tidak otomatis menghentikan render. Pemeriksaan tumpang-tindih adalah heuristik berbasis posisi dan skala, bukan deteksi siluet piksel.
