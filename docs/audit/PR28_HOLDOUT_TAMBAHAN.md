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