# Spesifikasi Tugas GPT 1–9 (semua selesai 27 Nov 2026)

Disimpan sebagai rujukan. Hasil dan keputusan tiap tugas ada di `docs/log_kerja/`.

## Tugas 1 — Penulisan naskah pindah ke jalur LLM bersama

**Tujuan:** penulisan naskah (`ide`, `tempel`, `revisi`) di `newmotion/application/antrean_naskah.py` memakai
`newmotion.infrastructure.llm.panggil` seperti tahap sutradara, bukan pemanggil sendiri dengan nama model
yang ditulis di kode.

**Selesai bila:**
- `ide` dan `revisi` memakai tahap `naskah`; `tempel` memakai tahap `rapikan` (keduanya sudah ada di
  `config/model.toml`; urutan dari config: Sonnet dulu, Gemini cadangan). Konstanta `MODEL_IDE`,
  `MODEL_RAPIKAN`, dan pemanggil Claude/Gemini lama tidak dipakai lagi oleh jalur ini.
- Aturan penulisan dipindah ke berkas skill `newmotion/paket_genre/kisah_islami/skill/naskah.md`
  (isi aturan yang sekarang tetap berlaku; boleh dirapikan, tidak boleh dilemahkan).
- Keluaran AI dicek validator (pakai `validasi()` yang sudah ada + bentuk JSON); bila ditolak, `llm.panggil`
  mengulang dengan daftar galat (sudah didukung lewat argumen `validasi=`).
- Mode `ide` juga mengeluarkan **uji cerita** (sesuai `CLAUDE.md` bagian PEMERIKSAAN SEBELUM KIRIM butir 1:
  kalimat inti, fakta terkuat di detik 0, jawaban hook ada di video ini, momen emosi/kejutan, alasan orang
  komentar/membagikan, daftar kalimat yang dibuang). Uji cerita disimpan di naskah dan tampil ringkas di
  kartu Telegram sebelum pemilik menekan Lanjut.
- Biaya dan model yang dipakai tercatat di status antrean (seperti `status["sutradara"]` di pratinjau).
- Mode `tempel` tetap tidak mengubah satu kata pun narasi pemilik (uji yang ada untuk ini tetap lulus).
- Uji baru dengan http palsu: ide berhasil, ide ditolak validator lalu berhasil di percobaan ulang,
  tempel tidak mengubah narasi, revisi hanya mengubah bagian yang diminta (cukup cek alurnya).

## Tugas 2 — Pencatat kekurangan renderer (antrean kebutuhan)

**Tujuan:** setiap kali sebuah kisah membutuhkan visual yang belum bisa digambar renderer, kebutuhan itu
tercatat, sehingga daftar komponen yang harus dibuat berasal dari kisah nyata, bukan tebakan. Saat ini
sutradara diam-diam mengganti dengan benda terdekat dan kekurangan itu hilang.

**Selesai bila:**
- Rencana sutradara boleh berisi bidang `belum_ada` (tingkat rencana atau per beat): daftar
  `{nama, alasan, bukti}` — visual yang ingin digambar tetapi tidak ada di katalog; `bukti` = potongan
  narasi. Skill sutradara menjelaskan kapan memakainya; validator memeriksa bentuknya dan menolak nama yang
  sebenarnya sudah ada di katalog (supaya tidak dipakai sebagai jalan pintas).
- Skill pemeriksa visual (`skill/periksa_visual.md`) punya kategori temuan "objek yang disebut narasi tidak
  tergambar karena renderer tidak punya bentuknya", dengan nama objek yang dibutuhkan.
- Keduanya dikumpulkan ke satu berkas antrean kebutuhan (mis. `newmotion/application/data/kebutuhan_renderer.json`):
  per nama kebutuhan — jumlah kemunculan, contoh kisah/beat, sumber (sutradara/pemeriksa), status
  (`menunggu`/`dibuat`). Nama yang mirip digabung (normalisasi sederhana sudah cukup).
- Pengumpulan terjadi otomatis di `sutradara_llm.py` (CLI uji) dan `sutradara_hibrida.py` (produksi);
  hasil produksi dari antrean ikut tersimpan (workflow `visual.yml` sudah meng-commit berkas antrean).
