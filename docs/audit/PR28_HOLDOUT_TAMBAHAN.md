# Registrasi blind holdout lanjutan — PR #28

Dipilih dari daftar nama berkas di repo referensi sebelum membuka isi papan/narasinya dan sebelum perubahan koreksi audit berikutnya.

Holdout yang dikunci:
- `mesin-video/papan/kisah/ghibah1.json`
- `mesin-video/papan/kisah/utang1.json`
- `mesin-video/papan/kisah/dabbah1.json`

Aturan:
1. Jangan gunakan isi/narasi tiga papan ini untuk menyetel pola pengarah.
2. Ambil narasi dan nilai baseline hanya setelah daftar ini tercatat dalam commit.
3. Jalankan pengarah dan ukur hasil holdout setelah koreksi umum selesai.
4. Laporkan skor dan diagnostik shot yang keliru/tidak tergambar. Jika ada masalah, jangan ubah aturan dengan pengecualian judul cerita; perbaiki aturan umum lalu tandai bahwa holdout telah dibuka.
5. Holdout ini adalah validasi prospektif untuk revisi audit sekarang; tidak menghapus fakta bahwa Nuh 2, Dabbah 2, dan Kubur 1 telah dilihat pada iterasi sebelumnya.
