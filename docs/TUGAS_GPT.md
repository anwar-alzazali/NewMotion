# Tugas untuk sesi AI pengerja (ChatGPT/Codex) — NewMotion

Pemilik: Anwar Alzazali. Bahasa kerja: Indonesia. Ditulis 27 Nov 2026 oleh Claude (pengaudit).

## Protokol setiap sesi (WAJIB dibaca dulu; ingatan sesi pendek)

1. Baca berkas ini sampai habis, lalu `CLAUDE.md` di akar dan `mesin-video/CLAUDE.md` bila ada.
2. Lihat **Log kerja** di paling bawah. Ambil tugas **pertama yang belum `[x]`**. Jangan mengulang tugas
   yang sudah selesai, jangan mendesain ulang keputusan yang sudah tercatat di log, kecuali log itu
   sendiri menyatakan ada masalah.
3. **Cabang kerja = `gpt/integrasi`** (bukan `main`). Satu tugas = satu branch dari `gpt/integrasi` terbaru
   = satu PR **ke `gpt/integrasi`**. Jangan menggabungkan dua tugas dalam satu PR. Jangan membuat PR ke `main`.
4. **Uji lewat CI (bukan lokal).** Sesi pengerja tidak bisa menjalankan pytest/browser sendiri; yang
   menjalankan adalah workflow `Uji runtime NewMotion` (`.github/workflows/test-runtime.yml`), otomatis
   setiap push ke branch bernama `tugas-*`. Ia menjalankan: sintaks Python/JS, ruff untuk berkas yang
   berubah (hanya galat ruff BARU yang menggagalkan; galat lama di berkas itu boleh tetap), ukur ulang benda (dan meng-commit `ukuran_benda.json` ke branch-mu bila berubah — tarik dulu
   sebelum push berikutnya), seluruh pytest, uji bot, dan uji tokoh lapis A (harus 0 temuan). Lembar
   bukti PNG ada di artefak run. Jadi: beri nama branch `tugas-<nomor>-<ringkas>`, push, tunggu run itu
   hijau, baru merge. Bila merah, baca log run, perbaiki, push lagi (ingat batas macet butir 7).
5. **Jangan menunggu audit.** Bila run CI butir 4 hijau, merge sendiri PR-mu ke `gpt/integrasi`,
   centang tugasnya `[x]` di daftar di bawah, lalu langsung lanjut ke tugas berikutnya. Pemilik/Claude
   mengaudit seluruh `gpt/integrasi` sekaligus setelah semua tugas selesai, lalu menggabungkannya ke `main`.
   (Cabang terpisah ini menjaga bot produksi, yang otomatis ter-deploy dari `main`, tetap aman.)
6. Di akhir sesi (selesai atau belum), **tulis entri log kerja sebagai BERKAS BARU** di
   `docs/log_kerja/` bernama `YYYY-MM-DD-HHMM-tugas-N.md` (jangan menambah baris di bagian Log kerja di
   bawah — dua pihak yang menambah baris di ujung berkas yang sama selalu membuat PR bentrok, dan alat
   GitHub-mu tidak bisa memperbarui branch). Sesi baru membaca semua berkas di folder itu, urut nama.
   Isi entri: tanggal, tugas, apa yang
   selesai, nomor PR, keputusan penting, dan langkah berikut yang persis. Sesi berikutnya hanya
   mengandalkan catatan ini. Bila sebuah tugas belum selesai, tulis bagian mana yang sudah ada di
   `gpt/integrasi` dan bagian mana yang belum.
7. **Batas macet:** bila satu masalah gagal dua kali dengan cara berbeda, berhenti mencoba. Tulis di log
   sebagai `MACET:` beserta apa yang sudah dicoba, lalu lanjut ke bagian lain tugas atau tugas berikutnya.
   Tugas yang macet tidak menghalangi tugas berikutnya.
8. Bila sebuah tugas ternyata sudah dikerjakan sebagian oleh sesi lain (lihat log dan `git log gpt/integrasi`),
   lanjutkan dari situ; jangan menulis ulang dari nol.

9. **Jangan audit diri berulang-ulang.** Satu putaran pemeriksaan sendiri + semua uji lulus = cukup, lalu
   merge dan lanjut. Hal yang belum pasti dicatat di log sebagai "catatan untuk audit", bukan alasan berhenti.
   Jangan menambah workflow baru untuk menguji; `test-runtime.yml` sudah mencakup semuanya. Bila memang
   butuh pemeriksaan baru, tambahkan langkah di workflow itu atau tambahkan uji pytest.

