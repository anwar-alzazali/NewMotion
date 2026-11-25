# ADR 0001: Memulai dengan monolit modular

- **Status:** Ditetapkan sebagai arah arsitektur awal
- **Tanggal:** 2026-11-25
- **Konteks:** NewMotion belum memiliki kode aplikasi maupun alur produk yang dikonfirmasi. Proyek sumber merupakan repositori otomatisasi dan produksi media dengan domain yang cukup spesifik.
- **Keputusan:** Mulai dari satu aplikasi yang dibagi menjadi batas domain, aplikasi, infrastruktur, antarmuka, dan pekerja latar belakang. Letakkan integrasi penyedia layanan di balik kontrak adapter. Buat layanan terpisah hanya jika ada kebutuhan terukur terkait skala, isolasi, penerapan, keamanan, atau kepemilikan.
- **Dampak:**
  - Kompleksitas operasional dan jumlah target penerapan lebih rendah pada tahap awal.
  - Batas modul yang jelas memungkinkan pemisahan layanan di kemudian hari tanpa terburu-buru menerapkan microservices.
  - Pilihan persistensi, antrean, runtime, dan framework tetap terbuka sampai kebutuhan produk diketahui.
  - Komunikasi lintas modul menggunakan antarmuka yang eksplisit; hindari keadaan global yang dapat diubah bersama.
- **Tinjau kembali jika:** diperlukan skala atau penerapan mandiri, suatu modul membutuhkan batas keamanan tersendiri, atau kepemilikan tim mengharuskan siklus rilis yang terpisah.
