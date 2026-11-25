# Audit Repository NewMotion

- Repositori: anwar-alzazali/NewMotion
- Cabang: feature/pembuat-karakter-gabungan
- Commit diperiksa: 6b77dae4fb48bef8eca772b997d788d8963a38de
- Tanggal: 25 November 2026
- Metode: audit statis pohon Git, pembacaan kode, konfigurasi, workflow, dan metadata CI. Belum termasuk instalasi bersih atau render E2E.

## 1. Ringkasan eksekutif

NewMotion saat ini menggabungkan dokumentasi fondasi arsitektur dengan implementasi produksi video lama di mesin-video/. Belum ada satu runtime aplikasi NewMotion sebagai entry point resmi. README menyatakan runtime aplikasi dan dependensi pihak ketiga belum ditambahkan. Pada snapshot cabang yang diaudit tidak ditemukan manifest/lock dependensi Python atau Node, .env.example, maupun paket runtime yang menghubungkan domain, application, infrastructure, interfaces, dan runtime.

Meski demikian, mesin-video bukan sekadar rancangan. Terdapat beberapa CLI Python, renderer JavaScript berbasis browser, spesifikasi cerita JSON, aset audio/font, dan workflow render GitHub Actions. Implementasi ini harus dipertahankan dan dibungkus adapter secara bertahap; jangan ditulis ulang atau dipindah massal.

Kesimpulan utama: bangun bootstrap dan CLI NewMotion yang mengorkestrasi entry point lama terlebih dahulu. Jadikan jalur render lama sebagai adapter pertama dan pertahankan kompatibilitas output.

## 2. Cabang dan ruang lingkup

Cabang yang ditemukan:
- main — default branch.
- feature/pembuat-karakter-gabungan — cabang kerja yang diaudit.
- test/yajuj2-visual3-characters — basis PR karakter.
- test/yajuj2-visual-variant — eksperimen visual.
- clone/mesin-video-baseline — baseline salinan mesin-video.
- chore/hybrid-architecture-foundation — cabang fondasi/dokumentasi terpisah.

Pohon cabang fitur yang diaudit berisi 99 entri; basis test/yajuj2-visual3-characters berisi 93 entri. PR karakter #3 menargetkan cabang test/yajuj2-visual3-characters, bukan main. Cabang eksperimen tidak boleh dianggap telah tergabung ke main. Integrasi lintas cabang harus didahului perbandingan commit dan uji regresi.

## 3. Inventaris kondisi aktual

### Implementasi yang sudah ada

