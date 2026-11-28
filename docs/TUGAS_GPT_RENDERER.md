# Tugas GPT — pembangunan ulang renderer

Dokumen ini adalah instruksi kerja khusus untuk AI pengembang pada cabang `renderer/pembangunan-ulang`. Dokumen ini **tidak menggantikan** `docs/TUGAS_GPT.md` untuk aturan umum NewMotion. Bila ada konflik, batas wajib proyek dan keputusan pemilik tetap berlaku.

## 1. Misi

Bangun renderer yang dapat menjalankan kontrak visual NewMotion secara konsisten dan menghasilkan video yang layak ditinjau. Sutradara tetap menjadi pengambil keputusan cerita; renderer hanya menjalankan instruksi visual yang sah.

## 2. Aturan sebelum mulai setiap sesi

1. Baca dokumen ini sampai selesai dan `docs/RENDERER_ROADMAP.md`.
2. Baca seluruh log kerja renderer terbaru di `docs/log_kerja/` (urut waktu). Ambil status dari log, bukan dari ingatan percakapan.
3. Periksa daftar tugas di bagian 4 dan status PR/branch yang terkait. Jangan mengambil tugas berstatus `SELESAI`, `DIBLOKIR`, atau sudah memiliki PR aktif.
4. Periksa perubahan pada branch kerja dan jangan menimpa commit pengembang lain.
5. Sebelum mengubah kode, tulis ringkasan: masalah terukur, bukti saat ini, target perubahan, file yang disentuh, dan tes penerimaan.
6. Bila konteks atau bukti tidak cukup, lakukan audit terbatas untuk mengumpulkan bukti; jangan langsung menulis ulang.

## 3. Protokol anti-loop — WAJIB

### 3.1 Satu masalah = satu tiket kerja yang dapat diuji
Setiap masalah harus memiliki:
- ID unik (contoh `RND-001`);
- gejala yang dapat diamati;
- cara reproduksi;
- bukti awal (frame, log, atau tes);
- dugaan akar masalah yang diberi label **hipotesis**, bukan fakta;
- perubahan yang direncanakan;
- kriteria selesai yang dapat diukur.

Dilarang membuat tugas kabur seperti “maksimalkan renderer”, “perbagus semua tokoh”, atau “rapikan sampai sempurna”.

### 3.2 Batas percobaan
- Maksimal **3 pendekatan implementasi** untuk satu gejala yang sama.
- Setiap pendekatan harus berbeda secara teknis dan menyebutkan hasil yang diharapkan.
- Jika dua pendekatan gagal, hentikan perubahan kode sementara dan lakukan diagnosis berbasis bukti (minimal satu reproduksi terisolasi atau instrumentasi).
- Jika pendekatan ketiga gagal, tandai `MACET`, lampirkan bukti, jelaskan apa yang sudah dicoba, dan minta keputusan pemilik/auditor. Jangan mengulang pendekatan dengan nama berbeda.
- Mengubah angka ambang, menyembunyikan elemen, menonaktifkan tes, atau mengganti adegan uji bukan perbaikan kecuali ada alasan teknis dan persetujuan tertulis.

### 3.3 Syarat mengulang tes
Tes boleh diulang hanya jika:
- kode/input berubah;
- lingkungan/ketergantungan diperbaiki;
- kegagalan sebelumnya bersifat sementara dan ada bukti;
- atau pengulangan memang diperlukan untuk mengukur determinisme.

Setiap pengulangan harus menyebutkan apa yang berubah. Menjalankan tes yang sama berkali-kali tanpa perubahan bukan kemajuan.

### 3.4 Bekukan baseline
- Simpan baseline frame/video dan metrik sebelum perubahan.
- Gunakan input, seed, waktu, ukuran kanvas, dan versi dependency yang sama untuk perbandingan.
- Perubahan dinilai dengan before/after berdampingan.
- Jika tidak ada perubahan terukur atau ada regresi, jangan lanjut menambah fitur di atasnya.

### 3.5 Satu sumber kebenaran
Jangan membuat renderer kedua, sistem wajah kedua, skeleton kedua, atau adapter alternatif hanya untuk menghindari memahami implementasi lama. Bila arsitektur memang perlu dipisah, buktikan konflik/biaya struktur lama dan tulis keputusan arsitektur terlebih dahulu.

### 3.6 Tidak mengejar kesempurnaan tanpa batas
Setiap tugas harus menyebutkan:
- ambang numerik atau daftar pemeriksaan;
- kasus yang masuk cakupan;
- kasus yang sengaja belum didukung;
- kondisi berhenti.
Setelah seluruh kriteria terpenuhi dan CI hijau, tugas ditutup. Catatan kosmetik yang tidak menghalangi sasaran masuk backlog baru, bukan alasan membuka ulang tugas.

## 4. Daftar tugas bertahap

Status awal seluruh tugas: `MENUNGGU`. Urutan tidak boleh dilompati kecuali ada dependensi yang jelas dan dicatat.