**Tugas antarmuka web (Studio Alur)** ada di berkas terpisah `docs/TUGAS_ANTARMUKA.md` dengan protokol yang
sama; boleh dikerjakan sesi lain secara paralel.

**Permintaan komponen dari naskah pemilik** (pemilik menempel naskah dan meminta komponen visualnya)
diutamakan di atas daftar tugas dan mengikuti `docs/ATURAN_KOMPONEN.md`. Setelah PR-nya dibuat, lanjutkan
daftar tugas dari posisi terakhir.

## Daftar tugas (centang bila selesai dan sudah di-merge ke `gpt/integrasi`)

- [x] Tugas 1 — Penulisan naskah pindah ke jalur LLM bersama
- [x] Tugas 2 — Pencatat kekurangan renderer (antrean kebutuhan)
- [x] Tugas 3 — Pustaka benda renderer untuk banyak jenis cerita
- [x] Tugas 4 — Lapis A uji tokoh menuju nol temuan
- [ ] Tugas 5 — Interaksi antartokoh dan benda yang dipegang
- [ ] Tugas 5b — Perbaikan benda lemah dari Tugas 3 (temuan audit Claude, kerjakan setelah Tugas 5)
- [ ] Tugas 5c — Pemeriksa naskah sebelum sampai ke pemilik (prioritas tinggi)
- [ ] Tugas 5d — Belajar dari revisi pemilik dan naskah yang disetujui
- [ ] Tugas 6 — Visual konsep abstrak
- [ ] Tugas 7 — Lembar uji renderer otomatis
- [ ] Tugas 8 — Pembuat komponen renderer (bersyarat, lihat syaratnya)
- [ ] Tugas 9 — Statistik video dan usulan pedoman dari data

## Batas wajib (berlaku untuk semua tugas)

- **Adab:** Allah tidak digambar dalam bentuk apa pun. Nabi/rasul = cahaya (`nur`), malaikat = cahaya,
  sahabat = wajah cahaya. Benda/tokoh bersosok manusia tidak boleh menjadi wujud tokoh mulia. Penjaga
  `newmotion/paket_genre/kisah_islami/penjaga_tokoh.py` tidak boleh dilemahkan.
- **Tanpa biaya diam-diam:** uji tidak boleh memanggil LLM, ElevenLabs, atau layanan berbayar sungguhan.
  Pakai `http` palsu seperti di `tests/test_llm.py` dan TTS palsu seperti di `tests/test_produksi_final.py`.
  `tests/conftest.py` memaksa sutradara produksi ke mode aturan; jangan dihapus.
- **Workflow GitHub baru** hanya `workflow_dispatch` (manual) atau dipicu bot; tidak boleh `on: push`/`pull_request`
  tanpa filter (kuota Actions).
