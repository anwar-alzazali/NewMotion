# Roadmap NewMotion

Prioritas pemilik: **Kisah Islami dulu**. Genre lain (komedi, edukasi/NGOPAI, cerita anak) baru dibuka setelah
beberapa video Kisah Islami lengkap dibuat lewat jalur ini, lulus `periksa.py`, dan disetujui pemilik secara
konsisten — satu video yang kebetulan berhasil belum cukup. Diperbarui 27 Nov 2026.

## Sudah jadi (di main)

- **Bot Mesin KONTEN** di repo ini: ide/naskah → dalil → tinjauan → pratinjau visual → final → statistik.
- **Jalur hibrida:** naskah LLM (skill + validator + pemeriksa naskah terhadap dalil), sutradara LLM dengan
  katalog renderer otomatis, periksa visual (vision) + revisi rencana, narasi ElevenLabs satu permintaan dengan
  intonasi dan jeda, render final bersuara. Model per tahap dan cadangan di `config/model.toml`.
- **Jalur manual tanpa LLM:** JSON lengkap (visual + narasi) dari AI sesi chat atau AI berakses GitHub →
  narasi sekali → render → periksa. Bekal dan prompt siap pakai (`/bekal`, `/prompt`).
- **Renderer:** ±140 benda vektor, tokoh bersendi lima sudut (Lapis A 0 temuan), wajah perempuan santun,
  figuran Arab, tampak samping/belakang utuh, kait kendaraan/kursi, interaksi serah-terima benda, tata letak
  dari ukuran benda, visual konsep abstrak, laut terbelah bergaya ombak Nuh, ciri raja Mesir kuno.
- **Belajar:** revisi pemilik dan naskah final disimpan sebagai pelajaran; pembuat draf komponen renderer;
  antrean kebutuhan renderer; statistik tayang + analisis dengan kekuatan bukti.

## Sekarang

1. **Uji video gabungan pertama** lewat bot (naskah Firaun sudah menunggu di tombol Lanjut): nilai pratinjau
   visual, lalu final bersuara. Ini bukti pertama jalur hibrida dari ujung ke ujung.
2. **Uji jalur manual dengan narasi sungguhan** (satu JSON pendek) untuk memastikan ElevenLabs + penyelarasan
   waktu berjalan di Actions.
3. Perbaiki temuan dari dua uji di atas sebelum menambah fitur.

## Berikutnya (setelah uji video lolos)

- **Studio Alur** (`docs/TUGAS_ANTARMUKA.md`): halaman web alur produksi node per node, pratinjau, edit
  tokoh/figuran per beat. UI-3 dst. dibuka dengan berkas izin setelah uji video lolos.
- Komponen renderer dari naskah nyata berikutnya (`docs/ATURAN_KOMPONEN.md`), termasuk penghalusan
  dinding air runtuh bila diminta.
- Verifikasi dalil opsional untuk jalur manual (membaca `sub` di teks layar).

## Nanti (bersyarat)

- **Genre lain** sebagai paket terpisah di `newmotion/paket_genre/` (fondasi pemisahan genre sudah ada),
  dimulai setelah beberapa video Kisah Islami konsisten.
- Pengisi statistik otomatis dari API Facebook Page (`statistik_video.ambil_dari_facebook`).
- Usulan pedoman dari statistik setelah ±20–30 video tercatat (disetujui pemilik, tidak otomatis).

## Bukan tujuan

- Gambar AI di Kisah Islami (renderer vektor tetap satu-satunya sumber visual).
- Workflow yang berjalan otomatis pada setiap push (kuota Actions).
- Proyek paralel baru sebelum ada bukti video yang konsisten.
