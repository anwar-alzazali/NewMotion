# NewMotion

Mesin produksi video pendek vertikal milik Anwar Alzazali, dengan prioritas **Kisah Islami**. Visual digambar
vektor oleh renderer sendiri (tanpa gambar AI), suara oleh ElevenLabs, dan semuanya dikendalikan dari bot
Telegram **Mesin KONTEN**.

## Dua jalur membuat video

- **Jalur hibrida (LLM):** kirim ide atau naskah ke bot → naskah + verifikasi dalil → tinjau → pratinjau
  visual tanpa suara → tinjau → video final bersuara.
- **Jalur manual (tanpa LLM):** AI sesi chat atau AI berakses GitHub menulis satu JSON lengkap (visual +
  narasi) → kirim ke bot → video bersuara langsung jadi. Paling irit.

Cara pakai lengkap: **[docs/CARA_PAKAI.md](docs/CARA_PAKAI.md)**.

## Dokumen

| Dokumen | Isi |
|---|---|
| [docs/CARA_PAKAI.md](docs/CARA_PAKAI.md) | langkah kedua jalur, statistik, biaya, rahasia, pemecahan masalah |
| [docs/FORMAT_PAPAN_MANUAL.md](docs/FORMAT_PAPAN_MANUAL.md) | format JSON jalur manual dan resep tokoh |
| [docs/PROMPT_JSON_LENGKAP.md](docs/PROMPT_JSON_LENGKAP.md) | prompt AI penulis JSON (sesi chat / berakses GitHub) |
| [docs/BEKAL_PAPAN_MANUAL.md](docs/BEKAL_PAPAN_MANUAL.md) | format + katalog benda, tokoh, suara terbaru (dibuat otomatis) |
| [docs/ROADMAP.md](docs/ROADMAP.md) | yang sudah jadi, sekarang, berikutnya |
| [docs/TUGAS_GPT.md](docs/TUGAS_GPT.md) | protokol, batas wajib, dan peta sistem untuk sesi AI pengerja |
| [docs/ATURAN_KOMPONEN.md](docs/ATURAN_KOMPONEN.md) | aturan membuat komponen renderer dari naskah |
| [docs/TUGAS_ANTARMUKA.md](docs/TUGAS_ANTARMUKA.md) | rencana halaman web Studio Alur |
| [bot/README.md](bot/README.md) | deploy dan rahasia bot Cloudflare |
| [newmotion/paket_genre/kisah_islami/PANDUAN_GAYA.md](newmotion/paket_genre/kisah_islami/PANDUAN_GAYA.md) | cara menggambarkan tokoh (adab) |
| `docs/log_kerja/` | catatan kerja per sesi (riwayat keputusan) |
| `docs/arsip/` | dokumen lama (arsitektur awal, audit, spesifikasi tugas selesai) |

## Batas wajib isi

Allah tidak digambar. Nabi, rasul, dan malaikat berupa cahaya + nama; sahabat bertubuh berwajah cahaya.
Bacaan Arab tidak disuarakan AI (tulisan Arab + latin + arti di layar). Hanya dalil sahih/hasan dengan sumber
tampil di layar. Label AI aktif saat unggah; tanpa watermark. Rinciannya di `docs/TUGAS_GPT.md` dan panduan gaya.

## Struktur kode

```
bot/                     Worker Telegram (deploy otomatis dari main)
mesin-video/             renderer (papan/cerita.js), papan_buat.py, periksa.py, aset, papan kisah referensi
newmotion/
  infrastructure/llm.py  pemanggil LLM bersama (model per tahap: config/model.toml)
  application/           antrean naskah, pratinjau, produksi final, jalur manual, statistik, katalog, tata letak
  paket_genre/kisah_islami/  skill LLM, sutradara, penjaga adab, verifikasi dalil, narasi
antrean/<id>/            status, naskah, rencana, papan, audio, statistik tiap video
.github/workflows/       semua manual atau dipicu bot (naskah, visual, final, manual, uji)
```

## Menjalankan lokal

Python 3.11+, FFmpeg, dan Chromium Playwright:

```bash
python -m pip install -e '.[uji,render]'
python -m playwright install chromium
python -m pytest -q                                   # uji (tanpa LLM/TTS sungguhan)
node --test bot/*.test.mjs                            # uji bot
python mesin-video/papan_buat.py mesin-video/papan/kisah/mahsyar1.json -o mahsyar1.mp4
python -m newmotion.application.jalur_manual mesin-video/papan/kisah/mahsyar1.json -o hasil.mp4
python mesin-video/papan/uji_tokoh.py -o /tmp/uji_tokoh    # uji anatomi tokoh (Lapis A)
```

## Ketentuan bahasa

Bahasa Indonesia adalah standar proyek: nama variabel, fungsi, modul, komentar, docstring, dan dokumentasi.
Pengecualian hanya untuk sintaks, nama bawaan pustaka, API eksternal, dan identifier yang diwajibkan sistem lain.

## Keamanan

Jangan memasukkan kredensial, kunci API, token, atau data pribadi ke repo. Rahasia disimpan di GitHub Actions
Secrets dan Cloudflare Worker Secrets. Workflow baru hanya `workflow_dispatch` atau dipicu bot.
