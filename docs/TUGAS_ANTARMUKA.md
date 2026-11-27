# Tugas antarmuka "Studio Alur" — NewMotion

Untuk sesi AI pengerja (ChatGPT/Codex). Bahasa kerja dan bahasa tampilan: Indonesia. Ditulis 27 Nov 2026
oleh Claude (pengaudit) atas permintaan pemilik (Anwar Alzazali).

**Protokol sesi, batas wajib, CI, dan cara menulis log sama dengan `docs/TUGAS_GPT.md`** (baca bagian
"Protokol setiap sesi" dan "Batas wajib" di sana). Perbedaannya hanya:
- Branch bernama `tugas-ui-<nomor>-<ringkas>`, PR ke `gpt/integrasi`, merge sendiri bila CI hijau.
- Log kerja: berkas baru `docs/log_kerja/YYYY-MM-DD-HHMM-ui-N.md`.
- Daftar tugas di berkas ini, dicentang di berkas ini. Tugas antarmuka boleh dikerjakan sesi yang berbeda
  dari sesi `TUGAS_GPT.md`; keduanya tidak boleh mengubah berkas yang sama tanpa perlu.

## Tujuan

Pemilik membuat video sendiri (bukan untuk dijual dulu). Ia butuh satu halaman web untuk:
1. melihat **alur pembuatan video node per node** (seperti n8n secara tampilan) untuk setiap antrean,
   lengkap dengan status, hasil, dan biaya tiap tahap;
2. **pratinjau** papan/video langsung di browser;
3. **mengedit tokoh dan figuran** per beat, lalu menjalankan ulang tahap yang perlu.

Bot Telegram tetap ada untuk alur cepat di HP; halaman ini untuk meninjau dan mengedit secara rinci.

## Keputusan yang sudah diambil (jangan didesain ulang)

- **Alur tetap, bukan editor bebas.** Node dan sambungannya mengikuti urutan produksi yang sudah ada:
  ide → naskah → verifikasi dalil → pemeriksa naskah (bila ada) → tinjauan naskah → sutradara →
  periksa visual → pratinjau visual → tinjauan visual → narasi → render final. Node tidak bisa
  ditambah/dihapus/disambung ulang oleh pengguna; urutan wajib (dalil, penjaga adab) tidak bisa dilewati.
  Bila tahap baru ditambahkan di mesin (mis. pemeriksa naskah), node-nya ditambahkan di kode, bukan oleh pengguna.
- **Sumber data = repo.** Status dan hasil tiap antrean sudah ada di `antrean/<id>/` (status.json, naskah.json,
  rencana.json, periksa.json, papan_pratinjau.json, papan_final.json, audio/...). Tidak ada database baru.
- **Tahap berat tetap di GitHub Actions** (LLM, TTS, render MP4) lewat workflow yang sudah dipakai bot
  (`naskah.yml`, `visual.yml`, `final.yml`, dst.). Halaman hanya memicu dan membaca hasilnya.
- **Renderer dipakai ulang di browser.** `mesin-video/papan/cerita.js` + `papan.js` memang berjalan di browser
  (`setT(t)`), jadi pratinjau dan hasil edit tampil seketika tanpa menunggu Actions.
- **Satu pengguna (pemilik).** Akses dikunci (kata sandi di secret Worker atau Cloudflare Access). Token GitHub
  hanya di sisi server (Worker), tidak pernah dikirim ke browser.
- **Tempat:** folder baru `antarmuka/` di repo ini sebagai Cloudflare Worker sendiri (bukan menumpang
  `bot/worker.js`, supaya bot produksi tidak terganggu). Pemilik menyambungkan Workers Builds sekali; tulis
  langkahnya di `antarmuka/README.md` (rahasia apa saja, izin token fine-grained minimum).

## Standar mutu (berlaku untuk semua tugas UI)

- **Nyaman di HP dan laptop.** Pemilik sering memakai HP: node bisa digeser/diperbesar dengan jari, panel
  detail menjadi lembar bawah di layar sempit. Teks bahasa Indonesia yang jelas, bukan istilah teknis mentah.
- **Cepat dan ringan:** halaman pertama terbuka < 2 dtk di 4G; data dimuat bertahap.
- **Status jelas:** warna + label per node (belum, berjalan, selesai, gagal, menunggu persetujuan),
  waktu terakhir, biaya tahap (bila ada), dan pesan galat yang bisa dimengerti.
- **Mode contoh untuk uji:** halaman bisa dijalankan dari data contoh lokal (mis. `tests/data/antarmuka/`
  berisi satu antrean lengkap) tanpa GitHub/kata sandi, agar CI bisa memotret layarnya.
- **Bukti di PR (wajib):** tangkapan layar ukuran HP (≈390×844) dan laptop (≈1440×900) dari mode contoh,
  dibuat otomatis di CI (tambahkan langkah di `test-runtime.yml` atau uji pytest dengan Playwright yang sudah
  terpasang di CI) dan diunggah sebagai artefak run. Mutu tampilan dinilai dari tangkapan layar ini.
