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
- [ ] Alur fitur pertama dibuat dan diuji.

Belum ada runtime aplikasi atau dependensi pihak ketiga yang ditambahkan. Ini disengaja: repositori sumber memiliki alur kerja khusus produksi video yang tidak boleh disalin ke produk dengan domain yang belum dipastikan.

## Dokumentasi

- [Gambaran arsitektur](docs/architecture/overview.md)
- [Peta adaptasi dari mesin-video](docs/architecture/adoption-map.md)
- [ADR 0001 — Monolit modular](docs/decisions/0001-modular-monolith.md)

## Keamanan

Jangan pernah memasukkan kredensial, kunci API, token akses, data pribadi pengguna, hasil produksi, atau berkas konfigurasi lokal ke repositori. Simpan rahasia melalui pengelola rahasia platform dan gunakan contoh data yang sudah disamarkan.
