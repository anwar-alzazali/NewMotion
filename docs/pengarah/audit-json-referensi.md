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
- masih menghasilkan satu shot awal untuk setiap beat/adegan; pemecahan shot berdasarkan subperistiwa belum diterapkan;
- menghitung durasi awal shot dari panjang teks dengan batas minimum dan maksimum;
- memberi setiap shot ID stabil, tujuan naratif, fokus tokoh, daftar ID peristiwa, dan urutan peristiwa;
- menautkan aktor, aksi, sasaran, serta sasaran tokoh pada urutan peristiwa tanpa mengubah urutan sumber;
- memilih skala komposisi dan rentang zoom berdasarkan aksi eksplisit (jatuh, interaksi, perpindahan, atau peristiwa umum);
- masih memakai posisi kamera, horizon, dan langit dasar yang tetap; zoom baru berupa rentang, belum lintasan kamera sinematik lengkap;
- menerima benda, tokoh, lintasan, dan pose melalui rencana visual eksplisit serta adapter, bukan dengan menciptakan aset dari kata kunci;
- belum menghasilkan lingkungan atmosferik kompleks dan komposisi foreground/background setara referensi.

Orkestrator inti menambahkan `rencana_cerita`, `rencana_blocking`, dan
`rencana_visual_tokoh`. Untuk paket yang secara eksplisit menyediakan pengarah visual
tokoh (saat ini cerita umum), adapter `terapkan_rencana_visual_tokoh` kini dipanggil
saat JSON pengarahan dibangun. Akibatnya, tokoh, lintasan, pose, dan benda yang memang
dinyatakan oleh rencana visual sudah masuk ke `cerita.shot` sebelum renderer dipanggil.
Adapter memiliki penanda idempotensi agar pemanggilan ulang oleh renderer tidak
menggandakan isi. Paket `kisah_islami` tidak memakai kait visual tokoh umum ini sehingga
pagar adabnya tidak dilewati.

Perubahan tersebut memperbaiki satu celah integrasi, tetapi belum membuat keluaran
setara referensi. Pengarah naskah cerita umum masih membuat satu shot per beat dengan
kamera, horizon, dan langit tetap. Objek lingkungan, atmosfer, dan komposisi shot belum
diturunkan secara kontekstual dari peristiwa.

## Matriks kesenjangan

| Dimensi | Referensi mesin-video | NewMotion cerita umum saat ini | Status |
|---|---|---|---|
| Identitas beat/peristiwa | Terwakili dalam urutan shot dan data adegan; tidak selalu memakai ID semantik eksplisit | ID beat/peristiwa stabil; urutan, aktor, aksi, sasaran, dan fokus tokoh tertaut pada metadata shot | Sebagian |
| Jumlah dan segmentasi shot | 12–20 shot pada contoh yang diperiksa | Satu shot awal per beat; urutan subperistiwa tercatat tetapi belum dipecah menjadi shot terpisah | Belum setara |
| Lingkungan dan atmosfer | Banyak parameter per shot dan variasi antar-shot | Horizon/langit tetap | Kesenjangan besar |
| Objek dan kontinuitas benda | 73–98 objek pada Nuh/Ya'juj; Mahsyar memakai elemen lingkungan/kerumunan | Daftar benda kosong dari pengarah umum | Kesenjangan besar |
| Tokoh dan ekspresi | Boneka, pose, ekspresi, atribut fisik dan keyframe | Tokoh/lintasan/pose dari rencana eksplisit sudah diterjemahkan ke shot; detail ekspresi dan atribut belum setara | Sebagian |
| Kamera | Keyframe kamera per shot dengan variasi x/y/z dan efek | Posisi dasar tetap; rentang zoom dibedakan menurut jenis aksi | Sebagian |
| Gerak dan interaksi | Properti gerak objek/tokoh dan perubahan antar-shot | Blocking dan adapter memetakan lintasan/pose untuk peristiwa eksplisit; urutan aksi tersedia, segmentasi temporal belum lengkap | Sebagian |
| Diagnostik | Tidak selalu tersedia sebagai lapisan semantik eksplisit pada file lama | Diagnostik relasi dan transisi tersedia | Lebih baik pada sisi audit semantik |

## Kesimpulan tahap

**Belum layak menyatakan spek JSON NewMotion mendekati kedalaman referensi.**

Fondasi kontrak, keterlacakan peristiwa, transisi keadaan, adapter visual, dan
pengarahan dasar per shot sudah tersedia. Keluaran sekarang telah memuat fokus,
tujuan shot, urutan peristiwa, komposisi dasar, serta zoom kontekstual. Namun
segmentasi subperistiwa, keyframe kamera lengkap, lingkungan atmosferik, dan
kekayaan objek/atribut visual masih tertinggal dari referensi.