- Tidak ada pustaka berat tanpa alasan; bila memakai pustaka kanvas node, tulis alasannya di PR.
- **Animasi aliran (gaya bebas, tujuan wajib):** cara menganimasikan sambungan dan node diserahkan ke
  pengerja, tetapi animasi harus *bermakna*: memperlihatkan tahap mana yang sedang berjalan, arah aliran
  hasil dari node ke node, dan perubahan status (mis. selesai/gagal) saat terjadi. Sambungan yang belum
  dilewati terlihat diam; yang sudah selesai terlihat berbeda dari yang sedang mengalir. Tidak boleh sekadar
  hiasan yang bergerak terus di semua tempat, tidak boleh membuat HP panas/patah-patah (ringan, berhenti saat
  tab tidak terlihat), dan menghormati pengaturan "kurangi gerakan" di perangkat.

## Daftar tugas

- [ ] UI-1 — Halaman alur (hanya baca)
- [ ] UI-2 — Pratinjau langsung di browser
- [ ] UI-3 — Editor tokoh dan figuran per beat (bersyarat)
- [ ] UI-4 — Jalankan ulang dari node (bersyarat)

### UI-1 — Halaman alur (hanya baca)

**Selesai bila:**
- Daftar antrean (judul, tanggal, tahap terakhir, status) dan halaman per antrean berisi kanvas node alur tetap.
- Klik node membuka panel hasil tahap itu: naskah per beat + dalil terverifikasi; temuan pemeriksa; rencana
  sutradara per beat (ringkas, bukan JSON mentah); temuan periksa visual + lembar frame; video pratinjau/final
  (tautan artefak/Telegram atau berkas di repo bila ada); biaya dan model LLM tiap tahap.
- Node yang belum punya data tampil "belum", bukan galat.
- Uji: pemetaan status.json -> status node (semua keadaan, termasuk gagal dan menunggu persetujuan).

### UI-2 — Pratinjau langsung di browser

**Selesai bila:**
- Papan antrean (`papan_pratinjau.json` / `papan_final.json`) dirender di halaman memakai renderer yang sama
  dengan video (bukan tiruan), dengan garis waktu, tombol putar/jeda, dan lompat per beat (label narasi beat).
- Bila ada narasi (`audio/narasi.mp3`), suara ikut diputar sinkron.
- Tampilan dalam bingkai 9:16 dengan opsi tampilan zona aman TikTok.
- Uji: pratinjau mode contoh tampil tanpa galat konsol (CI memeriksa log konsol Playwright).

### UI-3 — Editor tokoh dan figuran per beat (bersyarat)

**Syarat mulai:** ada berkas `docs/log_kerja/*izin-ui-3*.md` dari pemilik/Claude (diberikan setelah uji video
pertama, karena bentuk rencana sutradara mungkin masih berubah). Bila belum ada, lewati.

**Selesai bila:**
- Per beat: panel tokoh "kamu" (ada/utama/saksi/tidak, pose, hadap) dan figuran (jumlah, suku, tempat,
  gerak, hadap, pindah, naik) memakai pilihan yang dibaca dari katalog kemampuan
  (`newmotion/application/kemampuan_tokoh.py` — sediakan keluaran JSON-nya untuk halaman, jangan menyalin daftar).
- Perubahan tampil seketika di pratinjau (UI-2). Menggeser tokoh di pratinjau mengubah posisinya.
- Simpan = berkas koreksi (mis. `antrean/<id>/koreksi.json`) lalu workflow (baru, manual/dipicu halaman)
  menerapkannya ke rencana, menjalankan **validator rencana dan penjaga adab yang sama dengan sutradara**,
  membuat ulang papan pratinjau, dan mencatat hasilnya. Koreksi yang ditolak validator (mis. figuran di beat
  yang menyebut nabi) ditampilkan alasannya di halaman; tidak diterapkan.
- Uji: koreksi sah diterapkan; koreksi melanggar adab ditolak; pratinjau memakai koreksi.

### UI-4 — Jalankan ulang dari node (bersyarat)

**Syarat mulai:** UI-3 selesai.

**Selesai bila:**
- Node tertentu punya tombol jalankan ulang yang memicu workflow yang sama dengan bot: naskah (revisi),
  sutradara/pratinjau visual, narasi, render final.
- Sebelum menjalankan tahap berbayar (LLM, ElevenLabs), halaman menampilkan perkiraan biaya dan meminta
  konfirmasi. Narasi yang sudah ada dipakai ulang kecuali pemilik memilih "buat ulang narasi" secara tegas.
- Status node berubah menjadi berjalan, lalu diperbarui otomatis saat workflow selesai (cek berkala ringan).
- Uji: pemicuan memanggil workflow yang benar dengan input yang benar (GitHub API palsu).
