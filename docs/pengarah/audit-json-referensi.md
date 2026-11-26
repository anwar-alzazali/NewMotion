# Audit Tahap 4 — Perbandingan JSON referensi lintas cerita

## Tujuan dan batas

Tahap ini membandingkan kedalaman struktur JSON papan cerita dari mesin-video dengan
keluaran pengarah cerita umum NewMotion. Yang dibandingkan adalah struktur dan kemampuan
mengarahkan cerita, bukan kesamaan isi adegan, koordinat, palet, atau gaya genre.

Sumber referensi dibaca langsung dari branch `main` repository
`anwar-alzazali/mesin-video`. Tidak ada file referensi yang disalin atau diubah.

## Referensi yang ditemukan

| Cerita | File referensi | Jumlah shot | Objek pada shot | Boneka tokoh |
|---|---|---:|---:|---:|
| Nuh | `papan/kisah/nuh1.json` | 15 | 98 | 3 |
| Mahsyar | `papan/kisah/mahsyar1.json` | 12 | 0 objek `benda`; memakai lapisan kerumunan dan elemen lingkungan | 25 |
| Ya'juj 1 | `papan/kisah/yajuj1.json` | 20 | 73 | 2 |
| Ya'juj 2 | `papan/kisah/yajuj2.json` | 20 | 85 | 0 |

Jumlah di atas adalah isi file JSON yang diperiksa, bukan jumlah adegan naratif atau jumlah karakter unik.

## Kedalaman struktur yang tampak

### Nuh — `nuh1.json`

- Lapisan cerita memuat `cerah`, `shot`, `dialog`, `tengah`, `badan`, dan `kilat`.
- Shot memuat lingkungan (langit, horizon, debu, hujan), kamera, benda, teks, dan palet.
- Ada 11 jenis objek, termasuk bahtera, ombak berlapis, gunung, hewan, petir, dan elemen cahaya.
- Kamera tiap shot memakai keyframe; data mencakup x/y/z dan guncangan.
- Benda dan lingkungan membangun kedalaman depan/belakang, lapisan, seed, dan gerak.

### Mahsyar — `mahsyar1.json`

- Lapisan cerita lebih khusus: `label`, `meteran`, dan `shot`.
- Shot memuat kamera, horizon, langit, debu, panas, matahari, naungan, retak, kerumunan, teks, dan boneka.
- Ada 25 entri boneka pada keseluruhan shot, dengan data ekspresi, arah, kulit, rambut, keringat, keriput, lengan, dan gerak.
- Lingkungan bukan sekadar dekorasi; panas, matahari, naungan, kerumunan, dan retakan adalah elemen adegan.

### Ya'juj — `yajuj1.json` dan `yajuj2.json`

- Masing-masing memuat 20 shot.
- Lapisan cerita memuat `cerah`, `shot`, `dialog`, `tengah`, dan `kilat`.
- Variasi objek meliputi batu, bintang, bulan, danau, gunung, ngarai, penggali, arus, dan pemimpin.
- Kamera memakai keyframe dan properti gerak seperti guncangan/hentakan.
- Ya'juj 1 memiliki boneka tokoh; Ya'juj 2 menitikberatkan lingkungan dan objek tanpa boneka.

## Kondisi pengarah cerita umum NewMotion saat ini

Implementasi yang diperiksa adalah
`newmotion/paket_genre/cerita_umum/pengarah_naskah.py`.

Saat ini pengarah tersebut:
- menghasilkan tepat satu shot untuk setiap beat/adegan sumber;
- menghitung durasi shot dari panjang teks dengan batas minimum dan maksimum;
- memakai nilai horizon dan langit tetap;
- memakai kamera dengan posisi tetap dan rentang zoom yang sama;
- mengeluarkan `benda: []` dan `boneka: []` pada setiap shot;
- belum menghasilkan objek lingkungan, komposisi foreground/background, keyframe kamera yang kontekstual, maupun arahan gerak tokoh.