Karena itu, pekerjaan berikutnya bukan merender Nuh/Ya'juj/Mahsyar lagi. Yang perlu
dikerjakan adalah membangun segmentasi shot berbasis perubahan aksi/keadaan yang
benar-benar terpisah, lalu memperkaya kamera dan lingkungan secara deterministik serta
mengukur JSON hasilnya terhadap matriks di atas.

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

## Pembaruan audit setelah integrasi visual tokoh

Pada commit `d6e47cd` dan `4d66ca0` (disusul tes pada `84c5287`), adapter visual
kini mengisi JSON renderer dari rencana visual eksplisit sebelum proses render. Tes
memastikan tokoh penolong, lintasan berjalan, motor yang dinyatakan dalam cerita, dan
kontinuitas antar-shot hadir pada JSON serta adapter idempoten. Ketiga workflow GitHub
Actions pada commit `84c5287` lulus. Tidak ada video referensi yang dirender ulang.

### Kesenjangan yang masih harus ditutup

1. **Segmentasi shot:** satu beat masih dipetakan menjadi satu shot. Perlu pemecahan
   berdasarkan perubahan peristiwa/keadaan yang benar-benar ada, dengan ID sumber tetap
   tertaut; jangan menambah shot hanya demi mengejar angka referensi.
2. **Kamera:** pengarah cerita umum masih memakai x/y/z dan horizon statis. Renderer
   mendukung keyframe kamera `x`, `y`, `z`, serta efek `guncang`/`hentak` pada
   spesifikasi tertentu. Arahan harus dipilih dari kebutuhan peristiwa, bukan angka acak.
3. **Lingkungan:** renderer mendukung lapisan seperti `langit`, `palet`, `debu`,
   `hujan`, `panas`, `matahari`, `naungan`, dan `kerumunan`; pemilihannya harus
   berasal dari konteks tempat/waktu/kejadian yang eksplisit atau menghasilkan diagnostik.
4. **Benda:** objek hanya boleh dibuat jika disebut/diidentifikasi oleh cerita atau
   paket genre. Kontinuitas benda harus memakai ID stabil dan perubahan keadaan.
5. **Tujuan shot:** setiap shot perlu menyimpan alasan/fokus naratif dan daftar peristiwa
   yang dicakup agar keputusan kamera/komposisi dapat diaudit.

Tahap berikutnya adalah mengembangkan pengarah shot deterministik untuk lima hal di atas,
memakai kontrak renderer yang benar-benar didukung `papan/cerita.js`. Uji tetap berupa
JSON dan tes kontrak; render ditahan sampai gerbang penerimaan terpenuhi.


## Pembaruan setelah Tahap 8 — segmentasi shot renderer

Pembaruan ini menggantikan pernyataan historis di atas yang menyebut segmentasi
subperistiwa belum diterapkan. Pada commit `f53aa3d`, pengarah cerita umum sudah
memecah satu shot sumber menjadi beberapa shot renderer hanya ketika tahap semantik
memiliki relasi temporal eksplisit atau transisi keadaan berantai yang konsisten.
Peristiwa simultan tetap berada dalam satu shot.

Adapter mempertahankan ID tahap, urutan, ID peristiwa, aktor sasaran, identitas benda,
dan keadaan posisi lintas-shot. Durasi sumber dibagi untuk menentukan nilai `at`
shot turunan. Status segmentasi membedakan shot yang benar-benar dibagi dari shot
yang tetap satu tahap.

### Batas waktu renderer yang telah diverifikasi

Di `mesin-video/papan/cerita.js`, renderer mengurutkan `cerita.shot` berdasarkan
`at`, lalu menetapkan akhir shot dari nilai `at` shot sesudahnya. Waktu lokal
keyframe kamera dan visual dihitung relatif terhadap `at` shot aktif. Dengan demikian,
pergeseran `at` adalah mekanisme yang benar-benar menentukan batas antar-shot.
Field `durasi` pada JSON NewMotion saat ini adalah metadata; renderer tersebut tidak
membacanya sebagai penentu batas shot. Karena itu, audit tidak mengklaim bahwa field
`durasi` mengendalikan playback.

### Status setelah CI

Ketiga workflow pada commit `f53aa3d2a002b2f082d8a1e3264e429a060b52b2`
(`uji-runtime`, `uji-adab`, dan `kontrak-json`) telah selesai dengan hasil sukses.
Tidak ada workflow render yang dijalankan.

### Kesenjangan berikutnya

Segmentasi temporal kini terbukti pada level JSON dan tes kontrak, tetapi keluaran
belum mendekati kekayaan referensi secara keseluruhan. Pekerjaan berikutnya harus
memperkaya keputusan kamera dan lingkungan secara deterministik berdasarkan konteks
tempat, waktu, dan peristiwa yang eksplisit, sambil mempertahankan diagnostik ketika
informasi tidak tersedia. Uji tetap berupa JSON; jangan render referensi.
