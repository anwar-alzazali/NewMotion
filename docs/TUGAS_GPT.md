# Tugas untuk sesi AI pengerja (ChatGPT/Codex) — NewMotion

Pemilik: Anwar Alzazali. Bahasa kerja: Indonesia. Pengaudit: Claude. Diperbarui 27 Nov 2026.

## Status

**Tugas 1–9 selesai dan sudah di main** (spesifikasinya: `docs/arsip/tugas_gpt_selesai.md`; hasilnya:
`docs/log_kerja/`). Belum ada tugas baru di daftar. Pekerjaan yang boleh diambil tanpa menunggu:

1. **Permintaan komponen dari naskah pemilik** (pemilik menempel naskah): ikuti `docs/ATURAN_KOMPONEN.md`.
2. **Studio Alur** (`docs/TUGAS_ANTARMUKA.md`): UI-1 dan UI-2 boleh; UI-3 dst. menunggu berkas izin
   `docs/log_kerja/*izin-ui-3*.md` dari pemilik/Claude (setelah uji video lolos).

Bila tidak ada keduanya, berhenti dan tulis di log bahwa daftar kosong. Jangan mengarang tugas sendiri.

## Daftar tugas

(kosong — tugas baru ditambahkan di sini oleh pemilik/Claude dengan format: judul, tujuan, "Selesai bila:")

## Protokol setiap sesi (WAJIB; ingatan sesi pendek)

1. Baca berkas ini sampai habis, lalu berkas terbaru di `docs/log_kerja/` (urut nama). Jangan mengulang
   pekerjaan yang sudah tercatat selesai; jangan mendesain ulang keputusan di log kecuali log menyatakan masalah.
2. **Cabang kerja = `gpt/integrasi`** (disamakan dengan `main` setiap kali Claude menggabungkan). Satu tugas =
   satu branch `tugas-<nomor>-<ringkas>` dari `gpt/integrasi` terbaru = satu PR ke `gpt/integrasi`.
   Tidak membuat PR ke `main` (bot produksi ter-deploy otomatis dari `main`).
3. **Uji lewat CI.** Push ke branch `tugas-*` menjalankan `test-runtime.yml`: sintaks, ruff (hanya galat
   baru yang menggagalkan), ukur ulang benda + bekal papan manual (di-commit balik ke branch-mu: tarik dulu
   sebelum push lagi), pytest, uji bot, uji tokoh Lapis A (wajib 0 temuan). Lembar bukti ada di artefak run.
4. **Jangan menunggu audit.** CI hijau → merge sendiri ke `gpt/integrasi`, centang tugas, lanjut.
   Pengecualian: PR berlabel `komponen-draf` (gambar harus dilihat manusia) tidak di-merge sendiri.
5. Akhir sesi: tulis **berkas log baru** `docs/log_kerja/YYYY-MM-DD-HHMM-tugas-N.md` (tanggal, tugas, PR,
   keputusan, langkah berikut yang persis). Jangan menambah baris di berkas log orang lain (bentrok).
6. **Batas macet:** satu masalah gagal dua kali dengan cara berbeda → tulis `MACET:` di log, lanjut bagian lain.
7. **Jangan audit diri berulang.** Satu putaran periksa + CI hijau = cukup. Keraguan dicatat sebagai
   "catatan untuk audit". Jangan menambah workflow baru untuk menguji; tambahkan langkah di `test-runtime.yml`
   atau uji pytest.

## Batas wajib (semua tugas)

- **Adab:** Allah tidak digambar dalam bentuk apa pun. Nabi/rasul = cahaya `nur`, malaikat = cahaya,
  sahabat = bertubuh berwajah cahaya. Manusia biasa lewat boneka/figuran (bukan benda bersosok manusia).
  Penjaga `newmotion/paket_genre/kisah_islami/penjaga_tokoh.py` tidak boleh dilemahkan.
- **Tanpa biaya diam-diam:** uji tidak memanggil LLM/ElevenLabs/layanan berbayar sungguhan (pakai http dan
  TTS palsu; `tests/conftest.py` memaksa sutradara mode aturan, jangan dihapus).
- **Workflow baru** hanya `workflow_dispatch` atau dipicu bot; tidak boleh `on: push`/`pull_request` tanpa filter.
- **Video lama tidak berubah:** kemampuan baru = kunci/opsi baru, bawaan lama tetap
  (`tests/test_referensi_kisah.py`).
- **Tanpa gambar AI** di renderer Kisah Islami; semua vektor di `mesin-video/papan/cerita.js`.
- Tidak menulis rahasia/token. Tidak menghapus fitur tanpa alasan tertulis di PR.

## Peta sistem (agar tidak menebak)

| Bagian | Berkas |
|---|---|
| Renderer | `mesin-video/papan/cerita.js` (`benda()`, `boneka()`, `rangka()`, `KAIT`), pembungkus `mesin-video/papan_buat.py` (`--pratinjau 1,2` = PNG cepat) |
| Katalog otomatis dari kode | `newmotion/application/katalog_renderer.py`, `kemampuan_tokoh.py` (pose, aksi, hadap, kait, penutup kepala, suku), `katalog_suara.py` |
| Ukuran & tata letak | `mesin-video/papan/ukur_benda.py` → `newmotion/application/data/ukuran_benda.json`; `tata_letak.py` |
| Uji tokoh / lembar benda | `mesin-video/papan/uji_tokoh.py`, `mesin-video/papan/lembar_semua_benda.py`, workflow manual `uji-renderer.yml` |
| LLM bersama | `newmotion/infrastructure/llm.py` (`panggil(tahap, ...)`), model per tahap `config/model.toml` |
| Jalur hibrida (LLM) | naskah `application/antrean_naskah.py` (+ `pemeriksa_naskah.py`, `pelajaran_naskah.py`), dalil `paket_genre/kisah_islami/dalil/`, sutradara `sutradara_llm.py` + `rencana_sutradara.py`, periksa visual `periksa_visual.py`, produksi `sutradara_hibrida.py`, `narasi_final.py`, `application/produksi_final.py` |
| Jalur manual (tanpa LLM) | `application/jalur_manual.py`, workflow `manual.yml`, format `docs/FORMAT_PAPAN_MANUAL.md`, bekal `docs/BEKAL_PAPAN_MANUAL.md` |
| Pembuat komponen | `application/pembuat_komponen.py`, `penerbit_komponen.py`, `kebutuhan_renderer.py`, aturan `docs/ATURAN_KOMPONEN.md` |
| Statistik | `application/statistik_video.py` (ciri + analisis), data di `antrean/<id>/statistik.json` |
| Bot | `bot/worker.js` (Cloudflare Worker `mesin-konten`, deploy otomatis dari main); antrean di `antrean/<id>/` |
| Skill LLM | `newmotion/paket_genre/kisah_islami/skill/*.md` |
