# Peta adaptasi: mesin-video → NewMotion

## Kondisi repositori sumber dan tujuan

- Repositori sumber: `anwar-alzazali/mesin-video`, cabang utama `main`.
- Repositori tujuan: `anwar-alzazali/NewMotion`, cabang utama `main`.
- Saat pemeriksaan awal dilakukan, NewMotion baru berisi README awal.
- Repositori sumber merupakan sistem besar yang menggabungkan produksi video, rendering, otomatisasi, operasi Telegram, integrasi penyedia layanan, serta pencatatan status dan biaya melalui Supabase. Menyalin seluruh isinya akan membawa asumsi domain dan keterikatan operasional yang belum tentu sesuai dengan NewMotion.

## Pakai ulang, sesuaikan, atau tunda

| Bagian sumber | Temuan pada `main` | Keputusan untuk NewMotion |
|---|---|---|
| `otomatis.py` | Mengatur alur naskah → gambar → suara → perakitan dan dapat melewati hasil yang sudah tersedia saat dijalankan ulang | Terapkan prinsip alur yang dapat dilanjutkan; jangan salin implementasi khusus video |
| `papan_buat.py`, `rakit.py` | Komposisi HTML/SVG atau gambar, FFmpeg, Pillow, subtitle dan audio bertiming | Tunda sampai NewMotion dipastikan membutuhkan rendering video/media |
| `bot/worker.js` | Webhook Telegram, GitHub API, Supabase, serta alur Gemini utama dengan Claude sebagai cadangan | Jangan pindahkan seluruhnya; ambil pola provider atau webhook hanya jika ada kebutuhan nyata |
| `.github/workflows/*.yml` | Beberapa alur dijalankan manual; memasang alat lalu menjalankan skrip | Gunakan pemicu pekerjaan yang eksplisit jika sesuai; hindari pekerjaan mahal setiap ada push sebelum anggaran CI diketahui |
| `CLAUDE.md` dan `docs/ENGINEERING_AUDIT_LOG.md` | Batasan produk, arahan untuk memakai ulang, catatan audit dan verifikasi | Terapkan disiplin pencatatan keputusan, bukti, dan status pengujian; jangan salin aturan khusus produk |
| Tabel Supabase dan alur biaya | Tabel khusus video, jalur penyimpanan, kredit pengguna, dan pencatatan biaya | Tunda; rancang model data NewMotion berdasarkan alur dan kebutuhan privasinya sendiri |

## Catatan penting tentang cabang dan snapshot

Pohon berkas `main` sumber yang diperiksa untuk fondasi ini **tidak memuat** jalur historis `papan/task_worker.py`, `papan/task_supervisor.py`, atau `papan/sqlite_operation_ledger.py`. Sejumlah catatan audit merujuk pekerjaan dari cabang atau snapshot lain. Karena itu, modul-modul tersebut belum dianggap sebagai bagian dari `main` saat ini dan tidak boleh disalin sebelum cabang serta commit sumbernya dipastikan.

## Kemampuan awal yang layak diadaptasi

1. **Kontrak alur kerja** — skema masukan/keluaran berversi dan validasi di batas sistem.
2. **Pengaturan proses** — status setiap tahap, pelaporan kemajuan, dan kemampuan melanjutkan pekerjaan.
3. **Lapisan adapter** — implementasi penyedia layanan, penyimpanan, persistensi, dan antrean di balik antarmuka.
4. **Percobaan ulang yang aman** — bedakan kegagalan yang aman dicoba ulang dari hasil eksternal yang belum pasti.
5. **Metadata artefak** — checksum, tipe konten, ukuran, kepemilikan, dan retensi jika produk menggunakan berkas.
6. **Bukti operasional** — log dengan ID korelasi, pengujian, dan status verifikasi yang apa adanya.

## Yang tidak disalin

Perubahan fondasi ini tidak menyalin kode sumber, konten pengguna, aset video, aset karakter, dump basis data, kredensial, nilai lingkungan, kunci privat, maupun konfigurasi produksi.
