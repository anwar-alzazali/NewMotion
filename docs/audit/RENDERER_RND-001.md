# Audit RND-001 — baseline dan peta renderer

Tanggal: 2026-11-28  
Branch audit: `renderer/pembangunan-ulang`  
Basis kode yang diperiksa: `main` dan eksperimen branch yang disebut pada bagian 8.  
Status: **AUDIT SUMBER SELESAI; BASELINE RENDER BELUM DIVERIFIKASI DI ACTIONS.**

## 1. Kesimpulan eksekutif

1. Mesin gambar tokoh dan benda yang aktif saat ini terutama berada di satu file JavaScript: `mesin-video/papan/cerita.js` (sekitar 377.859 karakter / 2.605 baris pada basis yang diperiksa). Ini bukan dua renderer setara Python dan JavaScript.
2. Python berperan sebagai pembuat HTML/render pipeline, validasi, katalog, serializer karakter, adapter rencana visual, serta alat ukur/uji. Evaluasi geometri tokoh, pose, IK, dan gambar SVG dilakukan di JavaScript.
3. Renderer memiliki banyak kemampuan yang sudah berguna: benda SVG dengan parameter waktu, skeleton/pose, aksi berulang, wajah/ekspresi, titik kait, IK dua tulang, kamera dan lapisan adegan. Namun daftar kemampuan dari kode belum sama dengan bukti bahwa semua kemampuan bekerja benar di seluruh sudut dan adegan.
4. Kualitas visual yang buruk tidak bisa langsung disimpulkan sebagai batas alami renderer. Ada risiko nyata pada kontrak antarlapis: adapter, serializer Python, whitelist gerak, dan JavaScript tidak sepenuhnya menyepakati nama/semantik aksi.
5. Eksperimen mobil didorong berada di branch `uji/mobil-didorong-ekspresif`, bukan di `main`. Contoh JSON eksperimen menggunakan fitur yang tidak ada di renderer `main`. Jalur eksperimen itu juga belum membuktikan bahwa sutradara/adapter dapat menghasilkan adegan yang sama.
6. RND-001 belum boleh ditutup sebelum baseline render aktual (lembar tokoh, lembar benda, laporan, dan waktu render) diambil dari GitHub Actions dan diperiksa.

## 2. Peta pipeline yang ditemukan

```
JSON papan / rencana visual
        |
        v
mesin-video/papan_buat.py
  - validasi papan dan gerbang adab
  - adapter rencana visual tokoh
  - serializer integrasi karakter
  - membangun HTML
        |
        v
mesin-video/papan/cerita.js
  - gambar benda SVG
  - gambar boneka/tokoh
  - POSE + poseGerak + interpolasi
  - rangka + IK + titik kait
  - evaluasi tiap waktu/frame
        |
        v
Playwright Chromium
  - pratinjau PNG
  - frame video
        |
        v
FFmpeg / keluaran MP4
```

Catatan: urutan dan pemanggilan fungsi pembungkus harus tetap diperiksa terhadap jalur CLI yang benar saat uji runtime. Diagram ini menggambarkan pembagian tanggung jawab, bukan klaim bahwa setiap jalur produksi telah lulus.

## 3. Matriks komponen dan bukti sumber

