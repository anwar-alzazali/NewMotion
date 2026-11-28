# Keputusan arsitektur awal — batas tanggung jawab renderer

Tanggal: 2026-11-28  
Tugas: RND-001 — audit dan penetapan batas tanggung jawab  
Status keputusan: **ARAH ARSITEKTUR DISETUJUI UNTUK MENJADI DASAR AUDIT; BELUM MENJADI KONTRAK IMPLEMENTASI FINAL**

## 1. Keputusan inti

Renderer adalah pelaksana visual. Renderer tidak memahami makna naskah, memilih peristiwa, menentukan pesan cerita, atau memutuskan siapa harus melakukan apa. Keputusan tersebut milik Sutradara NewMotion.

Mesin gambar yang sudah ada di `mesin-video/papan/cerita.js` tetap menjadi satu-satunya sumber eksekusi gambar sampai audit membuktikan bagian tertentu perlu dipisah. Pemisahan pertama dilakukan pada **tanggung jawab, kontrak, dan validasi**, bukan dengan menyalin fungsi ke renderer kedua atau langsung memecah file monolitik.

## 2. Batas tanggung jawab

| Lapisan | Tanggung jawab | Tidak boleh mengambil alih |
|---|---|---|
| Sutradara NewMotion | Memahami naskah, menetapkan peristiwa/perubahan keadaan, menentukan aktor, aksi, tujuan, urutan, dan kebutuhan visual per shot | Menggambar SVG, menghitung anatomi atau interpolasi frame |
| Paket genre | Menegakkan aturan genre/adab dan menyusun arahan visual yang sesuai | Mengubah aturan internal mesin gambar atau mengarang kemampuan renderer |
| Adapter visual | Menerjemahkan arahan Sutradara ke kontrak papan/renderer; memetakan ID, aksi, posisi, dan referensi secara eksplisit | Menentukan makna cerita, menebak aksi/pose yang tidak diberikan, menggambar |
| Validator kontrak | Memeriksa struktur, tipe, rentang, referensi, kemampuan, urutan waktu, dan konsistensi input; memberi kesalahan yang dapat ditindaklanjuti | Memperbaiki input secara diam-diam atau mengganti aksi/objek yang tidak didukung |
| Model adegan/papan | Menjadi representasi data adegan: shot, waktu, kamera, aktor, benda, lingkungan, dan relasi | Menjalankan logika gambar atau membuat keputusan cerita |
| Sistem tokoh renderer | Menggambar tokoh; memiliki satu definisi anatomi/rangka, transformasi tubuh, kepala/wajah, pakaian, pose dan titik jangkar | Memilih aksi cerita atau membuat sistem rangka/wajah alternatif |
| Sistem gerak renderer | Mengevaluasi jadwal gerak, keyframe, interpolasi, transformasi pose, dan kontinuitas antar-frame | Menentukan alasan naratif gerakan atau mengubah rencana Sutradara |
| Sistem benda renderer | Menggambar benda dan mengevaluasi parameter visual benda terhadap waktu | Menentukan benda apa yang dibutuhkan cerita |
| Sistem lingkungan renderer | Menggambar latar, cuaca, air, partikel, tekstur, dan efek lingkungan yang dinyatakan dalam papan | Mengubah urutan peristiwa atau memilih lokasi cerita |
| Sistem kamera/komposisi | Menerapkan framing, skala, kedalaman/lapisan, horizon, dan pencahayaan sesuai instruksi papan | Mengubah blocking atau menghilangkan subjek penting tanpa aturan eksplisit |
| Mesin render | Mengorkestrasi evaluasi adegan pada waktu tertentu, menggambar frame, lalu menyusun output gambar/video | Menafsirkan naskah atau mengambil keputusan Sutradara |
| Penguji/evaluator | Menjalankan kasus uji, mengukur determinisme, kontinuitas, kualitas, performa, dan regresi; menyimpan bukti | Mengubah runtime atau melonggarkan ambang hanya agar tes lulus |

**Catatan:** tabel ini adalah batas konseptual. Tidak semua baris harus menjadi berkas atau kelas terpisah. Pembentukan modul fisik menunggu bukti kohesi, dependensi, dan kebutuhan pengujian.

## 3. Alur data yang ditetapkan

`Naskah → Sutradara → arahan visual semantik → paket genre/adab → adapter → papan/kontrak tervalidasi → mesin render → frame → MP4`

Jalur pengujian renderer mandiri:

`fixture JSON manual → validator papan uji → mesin render → frame/MP4 → evaluator dan artefak`

Jalur mandiri boleh melewati Sutradara dan adapter karena tujuannya menguji kemampuan renderer secara terisolasi. Jalur ini **tidak boleh** dipakai untuk melewati penjaga adab pada produksi Kisah Islami atau mengubah aturan produksi.

## 4. Kepemilikan data

