# Audit format waktu dan audio renderer lama

Tanggal: 28 November 2026  
Cabang audit: `renderer/pembangunan-ulang`  
Terkait: RND-001  
Status: audit sumber lanjutan; belum ada render baseline.

## Tujuan

Memetakan perilaku aktual format papan lama sebelum nama field dan skema kontrak RND-002 ditetapkan. Audit ini membaca implementasi Python dan JavaScript; tidak mengubah runtime.

## Sumber yang diperiksa

- `mesin-video/papan_buat.py`: `pasang_waktu`, `durasi_audio`, `campur_rekaman`, `buat_html`, dan `main`.
- `mesin-video/papan/papan.js`: pengumpulan SFX, kalkulasi `window.__durasi`, dan `window.setT`.
- `mesin-video/papan/cerita.js`: pengurutan shot, penentuan `akhir`, serta evaluasi adegan pada waktu global.
- `mesin-video/papan_suara.py`: pembuatan dan pencampuran efek suara sintetis.
- `mesin-video/papan_musik.py`: pembangkitan musik berdasarkan durasi.

## Fakta terverifikasi

### 1. Satuan waktu dan konversi kata

- Nilai waktu pada papan dinyatakan dalam detik.
- `pasang_waktu()` mengubah penanda seperti `@kata` menjadi waktu awal kata dari berkas `.waktu.json`.
- Pada `cerita.shot`, `shot.at` diperlakukan sebagai waktu absolut. Properti lain di dalam shot dikonversi dengan offset awal shot, sehingga nilai waktunya relatif terhadap awal shot.
- Untuk `adegan`, `adegan.at` juga absolut dan `adegan.isi` relatif terhadap awal adegan.
- Konversi tersebut dilakukan dengan mengurangi offset dari nilai hasil pencarian kata. Ini berarti format internal setelah konversi memiliki konvensi absolut untuk awal shot/adegan dan relatif untuk isi di dalamnya.

### 2. Durasi total video

Urutan penentuan durasi di `papan_buat.py`:

1. Argumen CLI `-d` mengalahkan durasi yang dihitung halaman.
2. Jika `spec.durasi` tersedia, `papan.js` memakai nilai itu sebagai `window.__durasi`.
3. Jika ada `spec.suara` dan `spec.durasi` belum diisi, Python mengisi `spec.durasi` dari durasi berkas narasi + `spec.ekor_suara` (bawaan 1,2 detik).
4. Jika tidak ada durasi eksplisit, `papan.js` menghitung durasi dari timestamp maksimum item, adegan, subtitle, dan SFX, lalu menambahkan `spec.ekor` (bawaan 3,2 detik), dibulatkan ke 0,1 detik.

Rumus JavaScript yang ditemukan:
`max(0, item.at, adegan.at + 1, subtitle.t1, SFX.at) + (SPEC.ekor || 3.2)`.

**Temuan risiko kontrak:** kalkulasi `window.__durasi` di `papan.js` tidak memasukkan `SPEC.cerita.shot[].at` secara langsung. Dengan demikian, timestamp shot cerita saja tidak memperpanjang durasi video. Jika papan tidak menetapkan `durasi` dan tidak memiliki item/subtitle/SFX lain yang mencapai waktu tersebut, shot yang berada setelah batas durasi hasil kalkulasi berisiko tidak pernah dirender. Ini adalah ketidaksesuaian lintas-lapisan yang perlu direproduksi pada fixture; belum dinyatakan sebagai kegagalan produksi tanpa bukti render.

Di `cerita.js`, shot diurutkan berdasarkan `at`; `akhir` tiap shot ditetapkan ke `at` shot berikutnya. Shot terakhir mendapat batas sentinel `1e9`, bukan durasi final video. Jadi durasi akhir dikendalikan oleh papan/orkestrasi, bukan oleh daftar shot itu sendiri.

### 3. Narasi, musik, dan efek suara