| Komponen | Lokasi utama | Peran nyata | Catatan audit |
|---|---|---|---|
| Gambar benda | `mesin-video/papan/cerita.js`, `benda(o,t,d)` | Membuat SVG benda dan membaca parameter keadaan/waktu | Banyak benda digabung dalam satu fungsi besar |
| Wajah | `cerita.js`, `mukaHidup()`, `mulutHidup()/mulutH()` dan jalur wajah terkait | Mata, pupil, kelopak, alis, mulut, ekspresi | Perlu pengujian koordinat dan orientasi; jangan menyimpulkan benar dari nama ekspresi |
| Rangka | `cerita.js`, `rangka(J,o)` | Menghitung anggota badan dan geometri sendi | Sumber utama geometri tokoh |
| Pose | `cerita.js`, `POSE`, `isiPose()`, `poseKini()` | Pose diam dan transisi | Pose statis berbeda dari aksi berulang |
| Aksi | `cerita.js`, `poseGerak()` | Menghasilkan gerak periodik/berdasarkan waktu | Nama harus cocok dengan whitelist Python bila melalui serializer |
| Titik kait dan IK | `cerita.js`, `KAIT`, `kaitDunia()`, `ik2()` | Menempelkan pinggul, tangan, kaki ke objek | Tidak semua objek memiliki titik kait |
| Serialisasi karakter | `mesin-video/papan/karakter/integrasi.py` | Memetakan atribut/gerak karakter ke data boneka | Tidak menghitung geometri atau IK |
| Kamus gerak | `mesin-video/papan/karakter/gerak.py` | Whitelist dan normalisasi jadwal gerak | Harus sinkron dengan pose/aksi JS |
| Adapter visual | `newmotion/adapter_visual_tokoh.py` | Menerjemahkan rencana genre ke boneka dan benda | Ada ketidaksesuaian nama kanal aksi yang perlu diperbaiki |
| Katalog benda | `newmotion/application/katalog_renderer.py` | Membaca nama dan parameter benda dari JS | Ekstraksi berbasis regex; rawan perubahan format JS |
| Katalog tokoh | `newmotion/application/kemampuan_tokoh.py` | Membaca POSE, poseGerak, KAIT, penutup kepala | Ekstraksi berbasis regex; bukan uji runtime kemampuan |
| Uji tokoh | `mesin-video/papan/uji_tokoh.py` | Render pose/sudut dan ukur A1–A6 | Pemeriksaan visual B/C tetap perlu penilaian manusia |
| Pembungkus render | `mesin-video/papan_buat.py` | Validasi, HTML, Chromium, pratinjau/render | Jalur utama untuk uji end-to-end |

## 4. Temuan teknis terkonfirmasi

### RND-F01 — Ketidaksesuaian kanal aksi pada adapter (prioritas tinggi)

**Fakta sumber:**
- `newmotion/adapter_visual_tokoh.py` menaruh aksi non-`jalan`/`lari` ke properti `aksi_cerita`.
- `mesin-video/papan/cerita.js` tidak memiliki pembacaan `aksi_cerita` pada renderer tokoh yang diperiksa.
- Jika arahan memiliki `pose`, adapter menaruhnya ke `karakter["gerak"]`.
- `mesin-video/papan/karakter/gerak.py` memvalidasi nama gerak dengan `SEMUA`; nama yang tidak terdaftar ditolak.
- Integrasi Python meneruskan jadwal gerak tersebut ke properti `boneka.pose`.

**Dampak:** suatu aksi dapat lolos sebagai metadata adapter tetapi tidak pernah dieksekusi renderer, atau ditolak saat serializer memvalidasi nama gerak. Ini adalah cacat kontrak antarlapis, bukan bukti bahwa JavaScript tidak mampu menggambar pose tertentu.

**Contoh nyata:** `dorong` ada sebagai pose statis pada eksperimen branch mobil, tetapi tidak terdaftar pada `GERAK_STATIS`/`GERAK_BERULANG` di main. Karena itu `pose: "dorong"` tidak dapat melewati serializer karakter saat jalur adapter memakai `karakter.gerak`.

**Tindakan:** RND-009 harus memiliki tes kontrak lintas adapter → serializer → JS. Jangan memperbaiki ini diam-diam dalam RND-001.

### RND-F02 — Eksperimen mobil didorong belum menjadi kemampuan main

**Fakta sumber:**
- `main` tidak memiliki cabang benda `mobil_dorong`, pose `dorong`, atau entri `KAIT.mobil_dorong` pada `cerita.js`.
- Branch `uji/mobil-didorong-ekspresif` menambahkan ketiganya dan file `mesin-video/papan/kisah/mobil_didorong1.json`.
- JSON eksperimen memanggil renderer secara langsung dengan `pose: "dorong"`, `kait: "mobil-uji"`, dan benda `mobil_dorong`; ini bukan bukti bahwa keluaran sutradara melalui adapter dapat menghasilkan aksi tersebut.
- Dalam eksperimen, koordinat mobil berubah dari 700 ke 716 selama 7 detik. Parameter `tekan` menambah tanda visual pada badan mobil; perlu pengujian visual untuk memastikan gerak dorong terbaca, bukan hanya efek dekoratif.

