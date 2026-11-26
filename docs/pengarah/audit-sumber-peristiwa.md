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


## Perluasan berikutnya — transisi keadaan dari narasi (Tahap 17)

Pengurai cerita umum kini menambahkan perubahan keadaan hanya untuk verba yang
memiliki keadaan akhir cukup jelas:
- `jatuh` / `terjatuh` → `terjatuh`;
- `duduk` → `duduk`;
- `berdiri` → `berdiri`.

Perubahan keadaan mula-mula menyimpan nama entitas dari bukti narasi. Orkestrator
menghubungkannya ke ID tokoh yang cocok secara tunggal; blocking memvalidasi
bahwa ID entitas terdaftar pada roster tokoh atau benda. Nama/ID yang tidak
terpetakan tidak boleh menghasilkan transisi keadaan yang seolah-olah sah.

Keadaan awal tidak disimpulkan dari verba. Transisi pertama hanya mencatat
`menjadi`; nilai `dari` baru diisi dari keadaan terakhir yang sebelumnya sudah
tercatat untuk entitas yang sama. Karena itu, “tergelincir” tidak otomatis
diubah menjadi “terjatuh”, dan “jatuh” tidak mengklaim bahwa tokoh sebelumnya
berdiri.

Tes mencakup narasi “Pengendara jatuh lalu berdiri”, keterlacakan ID entitas,
urutan keadaan akhir, validasi ID yang tidak terdaftar, dan larangan menebak
keadaan awal. Jalur pengurai tetap khusus `cerita_umum`; aturan Kisah Islami
tidak diubah. Tidak ada render video dijalankan.



## Perluasan tujuan aksi eksplisit (Tahap 18 — bagian tujuan)

Pengurai cerita umum kini mengenali pola tujuan yang eksplisit dengan bentuk
"aktor melakukan aksi utama untuk melakukan aksi tujuan", misalnya
"Penolong berjalan untuk menolong Pengendara".

Aturannya:
- Aksi utama menjadi peristiwa yang benar-benar dinyatakan.
- Aksi setelah kata "untuk" disimpan sebagai metadata `tujuan`, bukan sebagai
  peristiwa yang dianggap sudah terjadi.
- Sasaran tokoh pada tujuan disimpan sebagai nama, sedangkan sasaran benda hanya
  ditautkan melalui ID roster yang eksplisit; tujuan tidak mengubah sasaran aksi utama.
- Bentuk pasif dengan pelaku eksplisit tetap dapat memiliki tujuan, misalnya
  "Pengendara ditolong oleh Penolong untuk berdiri".
- Frasa "untuk ..." yang belum dapat diklasifikasikan menghasilkan diagnostik
  `frasa_untuk_belum_diklasifikasikan`. Sufiks tersebut tidak boleh keliru
  menjadi sasaran benda aksi utama.
- Tujuan dengan lebih dari satu aksi yang dikenali ditolak sebagai ambigu.

Batas bagian ini: kata kerja tujuan harus ada dalam kamus aksi; kata ganti,
tujuan implisit, tujuan spasial yang kompleks, sebab-akibat, dan relasi antar
peristiwa lintas kalimat belum ditafsirkan. Tujuan bukan bukti bahwa aksi tujuan
sudah dilaksanakan. Tidak ada perubahan pada paket Kisah Islami dan tidak ada
render video.



## Hubungan sebab-akibat eksplisit (Tahap 19)

Parser cerita umum mengenali penghubung kausal secara konservatif:
- A karena B: peristiwa A menjadi akibat dan ditautkan ke peristiwa B
  melalui hubungan_sebab_akibat dengan jenis "disebabkan_oleh" dan ID peristiwa.
- A sehingga B dan A akibatnya B: peristiwa B menjadi akibat dari A.
- Referensi sebab diselesaikan setelah ID peristiwa final diberikan, sehingga
  tautan memakai ID stabil, bukan nomor urutan sementara.
- Jika klausa sebab berupa kondisi atau frasa non-peristiwa, misalnya
  "Tokoh jatuh karena jalan licin", teks sebab disimpan pada sebab_teks.
  Sistem tidak membuat peristiwa palsu untuk "jalan licin" dan memberi
  diagnostik sebab_teks_tidak_dipetakan_ke_peristiwa.
- Penghubung kausal tidak dianggap sebagai urutan atau simultanitas.
- Lebih dari satu penghubung kausal dalam satu kalimat ditandai ambigu dan
  tidak dipaksakan menjadi graf sebab-akibat.
- Klausa sebab/akibat yang aksinya belum didukung kamus tidak dibuat menjadi
  peristiwa; relasi tidak diterbitkan jika salah satu sisi tidak dapat dipetakan.
- Kata "untuk" tetap merupakan penanda tujuan, bukan sebab.

Cakupan ini masih berupa pola permukaan satu penghubung kausal per kalimat.
Korelasi, sebab implisit, sebab jamak, sebab lintas kalimat, dan pengetahuan
dunia tidak digunakan untuk menebak hubungan. Tes memakai ragam konteks cerita;
contoh kendaraan bukan acuan utama. Tidak ada render video pada tahap ini.



## Rantai sebab-akibat eksplisit (Tahap 20)

- Mendukung rantai beberapa klausa dalam satu kalimat bila setiap klausa
  menghasilkan tepat satu peristiwa yang dikenali.
- Pada pola A sehingga B sehingga C, B ditautkan sebagai akibat A dan C
  ditautkan sebagai akibat B.
- Pada pola A karena B karena C, A ditautkan sebagai akibat B dan B sebagai
  akibat C. Arah relasi mengikuti penghubung di antara setiap pasangan klausa.
- ID relasi diselesaikan setelah seluruh ID peristiwa dibuat.
- Jika satu klausa tidak dikenali, menghasilkan lebih dari satu peristiwa,
  atau menimbulkan diagnostik, seluruh rantai ditolak; tidak ada tautan parsial.
- Dukungan ini terbatas pada rantai klausa eksplisit dalam satu kalimat.
  Sebab lintas kalimat, sebab implisit, sebab jamak, dan inferensi pengetahuan
  dunia tetap tidak dilakukan.