| ID | Tugas | Hasil utama | Gerbang selesai |
|---|---|---|---|
| RND-001 | Audit baseline dan peta renderer | Inventaris kode, alur render, kemampuan, bukti, bug, metrik baseline | Semua klaim kemampuan punya lokasi kode + bukti tes/visual; daftar gap disepakati |
| RND-002 | Kontrak data renderer | Skema tokoh, benda, pose, sudut, waktu, kamera, interaksi; validator | Kontrak terdokumentasi; input tidak sah ditolak dengan pesan jelas |
| RND-003 | Fondasi geometri | Sistem koordinat, skala, transformasi, jangkar, bounding box | Uji geometri lintas sudut dan skala lulus |
| RND-004 | Rangka dan anatomi tokoh | Skeleton tunggal, panjang tulang, sendi, pose dasar | Tes anatomi tanpa temuan tak terjelaskan; lembar pose terlampir |
| RND-005 | Wajah dan ekspresi | Sistem wajah tunggal yang mengikuti orientasi kepala | Tidak ada overlap fitur tak disengaja; lembar wajah lintas sudut lulus |
| RND-006 | Gerak dan kontinuitas | Keyframe, interpolasi, aksi, stabilitas antar-frame | Klip uji tanpa loncatan/jitter di atas ambang |
| RND-007 | Interaksi tokoh-benda | Titik kait, dorong/tarik/pegang/serah-terima | Jarak kontak dan keterbacaan aksi memenuhi ambang |
| RND-008 | Komposisi dan kualitas adegan | Kedalaman, kamera, pencahayaan, tekstur, determinisme | Lembar adegan ponsel dan metrik render lulus |
| RND-009 | Adapter dan integrasi NewMotion | Pemetaan kontrak, katalog kemampuan nyata, penanganan gap | Papan sutradara menghasilkan frame/video tanpa substitusi diam-diam |
| RND-010 | Uji penerimaan lintas cerita | Paket regresi dan MP4 dari beberapa cerita | Video lintas cerita ditinjau; tidak ada regresi yang belum disetujui |
| RND-011 | Dokumentasi dan rilis renderer | Panduan penggunaan, batas kemampuan, prosedur rilis | Pengembang baru dapat menjalankan dan menguji tanpa menebak |

Tugas pertama yang boleh diambil sekarang hanya **RND-001**. Tugas berikutnya tetap menunggu hasil dan keputusan Tahap 0.

## 5. Format wajib setiap PR

Setiap PR harus memuat:
1. ID tugas dan tahap roadmap.
2. Gejala/tujuan serta bukti awal.
3. Analisis akar masalah: fakta vs hipotesis.
4. Keputusan: pakai/perbaiki/tulis ulang/arsip untuk komponen terkait.
5. Perubahan yang dilakukan dan alasan tiap bagian.
6. Tes otomatis dan hasil CI.
7. Bukti visual before/after dan ukuran ponsel bila relevan.
8. Risiko/regresi serta fitur yang belum didukung.
9. Status kriteria selesai satu per satu.
10. Langkah berikut yang spesifik; jangan menulis “lanjut perbaikan” tanpa ID tugas.

Satu tugas = satu PR. Bila tugas bergantung pada PR sebelumnya yang belum digabung, gunakan branch bertumpuk dan tulis rantai basisnya. Jangan membuat beberapa PR paralel yang mengubah fungsi inti yang sama.

## 6. Kebijakan PR, audit, dan merge

- Semua pekerjaan dilakukan pada cabang renderer, tidak langsung pada `main`.
- PR pertama berasal dari `renderer/pembangunan-ulang` ke basis integrasi yang disepakati pemilik.
- PR tahap lanjutan boleh bertumpuk di atas PR sebelumnya; tulis jelas `base branch` dan urutannya.
- Jangan merge sendiri. CI hijau bukan izin merge.
- Jangan lanjut ke tahap yang bergantung pada tahap sebelumnya sebelum gerbangnya lulus dan hasilnya ditinjau.
- Jangan menutup atau menghapus branch lama. Branch lama adalah arsip bukti sampai pemilik memutuskan lain.
- Jangan cherry-pick massal. Ambil perubahan lama satu per satu setelah audit dan catat commit asalnya.

## 7. Log kerja dan serah-terima

Setiap sesi yang mengubah status tugas wajib membuat berkas baru:
`docs/log_kerja/YYYY-MM-DD-HHMM-renderer-RND-XXX.md`

Isi minimum:
- tanggal dan ID tugas;
- branch, commit awal/akhir, PR bila ada;
- bukti yang diperiksa;
- perubahan dan file yang disentuh;
- perintah/CI yang dijalankan dan hasil sebenarnya;
- kriteria selesai yang lulus/gagal;
- pendekatan yang sudah dicoba (agar tidak diulang);
- status: `LANJUT`, `SELESAI`, atau `MACET`;
- langkah berikut yang persis.

Jika tidak ada perubahan kode tetapi audit menghasilkan keputusan penting, tetap buat log audit. Jangan mengedit log sesi sebelumnya.

## 8. Definisi status

- `MENUNGGU`: belum dimulai atau dependensi belum selesai.
- `BERJALAN`: ada branch/PR aktif dan pemilik tugas jelas.
- `SELESAI`: semua kriteria penerimaan terpenuhi dan bukti tersedia.
- `MACET`: batas percobaan tercapai; perlu keputusan/masukan.
- `DIBATALKAN`: pemilik membatalkan dengan alasan tercatat.

Status hanya boleh berubah dengan bukti dan log. Jangan menandai selesai berdasarkan perkiraan.

## 9. Batas wajib proyek

- Bahasa dokumentasi, komentar, nama variabel/fungsi/modul: Bahasa Indonesia kecuali identifier eksternal.
- Jangan memasukkan rahasia atau token.
- Uji tidak boleh memanggil LLM/TTS berbayar sungguhan.
- Pertahankan batas adab Kisah Islami dan penjaga tokoh yang sudah ada.
- Tidak menggunakan gambar AI/foto sebagai pengganti renderer vektor untuk Kisah Islami.
- Video lama menjadi baseline regresi; perubahan yang disengaja harus dicatat.
- Jangan mengubah pipeline produksi/bot atau menggabungkan renderer ke `main` dalam tugas pembangunan ulang tanpa izin eksplisit.
