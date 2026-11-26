# Audit sumber peristiwa untuk pengarah JSON

## Tujuan

Memastikan dari mana data peristiwa berasal sebelum menambah algoritme visual lain.
Target NewMotion bukan hanya menerjemahkan objek `peristiwa` yang sudah diisi pihak
luar. Sutradara harus dapat membaca naskah/beat, membentuk pemahaman peristiwa,
menautkan bukti narasi, lalu menghasilkan spek JSON yang bisa diaudit.

## Jalur data yang ditemukan pada head audit

1. `newmotion/application/pratinjau_visual.py:naskah_untuk_pengarah` mengubah
   `naskah.beat` menjadi `adegan`.
2. Fungsi tersebut membuat identitas tokoh dari `tokoh` dan `peran`, serta
   meneruskan `dialog` dan teks narasi.
3. Field `peristiwa`, `aksi`, `sasaran`, `tujuan`, dan
   `perubahan_keadaan` hanya disalin jika sudah tersedia pada beat sumber.
4. `pengarah_naskah.py` membangun profil shot dari daftar peristiwa yang sudah ada.
   Jika daftar itu kosong, shot tetap dibuat tetapi tidak memiliki urutan peristiwa.
5. `pengarah_inti.py` memvalidasi dan menautkan ID, aktor, sasaran, bukti teks,
   blocking, dan adapter visual. Validasi ini bukan ekstraksi narasi bebas.

## Kesimpulan audit

Sebelum Tahap 15, ekstraksi semantik narasi menjadi peristiwa belum tersedia.
Tes generalisasi yang memakai field `peristiwa` siap-pakai tidak membuktikan
kemampuan sutradara memahami narasi biasa secara mandiri.

## Implementasi awal pengurai (Tahap 15)

Pengurai deterministik konservatif berada di
`newmotion/paket_genre/cerita_umum/pemahaman_peristiwa.py`. Integrasi hanya aktif
pada genre `cerita_umum` ketika beat belum memiliki field `peristiwa`.
Peristiwa eksplisit tetap menjadi otoritas dan jalur Kisah Islami tidak diubah.

Cakupan pola:
- aksi aktif dengan aktor dan sasaran tokoh yang terdaftar;
- kalimat pasif dengan pelaku eksplisit melalui frasa `oleh`;
- aksi berurutan melalui `lalu`, `kemudian`, atau `setelah itu`, termasuk
  elipsis subjek jika subjek klausa sebelumnya tunggal dan jelas;
- aksi simultan melalui `dan` atau `sementara`, termasuk elipsis subjek
  pada klausa lanjutan jika pelaku sebelumnya tunggal dan jelas;
- negasi dan kalimat pasif tanpa pelaku menghasilkan diagnostik, bukan aksi.

ID peristiwa diberi namespace ID beat. Bukti teks disimpan dan diverifikasi oleh
orkestrator inti. Diagnostik pemahaman ikut disimpan pada `rencana_cerita`.
Tes baru mencakup kasus simultan seperti “Penolong berjalan dan menolong
Pengendara”, dengan aktor yang sama pada kedua aksi.

## Batas yang belum selesai

Ini bukan pemahaman bahasa Indonesia umum. Aksi di luar kamus, sasaran benda,
kata ganti, kalimat kompleks, perubahan keadaan, tujuan gerak, koreferensi lintas
kalimat, dan banyak bentuk pasif masih belum didukung. Klausa ambigu atau memiliki
lebih dari satu aksi yang belum dapat dipisah dengan aman harus ditandai untuk
pemeriksaan, bukan dilengkapi dengan tebakan.

## Gerbang penerimaan

1. Uji peristiwa dari narasi tanpa field `peristiwa` yang dipasok sebelumnya.
2. Pastikan setiap peristiwa memiliki bukti yang cocok dengan teks sumber.
3. Pastikan aktor/sasaran tidak tertukar dan ambiguitas didiagnosis.
4. Uji negasi, pasif, urutan, simultan, serta elipsis subjek.
5. Pastikan JSON valid, deterministik, dan tertaut ke beat.
6. Pastikan jalur Kisah Islami tetap lulus.
7. Pastikan workflow kontrak JSON dan runtime lulus pada head terbaru.

Perubahan tes pengurai kini juga memicu workflow kontrak JSON. Tidak ada render
video pada tahap ini. Render baru dipertimbangkan setelah JSON hasil sutradara
lulus audit kedalaman lintas cerita.


## Perluasan berikutnya — resolusi sasaran benda (Tahap 16)

Pengurai narasi kini menerima roster benda eksplisit dari naskah. Nama dan alias
benda hanya dapat diresolusikan jika entitas memiliki ID pada roster. Jika
narasi menyebut “Pengendara menaiki motor” dan roster memuat motor ber-ID,
peristiwa mendapat `sasaran_benda_id`; ID tersebut diteruskan ke orkestrator,
blocking, dan adapter visual benda yang sudah ada.

Pengurai tidak membuat entitas dari kata benda bebas. Kata “motor” tanpa entitas
motor pada roster tidak menghasilkan ID benda atau objek renderer. Untuk verba
yang membutuhkan sasaran kendaraan seperti “menaiki” dan “mengendarai”, sasaran
yang tidak terdaftar juga menurunkan status pemahaman menjadi `sebagian` dengan
diagnostik. Dua entitas dengan nama/alias yang sama menghasilkan diagnostik
ambiguitas, bukan memilih salah satu. Resolusi ini tidak menentukan posisi benda; posisi eksplisit atau
relasi posisi yang valid tetap menjadi prasyarat adapter renderer.

Tes integrasi menguji alur narasi biasa → ID sasaran benda → objek renderer,
serta kasus tanpa roster dan nama benda ambigu. Status tahap ini menunggu
keempat workflow CI pada head terbaru. Tidak ada render video.
