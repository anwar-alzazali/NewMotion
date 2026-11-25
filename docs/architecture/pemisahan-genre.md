# Pemisahan inti dan paket genre

## Tujuan

NewMotion memakai pola monolit modular. Mesin inti menyediakan mekanisme produksi yang
netral genre; paket genre memasok kebijakan, aturan, resep, dan elemen khas cerita.
Menambah genre baru tidak boleh mengharuskan perubahan pada modul inti.

## Batas tanggung jawab

| Inti NewMotion | Paket genre |
|---|---|
| Runtime dan orkestrasi job | Pengarah naskah yang khas genre |
| Kontrak rencana dan pemuatan paket | Aturan penjaga khusus genre |
| Render dasar, kamera, keyframe, rangka tokoh dan gerak | Komponen visual khas genre |
| Garis waktu, audio, dan validasi teknis umum | Tambahan skema dan validasi genre |
| Pemeriksaan blocking, posisi, jarak, dan kontinuitas umum | Dalil, panduan gaya, resep, dan nilai bawaan genre |

Inti hanya mengenal kontrak PaketGenre dan registri. Inti tidak mengimpor
kisah_islami, komedi, atau nama genre lain secara langsung.

## Kontrak paket

Setiap paket menyediakan fungsi buat_paket() yang mengembalikan PaketGenre.
Paket dapat mendaftarkan komponen visual, validator, pengarah naskah, penyesuaian
adegan, skema tambahan, nilai bawaan, dan referensi dokumentasi/modul domain.

Rencana boleh menyertakan genre dengan nama paket. Rencana lama tanpa kolom genre
tetap memilih kisah_islami untuk menjaga kompatibilitas aset dan alur lama.

## Status migrasi

- [x] Kontrak paket genre dan registri pemuat dinamis tersedia di newmotion/domain/genre.py.
- [x] Paket kisah_islami memiliki manifest tersendiri.
- [x] Uji paket tiruan membuktikan paket baru dapat didaftarkan tanpa mengubah inti.
- [x] Hubungkan pemilihan paket ke validasi job.
- [ ] Pindahkan aturan pengarah dan visual khas Kisah Islami dari jalur lama ke paket, satu modul per satu modul.
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
