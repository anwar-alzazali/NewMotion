# Tahap 10 — Audit dan penguatan kamera serta lingkungan

## Tujuan

Memastikan keluaran kamera dan lingkungan memakai kemampuan nyata renderer
`mesin-video/papan/cerita.js`, bukan field spekulatif. Tahap ini menambah kontrak
metadata eksplisit dan profil framing dasar deterministik. Tahap ini belum mengklaim
kamera sinematik otomatis atau pemahaman atmosfer bebas dari naskah.

## Bukti kemampuan renderer

Audit dilakukan pada `anwar-alzazali/mesin-video:papan/cerita.js` dan empat JSON
referensi. Renderer membaca kamera `x`, `y`, `z`, `hentak`, dan `guncang`.
Nilai `x/y/z` dapat berupa angka atau keyframe; `hentak/guncang` adalah daftar
kejadian bertimestamp relatif terhadap awal shot.

Lingkungan yang dibaca renderer mencakup:
- `palet`, `langit`, `malam`, dan `horizon`;
- `matahari`, `debu`, `hujan`, dan `panas`;
- `naungan`, `kerumunan`, `retak`, dan `resap`;
- `ruang`, yang memilih tata ruang seperti tamu, dapur, kampung, kamar, kantor,
  rumah sakit, mobil, studio, penjara, istana, atau teras.

### Pola pada JSON referensi

| Referensi | Shot | Kamera z keyframe | Efek kamera | Lingkungan yang menonjol |
|---|---:|---:|---|---|
| Nuh | 15 | 15/15 | guncang pada 3 shot | palet pada 6 shot, hujan pada 10 shot |
| Mahsyar | 12 | 12/12 | tidak ada hentak/guncang pada sampel | panas 6, matahari 4, kerumunan 5, naungan 2, retak/resap |
| Ya'juj 1 | 20 | 20/20 | hentak 3, guncang 1 | ruang 2, palet 3 |
| Ya'juj 2 | 20 | 20/20 | hentak 3, guncang 1 | palet 3 |

Angka ini adalah hasil inspeksi file referensi, bukan kuota untuk ditiru. Setiap
properti tetap harus punya alasan cerita.

## Perubahan Tahap 10

1. Profil kamera dasar dibedakan menurut tujuan shot:
   - lokomosi: framing lebar;
   - interaksi: framing menengah;
   - jatuh/tergelincir: framing aksi lebih dekat;
   - peristiwa umum: framing menengah/lebar.
2. Metadata `kamera` dapat diberikan pada level naskah atau adegan. Metadata adegan
   mengoverride nilai global.
3. Metadata `lingkungan` dapat diberikan pada level naskah atau adegan. Metadata
   adegan mengoverride kunci global yang sama.
4. Hanya kunci yang diketahui renderer yang diteruskan. Palet dan jenis ruang yang
   tidak dikenal ditolak.
5. Jika konteks lingkungan tidak dinyatakan, pengarah tidak menciptakan palet,
   cuaca, kerumunan, atau ruang tertentu.
6. Dasar kamera dan lingkungan dicatat pada `shot.pengarahan` untuk audit.

## Batas yang masih terbuka

- Posisi kamera x/y belum mengikuti lintasan aktual aktor secara otomatis.
- Kamera belum memiliki pemilihan shot/reverse-shot atau komposisi multi-subjek
  berdasarkan jarak dan relasi blocking.
- Pengarah belum menyimpulkan lokasi, waktu, cuaca, dan atmosfer dari narasi bebas.
  Tahap ini hanya meneruskan metadata eksplisit agar tidak mengarang.
- Katalog benda/lingkungan yang luas dan relasi kontinuitasnya belum dibangun.
- Belum ada uji render; seluruh verifikasi tetap pada JSON.

## Gerbang penerimaan

- Tes memastikan keyframe kamera dan properti lingkungan diteruskan utuh.
- Metadata global dan per-adegan memiliki prioritas yang deterministik.
- Kunci renderer yang tidak dikenal ditolak.
- Tanpa metadata lingkungan, tidak ada ruang/cuaca/kerumunan/palet spesifik yang
  dibuat otomatis.
- CI kontrak, runtime, dan adab Kisah Islami harus lulus sebelum Tahap 10 dinyatakan
  selesai.
