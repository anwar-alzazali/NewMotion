# Registrasi blind holdout lanjutan — PR #28

Daftar ini dikunci dalam commit tersendiri sebelum isi papan/narasi dibuka dan sebelum aturan pengarah disetel terhadap holdout.

Holdout yang dikunci:
- `mesin-video/papan/kisah/doa2.json`
- `mesin-video/papan/kisah/bangkrut1.json`
- `mesin-video/papan/kisah/wali1.json`

Ketiganya tidak termasuk fixture tolok ukur maupun fixture tambahan yang sudah ada di NewMotion saat registrasi.

Aturan:
1. Jangan gunakan isi/narasi tiga papan ini untuk menyetel pola pengarah.
2. Ambil narasi dan nilai baseline setelah daftar ini tercatat dalam commit.
3. Jalankan pengarah dan ukur hasil holdout setelah koreksi umum selesai.
4. Laporkan skor dan diagnostik shot yang keliru/tidak tergambar. Jika ada masalah, jangan ubah aturan dengan pengecualian judul cerita; perbaiki aturan umum lalu tandai bahwa holdout telah dibuka.
5. Holdout ini adalah validasi prospektif untuk revisi audit sekarang; tidak menghapus fakta bahwa Nuh 2, Dabbah 2, dan Kubur 1 telah dilihat pada iterasi sebelumnya.

## Cara pembentukan fixture setelah daftar dikunci

- `doa2.json`: teks diambil berurutan dari subtitle bertimestamp pada papan sumber.
- `bangkrut1.json` dan `wali1.json`: teks diambil berurutan dari token kata bertimestamp pada `cerita.tengah`.
- Setiap potongan sumber menjadi satu adegan naskah; judul berasal dari nama papan, tanpa aturan pengarah khusus per judul.
- Fixture ini dipakai untuk membandingkan baseline `main` dan branch PR #28 dengan alat ukur PR #29 yang sama.
- Skor tetap hanya indikator kedalaman struktur dan kesesuaian leksikal; bukan bukti kualitas visual. Tidak ada render otomatis dari workflow ini.


## Pratinjau visual manual

Workflow `.github/workflows/pr28-pratinjau-semantik.yml` disiapkan dengan pemicu `workflow_dispatch` saja. Pilihan default adalah `yajuj1`; pilihan lain adalah `doa2`, `bangkrut1`, dan `wali1`.

Workflow akan menjalankan naskah melalui CLI NewMotion, menyimpan papan hasil pengarahan, memvalidasi subjek semantik penting, merender MP4 H.264 1080x1920, mengambil frame audit, lalu mengunggah artefak. Workflow ini belum dijalankan; pemilik repo perlu memicunya secara manual dan meninjau frame/video sebelum PR dinyatakan layak merge.