| Area | Berkas | Temuan |
|---|---|---|
| Otomatisasi produksi | mesin-video/otomatis.py | CLI Python yang mengorkestrasi sebagian produksi dan memanggil skrip lain sebagai subprocess |
| Rendering papan | mesin-video/papan_buat.py | CLI JSON ke HTML/PNG/MP4; memakai Playwright/Chromium, Pillow/NumPy, FFmpeg |
| Perakitan video | mesin-video/rakit.py | Perakitan media, subtitle, dan audio dengan Pillow/FFmpeg |
| Renderer adegan | mesin-video/papan/cerita.js | Renderer SVG/animasi JavaScript yang berjalan di halaman papan |
| Antarmuka browser | mesin-video/papan/papan.js dan papan.css | Lapisan halaman/browser |
| Arah visual | mesin-video/papan/arah_visual.py dan direktur.py | Modul arahan/penyusunan visual |
| Audio | papan_suara.py, papan_musik.py, efek_suara.py, narasi_api.py | Utilitas dan pipeline audio/narasi |
| Aset | mesin-video/aset/, audio_manual/, papan/font/ | Aset nyata yang dirujuk spesifikasi dan workflow |
| Validasi konten | penjaga_arab.py, penjaga_dalil.py, penjaga_tokoh_suci.py, periksa.py | Pemeriksaan khusus konten yang harus tetap berada pada jalur render |
| Karakter | papan/karakter/tokoh.py dan gerak.py | Renderer karakter Python pada cabang fitur; belum menjadi renderer utama JavaScript |
| Spesifikasi | papan/kisah/*.json dan modul Python terkait | Data cerita dan generator pendukung |

### Entry point yang ada

Entry point saat ini berupa skrip per subsistem, bukan satu aplikasi:
- python mesin-video/papan_buat.py <spec.json> -o <hasil.mp4>
- python mesin-video/otomatis.py ...
- python mesin-video/rakit.py ...
- python mesin-video/narasi_api.py ...
- utilitas lain memiliki blok eksekusi langsung.

Workflow Visual 3 menjalankan papan_buat.py langsung. Jalur ini adalah baseline adapter pertama yang harus dipertahankan.

### Rancangan/dokumentasi, belum runtime

- docs/architecture/overview.md menjelaskan target dan menyatakan runtime/domain belum dikonfirmasi.
- docs/architecture/adoption-map.md adalah peta adaptasi, bukan implementasi migrasi.
- docs/decisions/0001-modular-monolith.md menetapkan arah monolit modular.
- README menyatakan belum ada runtime aplikasi atau dependensi pihak ketiga untuk NewMotion.

### Belum ditemukan pada snapshot

- pyproject.toml, requirements*.txt, poetry.lock, uv.lock, atau manifest/lock Python resmi.
- package.json dan lockfile Node.
- .env.example dan konfigurasi terpusat.
- bootstrap/lifecycle/dependency container/job runner/CLI newmotion.
- paket modular yang benar-benar menghubungkan domain, application, infrastructure, interfaces, runtime.
- suite pengujian terpadu untuk runtime dan render E2E.

## 4. Peta dependensi aktual

Gambaran statis alur yang terlihat dari pemanggilan skrip:

- CLI lama → otomatis.py
- otomatis.py → gambar.py, papan_buat.py, rakit.py
- papan_buat.py → spesifikasi cerita JSON dan modul Python papan
- papan_buat.py → Playwright/Chromium → HTML dengan papan.js dan cerita.js
- papan_buat.py → FFmpeg/ffprobe untuk video dan audio
- audio pipeline → papan_suara.py, papan_musik.py, efek_suara.py
- spesifikasi cerita → aset audio, font, dan gambar
- karakter Python → belum memiliki adapter langsung menuju renderer JavaScript

Diagram ini bukan dependency graph lengkap hasil eksekusi. Paket karakter Python tidak dapat diimpor langsung oleh JavaScript browser; dibutuhkan kontrak data/adapter yang jelas.

## 5. Dependensi dan konfigurasi teramati

### Dependensi yang terlihat
- Python 3; workflow karakter memakai Python 3.11, workflow render belum mematok versi Python.
- Node.js 20 hanya untuk node --check di workflow karakter; belum ada package Node.
- Pillow, NumPy, Playwright, Chromium.
- FFmpeg dan ffprobe.
- DejaVu fonts pada runner Linux.
- OpenCV digunakan pada jalur deteksi wajah tertentu dan perlu dipastikan apakah opsional.
- Inventaris impor lengkap dan uji environment bersih tetap diperlukan sebelum lockfile diputuskan.

Workflow saat ini memasang pillow, numpy, playwright langsung dengan pip, lalu memasang Chromium. Versi paket belum dikunci.

### Variabel environment yang terlihat
- SUPABASE_URL
- SUPABASE_SERVICE_ROLE_KEY
- ELEVENLABS_API_KEY
- ELEVENLABS_VOICE_ID
- ELEVENLABS_MODEL
- Variabel GitHub Actions seperti GITHUB_RUN_ID, GITHUB_SERVER_URL, GITHUB_REPOSITORY.

Daftar ini hanya variabel yang ditemukan pada kode yang dibaca, bukan daftar kebutuhan wajib semua perintah. Doctor/config harus memeriksa kebutuhan per kapabilitas; render dari aset lokal tidak boleh dipaksa memiliki API key eksternal.

### Risiko impor yang belum terpecahkan

mesin-video/papan/direktur.py mengimpor dalil.quran_foundation, tetapi direktori/modul dalil/ tidak terlihat pada pohon cabang kerja. Modul itu mungkin disediakan oleh submodule, paket eksternal, atau jalur lain. Sampai diverifikasi, direktur tidak boleh dianggap dapat diimpor pada environment bersih.

## 6. CI dan pengujian

Workflow yang ditemukan:
- .github/workflows/render-yajuj2.yml
- .github/workflows/render-yajuj2-visual2.yml
- .github/workflows/render-yajuj2-visual3.yml
- .github/workflows/test-karakter.yml

Workflow render memasang dependensi secara ad hoc, menjalankan skrip lama, lalu mencoba mengambil metadata ffprobe dan mengunggah artifact. Workflow Visual 3 terikat pada cabang test/yajuj2-visual3-characters, bukan cabang fitur.

Workflow karakter memeriksa sintaks JS, validitas JSON Visual 3, dan pytest renderer karakter. Run terbaru yang terlihat pada cabang fitur berstatus success, tetapi cakupannya bukan render MP4 end-to-end. Status tersebut tidak membuktikan video/audio/artifact valid. Tes karakter Python saat ini hanya smoke test SVG; belum menguji integrasi Python ke rig JS atau hasil visual gerakan menggali.

## 7. Duplikasi, coupling, dan risiko migrasi

1. Beberapa entry point menjalankan bagian proses yang tumpang tindih. Runtime baru harus menjadi satu pintu masuk tanpa menghapus CLI lama.
2. papan_buat.py mencoba menyelesaikan path dari folder spesifikasi, current working directory, dan folder skrip. Ini dapat memberi hasil berbeda menurut lokasi eksekusi. Runtime perlu menetapkan project root/path context.
3. FFmpeg, ffprobe, dan skrip Python dipanggil dari beberapa modul. Timeout, cancellation, cleanup, dan korelasi log belum dikelola satu lapisan.
4. Dependensi tidak terkunci sehingga hasil instalasi ulang dapat berubah.
5. Variabel environment dibaca langsung di beberapa modul; validasi belum terpusat.
6. JSON adalah batas utama antara Python dan JavaScript. Schema harus diformalkan sebelum adapter karakter/renderer diubah.
7. Impor dalil.quran_foundation perlu ditelusuri.
8. Penjaga Arab, dalil, dan tokoh suci harus tetap aktif di jalur validasi; orkestrasi baru tidak boleh melewatinya.
9. Perubahan path, audio mixing, frame rate, subtitle, dan urutan render dapat mengubah video walau proses exit code 0.
10. Renderer karakter Python dan rig JavaScript adalah dua jalur berbeda; belum boleh disebut generator karakter terpadu sebelum adapter dan tes silang tersedia.

## 8. Struktur runtime yang diusulkan

Mulai dengan modular monolith Python yang membungkus implementasi mesin-video melalui adapter:

    newmotion/
      __init__.py
      __main__.py
      cli.py
      runtime/
        bootstrap.py
        lifecycle.py
        konfigurasi.py
        wadah_dependensi.py
        logging.py
        lingkungan.py
      domain/
        job.py
        status_job.py
        kontrak.py
      application/
        jalankan_job.py
        validasi_job.py
        layanan_render.py
      infrastructure/
        proses/subprocess.py
        render/papan_lama.py
        render/ffmpeg.py
        render/browser.py
        artefak/penyimpanan_lokal.py
      interfaces/cli/perintah.py
    config/
      development.toml
      test.toml
      production.toml
      worker.toml
    tests/
      unit/
      integration/
      e2e/
    docs/
      audit/
      architecture/
    .env.example
    pyproject.toml
    uv.lock (atau satu lockfile Python resmi setelah uji kompatibilitas)

Nama paket/folder final mengikuti standar Bahasa Indonesia README kecuali nama teknis yang diwajibkan tooling. mesin-video/ tetap menjadi implementasi legacy yang dipanggil adapter. Tidak perlu database atau distributed queue pada fondasi awal; job runner lokal dengan status eksplisit dan manifest hasil sudah cukup.

## 9. Rencana implementasi bertahap — belum dieksekusi

### Fase 1 — Audit
- Bekukan baseline commit dan catat entry point/kontrak.
- Inventarisasi impor, environment variables, proses eksternal, dan dependensi secara lengkap.
- Tandai modul yang belum dapat diimpor atau belum punya dependency.
- Siapkan regression fixture dari satu hasil render lama yang diketahui valid.

### Fase 2 — Bootstrap/lifecycle (P0)
1. Tambahkan package newmotion dan entry point python -m newmotion.
2. Bootstrap memuat konfigurasi, validasi environment, logger, dependency container, dan exception handler.
3. Lifecycle eksplisit BOOT → CONFIGURE → INITIALIZE → READY → EXECUTE → SHUTDOWN; cleanup tetap dijalankan saat sukses, exception, atau timeout.
4. Doctor memeriksa Python, Node bila diperlukan, FFmpeg/ffprobe, Playwright/Chromium, font, aset, dan konfigurasi per kapabilitas.
5. Adapter proses lama memakai cwd, timeout, environment allowlist, dan structured logging.
6. Tambahkan .env.example, profil development/test/production/render-worker, dan panduan setup.
7. Pilih versi Python/Node setelah jalur lama diuji di environment bersih; kunci dependency setelah matriks render lulus.

### Fase 3 — CLI dan job lokal (P1)
- Perintah doctor, version, validate, run, render, test.
- Job specification berversi, validasi, state machine, correlation ID, progress, timeout, cancellation, retry terbatas, dan ringkasan.
- Persistensi status/metadata lokal dahulu; jangan menambah queue/database tanpa kebutuhan.

### Fase 4 — Rendering runtime terpadu (P1)
- Pipeline INPUT → VALIDATE → PLAN → BUILD SPEC → RENDER → COMPOSE → VERIFY → PUBLISH.
- Adapter pertama menjalankan papan_buat.py dengan input/output absolut dan project root eksplisit.
- ffprobe memverifikasi video, audio stream, durasi, resolusi, codec, dan ukuran; simpan checksum dan metadata.
- Tambahkan timeout dan cleanup; exit code bukan bukti artifact valid.

### Fase 5 — Karakter dan E2E (P2)
- Tetapkan schema karakter/aksi/pose/properti.
- Buat adapter cerita lama dan rig JS; renderer Python menjadi sumber/alat melalui kontrak yang disepakati, bukan impor langsung di browser.
- Jadikan Yajuj Visual 3 integration/E2E fixture.
- Render potongan pendek deterministik, verifikasi MP4/audio, dan bandingkan frame kunci dengan baseline.

## 10. Daftar file

### Dibuat pada Fase 1
- docs/audit/REPOSITORY_AUDIT.md — laporan ini.

### Direncanakan untuk Fase 2 setelah fondasi disetujui
- pyproject.toml dan satu lockfile Python.
- .env.example.
- newmotion/__init__.py, __main__.py, cli.py.
- newmotion/runtime/{bootstrap.py,lifecycle.py,konfigurasi.py,wadah_dependensi.py,logging.py,lingkungan.py}.
- newmotion/infrastructure/proses/subprocess.py.
- newmotion/infrastructure/render/{papan_lama.py,ffmpeg.py,browser.py}.
- config/{development.toml,test.toml,production.toml,worker.toml}.
- tests/unit/test_lifecycle.py dan tests/integration/test_bootstrap.py.
- docs/architecture/runtime-lifecycle.md dan panduan setup/runtime/doctor.
- README dan workflow CI diperbarui secara terukur.

### Tidak diubah pada fondasi awal
- mesin-video/papan/cerita.js, papan_buat.py, rakit.py, audio pipeline, spesifikasi cerita, dan aset.
- Renderer karakter lama maupun baru sampai kontrak adapter/regression test disepakati.
- Tidak ada pemindahan atau penghapusan massal.

## 11. Gerbang penerimaan

Fondasi runtime siap untuk tahap P1 jika:
- environment bersih dapat dipasang dari manifest/lock resmi;
- python -m newmotion doctor memberi diagnosis akurat;
- satu entry point menjalankan job render lama melalui adapter;
- shutdown berjalan pada sukses, exception, dan timeout;
- job menghasilkan status, log berkorelasi, metadata artifact, dan exit code yang benar;
- MP4 lolos ffprobe serta verifikasi audio stream;
- tes bootstrap/adapter berjalan otomatis;
- render lama dapat direproduksi atau perbedaannya terdokumentasi.

## 12. Hal yang masih perlu dipastikan

- Versi Python minimum/maksimum kompatibel dengan semua skrip.
- Versi Node yang diperlukan oleh browser/runtime; Node 20 saat ini hanya dipakai syntax check.
- Sumber dan pemasangan dalil.quran_foundation.
- Apakah OpenCV wajib atau hanya fitur opsional.
- Daftar lengkap environment variables dan dependensi opsional dari seluruh jalur produksi.
- Artifact MP4 baseline untuk pembanding audio/visual.
- Kontrak produk NewMotion di luar pipeline video.

---
Audit ini tidak menyatakan NewMotion telah memenuhi Definition of Done. Belum dilakukan instalasi environment bersih, eksekusi runtime/doctor, render MP4 pada commit audit, atau E2E audio-video.


## 13. Tindak lanjut setelah persetujuan fondasi runtime

Bagian audit awal di atas merekam kondisi sebelum implementasi runtime. Setelah struktur runtime disetujui, fondasi tahap awal ditambahkan pada branch kerja:

- `pyproject.toml`: metadata paket, target Python 3.11+, entry point CLI, serta ekstra opsional `uji` dan `render`.
- `newmotion/`: paket runtime, konfigurasi TOML, lifecycle, logging, pemeriksaan lingkungan, pelaksana subprocess, adapter renderer papan lama, dan CLI.
- `config/`: profil development, test, production, dan worker.
- `tests/test_runtime.py`: tes konfigurasi, pemeriksaan lingkungan, hasil proses, dan timeout.
- `.github/workflows/test-runtime.yml`: workflow uji paket dan CLI.
- `.env.example` dan `docs/runtime/FOUNDATION.md`: panduan konfigurasi dan penggunaan.

### Status verifikasi

- Berkas implementasi telah ditulis ke branch dan diperiksa ulang melalui pembacaan GitHub.
- Format profil TOML dan fixture pengujian diperbaiki setelah pemeriksaan isi.
- Eksekusi pytest, instalasi bersih, serta workflow CI untuk commit terbaru belum dikonfirmasi dalam audit tindak lanjut ini.
- Tidak ada klaim bahwa render MP4 end-to-end sudah berhasil.
- Ekstra `render` masih inventaris awal: belum menggantikan inventaris impor lengkap seluruh skrip `mesin-video/`, belum menyediakan lockfile, dan belum mengatasi dependensi `dalil.quran_foundation` yang hilang pada audit awal.

Tahap ini adalah fondasi bootstrap dan adapter pertama, bukan penyelesaian seluruh P0/P1. Kontrak job, validasi job, orkestrasi lifecycle job, penyimpanan artefak, pipeline render terpadu, retry/cancellation, correlation ID, serta bukti render E2E tetap menjadi pekerjaan lanjutan.
