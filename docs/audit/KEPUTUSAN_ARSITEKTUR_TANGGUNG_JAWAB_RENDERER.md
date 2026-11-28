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


## 9. Keputusan koordinat dan transformasi — wajib untuk kontrak

Untuk mencegah gerak, benda, dan kamera menghitung posisi yang sama dua kali, kontrak memakai tiga ruang koordinat yang berbeda:

1. **Koordinat dunia/panggung**: posisi dan orientasi akar aktor serta benda independen. Ini adalah satu-satunya posisi semantik objek di panggung.
2. **Koordinat lokal**: posisi bagian tubuh relatif terhadap rangka; posisi benda yang sedang melekat relatif terhadap titik kait aktor; detail geometri relatif terhadap induknya.
3. **Koordinat kamera/layar**: hasil transformasi tampilan dari koordinat dunia melalui kamera. Ini hanya untuk proyeksi/framing, bukan sumber posisi dunia baru.

### Pemilik nilai dan aturan evaluasi

- Sutradara menetapkan *blocking* dan lintasan akar aktor/benda pada waktu tertentu dalam koordinat dunia. Untuk fixture manual, penulis fixture mengisi nilai yang sama secara eksplisit.
- Adapter hanya menerjemahkan nilai dan identitas tersebut; adapter tidak menggeser posisi untuk mengompensasi kamera.
- Sistem gerak mengevaluasi lintasan akar yang sudah ditetapkan dan pose/sendi lokal. Ia tidak menambahkan perpindahan panggung kedua di atas lintasan akar yang sama.
- Sistem tokoh menghitung geometri anggota tubuh dalam koordinat lokal, lalu menerapkannya pada transformasi akar aktor.
- Sistem benda menggambar geometri lokal benda. Benda independen memiliki transformasi dunia sendiri; benda yang dibawa/dipegang menggunakan relasi *attachment* ke titik kait aktor dan tidak boleh sekaligus menerima lintasan dunia independen untuk gerak yang sama.
- Kamera menghitung transformasi pandang dari dunia ke layar. Tracking/panning mengubah kamera, bukan koordinat dunia aktor atau benda.
- Mesin render mengevaluasi urutan transformasi secara konsisten: keadaan dunia → gerak akar dan pose lokal → relasi attachment → kamera/proyeksi → gambar. Urutan implementasi rinci harus disesuaikan dengan struktur renderer yang terukur, tetapi kepemilikan koordinat di atas tidak boleh berubah.

### Kasus tokoh berjalan sambil membawa benda dan kamera tracking

- Lintasan akar tokoh ditetapkan satu kali dalam koordinat dunia.
- Gerak kaki/tangan dan pose dihitung relatif terhadap akar tokoh.
- Benda yang dibawa memiliki `parent/attachment` ke aktor dan `anchor/socket` yang eksplisit; transformasi dunia benda diturunkan dari transformasi aktor + transformasi lokal attachment.
- Kamera tracking mengikuti target dengan offset/aturan kamera; kamera tidak mengubah lintasan tokoh atau benda.
- Validator menolak kombinasi yang ambigu, misalnya benda memiliki attachment aktif sekaligus lintasan dunia independen yang mengendalikan translasi yang sama, kecuali kontrak secara eksplisit mendefinisikan mode override dan rentang waktunya.
- Relasi attachment harus punya waktu mulai/akhir agar serah-terima atau benda terlepas dapat dinyatakan tanpa teleportasi.

Nama field di atas adalah konsep kontrak, bukan klaim bahwa field tersebut sudah ada di JSON runtime. Nama final ditetapkan dalam RND-002 setelah pemetaan kompatibilitas terhadap papan lama.

## 10. Pemilik timeline, durasi, dan audio

Timeline ditetapkan sebagai **kontrak waktu lintas-sistem**, bukan keputusan tersembunyi di dalam kamera, sistem gerak, atau mesin render.

- Sutradara menentukan struktur naratif: urutan peristiwa/shot, durasi sasaran, titik dialog/narasi, jeda, dan maksud sinkronisasi.
- Paket genre/adab memeriksa batas konten audio/visual yang relevan, tetapi tidak menggeser timestamp secara mandiri.
- Adapter menerjemahkan waktu semantik ke satuan waktu kontrak dan mempertahankan relasi waktunya.
- **Pengelola timeline** (logika ringan dalam orkestrasi, tidak harus layanan/modul terpisah) menjadi pemilik jadwal final: rentang shot, keyframe, cue narasi/dialog, musik, efek suara, fade, serta offset.
- Sistem gerak, benda, lingkungan, dan kamera hanya membaca waktu global yang sama dan mengevaluasi keadaan pada timestamp tersebut. Tidak satu pun membuat jam/durasi lokal yang mengubah timeline global.
- Mesin render menjadi pemilik *clock* eksekusi: mengambil sampel pada timestamp/frame yang diminta, memastikan frame menggunakan waktu global yang konsisten, dan mengirim hasil video ke tahap muxing.
- Sistem audio/muxing bertanggung jawab memuat aset audio yang dirujuk, menerapkan level/fade/penempatan yang sudah dijadwalkan, serta menyatukan audio-video. Ia tidak menentukan ulang isi narasi atau urutan cerita.

