# Cara pakai NewMotion

Ada dua jalur membuat video. Keduanya lewat bot Telegram **Mesin KONTEN**, dan keduanya berakhir di
render yang sama (`mesin-video/papan/cerita.js`), penjaga adab yang sama, dan `periksa.py` yang sama.

| | Jalur hibrida (LLM) | Jalur manual (tanpa LLM) |
|---|---|---|
| Masukan | ide/topik atau naskah jadi | satu JSON papan lengkap (visual + narasi) |
| Yang menulis visual | sutradara LLM di mesin | AI sesi chat (atau Anda) di luar mesin |
| Verifikasi dalil otomatis | ya (Quran Foundation, Sunnah.com) | tidak; tanggung jawab penulis JSON |
| Tinjauan bertahap | naskah → pratinjau visual tanpa suara → final | langsung video bersuara |
| Biaya per video (kira-kira) | LLM naskah + sutradara + periksa (± Rp2–5 rb) + ElevenLabs | ElevenLabs saja |
| Cocok untuk | produksi rutin, topik baru | video yang ingin dikendalikan penuh, hemat |

## 1. Jalur hibrida (LLM)

1. **Mulai:** di bot ketuk 💡 **Ide** (tulis topik) atau 📝 **Naskah** (tempel naskah jadi, atau kirim berkas
   `.txt`/`.md` berketerangan `naskah`). Naskah tempelan tidak diubah narasinya, hanya dirapikan ke format mesin.
2. **Naskah dan dalil:** kartu status di bot diperbarui sendiri. Mesin menulis naskah (Claude Sonnet, cadangan
   Gemini), memeriksa naskah terhadap teks dalil, lalu memverifikasi setiap dalil. Dalil yang tidak lolos
   memblokir tombol Lanjut.
3. **Tinjau naskah:** ✅ **Lanjut**, ✏️ **Revisi** (balas dengan catatan; revisi Anda dicatat untuk pembelajaran),
   atau ❌ **Batal**. Kartu yang gagal (mis. naskah ditolak validator) tetap punya tombol Revisi.
4. **Pratinjau visual (tanpa suara, tanpa biaya TTS):** sutradara LLM menyusun rencana, pemeriksa visual
   melihat lembar frame dan memperbaiki rencana bila perlu, lalu video pratinjau dikirim.
   Pilih **Setujui visual** atau **Tolak visual**. Bila pratinjau gagal: 🔁 **Ulangi pratinjau visual**.
5. **Final:** setelah visual disetujui, narasi ElevenLabs (Ozhy) dibuat satu kali, lalu video bersuara dikirim.
   Bila gagal: 🔁 **Ulangi produksi final** (audio yang sudah ada dipakai ulang).
6. **Setelah tayang:** ketuk 📊 **Catat hasil** di hari ke-1 dan ke-7 (lihat bagian 4).

Perintah lain: `/status` (daftar antrean), `/bantuan`, `/reset` (hapus riwayat obrolan). Pesan biasa = tanya jawab;
tangkapan layar komentar (tanpa keterangan atau `k ...`) = usulan balasan komentar.

## 2. Jalur manual (tanpa LLM)

1. Dapatkan JSON lengkap:
   - **AI sesi chat:** di bot ketik `/bekal` (berkas lampiran) dan `/prompt` (teks prompt). Lampirkan bekal ke
     sesi chat baru, tempel prompt, isi topik/naskah. Simpan jawabannya sebagai `<nama>.json`.
   - **AI yang bisa mengakses GitHub:** pakai prompt B di `docs/PROMPT_JSON_LENGKAP.md`; AI menaruh JSON di
     branch `video/<nama>`, menjalankan render sendiri, dan membuka PR ke main tanpa merge.
2. Kirim berkas `.json` ke bot (atau, untuk JSON yang sudah ada di `mesin-video/papan/kisah/`, ketik `/papan <nama>`).
3. Mesin membuat narasi dari kolom `narasi` tiap shot (satu permintaan ElevenLabs), mengisi waktu shot dari
   rekaman, merender, menjalankan `periksa.py`, lalu mengirim lembar kontak + video + hasil periksa.
4. Revisi visual: ubah JSON tanpa mengubah teks narasi lalu kirim ulang → narasi lama dipakai ulang, tanpa biaya.

Format lengkap dan resep tokoh: `docs/FORMAT_PAPAN_MANUAL.md`.

## 3. Hasil periksa

`periksa.py` memberi **GAGAL** hanya untuk kerusakan teknis atau pelanggaran batas wajib, dan **PERIKSA** untuk
pedoman (ukuran huruf, zona aman, kenyaringan, efek menutup narasi). PERIKSA adalah keputusan Anda, bukan larangan.
Tetap dengarkan di speaker HP dan headphone sebelum unggah; label AI wajib aktif.

## 4. Statistik tayang

Di video final ketuk 📊 **Catat hasil**, lalu balas satu baris:
`tiktok h1 12rb 850 40 12 35%` → platform, hari 1/7, tayang, suka, komentar, bagikan, % ditonton sampai habis
(opsional). Kirim ulang untuk menimpa. Ciri tiap video (jenis hook, durasi, beat, klimaks, efek, dll.) dicatat
otomatis. Analisis: `python -m newmotion.application.statistik_video analisis` (pola baru layak dipercaya
setelah ±20 video; usulan tidak pernah dipakai otomatis).

## 5. Biaya dan model

Model per tahap ada di `config/model.toml` (urutan = utama lalu cadangan). Untuk mengutamakan yang gratis,
pindahkan `"gemini"` ke depan pada tahap yang diinginkan. Biaya tiap tahap tercatat di `antrean/<id>/status.json`.

## 6. Rahasia yang dibutuhkan

- **GitHub Actions** (repo NewMotion): `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `ANTHROPIC_API_KEY`,
  `GEMINI_API_KEY`, `ELEVENLABS_API_KEY`, `QURAN_FOUNDATION_CLIENT_ID`, `QURAN_FOUNDATION_CLIENT_SECRET`.
- **Cloudflare Worker** `mesin-konten`: lihat `bot/README.md`.

## 7. Bila ada masalah

| Gejala | Penyebab biasa | Tindakan |
|---|---|---|
| Bot tidak membalas setelah revisi | kartu lama diedit di tempat | gulir ke kartu antrean itu; kartu gagal punya tombol Revisi |
| Kartu "dalil gagal" | nomor dalil salah atau tidak sahih | Revisi dengan catatan dalil yang benar |
| Pratinjau/final gagal | galat render atau kunci API | tombol Ulangi; lihat log run di GitHub Actions |
| Jalur manual "JSON tidak terbaca" | JSON tidak lengkap/terpotong | minta AI mengirim ulang JSON utuh dalam satu blok |
| Jalur manual "berkas narasi tidak ada" | `suara` merujuk berkas yang tidak ada | hapus kunci `suara`/`waktu` agar narasi dibuat dari kolom `narasi` |
