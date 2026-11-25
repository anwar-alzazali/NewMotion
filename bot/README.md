# Bot Telegram Mesin KONTEN — NewMotion

Bot Telegram Cloudflare Worker yang menjadi antarmuka antrean NewMotion. Worker tetap memakai nama deployment `mesin-konten`; kode sumber kini berada di repo NewMotion.

## Kemampuan yang dipindahkan

- Menu Telegram pribadi, pembatasan hanya untuk pemilik, dan webhook dengan secret.
- Kirim ide atau naskah melalui `/ide` dan `/naskah`.
- Antrean naskah: Gemini sebagai pilihan utama, Claude sebagai cadangan berbayar.
- Verifikasi dalil melalui paket `kisah_islami` NewMotion (Quran Foundation dan dataset Sunnah.com).
- Kartu status, revisi, dan penyimpanan persetujuan video.
- Chat pribadi dan bantuan balas komentar.

## Deploy Cloudflare

1. Cloudflare → Workers & Pages → Worker `mesin-konten` → Settings → Build.
2. Hubungkan repo `anwar-alzazali/NewMotion`, branch `main`, root directory `bot`.
3. Pastikan Secret Worker tersedia: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `WEBHOOK_SECRET`, `GH_TOKEN`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY` (opsional), `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`.
4. Fine-grained GitHub token harus punya akses ke repo NewMotion: Contents Read and write serta Actions Read and write.
5. Variabel `GH_REPO` dan `GH_BRANCH` disetel di `wrangler.toml`; jangan simpan token atau secret di berkas.
6. Setelah deployment, pasang ulang webhook melalui `/pasang?k=<WEBHOOK_SECRET>` pada alamat Worker. Respons yang diharapkan: `{"webhook":true,"perintah":true}`.

## Workflow antrean

Worker memanggil workflow `.github/workflows/naskah.yml` melalui `workflow_dispatch`. Workflow menjalankan `newmotion.application.antrean_naskah`, bukan modul `sutradara` dari repo lama. Rahasia AI, Telegram, dan Quran Foundation hanya dibaca dari GitHub Actions Secrets.

Workflow hanya dipicu manual/API melalui `workflow_dispatch`, sesuai aturan repo publik. Jangan menambahkan pemicu `push`, `issues`, `pull_request_target`, atau event dari fork pada workflow yang memakai rahasia.

## Alur persetujuan sebelum produksi

1. Setelah naskah dan dalil diverifikasi, pemilik meninjau naskah di Telegram.
2. Tombol **Lanjut** memicu `.github/workflows/visual.yml`.
3. Pengarah Kisah Islami mengubah beat menjadi adegan, lalu renderer membuat MP4 pratinjau **tanpa TTS dan tanpa trek narasi**.
4. Pratinjau dikirim ke Telegram dengan tombol **Setujui visual** atau **Tolak visual**. Penolakan menghentikan alur; revisi otomatis berdasarkan catatan visual belum tersedia.
5. Jika visual ditolak, tahap TTS tetap diblokir. Jika disetujui, status membuka tahap TTS; produksi TTS dan render final masih merupakan integrasi berikutnya.

Pratinjau visual menggunakan renderer yang sudah ada. Artefak MP4 disimpan sementara sebagai GitHub Actions artifact selama 7 hari; papan JSON dan status tinjauan disimpan di antrean. Workflow membutuhkan dependensi `.[render]`, Chromium Playwright, FFmpeg, serta secrets Telegram dan Quran Foundation.

## Batas migrasi saat ini

Tahap ini menghubungkan persetujuan naskah ke pratinjau visual tanpa suara dan menambahkan gerbang persetujuan visual sebelum TTS. Persetujuan visual belum memicu TTS atau render final secara otomatis; tahap tersebut tetap menunggu integrasi lanjutan.
