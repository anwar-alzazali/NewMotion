# Tahap 12 — Audit dan kontrak katalog benda renderer

## Bukti referensi

Inspeksi empat JSON referensi menunjukkan perbedaan besar antarcerita:

| Referensi | Entri benda | Jenis renderer berbeda |
|---|---:|---:|
| Nuh | 98 | 11 |
| Mahsyar | 0 pada `shot.benda`; memakai boneka dan lapisan lingkungan | 0 |
| Ya'juj 1 | 73 | 9 |
| Ya'juj 2 | 85 | 9 |

Jenis yang benar-benar dipakai:
- Nuh: `gunung`, `petir`, `ombak`, `bahtera`, `nur`, `surya`, `kota`,
  `arus`, `pancar`, `hewan`, dan `tebing`.
- Ya'juj: `bintang`, `bulan`, `ngarai`, `penggali`, `batu`, `pemimpin`,
  `arus`, `gunung`, dan `danau`.

Tidak semua jenis tersebut merupakan benda fisik biasa. `nur` adalah penanda visual
tokoh, sedangkan `penggali` dan `pemimpin` adalah siluet aksi. Ketiganya tidak
dimasukkan ke katalog benda umum karena berisiko mencampuradukkan prop, tokoh, dan
representasi khusus genre.

Renderer juga memiliki jenis lain yang relevan untuk cerita umum, termasuk
`jembatan`, `jalan`, `rumah`, `pohon`, `mobil_luar`, `warung`, `sekolah`,
`pagar`, `kursi`, `meja`, `ponsel`, dan banyak lainnya. Pengarah NewMotion
memakai subset yang diaudit, bukan mengklaim semua jenis renderer sudah didukung.

## Masalah sebelum Tahap 12

Adapter visual sudah dapat menerapkan daftar `benda` eksplisit ke shot dan memeriksa
ID duplikat. Namun, pengarah cerita umum belum memiliki roster entitas benda global,
relasi benda-peristiwa, atau penerapan benda ke shot berdasarkan beat/peristiwa.
Akibatnya, motor menjadi satu-satunya benda yang dibangun oleh pengarah visual tokoh.

## Kontrak entitas benda

Naskah dapat mendeklarasikan roster global:

```json
{
  "benda": [
    {
      "id": "jembatan-01",
      "nama": "Jembatan",
      "jenis_renderer": "jembatan",
      "posisi": {"x": 540, "y": 1480, "s": 1.1},
      "lapisan": {"belakang": true},
      "properti": {"cahaya": 0.25}
    }
  ],
  "adegan": [
    {
      "id": "beat-01",
      "benda_ids": ["jembatan-01"],
      "peristiwa": [
        {
          "id": "event-01",
          "sasaran_benda_id": "jembatan-01"
        }
      ]
    }
  ]
}
```

Aturan:
1. Setiap benda memiliki ID unik dan `jenis_renderer` eksplisit.
2. Benda muncul pada shot jika beat menautkannya lewat `benda_ids` atau peristiwa
   menautkannya lewat `sasaran_benda_id`.
3. ID yang sama dipertahankan saat benda muncul pada beberapa shot/beat.
4. Posisi x/y wajib untuk diterapkan ke renderer. Jika belum ada, pengarah mencatat
   `benda_perlu_penempatan` dan tidak mengarang koordinat.
5. Skala default 1; skala eksplisit harus positif.
6. Properti renderer harus JSON-valid dan tidak boleh menimpa ID, jenis, posisi, atau
   lapisan dasar.
7. Jenis renderer di luar subset terverifikasi ditolak.
8. Jika naskah memiliki entitas motor ber-ID dan peristiwa menautkan
   `sasaran_benda_id`, pengarah tokoh memakai ID tersebut sebagai `kendaraan_id`
   dan tidak membuat motor sintetis kedua. Jika entitas motor tidak dideklarasikan,
   pengarah tokoh mempertahankan fallback motor sintetis yang sudah ada.

## Integrasi

Pengarah benda adalah kait paket genre terpisah dari pengarah tokoh. Rencana benda
digabung dengan rencana tokoh sebelum adapter renderer tunggal dijalankan. Dengan
demikian, adapter tetap menjadi satu-satunya pemilik penerapan visual ke `shot.benda`
dan pemeriksaan ID duplikat.

## Batas yang masih terbuka

- Entitas benda belum diekstrak otomatis dari narasi bebas.
- Posisi benda belum dihitung otomatis dari relasi spasial seperti di atas, di samping,
  di dalam, melewati, atau menabrak.
