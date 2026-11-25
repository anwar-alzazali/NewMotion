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
- [ ] Hubungkan pemilihan paket ke validasi job.
- [ ] Pindahkan aturan pengarah dan visual khas Kisah Islami dari jalur lama ke paket, satu modul per satu modul.
- [ ] Pindahkan penjaga dalil dan tokoh suci ke paket dengan tes regresi.
- [ ] Pindahkan komponen visual khusus genre ke mekanisme ekstensi renderer; jangan menghapus atau mengganti perilaku lama sebelum hasil bingkai dibandingkan.

## Kompatibilitas dan batas tahap ini

Direktori mesin-video/ tetap dipertahankan sebagai jalur kompatibilitas renderer.
Manifest Kisah Islami saat ini menunjuk ke modul lama; ini bukan klaim bahwa seluruh kode
khusus genre sudah dipindahkan. Pemindahan fisik baru dilakukan setelah setiap modul
mempunyai adapter dan uji regresi, agar hasil render lama tidak berubah diam-diam.

Jangan membuat paket komedi atau edukasi pada tahap pemisahan ini. Paket tiruan dalam tes
cukup untuk membuktikan bahwa kontraknya dapat diperluas.
