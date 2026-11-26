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
4. Komentar implementasi secara eksplisit menyatakan tahap ini tidak menebak
   pelaku, sasaran, aksi, atau perubahan keadaan.
5. `newmotion/paket_genre/cerita_umum/pengarah_naskah.py:arahkan` kemudian
   membangun profil shot dari daftar peristiwa yang sudah ada. Jika daftar itu
   kosong, shot tetap dibuat tetapi tidak memiliki urutan peristiwa.
6. `newmotion/application/pengarah_inti.py` memvalidasi dan menautkan ID,
   aktor, sasaran, bukti teks, blocking, dan adapter visual. Validasi ini
   memastikan konsistensi data yang diberikan; bukan ekstraksi peristiwa dari
   kalimat narasi.

## Kesimpulan audit

**Kesenjangan utama belum tertutup: ekstraksi semantik narasi menjadi peristiwa.**

Tes generalisasi yang sudah lulus membangun fixture dengan field `peristiwa`
yang telah ditulis sebelumnya. Tes tersebut membuktikan pengarah dapat
menerjemahkan peristiwa terstruktur untuk kategori yang diuji. Tes itu tidak
membuktikan sutradara mampu menemukan sendiri aktor, aksi, sasaran, urutan,
tujuan, atau perubahan keadaan dari narasi bebas.

Dengan demikian, keberhasilan Tahap 1–14 tidak boleh ditafsirkan sebagai bukti
bahwa sutradara telah memahami naskah secara mandiri atau telah menghasilkan
JSON lengkap dari narasi biasa.

## Batas implementasi berikutnya

Tahap berikutnya harus membangun **pengurai narasi-ke-peristiwa** di lapisan
pemahaman cerita, sebelum blocking dan pengarah visual. Pengurai tersebut harus:

- menghasilkan ID peristiwa stabil dan bukti frasa yang benar-benar ada pada
  teks sumber;
- membedakan aktor, aksi, sasaran tokoh, sasaran benda, dan tujuan gerak;
- menjaga urutan temporal; aksi simultan tidak boleh dipecah secara spekulatif;
- mengenali negasi dan bentuk pasif/aktif agar peran pelaku tidak terbalik;
- menghubungkan perubahan keadaan hanya jika pemicunya didukung teks;
- memberi status `periksa` atau `tidak_didukung` untuk ambiguitas, bukan
  membuat adegan rekaan;
- tetap deterministik dan tidak memanggil LLM pada runtime;
- menguji beberapa pola kalimat dan cerita berbeda, bukan hanya fixture motor,
  jembatan, atau penolong;
- tidak mengubah paket Kisah Islami atau melewati penjaga adab/dalil.

Jangan menambah aturan visual khusus untuk menutupi kegagalan pemahaman cerita.
Jika narasi belum dapat diurai dengan bukti yang cukup, hasil JSON harus
menampilkan kekurangan itu secara eksplisit.

## Gerbang penerimaan

Tahap pengurai narasi-ke-peristiwa belum boleh dinyatakan selesai sampai tes
membuktikan:

1. peristiwa dapat dibentuk dari narasi tanpa field `peristiwa` yang
   dipasok sebelumnya;
2. setiap peristiwa mempunyai bukti teks yang cocok dengan sumber;
3. aktor/sasaran/tujuan tidak tertukar dan ambiguitas ditandai;
4. negasi, kalimat pasif, urutan, dan aksi simultan diuji;
5. keluaran tetap JSON-valid, deterministik, dan tertaut ke beat;
6. jalur Kisah Islami tetap lulus;
7. workflow runtime dan kontrak JSON lulus.

Tidak ada render video pada tahap pemahaman ini. Render baru dipertimbangkan
setelah JSON yang dihasilkan sutradara sendiri lulus audit kedalaman lintas
cerita.