- Perubahan keadaan benda belum diterjemahkan menjadi keyframe/properti temporal.
- Katalog saat ini hanya subset terverifikasi; belum mencakup semua jenis renderer.
- Belum ada render video. Tahap ini menguji kontrak JSON dan keterlacakan saja.


## Pembaruan implementasi dan validasi katalog

Katalog pada pengarah benda diselaraskan dengan daftar `SUPPORTED_JENIS` yang
terverifikasi di `mesin-video/papan/direktur.py`, yang mengambil sumber kosakata dari
fungsi `benda()` pada `papan/cerita.js`. Ini menghindari kesalahan mengambil jenis
ruang atau pakaian sebagai jenis benda. Daftar NewMotion tetap berupa salinan versi
tertentu; ia tidak dibaca dari repo renderer saat runtime.

Jenis `motor` termasuk katalog sah dan telah ditambahkan tes langsung. Properti objek
seperti `miring` tetap diteruskan sebagai data JSON jika tidak menimpa field kontrak
utama. Penempatan benda tetap wajib eksplisit. Objek tanpa posisi tidak masuk ke
renderer dan menghasilkan diagnostik, bukan posisi rekaan.

CI kontrak pada head implementasi awal Tahap 12 lulus dengan 70 tes. Setelah
penyelarasan katalog dan penambahan tes motor, hasil CI revisi terbaru masih harus
menjadi gerbang penerimaan; keberhasilan run sebelumnya tidak otomatis membuktikan
revisi baru lulus.


## Koreksi audit: relasi benda harus melewati blocking

Tes integrasi motor menemukan bahwa `sasaran_benda_id` sudah ada pada peristiwa
semantik tetapi sebelumnya hilang saat `susun_rencana_blocking()` membentuk kontrak
peristiwa blocking. Akibatnya pengarah tokoh menganggap motor belum dideklarasikan dan
membuat fallback sintetis, sementara pengarah benda juga menambahkan entitas motor
asli. Perbaikannya meneruskan `sasaran_benda_id` ke setiap entri peristiwa blocking.
Pengujian kini memeriksa sekaligus bahwa pengendara memakai ID motor deklaratif dan
hanya ada satu motor pada shot.


## Tahap 13 — Penempatan relatif terhadap lintasan tokoh

Entitas benda kini dapat memakai `relasi_posisi` jika koordinat eksplisit tidak
tersedia. Relasi harus menunjuk `tokoh_id` yang benar-benar dipetakan pada tahap
shot yang sama. Hubungan yang didukung: `di_samping_kiri`, `di_samping_kanan`,
`di_depan`, `di_belakang`, dan `mengikuti`. Offset x/y dapat ditentukan eksplisit;
nilai bawaan hubungan bersifat deterministik dan dapat ditinjau pada kode.

Jika tokoh memiliki keyframe x/y, benda mengikuti keyframe tersebut dengan offset
yang sama pada setiap waktu. Jika tokoh tidak hadir pada tahap terkait atau tidak
memiliki posisi yang dapat dibaca, benda tidak diberi koordinat palsu dan menghasilkan
diagnostik. Posisi eksplisit benda tetap menjadi prioritas jika tersedia.

Integrasi juga menyelaraskan benda yang ditautkan ke peristiwa tertentu dengan tahap
renderer yang memuat peristiwa tersebut. Ini mencegah objek dari event pertama muncul
pada shot event kedua hanya karena keduanya berasal dari beat yang sama. Tes mengunci
perilaku ini.

Batas: relasi spasial saat ini masih berupa offset 2D sederhana; belum menghitung
ukuran objek, kedalaman, occlusion, collision, atau ruang aman komposisi.


## Audit lapisan kedalaman renderer

Renderer menyusun urutan gambar benda melalui tiga kelompok: bintang/bulan/benda
berlapis belakang lebih dulu, benda biasa di tengah, lalu benda dengan `depan: true`
di atas tokoh. Karena itu `lapisan.belakang` dan `lapisan.depan` adalah kontrol
urutan gambar yang nyata, bukan sekadar label metadata. Keduanya tidak boleh bernilai
true bersamaan; pengarah sekarang menolak kombinasi yang kontradiktif.

Ini belum merupakan simulasi kedalaman 3D atau occlusion otomatis. Penentuan lapisan
masih eksplisit dari naskah/entitas, dan tidak disimpulkan hanya dari posisi y.