- Narasi dimuat sebagai audio utama. Saat dicampur dengan efek atau musik, jalur ffmpeg memakai `apad` dan memotong hasil akhir dengan `atrim=0:dur`.
- Musik dibuat sepanjang durasi target; pada jalur narasi + musik, musik dikecilkan otomatis (*sidechain compression/ducking*) mengikuti narasi.
- SFX sintetis dikumpulkan menjadi event `[detik, jenis, volume]`. Event berasal dari animasi masuk, efek visual, peta, dan `SPEC.efek_suara`.
- `papan_suara.campur()` membuat buffer sepanjang `durasi + 1` detik dan menempatkan tiap efek pada offset detik yang diberikan. Event yang offset-nya di luar buffer tidak ditambahkan. Fungsi ini tidak melakukan validasi semantik bahwa event harus berada dalam rentang video.
- `volume_efek` dan `volume_musik` mengatur level bus pada proses muxing. Nilai default yang tampak pada jalur narasi + musik adalah 0,45 dan 0,2.
- `rekaman` adalah jalur audio eksternal terpisah: tiap entri memakai `berkas`, `at`, `vol`, opsional `sampai`, `ulang`, `masuk`, `keluar`, dan `gain_db`. Posisi `at` diterapkan sebagai penundaan milidetik. Bila `sampai` ada, panjang potongan dihitung dari `sampai - at`; bila berulang tanpa `sampai`, panjangnya mengikuti sisa durasi video.
- Pencampuran `rekaman` memotong trek hasil ke durasi video.
- `ekor_suara` dan `ekor` adalah dua field berbeda dengan fungsi berbeda: yang pertama memperpanjang durasi turunan dari narasi; yang kedua menjadi ekor umum pada kalkulasi durasi JavaScript.

## Ketidaksesuaian dan risiko yang perlu dibawa ke RND-002

1. **Durasi vs shot cerita:** kalkulasi durasi global tidak membaca `cerita.shot[].at`. Perlu fixture yang hanya berisi shot dengan timestamp jauh dari nol untuk memastikan hasil aktual dan menguji perlunya aturan durasi eksplisit.
2. **Batas shot terakhir:** shot terakhir tidak memiliki durasi eksplisit pada struktur yang dibaca `cerita.js`; ia tetap aktif sampai batas sentinel. Durasi video menghentikan sampling.
3. **Dua field ekor:** `ekor` dan `ekor_suara` tidak boleh disatukan atau diberi nama baru sebelum kompatibilitas seluruh papan lama diperiksa.
4. **Cue audio di luar durasi:** jalur SFX sintetis tidak menunjukkan validasi rentang event; beberapa jalur muxing memotong audio ke durasi final. Validator baru perlu menolak atau memberi peringatan eksplisit untuk cue yang melewati durasi.
5. **Waktu absolut dan relatif bercampur secara sengaja:** shot/adegan dimulai pada waktu absolut, sedangkan keyframe/isi relatif terhadap awalnya. Kontrak baru harus menyebutkan ini tanpa ambiguitas.
6. **Narasi sebagai sumber durasi:** jika durasi tidak ditetapkan, panjang audio narasi + ekor menjadi dasar. Jika durasi eksplisit lebih pendek dari narasi, jalur muxing memotong hasil ke durasi eksplisit.

## Hal yang belum dibuktikan

- Belum ada fixture terisolasi yang membuktikan dampak shot cerita yang berada di luar durasi turunan.
- Belum diperiksa semua contoh JSON lama untuk mengetahui variasi pemakaian `durasi`, `ekor`, `ekor_suara`, `rekaman`, `suara`, dan `musik`.
- Belum ada pengukuran offset narasi-video, sinkronisasi SFX, atau durasi hasil MP4 dari GitHub Actions pada cabang ini.
- Belum diketahui apakah seluruh jalur pemanggil eksternal mengisi `durasi` sebelum renderer dipanggil.

## Rekomendasi tindak lanjut

1. Pertahankan nama field lama sebagai fakta kompatibilitas; jangan mengganti skema sekarang.
2. Tambahkan fixture reproduksi minimal untuk kasus shot cerita terlambat tanpa item lain dan kasus cue audio melewati durasi.
3. Periksa contoh JSON lama secara menyeluruh untuk matriks penggunaan field.
4. Jalankan workflow baseline renderer dari GitHub Actions dan simpan MP4, frame, laporan, waktu render, serta bukti Telegram.
5. Setelah baseline tersedia dan RND-001 ditinjau pemilik, tetapkan skema waktu/audio RND-002 berdasarkan bukti di atas.

## Dampak pada status tugas

RND-001 tetap **BERJALAN**. Audit sumber waktu/audio ini menambah bukti dan daftar reproduksi, tetapi tidak menggantikan baseline visual dari Actions. Tidak ada runtime yang diubah dan tidak ada render/CI/Telegram yang dijalankan dalam sesi ini.