- Sutradara memiliki makna semantik: identitas peristiwa, tujuan aksi, aktor, sasaran, urutan, dan perubahan keadaan.
- Adapter memiliki pemetaan antarformat dan pelaporan kesalahan pemetaan; ia tidak memiliki keputusan semantik.
- Papan/kontrak memiliki instruksi visual eksplisit dan referensi lintas-entitas yang dibutuhkan untuk render.
- Renderer memiliki keadaan turunan per-frame: transformasi, pose hasil evaluasi, geometri, posisi gambar, dan hasil visual. Keadaan turunan ini tidak boleh ditulis balik sebagai keputusan cerita.
- Evaluator memiliki metrik dan bukti pengujian, bukan data produksi.

ID aktor/benda harus stabil dalam satu papan. Referensi sasaran harus menunjuk ID yang sah; jangan mengandalkan indeks array sebagai identitas lintas-shot kecuali kontrak menyatakannya secara eksplisit.

## 5. Aturan kontrak antarlapisan

1. Setiap aksi/pose/jenis benda/parameter harus memiliki nama kanonis dan pemetaan eksplisit.
2. Kanal data yang ditulis adapter wajib dibaca dan dievaluasi renderer. Kanal yang tidak dikenal harus ditolak atau dilaporkan, bukan diabaikan.
3. Tidak ada substitusi diam-diam untuk aksi, pose, benda, sudut, atau efek yang tidak didukung.
4. Nilai animasi harus memiliki satu konvensi waktu dan interpolasi yang terdokumentasi.
5. Posisi, skala, arah hadap, titik jangkar, urutan lapisan, dan kamera harus memiliki satu definisi koordinat.
6. Validator memisahkan kesalahan struktur, referensi, kemampuan, dan batas adab.
7. Katalog kemampuan tidak boleh menyimpulkan dukungan runtime hanya dari kecocokan regex/nama kode. Setiap kemampuan perlu tautan ke implementasi, validasi, dan kasus uji yang membuktikannya.
8. Renderer deterministik untuk input, seed, waktu, ukuran kanvas, dan versi dependensi yang sama.

## 6. Temuan audit yang harus ditangani sebelum kontrak final

- Adapter saat ini menulis `aksi_cerita` untuk aksi non-lokomosi, sedangkan audit sumber menyatakan renderer tidak membaca kanal tersebut. Ini cacat kontrak terkonfirmasi pada jalur adapter → renderer; jangan memperbaikinya dengan menambah kanal baru sebelum perilaku kanonis diputuskan.
- Pose/gerak karakter melalui `karakter.gerak` dinormalisasi oleh `mesin-video/papan/karakter/gerak.py` lalu diserialisasi ke `boneka.pose`. Daftar whitelist Python dan kemampuan aktual JS perlu diuji kesetaraannya.
- `newmotion/application/katalog_renderer.py` dan `kemampuan_tokoh.py` mengekstrak kemampuan dengan regex. Hasil ekstraksi berguna sebagai inventaris, tetapi bukan bukti kemampuan bekerja.
- Mesin gambar masih terkonsentrasi di `cerita.js`. Jangan memecah file sebelum dependensi dan antarmuka internalnya dipetakan.

## 7. Keputusan implementasi

**Yang boleh dilakukan sekarang**
- Memperjelas spesifikasi kontrak dan pemilik setiap field.
- Menambahkan validator/pengujian kontrak yang tidak mengubah runtime produksi.
- Membuat fixture uji manual terisolasi setelah jalur render langsung dipastikan.
- Menyusun matriks kemampuan ↔ implementasi ↔ tes ↔ bukti.

**Yang belum boleh dilakukan**
- Menulis renderer kedua atau menyalin sistem tokoh/wajah/rangka.
- Memecah `cerita.js` secara mekanis menjadi banyak file tanpa peta dependensi.
- Mengubah format papan produksi atau adapter sebelum ada tes kontrak dan keputusan kompatibilitas.
- Menghapus/mengganti penjaga adab atau melewati penjaga tersebut pada jalur produksi.
- Mengklaim kemampuan lulus hanya karena nama fungsi/aksi ditemukan di sumber.

## 8. Gerbang sebelum RND-002

RND-001 tetap **BERJALAN** sampai baseline render dari GitHub Actions diperoleh dan ditinjau. Sebelum RND-002 dimulai, harus tersedia:
- baseline frame/video dan waktu render;
- peta dependensi serta pemilik tanggung jawab yang diverifikasi;
- matriks kemampuan dengan bukti, termasuk keterbatasan;
- daftar ketidaksesuaian kontrak prioritas;
- tinjauan pemilik atas keputusan arsitektur ini.

RND-002 kemudian merinci skema input/output dan validator berdasarkan batas tanggung jawab di dokumen ini. Dokumen ini tidak mengubah status RND-001 menjadi selesai.