- Perintah ringkas, mis. `python -m newmotion.application.kebutuhan_renderer`, mencetak daftar teratas.
- Uji dengan http palsu: rencana dengan `belum_ada` lolos, nama yang sudah ada di katalog ditolak, antrean
  menghitung kemunculan dengan benar.

**Hubungan dengan Tugas 3:** Tugas 3 boleh langsung dikerjakan tanpa menunggu antrean terisi (belum ada uji
LLM sungguhan); daftar contoh di Tugas 3 dipakai sebagai titik awal. Setelah antrean terisi dari produksi,
kebutuhan teratas menjadi prioritas pembuatan komponen berikutnya (Tugas 8).

## Tugas 3 — Pustaka benda renderer untuk banyak jenis cerita

**Tujuan:** sutradara punya cukup "bahasa visual" untuk kisah apa pun (kisah nabi, kisah umat, kehidupan
sehari-hari, akhirat), bukan hanya kisah yang sudah pernah dibuat. Benda yang ada saat ini: lihat
`python -c "from newmotion.application.katalog_renderer import katalog; print(sorted(katalog()))"`.

**Target:** minimal **20 jenis benda baru** yang paling sering dibutuhkan kisah-kisah yang belum bisa
digambar. Contoh kebutuhan (boleh diganti bila ada alasan lebih kuat, tulis alasannya di PR):
pasar/kios, tenda badui, sumur, kebun kurma, ladang gandum, sungai, perahu kecil, jembatan kayu sederhana,
lentera/pelita, api unggun, pintu gerbang kota kuno, timbangan pedagang, karung/keranjang, kambing/domba,
kuda, burung (kawanan), ular (siluet, tidak menakutkan berlebihan), kapal dagang, menara pengawas, rak
kitab, jam pasir, rantai belenggu, pedang tersarung (tanpa adegan kekerasan), awan badai.

**Standar mutu per benda:**
- Gaya sama dengan benda yang ada (garis tinta `INK`, warna datar + bayangan lembut, proporsi kartun).
- Punya komentar keterangan di cabang `j === "nama"` (dipakai katalog sutradara) dan minimal satu
  parameter keadaan yang bermakna bagi cerita (mis. `api` 0–1, `penuh` 0–1, `buka` 0–1), dibaca lewat
  `v(o.param, t, d, bawaan)` agar bisa dianimasikan `[awal, akhir]`.
- Titik jangkar (0,0) = titik pijak di tanah, konsisten dengan benda lain.
- Bila bisa diduduki/dinaiki (kuda, perahu, unta bila belum), tambahkan entri `KAIT` dan pastikan
  `uji_tokoh.py` A6 lulus untuk benda itu (tambahkan adegannya di `ADEGAN_KAIT`).
- `ukur_benda.py` dijalankan ulang; semua benda baru tercatat.

**Bukti yang dilampirkan di PR:** satu lembar PNG semua benda baru (buat skrip kecil atau pakai
`papan_buat.py --pratinjau`), masing-masing dalam dua keadaan (awal/akhir parameter). Tidak ada galat
JavaScript saat render.

## Tugas 4 — Lapis A uji tokoh menuju nol temuan

**Tujuan:** tokoh bersendi benar secara anatomi di semua pose dan sudut.
Jalankan `python mesin-video/papan/uji_tokoh.py -o /tmp/uji_tokoh`; saat ini tersisa temuan:
- A2 kaki menapak: `gali` (depan), `menolong` (semua sudut);
- A3 arah tidak searah: `rebahan`, `rebahan_hp` tampak samping (badan rebahan belum digambar samping);
- A5 loncatan: `lompat` (depan, samping);
- dan secara visual: **gali tampak samping** — beliung tampak di belakang kepala, seharusnya diayun ke depan
  ke arah titik gali.

**Selesai bila:** laporan lapis A = 0 temuan, atau sisa temuan dijelaskan sebagai pengecualian yang benar
secara anatomi (mis. fase melayang lompat) dan dicatat di `TIDAK_MENAPAK`/dokumentasi uji dengan alasan.
Lampirkan `lembar_gerak_samping_*.png` dan lembar pose yang berubah sebelum/sesudah di PR.
Jangan membuat lolos dengan melonggarkan ambang tanpa alasan anatomi.

