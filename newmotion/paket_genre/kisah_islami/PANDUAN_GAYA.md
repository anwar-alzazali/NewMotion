# Panduan gaya visual — paket Kisah Islami

Asal keputusan: `sutradara-ai-studio/docs/PANDUAN_GAYA.md` dan
`sutradara-ai-studio/sutradara/paket_genre/kisah_islami/PANDUAN_GAYA.md`.
Aturan ini berlaku hanya untuk genre `kisah_islami`. Perubahan keputusan visual yang
dikunci pemilik harus mendapat persetujuan pemilik.

## Penggambaran tokoh

| Golongan | Bentuk wajib | Larangan |
|---|---|---|
| Nabi dan rasul | Pilar cahaya putih khusus nabi (`nur`), tanpa lekuk kepala, bahu, tangan, wajah, atau tubuh | Tidak boleh berupa boneka, siluet, atau manusia bercahaya |
| Malaikat | Berkas/sinar dari tepi atas, tanpa wujud fisik | Tidak boleh memakai pilar nabi, siluet, tubuh, wajah, atau anggota badan |
| Sahabat Nabi Muhammad ﷺ | Tubuh manusia berbaju dengan rangka, gerak, gestur, dan barang; bidang wajah berupa cahaya lembut tanpa mata, hidung, mulut, janggut wajah, atau ekspresi | Tidak boleh menggambar fitur wajah; tidak boleh diganti pilar nur atau siluet |
| Allah | Tidak divisualisasikan dalam bentuk apa pun | Termasuk sosok, tubuh, pilar, atau representasi cahaya yang diberi identitas Allah |
| Manusia biasa | Tubuh berpakaian dengan wajah berekspresi sesuai kebutuhan cerita | Tidak memakai bentuk khusus nabi, malaikat, atau sahabat |

## Aturan pendukung

- Siluet hanya boleh dipakai untuk misteri, kilas balik/mimpi, kerumunan sangat jauh berskala besar, atau wajah yang sengaja disembunyikan. Siluet bukan gaya bawaan.
- NPC/kerumunan jauh tetap berpakaian, diperkecil dan dipudarkan oleh kabut; bukan siluet hitam.
- Makhluk gaib yang wujudnya tidak dijelaskan dalil sahih ditampilkan tanpa wujud fisik yang direka.
- Identitas dan mode tampil tokoh harus konsisten antar-shot.
- Barang milik nabi ditampilkan di sisi pilar cahaya, tanpa tangan atau tubuh nabi.
- Buraq tidak boleh digambar dengan penunggang manusia; penanda kehadiran nabi menggunakan pilar cahaya terpisah.

## Status dukungan renderer

Kontrak validator NewMotion sudah mengenali mode `wajah_cahaya` dan berkas cahaya malaikat.
Namun renderer JavaScript lama saat ini belum mengimplementasikan kedua mode tersebut.
Karena itu, spek lama yang mencoba menggambar sahabat sebagai boneka tetap ditolak;
dukungan visualnya harus ditambahkan sebelum mode tersebut dapat dirender.