- **Video lama tidak boleh berubah:** spek tanpa kunci baru harus dirender persis sama
  (`tests/test_referensi_kisah.py`, video referensi Nuh/Ya'juj/Mahsyar di `mesin-video/papan/kisah/`).
  Kemampuan baru = kunci/opsi baru, bukan mengubah bawaan.
- **Tidak ada gambar AI** di renderer Kisah Islami; semua digambar vektor di `mesin-video/papan/cerita.js`.
- Tidak menulis rahasia/token. Tidak menghapus fitur yang sudah ada tanpa alasan tertulis di PR.

## Peta singkat sistem (agar tidak menebak)

- Renderer: `mesin-video/papan/cerita.js` (fungsi `benda()` = semua jenis benda; `rangka()`/`boneka()` = tokoh
  bersendi; `KAIT` = benda yang bisa dinaiki/diduduki), dibungkus `mesin-video/papan_buat.py`
  (`--pratinjau 1,2,3` = PNG cepat tanpa MP4).
- Katalog otomatis dari kode: `newmotion/application/katalog_renderer.py` (benda + parameter; `*` = bisa
  dianimasikan karena dibaca lewat `v(o.x, t, ...)`), `kemampuan_tokoh.py` (pose, aksi, hadap, kait, suku),
  `katalog_suara.py`. Skill sutradara membaca katalog ini, jadi kemampuan baru otomatis diketahui sutradara.
- Ukuran benda untuk tata letak: `python mesin-video/papan/ukur_benda.py` -> `newmotion/application/data/ukuran_benda.json`.
  Jalankan ulang setiap menambah/mengubah benda. Tata letak: `newmotion/application/tata_letak.py`.
- Alat ukur tokoh: `python mesin-video/papan/uji_tokoh.py -o /tmp/uji_tokoh` (lapis A1–A6 + lembar PNG).
- Jalur hibrida: `paket_genre/kisah_islami/sutradara_llm.py` (rencana), `rencana_sutradara.py` (validator +
  terjemahan ke papan), `periksa_visual.py` (vision), `sutradara_hibrida.py` (produksi), `narasi_final.py` +
  `application/produksi_final.py` (TTS + render final). LLM bersama: `newmotion/infrastructure/llm.py`
  (`llm.panggil(tahap, ...)`, model per tahap di `config/model.toml`, cadangan otomatis, ulang bila ditolak
  validator, biaya).
- Bot: `bot/worker.js` (Cloudflare Worker, deploy otomatis saat merge ke main), antrean di `antrean/<id>/`.

---

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

---

## Log kerja

Format: `- YYYY-MM-DD | Tugas N | status (selesai/sebagian/MACET) | PR #.. | catatan + langkah berikut`

- 2026-11-27 | — | disiapkan oleh Claude | — | Sistem hibrida utuh (PR #51), tata letak (#49), kemampuan
  figuran/variasi (#47, #52). Belum ada uji gabungan LLM/ElevenLabs sungguhan (menunggu pemilik). Mulai dari Tugas 1.
- 2026-11-27 | — | disiapkan oleh Claude | — | Cabang `gpt/integrasi` dibuat dari main. Kerja berlanjut tanpa
  menunggu audit (protokol butir 5); audit + merge ke main dilakukan pemilik/Claude setelah semua tugas selesai.

- 2026-11-27 | Tugas 1 | sebagian | PR #54 | Jalur mandiri Claude/Gemini di antrean dihapus; ide/revisi memakai llm.panggil tahap naskah, tempel tahap rapikan; aturan dipisah ke skill; uji_cerita enam unsur tampil ringkas di kartu Telegram; metadata model/penyedia/token/biaya/percobaan dicatat. Dihapus tiga tes duplikat. Ruff awal menemukan dua E702 pada baris lama; keduanya diperbaiki. CI akhir: Ruff lulus; runtime 386 passed, 1 skipped; uji bot lulus; uji adab tokoh lulus. Workflow lint-naskah.yml ditambahkan agar pemeriksaan Ruff berulang otomatis. CLAUDE.md dan mesin-video/CLAUDE.md tidak ditemukan di main. Berikutnya: audit pemilik atas PR #54; jangan merge sebelum audit.

- 2026-11-27 | Audit Tugas 1 | sebagian | PR #54 | Audit jalur LLM: tahap `naskah`/`rapikan` benar-benar mengambil rantai model dari `config/model.toml`; struktur `Jawaban`, metadata token/biaya/model/penyedia, dan percobaan cocok dengan `infrastructure/llm.py`. Ditemukan celah pada pemetaan tempel: AI bisa menghilangkan, menggandakan, membalik, atau menunjuk paragraf di luar teks; sebelumnya paragraf yang hilang diam-diam ditambahkan sebagai beat tanpa metadata. Validator kini mewajibkan semua paragraf dipetakan tepat sekali, urutan menaik, dan nomor dalam rentang; ditambah tes regresi. Berikutnya: tunggu CI, lalu audit makna rujukan tempel (pastikan AI tidak mengarang dalil) dan uji revisi agar perubahan tetap sesuai catatan pemilik. Belum merge.

- 2026-11-27 | Audit lanjutan Tugas 1 | sebagian | PR #54 | Setelah penguatan pemetaan tempel, audit menemukan keluaran CLI membaca `penyedia_ai` padahal metadata disimpan di `naskah_ai`; diperbaiki dan ditambah assertion metadata model/penyedia/token pada uji proses. CI untuk commit pemetaan: Ruff lulus, bot lulus, adab tokoh lulus; runtime masih berjalan saat catatan dibuat. Catatan terbuka: harga Gemini di `config/model.toml` masih 0 sehingga angka biaya Gemini belum dapat dianggap biaya aktual; pemetaan dalil tempel dan batas revisi sesuai catatan pemilik masih perlu audit. Berikutnya: pastikan runtime CI terbaru lulus, lalu tuntaskan dua audit semantik tersebut. Jangan merge.

- 2026-11-27 | Audit dalil mode tempel | sebagian | PR #54 | Ditemukan risiko AI menambah/mengubah/menghilangkan rujukan saat memetakan teks tempelan. Validator kini membandingkan label dalil keluaran dengan daftar rujukan yang benar-benar tertulis pemilik; tanpa rujukan asli, AI tidak boleh menyisipkan dalil. Tes mencakup rujukan palsu, hilang, dan cocok. Juga memperketat cakupan paragraf dan memperbaiki keluaran CLI metadata penyedia. CI pada commit sebelumnya: Ruff, runtime, bot, dan adab tokoh lulus; perubahan validasi rujukan terbaru sedang menunggu CI. Catatan terbuka: biaya Gemini masih tercatat 0 karena harga belum dikonfigurasi, dan batas perubahan revisi belum dapat ditegakkan secara deterministik; harus diuji/audit sebelum Tugas 1 dinyatakan selesai. Jangan merge.

- 2026-11-27 | Verifikasi audit Tugas 1 | sebagian | PR #54 | CI untuk kode terbaru (commit `8b6f721`) selesai seluruhnya: Ruff sukses, runtime sukses, bot Telegram sukses, dan uji adab tokoh sukses. Audit teknis LLM mengonfirmasi pemilihan tahap dari `config/model.toml`, struktur metadata `Jawaban`, dan mekanisme retry validator di pemanggil bersama. Pemetaan paragraf dan rujukan tempel kini dijaga validator. Dua hal belum ditutup: harga Gemini 0 membuat biaya yang tercatat tidak representatif; revisi masih mengandalkan instruksi LLM dan belum punya uji yang membuktikan bagian di luar permintaan tetap identik. Tugas 1 tetap sebagian sampai dua hal itu diselesaikan atau diberi keputusan eksplisit. Jangan merge.

- 2026-11-27 | Penutupan temuan biaya/revisi Tugas 1 | sebagian | PR #54 | Status antrean kini memberi `biaya_status=belum_terverifikasi` untuk respons Gemini dengan biaya 0, sehingga angka nol tidak disalahartikan sebagai biaya aktual; ditambah tes. Uji revisi diperkuat: memastikan prompt memuat naskah lama + catatan pemilik, hasil contoh mengubah pembuka yang diminta, dan beat lain tetap sama. CI untuk perubahan ini sedang berjalan. Sisa keputusan: harga Gemini dinamis belum dapat diisi dengan angka tetap tanpa mengetahui model aktual/tingkat harga; status ketidakpastian sudah eksplisit. Setelah CI hijau, Tugas 1 bisa diserahkan untuk audit pemilik; jangan merge sebelum persetujuan.

- 2026-11-27 | Status CI audit akhir | sebagian | PR #54 | Untuk commit kode terbaru `d4770c9`: Ruff sukses, uji bot Telegram sukses, uji adab tokoh sukses; runtime masih berjalan di langkah persiapan FFmpeg (belum gagal, belum selesai). Ditambahkan penanda `biaya_status=belum_terverifikasi` untuk biaya Gemini nol dan uji revisi yang memeriksa prompt serta mempertahankan beat yang tidak diminta pada keluaran uji. Berikutnya: tunggu runtime CI selesai; jika hijau, serahkan PR #54 kepada pemilik/Claude untuk audit final. Tugas 1 tetap belum dinyatakan selesai sampai audit final; jangan merge.

- 2026-11-27 | Audit ulang protokol & uji integrasi Tugas 1 | sebagian | PR #54 | Membaca ulang dokumen ini penuh dan memeriksa ulang berkas instruksi CLAUDE; keduanya tidak ditemukan di branch. Perbandingan dengan prompt lama di `main` menemukan beberapa aturan rinci yang belum dipindahkan ke skill (format nama peran nabi/sahabat, format dialog, daftar suasana, hikmah pada topik berat, aturan deduplikasi dalil, dan aturan pemetaan paragraf tempel); semuanya dipulihkan ke `skill/naskah.md`. Menambahkan tes integrasi dengan HTTP palsu untuk ide sukses, ide ditolak validator lalu retry pada model yang sama, tempel menjaga narasi, dan revisi membawa naskah lama/catatan. Ruff untuk tes HTTP palsu sudah lulus; runtime untuk kode/tes terbaru belum terverifikasi. Agar Actions benar-benar menjalankan seluruh pytest pada branch PR, branch `tugas-1-llm-naskah` ditambahkan ke pemicu push yang sudah dibatasi paths pada `test-runtime.yml`. Berikutnya: tunggu runtime CI terbaru, perbaiki bila ada gagal, lalu audit ulang seluruh checklist Tugas 1. Jangan merge.

- 2026-11-27 | Verifikasi CI lengkap Tugas 1 | sebagian | PR #54 | CI runtime terbaru pada commit kode `c65e409` sukses: `394 passed, 1 skipped`; langkah bot `node --test`, pembandingan alat ukur, CLI ukur, dan `newmotion doctor` juga selesai tanpa gagal (workflow sukses). Ruff sukses. Uji HTTP palsu untuk ide sukses, retry setelah ditolak validator, tempel mempertahankan narasi, dan alur revisi ikut tercakup dalam 394 tes. Skill penulisan diselaraskan kembali dengan semua ketentuan lama yang ditemukan dari prompt `main`; CLAUDE.md dan mesin-video/CLAUDE.md tidak ada. Review PR masih kosong (tidak ada review, thread, atau komentar pemilik/Claude). Berikutnya secara persis: serahkan PR #54 kepada pemilik/Claude untuk audit dan keputusan merge; jangan merge sendiri dan jangan mulai Tugas 2 sebelum PR #54 diaudit serta digabung pemilik.

- 2026-11-27 | Tugas 1 | selesai | PR #54 | Claude: PR #54 dibuat sebelum protokol diganti, jadi basisnya
  dipindah ke `gpt/integrasi` dan di-merge (pytest lulus lokal). Tugas 1 dianggap selesai; catatan terbuka
  (harga Gemini 0 = `belum_terverifikasi`) diaudit belakangan. PROTOKOL SEKARANG: jangan menunggu audit,
  merge sendiri ke `gpt/integrasi` bila uji lulus, lalu lanjut. Jangan audit diri berulang-ulang: satu
  putaran periksa + uji lulus sudah cukup. Workflow tambahan per-branch tidak perlu lagi; jalankan uji lokal.
  Berikutnya: Tugas 2.


- 2026-11-27 | Tugas 2 | selesai | PR #56 | Menambahkan `belum_ada` di tingkat rencana/per beat dengan validasi katalog dan bukti narasi; skill sutradara tidak boleh mengganti objek yang belum tersedia dengan benda terdekat; pemeriksa visual dapat melaporkan kebutuhan objek; kebutuhan dari sutradara CLI, produksi hibrida, dan pemeriksa dikumpulkan ke JSON dengan normalisasi nama, jumlah kemunculan, contoh kisah/beat, sumber, serta status. Ditambahkan perintah daftar kebutuhan dan workflow pratinjau menyimpan antrean. CI GitHub pada kode terbaru: runtime 401 passed, 1 skipped (Chromium opsional); uji bot sukses; uji adab tokoh sukses. Ruff ditambahkan ke test-runtime untuk berkas yang berubah dan pemicu push generik `tugas-*` agar tugas berikutnya diuji di GitHub. Berikutnya: Tugas 3 — pustaka benda renderer untuk banyak jenis cerita; gunakan daftar contoh di spesifikasi sebagai titik awal, minimal 20 jenis benda baru, jaga kunci bawaan agar video lama tidak berubah.

- 2026-11-27 | Tugas 3 | selesai | PR #57 | Menambahkan 24 benda vektor baru di `mesin-video/papan/cerita.js`, seluruhnya terdaftar di katalog dan memiliki parameter keadaan yang dapat dianimasikan; benda lama tidak dihapus/diubah. Perahu kecil ditambahkan ke `KAIT` dengan adegan uji A6 (kedua kaki menapak pada dek; tidak memaksakan titik pegangan tangan yang tidak ada). Uji kontrak katalog, skrip lembar PNG dua keadaan, dan ukuran bbox telah ditambahkan; `ukuran_benda.json` hasil ukur sudah tersimpan di branch. GitHub Actions run #45924118040 sukses pada seluruh 17 langkah: `node --check`, pengukuran, lembar visual, A6 perahu kecil, Ruff, pytest (404 passed), uji bot, alat ukur PR, CLI, dan doctor. Artifact `bukti-pustaka-benda-baru` tersedia (PNG + JSON). Catatan: laporan umum `uji_tokoh.py` masih menampilkan temuan A1–A5 yang memang menjadi ruang lingkup Tugas 4; pemeriksaan A6 khusus perahu baru lulus. PR digabung ke `gpt/integrasi` setelah verifikasi CI. Berikutnya: Tugas 4 — Lapis A uji tokoh menuju nol temuan.

- 2026-11-27 | Tugas 4 | selesai | PR #58 | Memperbaiki pijakan kaki aksi `gali`/`menolong` dengan IK, menjaga badan samping pada pose `rebahan`/`rebahan_hp`, mengarahkan ayunan beliung ke depan-bawah, dan menyatukan panjang tulang kaki dengan acuan 100 px. Siklus `lompat` dijadikan lintasan periodik halus tanpa patahan pada batas modulo. `uji_tokoh.py` terbaru menguji 29 pose, lima sudut, dan sepuluh aksi; hasil eksplisit: **Lapis A: tidak ada temuan**. A6 perahu kecil juga lulus. Pada commit akhir `aa8f4ae`, GitHub Actions runtime dan uji pembuat karakter sukses; pytest **404 passed**, Ruff bersih, uji bot/CLI/doctor sukses. Perbaikan pencatatan `badan_samping` mencegah false positive pada pose rebah. PR #58 digabung ke `gpt/integrasi`. Berikutnya: Tugas 5 — interaksi antartokoh dan benda yang dipegang.

- 2026-11-27 | Audit bertahap Tugas 1–4 | Claude | — | 404 uji lulus di gpt/integrasi; uji tokoh lapis A memang 0
  temuan tanpa melonggarkan ambang. Tugas 3: 20 dari 24 benda layak; empat benda lemah dijadikan Tugas 5b
  (kerjakan setelah Tugas 5 selesai, sebelum Tugas 6). Catatan untuk audit akhir: test-runtime.yml kini
  terpicu push `tugas-*` dan meng-commit balik ukuran_benda.json — dirapikan saat merge ke main.
- 2026-11-27 | Protokol | Claude | — | Pengerja tidak bisa pytest lokal: butir 4 kini resmi memakai CI
  `test-runtime.yml` (dirapikan: push `tugas-*`, ruff otomatis untuk berkas berubah, ukur benda + commit balik,
  pytest, bot, uji tokoh 0 temuan, artefak bukti). Workflow lama lint-naskah.yml dihapus (sudah tercakup).
- 2026-11-27 | Tambahan tugas | Claude | — | Dari uji naskah nyata (Firaun): ditambah Tugas 5c (pemeriksa
  naskah, prioritas tinggi), 5d (belajar dari revisi & contoh), 9 (statistik video). Urutan: 5 -> 5b -> 5c -> 5d -> 6 ...
- 2026-11-27 | Tugas 5 | sebagian | PR #59 | Menambahkan katalog otomatis pose benda genggam dari `POSE` renderer (tongkat, kendi, lentera, keranjang, tasbih, surat, gulungan, karung kecil, roti, koin); figuran bernama dapat saling menghadap dan memegang benda. Rencana `serahkan_ke` diterjemahkan menjadi lintasan tiga fase: pemberi membawa benda ke titik temu, kedua tangan menempel, lalu penerima mengambil alih. Kedua tangan memakai IK ke satu titik benda; pengarah panggung mendekatkan dua figuran dan mengatur profil saling menghadap. CI pembuat karakter run #45938860940 lulus, bukti tujuh sampel menunjukkan perpindahan 102,62 px dan jarak tangan-benda maksimum 0 px (batas 14 px). Runtime run #45938860963 lulus: Ruff bersih, pytest 410 passed, bot, CLI, doctor dan pengukuran benda sukses. Artifact `bukti-interaksi-tokoh` berisi lembar PNG + laporan JSON. Belum digabung: perlu menyelaraskan branch dengan tiga commit terbaru `gpt/integrasi`, menjalankan ulang CI di merge-base terbaru, lalu audit PR.