## Tugas 5 — Interaksi antartokoh dan benda yang dipegang

**Tujuan:** adegan dua tokoh atau lebih terbaca sebagai interaksi, bukan tokoh berdiri berjajar.

**Target:**
- Tokoh bisa **menghadap tokoh lain** (kunci baru, mis. `hadap_ke: <id boneka>`) — sudut samping/tiga
  perempat dipilih otomatis sesuai posisi tokoh lain.
- **Memberi/menerima benda**: satu benda kecil berpindah dari tangan tokoh A ke tangan tokoh B dalam
  rentang waktu (mis. roti, koin, surat, kendi), tangan kedua tokoh menempel ke benda (pakai cara titik kait
  yang sudah ada: `ik2`, `keT`).
- Daftar `pegang` diperluas (sekarang hp, buku, gelas, beliung, palu) dengan benda yang sering muncul di
  kisah: tongkat, kendi, lentera, keranjang, tasbih, surat/gulungan, karung kecil.
- Semua kemampuan baru muncul otomatis di `kemampuan_tokoh.py` (perbarui pembacaannya bila perlu) dan
  bisa dipakai lewat rencana sutradara (tambahkan bidang di `rencana_sutradara.py` + validator + uji).

**Selesai bila:** ada uji otomatis yang mengukur jarak tangan ke benda saat memberi/menerima (seperti A6,
batas 14 px) dan lembar PNG bukti di PR.

## Tugas 5b — Perbaikan benda lemah dari Tugas 3 (temuan audit Claude, 27 Nov)

Audit lembar `hasil/pustaka-benda-baru.png`: 20 benda sudah layak pakai, empat belum terbaca di layar ponsel.

| Benda | Masalah yang terlihat | Yang harus terbaca |
|---|---|---|
| `ladang_gandum` | hanya coretan hitam kecil berserakan; tidak terbaca sebagai tanaman | hamparan batang gandum berbulir, warna gandum (hijau saat muda, keemasan saat `matang`), bergoyang tertiup angin; rapat di belakang, lebih besar di depan |
| `kambing` | kaki seperti kawat tipis, kepala/telinga janggal, lebih mirip rusa | kambing kampung yang jelas: badan berisi, kaki proporsional, tanduk pendek melengkung, janggut kecil, telinga menggantung; gaya sama dengan `domba` |
| `rantai_belenggu` | hanya deretan lingkaran kecil; tidak terbaca sebagai belenggu | rantai mata besar yang tebal dengan kilau logam, borgol/gelang di ujung; `tegang` membuat rantai lurus vs kendur melengkung |
| `sungai` | keadaan awal dan akhir hampir sama; `arus` tidak terasa | arus terlihat bergerak (garis arus/riak mengalir sepanjang waktu, makin deras saat `arus` 1), tepi sungai jelas |

**Selesai bila:** lembar dua keadaan baru untuk keempatnya terbaca tanpa label pada ukuran seperempat
layar, gaya sama dengan benda lain (garis `INK`, warna datar + bayangan lembut), `ukur_benda.py` dijalankan
ulang, semua uji lulus. Benda lain dari Tugas 3 tidak perlu diubah.

## Tugas 5c — Pemeriksa naskah sebelum sampai ke pemilik (prioritas tinggi)

**Latar (uji nyata 27 Nov, naskah "Detik Terakhir Firaun di Dasar Laut"):** penulis naskah melanggar aturan
yang sudah tertulis di skill-nya — hook berupa pertanyaan umum padahal judul menjanjikan detik terakhir
Firaun; detail yang tidak ada di dalil ("Laut Merah", "bersenjata lengkap", "berteriak", "binasa"); dan
fakta paling kuat dari ayat di sekitarnya terlewat (QS Yunus 92: jasad Firaun diselamatkan sebagai
pelajaran). Menambah aturan ke penulis tidak cukup; dibutuhkan pemeriksa terpisah.

