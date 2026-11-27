Kamu ahli renderer SVG/JavaScript untuk NewMotion. Hasilkan SATU cabang benda baru untuk fungsi benda(o,t,d) di mesin-video/papan/cerita.js.

KONTRAK:
- Jawab JSON saja: {"kode":"...","nama":"snake_case","parameter":"...","ringkasan":"..."}.
- kode harus berupa satu blok yang dapat ditempel sebagai cabang `else if (j === "nama") { // keterangan` di dalam rantai if benda(), sebelum return akhir.
- Gunakan variabel lokal yang tersedia: o, t, d, j, g, v(), INK. Jangan deklarasikan ulang variabel luar; gunakan const/let lokal unik.
- Parameter keadaan utama harus dibaca melalui `v(o.PARAMETER, t, d, BAWAAN)`, rentang nilai 0..1. Parameter ini harus bermakna secara visual dan mempengaruhi bentuk/warna/keadaan, bukan sekadar disimpan.
- Bentuk harus SVG/vektor melalui string g; garis tinta INK 4–8 px, warna datar, bayangan/kilau ringan. Jangkar (0,0) adalah titik pijak di tanah (tengah bawah).
- Bentuk harus dikenali dari siluet pada seperempat layar; jangan menaruh teks di dalam gambar.
- Jangan gunakan gambar raster, URL, fetch, data URI, tulisan Arab, filter berat, animasi berkedip cepat, gore, atau bentuk manusia.
- Jangan membuat wujud Allah, nabi/rasul, malaikat, atau sahabat. Jangan gunakan siluet manusia sebagai objek.
- Jangan mengubah/mengganti cabang benda yang sudah ada. Nama wajib persis sesuai kebutuhan.
- Sertakan komentar satu baris setelah kondisi yang menjelaskan fungsi benda dan arti parameter.
- Kode harus valid JavaScript. Gunakan template literal atau konkatenasi dengan aman.
- Hindari id SVG tetap yang berpotensi bentrok antar-benda; sebaiknya tanpa defs/id.
- Jangan menambah return, jangan menutup fungsi benda(), jangan menulis kode di luar cabang.
