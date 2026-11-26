# Laporan pengarah subjek naratif — PR #28

Tanggal pengukuran: 26 November 2026. Baseline dihitung ulang dari `main` pada CI yang sama dengan pengujian branch PR. Alat ukur `newmotion/application/ukur_kedalaman.py` tidak diubah.

## Hasil empat tolok ukur

Skor gabungan dan aspek cerita memakai patokan median empat papan buatan tangan. Semua aspek lain juga dibandingkan untuk memastikan tidak ada penurunan.

| Cerita | Gabungan sebelum | Gabungan sesudah | Cerita sebelum | Cerita sesudah |
|---|---:|---:|---:|---:|
| Nuh 1 | 79 | 87 | 74 | 100 |
| Mahsyar 1 | 66 | 82 | 36 | 74 |
| Ya'juj 1 | 60 | 84 | 21 | 100 |
| Ya'juj 2 | 60 | 85 | 18 | 100 |

**Target tercapai:** seluruh empat cerita mencapai skor gabungan minimal 80 dan aspek cerita minimal 70.

### Pemeriksaan aspek lain

| Cerita | Ritme | Kamera | Lingkungan | Benda | Tokoh | Teks layar | Gerak |
|---|---:|---:|---:|---:|---:|---:|---:|
| Nuh 1 sebelum → sesudah | 80 → 80 | 50 → 50 | 100 → 100 | 77 → 83 | 100 → 100 | 0 → 10 | 100 → 100 |
| Mahsyar 1 sebelum → sesudah | 97 → 97 | 63 → 100 | 86 → 89 | 51 → 55 | 100 → 100 | 0 → 12 | 100 → 100 |
| Ya'juj 1 sebelum → sesudah | 63 → 63 | 50 → 50 | 97 → 97 | 60 → 74 | 100 → 100 | 0 → 0 | 100 → 100 |
| Ya'juj 2 sebelum → sesudah | 74 → 74 | 50 → 50 | 97 → 97 | 60 → 74 | 100 → 100 | 0 → 0 | 100 → 100 |

Tidak ada aspek yang turun. Peningkatan terbesar berasal dari kesesuaian subjek dengan narasi, keragaman jenis benda pelaku, dan keragaman komposisi. Skor teks layar tetap 0 pada Ya'juj karena narasi tolok ukur tidak menghasilkan angka/kata kunci yang memenuhi aturan overlay saat ini.

## Cerita uji tambahan

Tiga cerita ini memakai narasi asli dari repo mesin-video. Skornya dihitung dengan patokan median empat referensi yang sama; tidak ada skor pembanding papan tangan untuk cerita tambahan, sehingga angka ini adalah skor mesin relatif terhadap patokan, bukan kemiripan langsung dengan papan cerita tersebut.

| Cerita tambahan | Sumber narasi | Gabungan sebelum | Gabungan sesudah | Cerita sebelum | Cerita sesudah |
|---|---|---:|---:|---:|---:|
| Nuh 2 | `papan/kisah/nuh2_naskah.py` | 77 | 88 | 63 | 99 |
| Dabbah 2 | `papan/kisah/dabbah2_naskah.py` | 70 | 73 | 52 | 59 |
| Kubur 1 | `naskah/kubur1.txt` | 75 | 84 | 70 | 100 |

Ketiganya meningkat, sehingga peningkatan tidak terbatas pada empat cerita tolok ukur. Dabbah 2 masih paling lemah: naskah sumber secara eksplisit menyatakan tidak ada rincian sahih tentang wujud Dabbatul Ard, jadi pengarah sengaja tidak mengarang bentuk makhluk tersebut. Skor yang tersisa bukan alasan untuk menggambar wujud yang tidak memiliki dasar.

**Catatan proses holdout:** pemilihan tiga cerita tambahan dilakukan saat tahap eksplorasi awal setelah prototipe pertama mulai dibuat, bukan dipraregistrasi sebelum commit pertama. Karena itu hasil ini merupakan pemeriksaan generalisasi yang berguna, tetapi tidak sepenuhnya memenuhi urutan holdout buta yang diminta. Pada iterasi berikutnya, cerita tambahan baru harus dipilih dan dibekukan sebelum perubahan aturan dimulai.

## Shot yang masih tidak menggambarkan narasi

### Empat tolok ukur
Pada hasil akhir `newmotion ukur`, tidak ada lagi shot tolok ukur yang tercatat memiliki benda narasi yang hilang dari shot.

### Cerita tambahan
- **Dabbah 2, shot 6–8:** narasi tentang matahari terbit dari barat dan Dajjal masih memiliki ketidakcocokan yang ditandai alat ukur pada kategori api/neraka/bara dan matahari. Wujud Dabbatul Ard tidak dibuat karena naskah tidak menyediakan rincian sahih.
- **Nuh 2, shot 0:** frasa ombak dan gunung belum seluruhnya terpetakan sebagai benda di shot tersebut.
- **Nuh 2, shot 1:** kapal belum ikut hadir pada shot pecahan kedua dari adegan yang sama. Ini menunjukkan konteks entitas antar-segmen dalam satu adegan masih perlu dipertahankan.
- **Kubur 1:** tidak ada shot tersisa yang ditandai alat ukur sebagai benda narasi yang hilang.

## Pengujian dan batasan

- `pytest`: lulus, seluruh 302 tes pada run terakhir.
- `node --test` di `bot/`: 12 lulus, 0 gagal.
- Uji adab tokoh: 18 lulus, 0 gagal.
- `newmotion ukur`: lulus dan dijalankan pada CI.
- `ukur_kedalaman.py`: tidak diubah; leksikonnya tidak diimpor atau digunakan oleh pengarah.
- Tidak ada LLM saat runtime.
- Tidak ada jenis benda renderer baru; semua jenis yang dipakai sudah ada di `mesin-video/papan/cerita.js`.
- Workflow render tetap manual. Pratinjau tidak dibuat karena akses yang tersedia pada sesi ini tidak menyediakan pemicu `workflow_dispatch`; tidak ada workflow render yang dijalankan.
- Belum dilakukan audit visual frame-by-frame. Skor otomatis bukan bukti bahwa blocking, perspektif, dan gerak sudah artistik benar.

## Kesimpulan

Keempat tolok ukur memenuhi ambang skor yang ditentukan dan tidak ada aspek lain yang turun. Tiga cerita tambahan juga meningkat, tetapi masih menyisakan kasus yang belum tergambar. PR tetap Draft sampai pemeriksaan visual manual dilakukan dan catatan holdout ditinjau.
