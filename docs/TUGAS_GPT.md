# Tugas untuk sesi AI pengerja (ChatGPT/Codex) — NewMotion

Pemilik: Anwar Alzazali. Bahasa kerja: Indonesia. Ditulis 27 Nov 2026 oleh Claude (pengaudit).

## Protokol setiap sesi (WAJIB dibaca dulu; ingatan sesi pendek)

1. Baca berkas ini sampai habis, lalu `CLAUDE.md` di akar dan `mesin-video/CLAUDE.md` bila ada.
2. Lihat **Log kerja** di paling bawah. Ambil tugas **pertama yang belum `[x]`** dan belum ada PR terbukanya
   (`gh pr list`). Jangan mengulang tugas yang sudah selesai, jangan mendesain ulang keputusan yang sudah
   tercatat di log, kecuali log itu sendiri menyatakan ada masalah.
3. Satu tugas = satu branch dari `main` terbaru = satu PR. Jangan menggabungkan dua tugas dalam satu PR.
4. Sebelum PR: `python -m pytest -q` lulus semua (saat ini 384), `ruff check` bersih untuk berkas yang
   kamu ubah, dan `node --test bot/` lulus bila menyentuh bot.
5. Di akhir sesi (selesai atau belum), **tambahkan satu entri di Log kerja**: tanggal, tugas, apa yang
   selesai, nomor PR, keputusan penting, dan langkah berikut yang persis. Sesi berikutnya hanya
   mengandalkan catatan ini.
6. **Batas macet:** bila satu masalah gagal dua kali dengan cara berbeda, berhenti mencoba. Tulis di log
   sebagai `MACET:` beserta apa yang sudah dicoba, lalu lanjut ke bagian lain tugas atau tugas berikutnya.
7. Jangan merge PR sendiri. Pemilik/Claude mengaudit dan merge.

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

## Tugas 2 — Pustaka benda renderer untuk banyak jenis cerita

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

## Tugas 3 — Lapis A uji tokoh menuju nol temuan

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

## Tugas 4 — Interaksi antartokoh dan benda yang dipegang

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

## Tugas 5 — Visual konsep abstrak yang sering muncul di Kisah Islami

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

## Tugas 6 (cadangan bila 1–5 selesai/macet) — Lembar uji renderer otomatis

Satu workflow manual `uji-renderer.yml` yang menjalankan `uji_tokoh.py`, membuat lembar semua benda
(dua keadaan per benda), dan menyimpan hasil ke branch `hasil/renderer-<run_id>` (contoh pola:
`.github/workflows/uji-sutradara-llm.yml`). Ringkasan di `GITHUB_STEP_SUMMARY`: jumlah benda, benda tanpa
ukuran, temuan lapis A. Tanpa LLM.

---

## Log kerja

Format: `- YYYY-MM-DD | Tugas N | status (selesai/sebagian/MACET) | PR #.. | catatan + langkah berikut`

- 2026-11-27 | — | disiapkan oleh Claude | — | Sistem hibrida utuh (PR #51), tata letak (#49), kemampuan
  figuran/variasi (#47, #52). Belum ada uji gabungan LLM/ElevenLabs sungguhan (menunggu pemilik). Mulai dari Tugas 1.

- 2026-11-27 | Tugas 1 | sebagian | PR #54 | Jalur mandiri Claude/Gemini di antrean dihapus; ide/revisi memakai llm.panggil tahap naskah, tempel tahap rapikan; aturan dipisah ke skill; uji_cerita enam unsur tampil ringkas di kartu Telegram; metadata model/penyedia/token/biaya/percobaan dicatat. Dihapus tiga tes duplikat. Ruff awal menemukan dua E702 pada baris lama; keduanya diperbaiki. CI akhir: Ruff lulus; runtime 386 passed, 1 skipped; uji bot lulus; uji adab tokoh lulus. Workflow lint-naskah.yml ditambahkan agar pemeriksaan Ruff berulang otomatis. CLAUDE.md dan mesin-video/CLAUDE.md tidak ditemukan di main. Berikutnya: audit pemilik atas PR #54; jangan merge sebelum audit.
