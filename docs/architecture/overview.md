# Gambaran arsitektur NewMotion

## Status

Ini baru fondasi yang diusulkan. Domain produk, runtime, target penerapan, dan alur utama pengguna belum dikonfirmasi. Nama bagian di bawah merupakan batas tanggung jawab yang direncanakan, bukan klaim bahwa kode tersebut sudah tersedia.

## Prinsip perancangan

1. Aturan domain tidak bergantung pada framework atau penyedia layanan tertentu.
2. Pekerjaan berdurasi panjang dapat dipantau, dilanjutkan, dan dicoba ulang dengan aman.
3. Data dari luar divalidasi ketika memasuki sistem.
4. Implementasi basis data, antrean, penyimpanan, dan penyedia layanan dapat diganti.
5. Dependensi dijaga tetap sedikit sampai kebutuhan fitur benar-benar jelas.
6. Pengujian dan kesiapan operasional menjadi bagian dari setiap fitur.

## Batas tanggung jawab yang direncanakan

| Bagian | Tanggung jawab | Aturan ketergantungan |
|---|---|---|
| `domain/` | Entitas, objek nilai, aturan inti, dan peristiwa domain | Tidak bergantung pada infrastruktur |
| `application/` | Kasus penggunaan, pengaturan alur, dan kontrak antarmuka | Bergantung pada domain |
| `infrastructure/` | Basis data, antrean, penyimpanan, serta adapter AI/penyedia layanan | Menerapkan kontrak aplikasi |
| `interfaces/` | HTTP/API, CLI, webhook, dan pintu masuk pengguna | Memanggil kasus penggunaan |
| `workers/` | Pekerjaan latar belakang dan tugas terjadwal/antrean | Memanggil kasus penggunaan |
| `tests/` | Pengujian unit, integrasi, kontrak, dan alur menyeluruh | Memastikan perilaku sistem |
| `docs/` | Keputusan arsitektur, panduan operasional, dan kontrak | Menjelaskan perilaku yang benar-benar ada |

Monolit modular tetap dapat berjalan sebagai satu aplikasi yang diterapkan bersama. Jangan membuat layanan atau basis data terpisah untuk setiap bagian tanpa alasan yang terukur.

## Pola alur kerja

Untuk alur yang terdiri dari beberapa tahap:

1. Terima masukan dengan kontrak berversi, lalu validasi.
2. Buat identitas operasi atau tugas yang tersimpan secara persisten.
3. Catat perubahan status dan konteks kesalahan yang berguna.
4. Jalankan tahap demi tahap melalui adapter yang dapat diganti.
5. Tetapkan aturan percobaan ulang secara eksplisit. Gunakan kunci idempotensi untuk efek samping eksternal jika didukung.
6. Simpan hasil sebagai artefak beserta metadata dan pemeriksaan integritas jika diperlukan.
7. Sediakan status dan alasan kegagalan bagi pemanggil atau operator.

Jangan menjanjikan eksekusi tepat satu kali. Jika waktu permintaan habis setelah penyedia layanan menerima pekerjaan, hasil akhirnya bisa tidak pasti. Periksa status ke penyedia layanan atau minta keputusan operator sebelum mengirim ulang efek samping yang hasilnya belum jelas.

## Batas data dan keamanan

- Rahasia disediakan melalui lingkungan aplikasi atau pengelola rahasia, bukan disimpan di repositori.
- Gunakan kredensial dengan hak minimum untuk setiap integrasi dan lingkungan.
- Validasi jalur berkas, identifier, ukuran muatan, tipe MIME, dan skema saat data masuk.
- Jangan masukkan data pribadi atau artefak produksi ke repositori publik maupun log.
- Terapkan otorisasi pada lapisan aplikasi; jangan hanya mengandalkan tampilan antarmuka.
- Gunakan penyimpanan objek privat dan tautan kedaluwarsa untuk hasil privat jika diperlukan.
- Tetapkan aturan retensi, penghapusan, dan pencadangan sebelum menyimpan data pengguna.

## Pemeriksaan mutu

Setiap fitur utuh minimal mencakup:

- pengujian unit yang konsisten untuk aturan domain;
- pengujian integrasi untuk batas penyimpanan dan penyedia layanan;
- pengujian kontrak untuk muatan eksternal;
- pemeriksaan sintaks, tipe, dan gaya kode sesuai teknologi yang dipilih;
- langkah penerimaan manual untuk perilaku yang terlihat pengguna;
- keterangan jujur jika ada pemeriksaan yang belum dijalankan.

## Kebijakan runtime dan dependensi

Bahasa pemrograman, framework, basis data, antrean, dan penyedia cloud belum dipilih. Tentukan setelah alur produk dan batasan penerapan diketahui. Utamakan kemampuan bawaan bahasa dan sedikit dependensi yang terawat daripada menambah kerangka kerja yang belum dibutuhkan.

## Standar penulisan kode

Ikuti gaya bahasa Indonesia seperti pada repositori `mesin-video`. Nama variabel, konstanta, fungsi, metode, kelas, modul, komentar, dan docstring harus berbahasa Indonesia. Nama berkas dan folder juga diutamakan dalam bahasa Indonesia selama tidak melanggar kebutuhan teknis atau kompatibilitas. Identifier bawaan bahasa, framework, pustaka, API, dan protokol eksternal tetap menggunakan nama aslinya.
