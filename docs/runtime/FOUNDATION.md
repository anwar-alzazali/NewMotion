# Fondasi Runtime NewMotion

## Status

Fondasi awal runtime ditambahkan sebagai lapisan orkestrasi di atas implementasi lama. Kode pada `mesin-video/` tidak dipindah, dihapus, atau ditulis ulang.

## Komponen saat ini

- `newmotion.cli`: perintah `doctor` dan `render`.
- `newmotion.runtime.konfigurasi`: profil TOML dan override variabel lingkungan.
- `newmotion.runtime.lifecycle`: inisialisasi dan penghentian runtime.
- `newmotion.runtime.logging`: format logging terpusat.
- `newmotion.runtime.lingkungan`: pemeriksaan alat eksternal dan modul render.
- `newmotion.infrastructure.proses.subprocess`: pelaksana proses dengan timeout dan hasil terstruktur.
- `newmotion.infrastructure.render.papan_lama`: adapter ke `mesin-video/papan_buat.py`.

## Instalasi dan penggunaan

Persyaratan dasar: Python 3.11+.

```bash
python -m pip install -e '.[uji]'
newmotion --version
newmotion doctor
```

Untuk jalur renderer papan, pasang ekstra opsional dan siapkan browser Playwright serta FFmpeg/FFprobe pada sistem:

```bash
python -m pip install -e '.[render]'
python -m playwright install chromium
newmotion render mesin-video/papan/kisah/yajuj2_visual3.json -o yajuj2_visual3.mp4
```

Perintah render adalah adapter kompatibilitas. Belum ada kontrak job/domain, antrean, penyimpanan artefak terpadu, atau jaminan render E2E.

## Konfigurasi

Profil tersedia pada `config/development.toml`, `test.toml`, `production.toml`, dan `worker.toml`.

Override:
- `NEWMOTION_PROFILE`
- `NEWMOTION_ROOT`
- `NEWMOTION_OUTPUT_DIR`
- `NEWMOTION_LOG_LEVEL`
- `NEWMOTION_SUBPROCESS_TIMEOUT`

Integrasi lama dapat memakai variabel seperti Supabase, ElevenLabs, dan Cloudflare. Contoh nama variabel tersedia di `.env.example`; rahasia harus diberikan melalui secret manager atau lingkungan eksekusi, bukan disimpan di Git.

## Batasan yang diketahui

1. Daftar ekstra `render` adalah inventaris awal, bukan manifest lengkap semua impor transitif `mesin-video`.
2. Playwright memerlukan instalasi browser terpisah; FFmpeg/FFprobe adalah dependensi sistem.
3. Adapter saat ini meneruskan stdout/stderr dan kode keluar. Pelacakan job, pembatalan, retry, dan cleanup terstandar belum diterapkan.
4. Path konfigurasi ditentukan dari akar proyek saat ini; pemilihan akar eksplisit dapat dilakukan melalui `NEWMOTION_ROOT`.
5. Modul `dalil.quran_foundation` yang terdeteksi pada audit masih perlu diselesaikan sebelum seluruh jalur direktur dinyatakan siap.

## Tahap berikutnya

1. Lengkapi inventaris dependensi Python dan Node serta uji instalasi bersih.
2. Tetapkan lockfile dan versi runtime yang konsisten untuk CI.
3. Tambahkan kontrak job, validasi input, status lifecycle, dan correlation ID.
4. Tambahkan layanan render terpadu, adapter FFmpeg/browser, serta penyimpanan artefak.
5. Tambahkan tes integrasi dan render E2E dengan artefak bukti.
