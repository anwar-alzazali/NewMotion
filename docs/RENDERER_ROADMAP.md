# Roadmap pembangunan ulang renderer

Status: **rencana disetujui untuk dikerjakan bertahap**  
Cabang dasar: `renderer/pembangunan-ulang`  
Acuan awal: kondisi `main` pada saat cabang dibuat.  
Tujuan: membangun renderer yang dapat menghasilkan tokoh dan adegan yang konsisten, terbaca pada layar ponsel, dapat diuji secara visual, dan dapat menerima kontrak visual dari NewMotion tanpa mencampur tanggung jawab sutradara dengan tanggung jawab renderer.

## 1. Sasaran akhir

Renderer menerima papan/kontrak visual yang tervalidasi, lalu menghasilkan frame dan video. Renderer **tidak** menentukan makna cerita, memilih peristiwa, atau mengarang adegan. Keputusan cerita tetap milik sutradara NewMotion.

Alur tanggung jawab:

`Naskah → Sutradara → kontrak visual/papan → adapter → renderer → frame → video`

Hasil akhir wajib dibuktikan dengan video nyata, bukan hanya JSON valid, tes unit, atau gambar satu frame.

## 2. Prinsip arsitektur

1. **Pisahkan pengarah dan pelaksana.** Sutradara menentukan siapa melakukan apa, kapan, di mana, dan perubahan keadaan yang dibutuhkan. Renderer menggambar serta menganimasikan instruksi itu.
2. **Satu sumber kebenaran untuk anatomi dan pose.** Tidak boleh ada dua sistem rangka, wajah, atau transformasi yang saling bertentangan.
3. **Kontrak eksplisit.** Bentuk data tokoh, benda, pose, sudut, interaksi, kamera, dan waktu didokumentasikan serta divalidasi sebelum render.
4. **Kemampuan harus jujur.** Katalog hanya menyatakan fitur yang benar-benar didukung dan sudah diuji. Fitur yang belum ada tidak boleh diam-diam diganti dengan visual lain.
5. **Kompatibilitas dijaga.** Papan/video lama menjadi baseline regresi. Perubahan visual lama harus disengaja, diukur, dan disetujui.
6. **Visual adalah hasil uji.** Setiap kemampuan penting memiliki lembar bukti dan pemeriksaan pada ukuran layar ponsel.
7. **Tidak mengunci renderer ke satu adegan.** Adegan mobil didorong adalah uji integrasi, bukan satu-satunya sasaran desain.
8. **Python tetap dipakai untuk orkestrasi, validasi, katalog, dan alat uji sesuai batasnya.** Mesin gambar yang ada saat ini berada terutama di `mesin-video/papan/cerita.js`; jangan membuat implementasi kedua tanpa keputusan arsitektur tertulis.

## 3. Tahapan roadmap

### Tahap 0 — Inventarisasi, audit, dan kontrak renderer
Tujuan: mengetahui kemampuan nyata yang sudah ada sebelum menulis ulang atau memindahkan kode.

Hasil wajib:
- Peta alur dari JSON papan sampai PNG/MP4, termasuk batas Python, JavaScript, Chromium, dan adapter.
- Daftar kemampuan yang benar-benar ada: tokoh, wajah, sudut, pose, aksi, IK/titik kait, benda, kamera, latar, audio/timeline bila relevan.
- Matriks bukti: kemampuan, berkas/fungsi sumber, tes yang mengujinya, artefak visual, keterbatasan.
- Daftar bug terkonfirmasi, risiko, kode yang layak dipakai ulang, dan kode yang perlu diganti.
- Spesifikasi kontrak input/output renderer dan daftar kesalahan validasi.
- Baseline video/frame referensi serta waktu render awal.

**Gerbang lulus:** tidak ada implementasi ulang besar sebelum inventaris dan kontrak ditinjau. Tidak boleh menandai kemampuan “lulus” hanya karena nama aksi ditemukan di kode.