Orkestrator inti kemudian menambahkan `rencana_cerita`, `rencana_blocking`, dan
`rencana_visual_tokoh`. Lapisan semantik ini sudah memberi identitas peristiwa dan
transisi keadaan, tetapi belum otomatis membuat isi shot renderer menjadi setara detail
referensi.

## Matriks kesenjangan

| Dimensi | Referensi mesin-video | NewMotion cerita umum saat ini | Status |
|---|---|---|---|
| Identitas beat/peristiwa | Terwakili dalam urutan shot dan data adegan; tidak selalu memakai ID semantik eksplisit | ID beat/peristiwa stabil dan relasi aktor/sasaran tersedia pada rencana semantik | Sebagian |
| Jumlah dan segmentasi shot | 12–20 shot pada contoh yang diperiksa | Satu shot per beat | Belum setara |
| Lingkungan dan atmosfer | Banyak parameter per shot dan variasi antar-shot | Horizon/langit tetap | Kesenjangan besar |
| Objek dan kontinuitas benda | 73–98 objek pada Nuh/Ya'juj; Mahsyar memakai elemen lingkungan/kerumunan | Daftar benda kosong dari pengarah umum | Kesenjangan besar |
| Tokoh dan ekspresi | Boneka, pose, ekspresi, atribut fisik dan keyframe | Rencana visual tokoh terpisah; belum masuk ke shot renderer secara otomatis | Kesenjangan besar |
| Kamera | Keyframe kamera per shot dengan variasi x/y/z dan efek | Posisi tetap, zoom sempit yang sama | Kesenjangan besar |
| Gerak dan interaksi | Properti gerak objek/tokoh dan perubahan antar-shot | Blocking mulai mencatat aksi dan transisi; terjemahan visual masih terbatas | Sebagian |
| Diagnostik | Tidak selalu tersedia sebagai lapisan semantik eksplisit pada file lama | Diagnostik relasi dan transisi tersedia | Lebih baik pada sisi audit semantik |

## Kesimpulan tahap

**Belum layak menyatakan spek JSON NewMotion mendekati kedalaman referensi.**

Tahap 1–3 telah membangun fondasi penting: kontrak, keterlacakan peristiwa, dan
transisi keadaan. Namun keluaran renderer cerita umum masih berupa papan minimal:
satu shot per beat, kamera nyaris tetap, tanpa objek, dan tanpa tokoh visual.

Karena itu, pekerjaan berikutnya bukan merender Nuh/Ya'juj/Mahsyar lagi. Yang perlu
dikerjakan adalah memperkaya algoritme pengarah agar menghasilkan spesifikasi shot
yang diturunkan dari peristiwa dan keadaan cerita, lalu mengukur JSON hasilnya terhadap
matriks di atas.

## Gerbang penerimaan sebelum render

Sebelum uji render cerita baru:
1. Setiap beat memiliki ID stabil dan satu atau lebih peristiwa yang tertaut bukti teks.
2. Setiap peristiwa memiliki aktor, aksi, sasaran/objek, tujuan bila relevan, dan status
   validasi; ketidakpastian menjadi diagnostik.
3. Perubahan keadaan konsisten dan memengaruhi arahan shot berikutnya.
4. Setiap shot mempunyai alasan naratif, fokus, komposisi, lingkungan, kamera, serta
   objek/tokoh yang benar-benar diperlukan oleh peristiwa.
5. Lintasan dan kontinuitas tokoh/benda mempunyai ID dan keyframe yang dapat diuji.
6. JSON terserialisasi, lolos tes kontrak, dan memiliki diagnostik nol untuk fixture
   yang memang lengkap.
7. Uji lintas cerita umum dilakukan pada JSON saja. Render baru dilakukan setelah
   audit JSON menyatakan semua dimensi wajib memenuhi ambang.

## Sumber referensi

- `anwar-alzazali/mesin-video:papan/kisah/nuh1.json`
- `anwar-alzazali/mesin-video:papan/kisah/mahsyar1.json`
- `anwar-alzazali/mesin-video:papan/kisah/yajuj1.json`
- `anwar-alzazali/mesin-video:papan/kisah/yajuj2.json`

Tidak ada render yang dijalankan dalam audit ini.