**Tujuan:** setelah naskah ditulis dan dalil diverifikasi (teks ayat/hadis resmi sudah ada), satu tahap LLM
terpisah memeriksa naskah terhadap teks dalilnya dan memperbaikinya sebelum kartu dikirim ke pemilik.

**Selesai bila:**
- Tahap baru (mis. `periksa_naskah` di `config/model.toml`, lewat `llm.panggil`) dengan skill sendiri,
  menghasilkan temuan per beat berkategori, minimal: `detail_tanpa_dalil` (frasa yang tidak didukung teks
  dalil beat itu), `hook_lemah` (pembuka tidak memakai fakta terkuat / tidak terkait janji judul),
  `fakta_kuat_terlewat` (fakta dari dalil atau ayat yang berdekatan yang lebih kuat untuk hook/penutup),
  `janji_tidak_dijawab`, `kalimat_mengulang`.
- Temuan berat diperbaiki otomatis oleh penulis (satu putaran, maksimal dua), lalu dalil diverifikasi ulang
  bila berubah. Naskah yang sampai ke pemilik adalah hasil perbaikan; ringkasan temuan & apa yang sudah
  diperbaiki tampil singkat di kartu Telegram (agar pemilik tahu apa yang dicek).
- Pemeriksa tidak boleh menambah dalil yang tidak terverifikasi; usulan ayat baru (seperti Yunus 92) ikut
  diverifikasi mesin seperti dalil lain sebelum dipakai.
- Uji dengan LLM palsu memakai naskah Firaun di atas sebagai kasus: detail tanpa dalil terdeteksi dan
  diperbaiki, hook lemah terdeteksi. Simpan naskah itu sebagai data uji.
- Biaya tahap ini tercatat di status antrean.

## Tugas 5d — Belajar dari revisi pemilik dan naskah yang disetujui

**Tujuan:** LLM tidak belajar sendiri; mesin yang menyimpan pelajaran dan memberikannya kembali saat menulis.

**Selesai bila:**
- Setiap revisi pemilik tersimpan: catatan pemilik, naskah sebelum, naskah sesudah (mis. `antrean/<id>/revisi/NN.json`)
  dan dikumpulkan ke satu berkas pelajaran (mis. `newmotion/application/data/pelajaran_naskah.jsonl`).
- Alat ringkas (manual, mis. `python -m newmotion.application.pelajaran_naskah --ringkas`) memakai LLM murah
  untuk merangkum pola berulang dari kumpulan revisi menjadi **usulan pedoman** beserta bukti (berapa revisi,
  contoh kalimat). Usulan ditulis ke berkas usulan dan **hanya dipakai penulis setelah pemilik menyetujuinya**
  (dipindah ke berkas pedoman yang dibaca skill naskah). Pedoman adalah pertimbangan, bukan aturan wajib
  yang mengekang (sesuai prinsip CLAUDE.md "temuan bukan aturan baku").
- Naskah yang disetujui pemilik sampai video final disimpan sebagai **contoh**; saat menulis naskah baru,
  penulis diberi 1–2 contoh paling mirip topiknya (cara memilih mirip boleh sederhana: kata kunci/peran).
- Uji dengan LLM palsu untuk penyimpanan revisi, pemilihan contoh, dan alur usulan -> disetujui -> dipakai.

## Tugas 6 — Visual konsep abstrak yang sering muncul di Kisah Islami

