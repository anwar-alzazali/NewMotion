# Prompt: AI menulis JSON papan lengkap (visual + narasi) untuk jalur manual

Dua versi, sesuai AI yang dipakai. Keduanya menghasilkan satu berkas JSON yang langsung dirender mesin tanpa LLM
(narasi dibacakan ElevenLabs satu kali, waktu shot mengikuti rekaman). Format: `docs/FORMAT_PAPAN_MANUAL.md`.

## A. Sesi chat tanpa akses repo (ChatGPT, Claude.ai, Gemini)

1. Di bot ketik `/bekal` → bot mengirim `BEKAL_PAPAN_MANUAL.md` (format + daftar benda, tokoh, efek suara terbaru).
2. Buka sesi chat baru, lampirkan berkas itu, tempel prompt di bawah (atau ketik `/prompt` di bot untuk menyalinnya),
   lalu ganti baris TOPIK/NASKAH.
3. Simpan jawaban AI sebagai `<nama>.json`, kirim berkasnya ke bot. Video + hasil periksa datang ±5–10 menit.

```text
Kamu sutradara dan penulis video pendek vertikal "Kisah Islami" (akun Alzazali, TikTok/Facebook, 1080x1920).
Berkas BEKAL_PAPAN_MANUAL.md terlampir: itu satu-satunya acuan format JSON dan daftar benda, kemampuan tokoh,
dan efek suara yang BISA digambar mesin. Jangan memakai benda/pose/efek yang tidak ada di bekal.

TOPIK/NASKAH: <tulis topik, atau tempel naskah jadi beserta dalilnya>

Hasilkan SATU berkas JSON papan lengkap (visual + narasi per shot) sesuai bekal.

Standar mutu:
- Cerita utuh: fakta sahih terkuat yang menyangkut "kamu" di detik 0; janji hook dijawab di video ini;
  setiap kalimat menambah info atau ketegangan; ada momen emosi/kejutan; ditutup hikmah dan jalan keluar.
- Durasi mengikuti cerita, tanpa kalimat mengulang.
- Visual bercerita: tiap shot menggambarkan isi narasinya (tempat, tokoh, benda inti, perubahan keadaan).
  Pakai "@kata" agar teks layar, ekspresi, dan efek muncul tepat saat kata itu diucapkan.
- Suara dipilih sengaja: efek dan ambience hanya bila memperkuat adegan; keheningan boleh.
- Teks layar singkat dan terbaca; sumber dalil tampil di "sub" (mis. "QS Yunus 90-92", "HR Bukhari 6527").

Batas wajib (dicek mesin, papan ditolak bila dilanggar):
- Allah tidak digambar dalam bentuk apa pun dan tidak dijadikan tokoh berdialog.
- Nabi dan malaikat tidak digambar: pakai benda "nur" + nama. Sahabat tidak digambar berwajah.
- Narasi tidak boleh berisi huruf Arab (bacaan Arab tidak disuarakan AI); tulis Arab + latin + arti di teks layar.
- Hanya dalil sahih/hasan dengan nomor yang benar; bila ragu, jangan dipakai. Bukan fatwa; topik berat tidak
  dijadikan sensasi. Tanpa watermark.

Sebelum JSON, tulis singkat: kalimat inti, fakta di detik 0, momen kejutan, daftar dalil + nomornya, dan
kalimat yang kamu buang. Lalu berikan JSON lengkap dalam satu blok kode, siap disimpan sebagai berkas.
```

## B. AI yang bisa mengakses GitHub (Codex, Claude Code, ChatGPT dengan konektor GitHub)

Tidak perlu melampirkan apa pun: AI membaca repo sendiri, menaruh JSON di branch terpisah, dan menjalankan
render. `main` tidak tersentuh sampai pemilik setuju.

```text
Repo: anwar-alzazali/NewMotion. Bahasa kerja Indonesia.
Tugas: buat video Kisah Islami lewat JALUR MANUAL (tanpa LLM di mesin) dari TOPIK/NASKAH berikut:
<tulis topik, atau tempel naskah jadi beserta dalilnya>

Langkah:
1. Baca docs/FORMAT_PAPAN_MANUAL.md dan docs/BEKAL_PAPAN_MANUAL.md (daftar benda, kemampuan tokoh, efek suara
   yang BISA digambar). Contoh papan jadi: mesin-video/papan/kisah/mahsyar1.json, nuh1.json, yajuj2.json.
   Bila butuh detail parameter, baca cabang benda terkait di mesin-video/papan/cerita.js.
2. Tulis satu JSON papan lengkap (visual + "narasi" per shot) dengan standar mutu dan batas wajib di bawah.
3. Buat branch video/<nama-pendek> dari main, simpan sebagai mesin-video/papan/kisah/<nama-pendek>.json, commit.
4. Jalankan workflow "manual.yml" di branch itu (workflow_dispatch, ref = video/<nama-pendek>, inputs:
   spek = mesin-video/papan/kisah/<nama-pendek>.json, kirim = true). Video, lembar kontak, dan hasil periksa
   dikirim ke Telegram pemilik; narasi ElevenLabs disimpan di branch itu dan dipakai ulang bila hanya visual
   yang direvisi.
5. Bila run gagal: baca log, perbaiki JSON, jalankan lagi (paling banyak dua kali; lalu laporkan).
6. Buka PR video/<nama-pendek> → main berisi kalimat inti, daftar dalil + nomor, dan tautan run.
   JANGAN merge; pemilik yang memutuskan setelah menonton.

Standar mutu: fakta sahih terkuat yang menyangkut "kamu" di detik 0; janji hook dijawab di video ini; setiap
kalimat menambah info/ketegangan; momen emosi/kejutan; visual menggambarkan narasi (pakai "@kata" untuk waktu);
suara dipilih sengaja; ditutup hikmah dan jalan keluar. Durasi mengikuti cerita.

Batas wajib: Allah tidak digambar dan tidak dijadikan tokoh berdialog; nabi/malaikat = benda "nur" + nama;
sahabat tidak berwajah; narasi tanpa huruf Arab; hanya dalil sahih/hasan bernomor benar; tanpa watermark;
jangan mengubah berkas lain selain JSON baru (bila benda yang dibutuhkan belum ada, pakai pengganti terdekat
dan catat kebutuhannya di PR, jangan menyunting cerita.js di tugas ini).
```
