# Bot Telegram Mesin KONTEN

Cloudflare Worker `mesin-konten` (kode: `bot/worker.js`) — antarmuka HP untuk seluruh produksi NewMotion.
Deploy otomatis setiap ada perubahan di `main`. Cara pakai untuk pemilik: `docs/CARA_PAKAI.md`.

## Kemampuan

- Menu pribadi (hanya `TELEGRAM_CHAT_ID` pemilik), webhook dengan secret.
- **Jalur hibrida:** 💡 Ide / 📝 Naskah → workflow `naskah.yml` → kartu status (Lanjut / Revisi / Batal) →
  `visual.yml` (pratinjau tanpa suara; Setujui / Tolak / Ulangi) → `final.yml` (narasi + render; Ulangi).
- **Jalur manual:** berkas `.json` atau `/papan <nama>` → `manual.yml`. `/bekal` mengirim
  `docs/BEKAL_PAPAN_MANUAL.md`, `/prompt` mengirim prompt penulis JSON.
- **Statistik:** tombol 📊 Catat hasil di video final → `antrean/<id>/statistik.json`.
- Persetujuan video lama (Setujui/Tolak + alasan) → `data/persetujuan/`.
- Obrolan pribadi dan usulan balas komentar dari tangkapan layar.
- Perintah: `/menu`, `/naskah`, `/ide`, `/status`, `/papan`, `/bekal`, `/prompt`, `/bantuan`, `/reset`.

## Deploy

1. Cloudflare → Workers & Pages → `mesin-konten` → Settings → Build: repo `anwar-alzazali/NewMotion`,
   branch `main`, root directory `bot`.
2. Secret Worker: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `WEBHOOK_SECRET`, `GH_TOKEN`, `ANTHROPIC_API_KEY`,
   `GEMINI_API_KEY` (opsional), `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`.
3. `GH_TOKEN` (fine-grained) untuk repo NewMotion: Contents Read and write, Actions Read and write.
4. `GH_REPO` dan `GH_BRANCH` ada di `wrangler.toml`; jangan menaruh token di berkas.
5. Setelah deploy pertama atau ganti domain: buka `/pasang?k=<WEBHOOK_SECRET>` di alamat Worker →
   `{"webhook":true,"perintah":true}` (sekaligus memperbarui daftar perintah). Diagnosa AI: `/cek?k=<WEBHOOK_SECRET>`.

## Aturan workflow

Semua workflow yang dipanggil bot hanya `workflow_dispatch`; rahasia AI, ElevenLabs, Telegram, dan Quran
Foundation hanya dibaca dari GitHub Actions Secrets. Jangan menambah pemicu `push`, `issues`,
`pull_request_target`, atau event dari fork pada workflow yang memakai rahasia.

## Uji

`node --test bot/*.test.mjs` (fungsi murni: tombol, kartu, id antrean, format statistik, cek papan, dll.).
