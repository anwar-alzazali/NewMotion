# Pemisahan inti dan paket genre

## Tujuan

NewMotion memakai pola monolit modular. Mesin inti menyediakan mekanisme produksi yang
netral genre; paket genre memasok kebijakan, aturan, resep, dan elemen khas cerita.
Menambah genre baru tidak boleh mengharuskan perubahan pada modul inti.

## Batas tanggung jawab

| Inti NewMotion | Paket genre |
|---|---|
| Runtime, orkestrasi job, dan dispatch sutradara inti | Kebijakan pengarahan khas genre |
| Kontrak rencana dan pemuatan paket | Aturan penjaga khusus genre |
| Render dasar, kamera, keyframe, rangka tokoh dan gerak | Komponen visual khas genre |
| Garis waktu, audio, dan validasi teknis umum | Tambahan skema dan validasi genre |
| Pemeriksaan blocking, posisi, jarak, dan kontinuitas umum | Dalil, panduan gaya, resep, dan nilai bawaan genre |

Inti hanya mengenal kontrak PaketGenre dan registri. Inti tidak mengimpor
kisah_islami, komedi, atau nama genre lain secara langsung.

## Kontrak paket dan konteks konten

Setiap paket menyediakan fungsi buat_paket() yang mengembalikan PaketGenre.
Paket dapat mendaftarkan komponen visual, validator, pengarah naskah, penyesuaian
adegan, skema tambahan, nilai bawaan, dan referensi dokumentasi/modul domain.

Genre dan konteks konten adalah dua sumbu berbeda:
- `genre` menentukan strategi penceritaan/pengarahan, misalnya `komedi`,
  `drama`, atau `kisah_islami`.
- `konteks_konten` menentukan lapisan batasan isi: `umum`, `islami`,
  `sejarah_islam`, atau `kehidupan_muslim`.

Kombinasi seperti `genre=komedi` dan `konteks_konten=islami` tetap memakai
pengarah komedi, tetapi gerbang renderer juga menerapkan penjaga adab tokoh dan
verifikasi dalil dari kebijakan Kisah Islami. Ini bukan paket `komedi_islami`
dan tidak menggandakan pengarah. Untuk kompatibilitas, `kisah_islami` tanpa
konteks eksplisit otomatis mendapat konteks `islami`. Naskah baru dengan genre
lain wajib menyatakan `konteks_konten` secara eksplisit agar konten Islami tidak
diam-diam diperlakukan sebagai umum. Spesifikasi papan lama tetap kompatibel:
konteks yang tidak dicantumkan diturunkan dari genre (atau `umum` untuk genre
non-Islami). Konteks yang tidak dikenal ditolak.

Rencana boleh menyertakan genre dengan nama paket. Rencana lama tanpa kolom genre
tetap memilih kisah_islami untuk menjaga kompatibilitas aset dan alur lama.

## Status migrasi

- [x] Kontrak paket genre dan registri pemuat dinamis tersedia di newmotion/domain/genre.py.
- [x] Paket kisah_islami memiliki manifest tersendiri.
- [x] Uji paket tiruan membuktikan paket baru dapat didaftarkan tanpa mengubah inti.
- [x] Hubungkan pemilihan paket ke validasi job.
- [x] Tambahkan orkestrator sutradara inti netral genre untuk memilih paket, memvalidasi naskah/hasil shot, dan memanggil pengarah paket satu kali.
- [x] Wajibkan genre eksplisit untuk mode naskah baru; pertahankan default Kisah Islami hanya untuk spesifikasi papan lama.
- [x] Pisahkan `konteks_konten` dari `genre`; propagasikan konteks ke papan dan terapkan penjaga Islami lintas genre pada satu gerbang renderer.
- [x] Pindahkan aturan pengarah dan visual khas Kisah Islami ke paket; mode `newmotion render --naskah` memanggil kait pengarah sebelum renderer.
- [x] Pindahkan penjaga adab tokoh ke paket Kisah Islami, pasang sebagai kait kontrak genre sebelum render, dan uji nabi, malaikat, sahabat, serta larangan visualisasi Allah.
- [ ] Pindahkan penjaga dalil sepenuhnya ke paket; sumber verifikasinya sudah berada di paket, tetapi gerbang spek lama masih memakai adapter kompatibilitas.
- [ ] Pindahkan komponen visual khusus genre ke mekanisme ekstensi renderer; jangan menghapus atau mengganti perilaku lama sebelum hasil bingkai dibandingkan.

## Kompatibilitas dan batas tahap ini

Direktori mesin-video/ tetap dipertahankan sebagai jalur kompatibilitas renderer. Penjaga tokoh
lama kini menjadi shim menuju implementasi di paket Kisah Islami. Validator rencana baru
menolak representasi yang salah sebelum render. Renderer JavaScript lama belum mendukung
wajah bercahaya sahabat dan berkas cahaya malaikat; spek lama yang memerlukan dua bentuk itu
masih ditolak sampai komponen visualnya benar-benar tersedia. Modul khusus genre lainnya
belum seluruhnya dipindahkan.

Jangan membuat paket komedi atau edukasi pada tahap pemisahan ini. Paket tiruan dalam tes
cukup untuk membuktikan bahwa kontraknya dapat diperluas.


## Batas ekstraksi sutradara inti

Orkestrator bersama berada di `newmotion/application/pengarah_inti.py`. Tugasnya adalah
memilih paket berdasarkan genre eksplisit, memvalidasi struktur naskah dan hasil shot, serta
menjalankan kait pengarah paket satu kali. Ia belum mengklaim bahwa pemahaman cerita dan
perencanaan visual Kisah Islami sudah menjadi algoritme universal. Implementasi
`pengarah_naskah.py` masih merupakan strategi pengarahan Kisah Islami (termasuk boneka
penonton, tema visual, dan kartu dalil). Ekstraksi algoritme peristiwa, blocking, gerak, dan
kontinuitas menjadi layanan inti harus dilakukan setelah kontrak semantik dan uji lintas
genre tersedia, bukan dengan memindahkan kode secara mekanis.