### Aturan waktu

- Satu *timebase* kanonis: detik pecahan dari awal video; frame dihitung dari `fps` yang dinyatakan pada dokumen render. Konversi frame ↔ detik dilakukan satu tempat.
- Durasi total video dinyatakan eksplisit; tidak boleh hanya disimpulkan berbeda-beda oleh tiap subsistem.
- Setiap shot memiliki waktu mulai dan batas akhir/durasi yang tidak tumpang tindih secara ambigu. Transisi memiliki rentang eksplisit.
- Cue audio memiliki waktu mulai, durasi atau aturan akhir, sumber aset, kanal/jenis, gain, dan fade bila diperlukan.
- Narasi/dialog, musik, dan efek suara menggunakan clock yang sama dengan animasi.
- Perubahan durasi shot harus memicu validasi ulang cue dan keyframe yang bergantung padanya; jangan menggeser audio secara diam-diam.
- Pengujian wajib memeriksa durasi akhir, offset audio-video, dan batas toleransi sinkronisasi.

Nama field dan format cue final belum dikunci di sini. Inventaris format audio papan lama harus selesai sebelum RND-002 menetapkan skema yang kompatibel.

## 11. Menjaga pipeline tetap ringan

Sebelas peran dalam tabel adalah **pemisahan tanggung jawab logis**, bukan sebelas proses, layanan, atau panggilan serial.

Batas implementasi:
1. Pertukaran antarbagian memakai satu objek papan/scene terstruktur yang tervalidasi, bukan rangkaian salin-tempel objek per lapisan.
2. Gunakan referensi ID dan data immutable sebisa mungkin; jangan serialisasi ulang seluruh papan di antara fungsi internal.
3. Evaluasi per-frame memakai konteks waktu dan transformasi yang dibagikan; hindari menghitung transformasi akar/kamera berulang kali di setiap subsistem.
4. Modul hanya dibuat terpisah bila punya tanggung jawab kohesif, antarmuka stabil, atau kebutuhan uji/isolasi yang nyata.
5. Pengelola timeline dan mesin render boleh menjadi bagian dari orkestrator yang sama; validator dapat menjadi tahap sebelum render, bukan layanan runtime terpisah.
6. Log diagnostik harus menyertakan ID shot, aktor/benda, timestamp, dan tahap transformasi agar sumber koordinat ganda dapat dilacak.
7. Hindari salinan penuh objek adegan per frame; gunakan data papan sebagai sumber dan simpan keadaan evaluasi yang diperlukan saja.

Target bentuk pipeline runtime yang disederhanakan:

`papan tervalidasi → evaluasi scene pada t → transformasi aktor/benda/lingkungan → kamera → frame → mux audio-video`

Ini adalah urutan kerja logis, bukan kewajiban membuat tujuh modul fisik.

## 12. Gerbang kontrak RND-002 yang diperbarui

RND-002 wajib mengunci dan menguji:
- ruang koordinat dunia/lokal/kamera serta urutan transformasi;
- pemilik lintasan akar aktor dan benda;
- relasi attachment, anchor/socket, dan perpindahan kepemilikan benda;
- larangan translasi ganda dan cara menyatakan override yang sah;
- satu timebase, durasi total, rentang shot, keyframe, cue audio, dan transisi;
- pemisahan maksud timing Sutradara dari jadwal final timeline;
- satu struktur papan yang dipakai bersama dan batas kapan modul fisik dipisah;
- kompatibilitas dengan JSON lama, termasuk perilaku `at`, `durasi`, kamera, `suara`, `musik`, dan `ekor_suara` setelah seluruh penggunaannya diaudit.

Kasus penerimaan kontrak minimum:
1. Tokoh berjalan membawa benda sementara kamera tracking; posisi dunia tokoh tidak digeser kamera dan benda tidak memiliki translasi ganda.
2. Tokoh meletakkan/melepas benda; attachment berakhir pada waktu yang dinyatakan dan benda melanjutkan transformasi dunia tanpa loncatan.
3. Kamera panning pada aktor diam; koordinat dunia aktor/benda tetap.
4. Dua shot berurutan dengan narasi, musik, dan efek suara; semua cue tetap sinkron dengan timebase dan durasi total.
5. Perubahan durasi shot; validator menemukan cue/keyframe yang keluar rentang atau jadwal yang perlu disusun ulang.

Urutan prioritas kerja ditetapkan: **kontrak data dan kepemilikan koordinat/timeline terlebih dahulu; setelah itu urutan migrasi komponen berdasarkan dependensi dan hasil baseline.** Migrasi kode tidak dimulai sebelum kontrak dan baseline disetujui.
