# Log kerja — persiapan pembangunan ulang renderer

- Tanggal: 2026-11-28
- Tugas: penyusunan roadmap dan protokol kerja GPT renderer
- Branch: `renderer/pembangunan-ulang`
- Status: **DOKUMENTASI AWAL DIBUAT; audit teknis RND-001 belum dimulai**

## Dasar yang dibaca
- `README.md`
- `docs/TUGAS_GPT.md`
- `docs/ROADMAP.md`
- `docs/arsip/tugas_gpt_selesai.md`
- `docs/ATURAN_KOMPONEN.md`
- `mesin-video/papan/uji_tokoh.py`
- `mesin-video/papan/karakter/test_uji_tokoh.py`

## Keputusan
1. Pembangunan ulang dimulai dengan inventaris dan audit, bukan langsung mengganti renderer.
2. `mesin-video/papan/cerita.js` dicatat sebagai mesin gambar utama saat ini; Python berperan pada orkestrasi, validasi, adapter, dan alat uji sesuai implementasi yang ada.
3. Adegan mobil didorong dipakai sebagai salah satu uji integrasi, bukan satu-satunya ukuran keberhasilan.
4. Kode dari branch lama hanya boleh diambil setelah pemeriksaan fungsi, commit asal, tes, dan bukti visual.
5. Sistem anti-loop memakai ID tugas, kriteria terukur, baseline beku, batas tiga pendekatan, catatan percobaan, dan status MACET.
6. Tidak ada merge ke `main` tanpa izin pemilik.

## Berkas yang dibuat
- `docs/RENDERER_ROADMAP.md`
- `docs/TUGAS_GPT_RENDERER.md`

## Yang belum dilakukan
- Belum ada kode renderer yang diubah.
- Belum ada tes atau render yang dijalankan.
- Belum ada PR yang dibuat.
- Belum ada klaim bahwa renderer sudah lulus tahap apa pun.

## Langkah berikut
Mulai **RND-001 — Audit baseline dan peta renderer**. Periksa sumber kode dan branch eksperimen yang relevan, buat matriks kemampuan dengan bukti, lalu simpan hasilnya di log baru. Jangan mulai RND-002 sebelum audit RND-001 ditinjau.