**Dampak:** contoh manual dan jalur otomatis tidak setara. Pengujian dorong mobil wajib melewati dua jalur: papan manual langsung dan kontrak NewMotion melalui adapter.

**Tindakan:** jadikan adegan mobil salah satu kasus penerimaan RND-007/RND-010, bukan fitur yang langsung disalin.

### RND-F03 — Katalog kemampuan dibaca dengan regex, bukan deklarasi kontrak

**Fakta sumber:** `katalog_renderer.py` mencari pola cabang `j === "..."` dan parameter `o.nama`; `kemampuan_tokoh.py` mengambil nama dari blok `POSE`, `poseGerak`, dan `KAIT` menggunakan regex.

**Risiko:** refactor format JS dapat membuat katalog tidak lengkap tanpa kegagalan semantik. Kehadiran nama di katalog juga tidak membuktikan aksi dapat dirender dengan benar.

**Tindakan:** RND-002 menetapkan kontrak/manifest kemampuan yang eksplisit atau parser yang tervalidasi. Jangan mengubah katalog saat audit ini.

### RND-F04 — Renderer terlalu terkonsentrasi di satu berkas

**Fakta sumber:** `cerita.js` menampung fungsi benda, wajah, pose, aksi, rangka, IK, tokoh, efek, dan komposisi dalam satu IIFE besar.

**Dampak:** perubahan kecil berisiko memengaruhi fungsi lain; sulit menguji komponen secara terisolasi; pencarian akar masalah menjadi mahal.

**Tindakan:** jangan memecah file secara kosmetik sekarang. Tahap 0 harus menentukan batas modul dan kontrak sebelum ekstraksi dilakukan.

### RND-F05 — Bukti otomatis belum sama dengan penilaian mutu visual

**Fakta sumber:**
- `uji_tokoh.py` membuat lembar pose/sudut, laporan, dan mengukur A1–A6.
- Instrumentasi `window.__catatBoneka` mengambil data sendi dari hasil render.
- Laporan Lapis A dapat diperiksa otomatis, tetapi bentuk wajah, keterbacaan aksi, komposisi, dan kualitas frame tetap membutuhkan lembar visual dan tinjauan manusia.
- `test-runtime.yml` menjalankan `python mesin-video/papan/lembar_benda_baru.py || true`, sehingga kegagalan langkah lembar benda itu tidak menggagalkan job.

**Dampak:** CI hijau tidak otomatis berarti seluruh kualitas gambar sudah baik. Langkah yang memakai `|| true` juga tidak dapat dipakai sebagai gerbang wajib.

**Tindakan:** RND-008/RND-010 menentukan pemeriksaan visual yang tidak dapat dilewati dan memperbaiki masking kegagalan pada workflow yang disepakati.

### RND-F06 — Jalur CI otomatis tidak mencakup branch renderer baru

Workflow `test-runtime.yml` pada basis yang diperiksa menjalankan push hanya untuk branch `tugas-*`; workflow lengkap renderer menggunakan `workflow_dispatch`. Branch `renderer/pembangunan-ulang` tidak otomatis menjalankan workflow push tersebut.

**Dampak:** commit pada branch renderer dapat tidak memperoleh hasil CI otomatis kecuali workflow manual dipilih atau trigger khusus ditetapkan.

**Tindakan:** jangan menambah workflow baru tanpa kebutuhan. Tentukan strategi CI branch renderer pada tahap implementasi pertama, gunakan workflow yang sudah ada bila dapat dipicu manual.

## 5. Status bukti dan baseline

| Bukti | Status | Keterangan |
|---|---|---|
| Peta kode dan tanggung jawab | Diperiksa | Sumber file di atas |
| Kontrak adapter/serializer | Diperiksa statis | Ketidaksesuaian RND-F01 ditemukan |
| Uji anatomi A1–A6 | Belum dijalankan pada branch ini | Perlu GitHub Actions |
| Lembar tokoh lintas sudut | Belum diperiksa visual pada run baru | Perlu artefak |
| Lembar seluruh benda | Belum diperiksa visual pada run baru | Perlu artefak |
| Manifest dan galat JavaScript | Belum ada hasil run baru | Perlu artefak |
| Waktu render baseline | Belum diukur | Perlu run dengan input dan lingkungan tetap |
| Video MP4 baseline | Belum dihasilkan/diperiksa pada sesi audit | Jangan klaim baseline visual lulus |

