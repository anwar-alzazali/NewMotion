# NewMotion

NewMotion disiapkan sebagai fondasi aplikasi yang rapi, dengan batas domain yang jelas dan tidak mengunci pilihan teknologi terlalu dini.

## Arah arsitektur

Mulai dengan **monolit modular**: pisahkan tanggung jawab domain, alur aplikasi, infrastruktur, dan antarmuka. Semua integrasi eksternal dibuat agar bisa diganti tanpa mengubah aturan inti aplikasi. Pecah menjadi layanan terpisah hanya jika kebutuhan skala, penerapan, keamanan, atau kepemilikan memang mengharuskannya.

## Ketentuan bahasa dan penamaan

**Bahasa Indonesia adalah standar utama proyek ini, mengikuti gaya penulisan `mesin-video`.** Nama variabel, konstanta, fungsi, metode, kelas, modul, serta komentar dan docstring wajib menggunakan bahasa Indonesia yang jelas dan konsisten. Nama folder dan berkas juga gunakan bahasa Indonesia jika tidak berbenturan dengan kebiasaan alat atau kontrak teknis yang sudah ada.

Pengecualian hanya untuk sintaks bahasa pemrograman, nama bawaan framework atau pustaka, API eksternal, protokol, serta identifier yang memang diwajibkan sistem terkait. Jangan menerjemahkan identifier eksternal yang harus persis.

Contoh:

```python
def buat_video(naskah, folder_hasil):
    """Membuat video berdasarkan naskah dan menyimpan hasilnya."""
    durasi_video = hitung_durasi(naskah)
    return durasi_video
```

Dokumentasi, pesan internal pengembang, panduan penggunaan, dan komentar konfigurasi juga ditulis dalam bahasa Indonesia. Istilah teknis boleh dipertahankan jika lebih tepat, tetapi penjelasannya tetap berbahasa Indonesia.

## Status saat ini

- [x] Struktur awal repositori diperiksa.
- [x] Batas arsitektur dan arah adaptasi awal didokumentasikan.
- [ ] Domain produk dan alur utama pengguna dikonfirmasi.
- [ ] Bahasa pemrograman, runtime, dan target penerapan dipilih.
- [x] Runtime bootstrap, konfigurasi profil, lifecycle, logging, CLI, kontrak job, validasi masukan, orkestrasi job lokal, dan adapter renderer lama ditambahkan.
- [ ] Inventaris dependensi lengkap, lockfile, dan instalasi bersih diverifikasi.
- [ ] Orkestrasi job, kontrak domain, dan pipeline render terpadu diselesaikan.

Fondasi runtime NewMotion kini tersedia pada branch kerja: paket Python `newmotion`, konfigurasi profil TOML, CLI, pemeriksaan lingkungan, kontrak dan orkestrasi job render lokal, serta adapter ke renderer lama. Dependensi renderer lama masih dipisahkan sebagai ekstra opsional dan belum dikunci sampai audit impor serta uji instalasi bersih selesai. Implementasi `mesin-video/` tetap dipertahankan.

## Menjalankan runtime

Gunakan Python 3.11 atau lebih baru:

```bash
python -m pip install -e '.[uji]'
newmotion --version
newmotion doctor
newmotion render mesin-video/papan/kisah/yajuj2_visual3.json -o yajuj2_visual3.mp4
```

Ekstra `render` menyediakan pustaka Python yang telah teridentifikasi pada jalur papan, tetapi pemasangan browser Playwright dan FFmpeg sistem tetap perlu disiapkan sesuai lingkungan. Perintah `render` meneruskan pekerjaan ke `mesin-video/papan_buat.py`; ini adapter kompatibilitas, belum pipeline job terpadu.

## Dokumentasi

- [Gambaran arsitektur](docs/architecture/overview.md)
- [Peta adaptasi dari mesin-video](docs/architecture/adoption-map.md)
- [Pemisahan inti dan paket genre](docs/architecture/pemisahan-genre.md)
- [ADR 0001 — Monolit modular](docs/decisions/0001-modular-monolith.md)

## Keamanan

Jangan pernah memasukkan kredensial, kunci API, token akses, data pribadi pengguna, hasil produksi, atau berkas konfigurasi lokal ke repositori. Simpan rahasia melalui pengelola rahasia platform dan gunakan contoh data yang sudah disamarkan.
