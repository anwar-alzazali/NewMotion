# Tahap 9 — Audit generalisasi spek JSON lintas cerita

## Tujuan

Menguji apakah pengarah cerita umum menghasilkan JSON yang konsisten pada kategori
aksi yang berbeda, tanpa mengunci tes pada koordinat satu fixture. Tahap ini adalah
pengukuran kemampuan yang sudah ada; bukan alasan untuk menambah aturan khusus agar
semua contoh tampak berhasil.

Pengujian hanya menghasilkan dan memeriksa JSON. Tidak menjalankan renderer, membuat
MP4, atau memicu workflow render visual.

## Cakupan uji

| Kasus | Kategori | Kriteria terukur |
|---|---|---|
| Pelari mendekati pejalan | Lokomosi | Tokoh memiliki lintasan posisi nyata dan kecepatan jalan/lari |
| Penolong membantu korban | Interaksi | Pelaku dan sasaran hadir; relasi sasaran terhubung |
| Penjaga menunggu | Aksi statis | Aksi diteruskan sebagai aksi cerita, bukan gerak palsu |
| Pengendara menaiki motor | Kendaraan | Motor hanya dibuat karena disebut eksplisit dan terhubung ke pengendara |
| Pengamat memperhatikan keadaan | Aksi belum didukung | Diagnostik menyatakan keterbatasan; tidak membuat boneka/gerak rekaan |
| Dua aksi berurutan | Segmentasi temporal | Dua tahap menjadi dua shot renderer, urutan dan waktu stabil |
| Percakapan/pertolongan tanpa objek | Anti-invensi | Daftar benda tetap kosong bila naskah tidak menyatakan benda |

## Metrik

Setiap kasus diperiksa untuk:
- JSON dapat diserialisasi dan dibaca kembali.
- ID beat, peristiwa, aktor, dan tautan blocking konsisten.
- Semua shot memiliki metadata pengarahan dan tautan peristiwa.
- Status visual membedakan hasil siap dari aksi yang belum didukung.
- Lokomosi benar-benar mengubah posisi, bukan hanya mengganti pose.
- Interaksi memiliki pelaku dan sasaran yang dapat dihubungkan.
- Objek tidak diciptakan tanpa dasar eksplisit.
- Segmentasi temporal deterministik dan menggeser nilai `at` renderer.

Tes ini sengaja tidak menyamakan jumlah shot/objek dengan angka referensi Nuh, Mahsyar,
atau Ya'juj. Angka pada file referensi adalah karakteristik cerita tertentu, bukan
target kuota yang boleh dikejar dengan mengarang visual.

## Hasil inspeksi struktur saat ini

| Dimensi | Hasil audit kode | Status |
|---|---|---|
| Identitas dan keterlacakan peristiwa | ID stabil, beat asal, aktor/sasaran dan diagnostik tersedia | Ada fondasi |
| Lokomosi umum | Jalan/lari memiliki lintasan posisi; daftar aksi masih terbatas | Parsial |
| Interaksi | Menolong dipetakan; aksi interaksi lain belum seluruhnya didukung pengarah visual | Kesenjangan |
| Kendaraan | Motor dipetakan bila eksplisit; dukungan jenis kendaraan lain belum terbukti | Kesenjangan |
| Objek umum | Tidak ada katalog/pemetaan umum lintas objek yang dibuktikan oleh kasus ini | Kesenjangan besar |
| Kamera | Profil zoom dipilih dari kategori aksi; posisi dasar dan horizon masih statis | Kesenjangan besar |
| Lingkungan | Belum ada pemilihan atmosfer/lingkungan kontekstual yang dibuktikan | Kesenjangan besar |
| Ekspresi dan detail tokoh | Terbatas pada instruksi visual yang tersedia; belum mendekati atribut referensi | Kesenjangan besar |
| Diagnostik | Aksi tak didukung dapat ditandai tanpa memaksakan visual | Ada fondasi |

## Perbandingan dengan JSON referensi

Referensi yang telah diaudit pada Tahap 4:
- Nuh: 15 shot, 98 objek, 3 entri boneka.
- Mahsyar: 12 shot, 25 entri boneka serta lapisan lingkungan/kerumunan.
- Ya'juj 1: 20 shot, 73 objek, 2 entri boneka.
- Ya'juj 2: 20 shot, 85 objek.

Jumlah tersebut tidak dijadikan ambang jumlah. Perbandingan yang benar adalah kemampuan struktur:
keyframe kamera, lapisan lingkungan, variasi objek, atribut tokoh, gerak, kontinuitas,
dan hubungan keputusan visual dengan peristiwa.

Pada implementasi yang diperiksa, pengarah umum masih membangun profil kamera dasar
dari kategori aksi. Ia belum menghasilkan variasi kamera dan lingkungan peristiwa
dengan kedalaman yang tampak pada JSON referensi. Karena itu, keberhasilan tes Tahap 9
hanya membuktikan generalisasi terbatas pada kontrak/aksi yang diuji, bukan kesetaraan
kedalaman JSON dengan referensi.

## Gerbang keputusan

1. Jalankan tes generalisasi di GitHub Actions.
2. Jika gagal, perbaiki cacat kontrak atau integrasi yang terbukti; jangan mengubah
   ekspektasi tes hanya agar lulus.
3. Jika lulus, catat bahwa generalisasi terbatas telah terbukti untuk kasus yang diuji.
4. Kesenjangan kamera, lingkungan, objek umum, serta ekspresi tetap menjadi pekerjaan
   algoritme berikutnya. Jangan menandai PR siap merge hanya karena tes ini lulus.
5. Tetap tahan render video sampai audit kedalaman JSON lintas cerita menyatakan layak.

## Batas tahap

Tahap ini tidak mengubah kebijakan genre Kisah Islami, tidak menyalin koordinat JSON
referensi, tidak menambah LLM runtime, dan tidak menjalankan render video.


## Pembaruan setelah Tahap 10 — kamera dan lingkungan

Audit renderer pada `mesin-video/papan/cerita.js` membuktikan dukungan untuk kamera
`x/y/z`, efek `hentak/guncang`, serta properti lingkungan seperti `palet`, `ruang`,
`langit`, `horizon`, `debu`, `hujan`, `panas`, `matahari`, `naungan`,
`kerumunan`, `retak`, dan `resap`. Rincian bukti dan pola empat JSON referensi ada
pada `docs/pengarah/audit-kamera-lingkungan.md`.

Pengarah cerita umum kini memilih framing dasar kamera menurut tujuan shot dan menerima
metadata kamera/lingkungan eksplisit pada level naskah atau adegan. Metadata adegan
mengoverride metadata global. Kunci yang tidak didukung serta palet/jenis ruang yang
tidak dikenal ditolak. Tanpa metadata lingkungan, pengarah tidak menciptakan cuaca,
kerumunan, ruang, atau palet spesifik.

Status kamera berubah dari statis penuh menjadi **parsial**. Kamera belum melacak
lintasan aktor secara otomatis dan belum memilih shot/reverse-shot berdasarkan geometri
blocking. Lingkungan masih bergantung pada metadata eksplisit; inferensi konteks dari
narasi bebas dan katalog objek/lingkungan umum tetap menjadi kesenjangan.