## 6. Keputusan pakai/perbaiki/tulis ulang/arsip

| Bagian | Keputusan sementara | Alasan |
|---|---|---|
| Mesin gambar `cerita.js` | **PERBAIKI bertahap; evaluasi modul setelah kontrak** | Banyak kemampuan yang dapat dipakai, tetapi monolit dan beberapa cacat lintas lapis |
| Pembungkus `papan_buat.py` | **PAKAI** sebagai jalur render baseline | Sudah menjadi jalur HTML/Chromium/pratinjau |
| Serializer `integrasi.py` + `gerak.py` | **PAKAI lalu PERBAIKI kontrak** | Pemisahan peran benar, daftar gerak perlu diselaraskan |
| Adapter visual | **PERBAIKI setelah kontrak disepakati** | Ada kanal aksi yang tidak terhubung ke renderer |
| Katalog regex | **GANTI dengan manifest/kontrak tervalidasi pada tahap kontrak** | Tidak cukup kuat menjadi sumber kebenaran jangka panjang |
| Uji tokoh A1–A6 | **PAKAI dan perluas** | Dasar ukur anatomi sudah tersedia; perlu bukti visual dan interaksi lebih luas |
| Branch eksperimen | **ARSIP sebagai referensi** | Jangan cherry-pick massal; periksa perubahan satu per satu |

## 7. Batas audit dan hal yang belum dapat disimpulkan

- Belum ada bukti render baru dari branch `renderer/pembangunan-ulang`, sehingga belum boleh menyatakan baseline lulus/gagal secara visual.
- Belum dibuktikan bahwa semua pose yang terdaftar memiliki visual yang benar.
- Belum dibuktikan bahwa masalah wajah pada adegan mobil berasal dari satu baris tertentu; diperlukan reproduksi dengan output dan instrumentasi sebelum menetapkan akar masalah rinci.
- Belum dilakukan benchmark waktu render.
- Belum dilakukan pemecahan file atau perubahan kode runtime.

## 8. Branch eksperimen yang diperiksa

Perbandingan terhadap `main`:
- `fix/renderer-tokoh-lima-sudut`: 26 commit di depan dan 153 di belakang; mengubah `cerita.js`, integrasi karakter, dan alat uji. Referensi historis anatomi lima sudut; tidak aman digabung massal karena basisnya jauh tertinggal.
- `uji/mobil-didorong-ekspresif`: 12 commit di depan, 0 di belakang; menambahkan benda mobil dorong, pose dorong, kait, papan uji, audio, dan jalur manual. Berguna sebagai kasus uji, belum membuktikan integrasi adapter.
- `tugas-5-interaksi-tokoh-benda`: 54 commit di depan dan 64 di belakang; mengandung eksperimen interaksi/IK dan pengarah. Perlu audit per commit jika bagian tertentu dibutuhkan.
- `tugas-7-lembar-uji-renderer`: 8 commit di depan dan 55 di belakang; berisi lembar benda dan workflow uji. Workflow/tes di main harus dibandingkan sebelum mengambil perubahan.

Branch lama tetap dibiarkan utuh. Tidak ada cherry-pick atau penghapusan dalam audit ini.

## 9. Langkah berikut dan gerbang RND-001

1. Jalankan workflow manual `uji-renderer.yml` pada branch `renderer/pembangunan-ulang`.
2. Ambil artefak laporan tokoh, manifest renderer, lembar pose, lembar benda, dan ringkasan.
3. Periksa visual setidaknya pada 1080×1920 dan seperempat ukuran.
4. Ukur render baseline dengan input/lingkungan tetap.
5. Catat hasil faktual dan tutup RND-001 hanya jika semua bukti tersedia.

**Belum boleh mulai RND-002** sampai baseline ini ditinjau. RND-F01 sampai RND-F06 menjadi backlog terukur, bukan alasan untuk langsung mengubah banyak komponen sekaligus.