**Tujuan:** pemeriksa visual berulang menemukan bahwa konsep abstrak tidak tergambar (contoh Mahsyar:
"keringat setinggi mata kaki, lutut, pinggang, mulut"; "meresap ke tanah 70 hasta"; "naungan bagi tujuh
golongan"). Buat cara menggambar konsep seperti itu yang jelas dibaca di layar ponsel.

**Target minimal:** (a) tingkat genangan pada tubuh tokoh dengan penanda ketinggian yang terbaca (mata
kaki/lutut/pinggang/dada/mulut), (b) penampang tanah yang memperlihatkan sesuatu meresap ke kedalaman,
(c) naungan/awan yang jelas menaungi sekelompok orang dengan bayangan teduh di bawahnya, (d) timbangan amal
dengan dua piring yang bisa miring (bila belum ada/kurang jelas). Masing-masing parameter bisa
dianimasikan dan tercatat di katalog.

**Selesai bila:** lembar PNG bukti di PR menunjukkan tiap konsep terbaca tanpa teks penjelas, pada ukuran
seperempat layar (simulasi ponsel).

## Tugas 7 — Lembar uji renderer otomatis

**Tujuan:** satu workflow manual `uji-renderer.yml` yang menjalankan `uji_tokoh.py`, membuat lembar semua benda
(dua keadaan per benda), dan menyimpan hasil ke branch `hasil/renderer-<run_id>` (contoh pola:
`.github/workflows/uji-sutradara-llm.yml`). Ringkasan di `GITHUB_STEP_SUMMARY`: jumlah benda, benda tanpa
ukuran, temuan lapis A. Tanpa LLM.

## Tugas 8 — Pembuat komponen renderer (bersyarat)

**Syarat mulai:** Tugas 2, 3, dan 7 sudah di-merge ke `gpt/integrasi`. Bila belum, lewati tugas ini.
Standar gambar, adab, dan bukti komponen mengikuti `docs/ATURAN_KOMPONEN.md`.

**Tujuan:** mengambil kebutuhan teratas dari antrean kebutuhan (Tugas 2) atau dari daftar contoh Tugas 3
yang belum dibuat, lalu menghasilkan **draf** komponen benda baru beserta bukti mutunya, sehingga pembuatan
komponen menjadi proses berulang yang terukur, bukan pekerjaan manual dari nol.

**Selesai bila:**
- Ada alat (skrip) yang untuk satu nama kebutuhan menghasilkan: cabang benda di `cerita.js` di branch
  terpisah, lembar PNG (dua keadaan parameter, ukuran penuh dan seperempat layar), dan laporan pemeriksaan
  otomatis: render tanpa galat JS, ukuran tercatat oleh `ukur_benda.py`, video referensi tidak berubah,
  gaya konsisten (garis `INK`, tanpa gambar raster/teks Arab), penjaga adab lulus (benda tidak berwujud
  tokoh mulia).
- Komponen yang dihasilkan alat **selalu menjadi PR terpisah ke `gpt/integrasi` berlabel `komponen-draf`
  yang TIDAK di-merge otomatis**: ini satu-satunya pengecualian dari protokol butir 5, karena mutu gambar
  harus dilihat manusia. Status kebutuhannya di antrean berubah menjadi `draf`.
- Alat boleh memakai LLM sungguhan hanya bila dijalankan manual dengan kunci di lingkungan; ujinya tetap
  memakai LLM palsu.
- Contoh nyata: minimal 3 komponen draf dibuat dengan alat ini, lembarnya dilampirkan di PR masing-masing.

## Tugas 9 — Statistik video dan usulan pedoman dari data

**Tujuan:** hasil tayang tiap video tercatat sejak video pertama, sehingga kelak (setelah ±20–30 video)
pola yang benar-benar bekerja bisa dilihat dengan bukti, bukan dugaan.

**Selesai bila:**
- Kartu video final di Telegram punya tombol "📊 Catat hasil": pemilik mengisi tayangan, suka, komentar,
  bagikan, dan (bila ada) persen ditonton sampai habis, untuk hari ke-1 dan ke-7, per platform
  (TikTok/FB). Tersimpan di antrean video itu.
- Ciri naskah tiap video dicatat otomatis (jenis hook, jumlah beat, durasi, topik/tokoh, ada kejutan/klimaks,
  suku/latar, pemakaian suara) agar bisa dibandingkan dengan statistik.
- Alat analisis manual mencetak perbandingan ciri vs hasil dan **usulan pedoman dengan kekuatan bukti**
  (jumlah video, selisih rata-rata). Di bawah 20 video, alat menyatakan terang-terangan bahwa pola belum
  bisa dipercaya. Usulan tidak dipakai otomatis; jalurnya sama dengan Tugas 5d (disetujui pemilik dulu).
- Struktur penyimpanan disiapkan agar kelak bisa diisi otomatis dari API Facebook Page (tidak wajib dibuat
  sekarang; cukup satu fungsi pengisi yang bisa diganti).
- Uji untuk penyimpanan, perhitungan, dan peringatan data kurang.