### Tahap 1 — Fondasi geometri dan sistem koordinat
Tujuan: memastikan skala, titik asal, transformasi, proporsi, dan urutan gambar dapat diprediksi.

Hasil wajib:
- Satuan dan sistem koordinat tunggal yang terdokumentasi.
- Skala acuan tokoh dan aturan skala benda.
- Transformasi lokal/dunia/kamera yang konsisten.
- Titik pijak, bounding box, dan titik jangkar yang dapat diperiksa otomatis.
- Uji depan, samping, tiga-perempat, belakang; ukuran penuh dan ukuran seperempat layar.

**Gerbang lulus:** proporsi dan jangkar stabil lintas sudut; tidak ada bagian terpotong atau bergeser tanpa alasan; tes geometri lulus.

### Tahap 2 — Anatomi, rangka, dan pose dasar
Tujuan: membangun tokoh bersendi yang anatominya masuk akal dan stabil.

Hasil wajib:
- Definisi tulang dan sendi yang tunggal.
- Panjang segmen tubuh konsisten; aturan perspektif tidak memendekkan tulang secara tidak wajar.
- Pose dasar (berdiri, duduk, berjalan, berlari, membungkuk, berlutut, rebahan, bangkit, melompat) dengan pengecualian kontak tanah yang eksplisit.
- Uji otomatis A1–A5 atau penggantinya yang setara, dengan alasan anatomi untuk setiap pengecualian.
- Lembar pose lintas sudut dan ukuran ponsel.

**Gerbang lulus:** nol temuan anatomi yang belum dijelaskan. Ambang tes tidak boleh dilonggarkan hanya agar hijau.

### Tahap 3 — Wajah, orientasi kepala, dan ekspresi
Tujuan: wajah terbaca, tidak bertumpuk, dan mengikuti orientasi kepala.

Hasil wajib:
- Satu sistem wajah; mata, kelopak, iris, pupil, alis, hidung, mulut, telinga, rambut, dan penutup kepala mengikuti transformasi kepala.
- Aturan visibilitas fitur berdasarkan sudut pandang (depan/tiga-perempat/samping/belakang).
- Ekspresi memiliki bentuk yang dapat dibedakan pada layar ponsel.
- Uji tabrakan/overlap fitur dan lembar ekspresi lintas sudut.

**Gerbang lulus:** tidak ada mata/iris/pupil/alis yang saling menimpa secara tidak sengaja; wajah samping tidak menampilkan fitur depan yang mustahil.

### Tahap 4 — Gerak, interpolasi, dan kontinuitas waktu
Tujuan: gerakan halus, dapat diulang, dan konsisten antar-frame.

Hasil wajib:
- Model waktu/keyframe dan interpolasi terdokumentasi.
- Gerak berjalan, berlari, mendorong, menarik, mengangkat, membawa, memberi/menerima, jatuh, dan bangkit bila masuk kontrak kemampuan.
- Batas kecepatan sendi, deteksi loncatan, stabilitas kaki, dan pencegahan jitter.
- Render urutan frame, bukan hanya pose statis.

**Gerbang lulus:** tidak ada loncatan/jitter yang melampaui ambang terukur; aksi terbaca dalam klip pendek.

### Tahap 5 — Interaksi tokoh dengan benda dan lingkungan
Tujuan: kontak fisik terlihat benar, bukan sekadar tokoh dan benda berada berdekatan.

Hasil wajib:
- Titik kait tangan/kaki/tubuh dan target interaksi yang eksplisit.
- Kontak dorong/tarik/pegang/serah-terima dengan relasi waktu.
- Uji jarak titik kontak dan arah gaya/gerak yang relevan.
- Adegan uji yang beragam: mendorong mobil, mengangkat benda, membuka pintu, memberi benda, dan duduk/menaiki objek sesuai dukungan.

**Gerbang lulus:** kontak memenuhi toleransi yang ditetapkan dan maksud aksi terbaca tanpa bergantung pada subtitle.

### Tahap 6 — Komposisi adegan, kamera, pencahayaan, dan keterbacaan
Tujuan: membuat frame memiliki kedalaman, fokus, dan komposisi konsisten.

Hasil wajib:
- Lapisan depan/tengah/belakang dan aturan kedalaman.
- Kamera, framing, skala tokoh/benda, horizon, dan transisi shot.
- Pencahayaan, bayangan, tekstur, dan latar yang deterministik.
- Pemeriksaan keterbacaan pada 1080×1920 dan pratinjau seperempat ukuran.
- Ukur waktu render dan penggunaan sumber daya.

**Gerbang lulus:** komposisi tidak memotong subjek penting; tidak ada flicker; target waktu render disepakati berdasarkan baseline.

### Tahap 7 — Integrasi kontrak NewMotion
Tujuan: menghubungkan sutradara dan renderer tanpa menggabungkan tanggung jawabnya.

Hasil wajib:
- Adapter mengubah kontrak visual ke format renderer dengan pemetaan eksplisit.
- Validator menolak aksi/pose/parameter yang tidak didukung.
- Katalog renderer dihasilkan dari kemampuan yang benar-benar teruji.
- Tidak ada substitusi diam-diam atas objek/aksi yang hilang; kekurangan masuk antrean kebutuhan.
- Uji dari papan keluaran sutradara sampai frame dan video.

**Gerbang lulus:** papan yang sama menghasilkan output deterministik; kesalahan kontrak memberi pesan yang bisa ditindaklanjuti.

### Tahap 8 — Uji penerimaan lintas cerita dan rilis
Tujuan: membuktikan renderer tidak hanya berhasil pada satu demo.

Paket uji minimum:
- Tokoh tunggal: beberapa sudut, pose, ekspresi, dan gerak.
- Interaksi benda: dorong mobil dan minimal dua jenis interaksi lain.
- Adegan kelompok dan latar.
- Kisah Nuh, Yajuj, Mahsyar, dan Firaun sebagai uji regresi yang relevan dengan aset/papan yang tersedia.
- Satu naskah baru yang belum pernah dijadikan contoh.
- Video MP4 akhir dengan audio/timeline bila jalur produksi memerlukannya.

**Gerbang rilis:** seluruh tes otomatis hijau, artefak visual diperiksa, video nyata ditinjau, regresi lama tidak rusak, dan audit pemilik selesai. Tidak ada merge ke `main` tanpa izin pemilik.

## 4. Strategi penggunaan kode lama

Kode lama tidak otomatis dibuang dan tidak otomatis dipindahkan. Pada Tahap 0 setiap bagian diberi salah satu status:
- `PAKAI`: terbukti benar dan kontraknya sesuai.
- `PERBAIKI`: konsepnya layak, implementasinya punya cacat terukur.
- `TULIS_ULANG`: struktur/kontraknya menghambat dan bukti menunjukkan perbaikan lokal tidak memadai.
- `ARSIP`: tidak dipakai runtime, tetapi disimpan sebagai referensi/riwayat.

Branch lama yang memiliki eksperimen tokoh, IK, benda, atau bukti render hanya sumber audit. Jangan cherry-pick massal. Catat commit dan fungsi yang diambil serta alasan teknisnya.

## 5. Definisi selesai global

Renderer belum dianggap selesai hanya karena:
- JSON valid;
- tes unit hijau;
- satu gambar terlihat bagus;
- satu adegan mobil berhasil;
- workflow selesai tanpa artefak visual;
- kode baru lebih modular.

Renderer dianggap mencapai sasaran bila kontrak jelas, kemampuan terukur, beberapa cerita berbeda berhasil dirender menjadi MP4, hasil visual konsisten, dan regresi terjaga.
