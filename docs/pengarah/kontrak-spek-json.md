# Kontrak audit spek pengarahan NewMotion

## Tujuan

NewMotion harus menghasilkan satu JSON pengarahan yang dapat diaudit sebelum renderer
dijalankan. JSON tersebut bukan sekadar daftar shot siap-render: ia harus mempertahankan
jejak dari naskah, peristiwa, keputusan keadaan, hingga instruksi visual. Pengarahan tetap
deterministik dan tidak menambahkan aksi, tokoh, benda, atau akibat yang tidak didukung
naskah.

Dokumen ini menetapkan kriteria penerimaan untuk pekerjaan bertumpuk berikutnya. Ini
bukan skema kedua dan tidak menggantikan kontrak papan renderer yang sudah ada.

## Pemisahan lapisan data

Keluaran harus dapat dibaca sebagai lapisan yang saling tertaut:

1. **Sumber cerita** — judul, genre, konteks konten, beat/adegan, teks narasi, daftar tokoh,
   dan identitas stabilnya.
2. **Peristiwa** — ID stabil, beat asal, bukti teks/frasa, aktor, aksi, sasaran (tokoh atau
   objek/lingkungan), tujuan gerak bila berbeda dari sasaran, serta relasi sebab-akibat
   bila memang dinyatakan.
3. **Keadaan dunia** — keadaan awal, transisi yang dipicu peristiwa, keadaan setelah
   peristiwa, dan riwayat yang tetap berlaku pada beat/shot berikutnya. Keadaan tidak
   boleh berubah hanya karena indeks beat, persentase cerita, atau kebutuhan dramatis.
4. **Keputusan penyutradaraan** — fokus visual, siapa berada di panggung, blocking,
   lintasan gerak, pose/interaksi, benda, kamera, komposisi, dan alasan keputusan.
5. **Spesifikasi renderer** — data shot yang benar-benar dipahami adapter/renderer lama.
   Lapisan ini merupakan hasil terjemahan, bukan sumber kebenaran semantik.
6. **Diagnostik** — status `siap`, `periksa`, atau `tidak_didukung`; kode temuan; ID
   peristiwa/beat terkait; dan alasan yang dapat ditindaklanjuti. Ambiguitas tidak boleh
   disamarkan menjadi keputusan visual seolah-olah pasti.

## Kriteria kelengkapan JSON

Satu keluaran dinilai lengkap hanya jika:

- ID beat, tokoh, peristiwa, benda, dan shot stabil serta tidak saling bertabrakan.
- Setiap peristiwa dapat ditelusuri kembali ke beat dan bukti narasinya.
- Aktor, aksi, sasaran, dan tujuan tidak tertukar; relasi yang tidak pasti ditandai
  `periksa`, bukan ditebak.
- Setiap perubahan keadaan menunjuk peristiwa pemicunya; keadaan yang tidak berubah
  tetap dibawa ke shot berikutnya.
- Segmentasi aksi hanya memisahkan tahap bila ada relasi temporal eksplisit atau
  transisi keadaan berantai yang konsisten; aksi tanpa relasi tersebut tetap satu
  kelompok agar aksi simultan tidak dipecah secara spekulatif.
- Rencana tahap semantik dibedakan dari pemecahan shot renderer; pemecahan aktual baru
  boleh dilakukan setelah adapter menjaga indeks, aktor, benda, dan kontinuitas lintas-shot.
- Setiap arahan visual tokoh menunjuk tokoh/peristiwa yang mendasarinya.
- Gerak mempunyai lintasan dan waktu yang masuk akal; aksi berjalan/berlari tidak boleh
  hanya mengganti pose tanpa perpindahan posisi.
- Benda yang sama mempertahankan ID, posisi, dan keadaan lintas-shot sampai ada peristiwa
  yang mengubahnya.
- Setiap properti renderer yang dikeluarkan berada dalam kemampuan renderer; hal yang
  belum didukung dicatat sebagai diagnostik.
- JSON dapat diserialisasi dan lolos validasi kontrak tanpa menghilangkan lapisan semantik.

## Batas keselamatan dan arsitektur

- Tidak membuat parser, reducer keadaan, blocking, renderer, atau timeline kedua bila
  pemilik kemampuan sudah tersedia.
- Inti NewMotion tetap netral genre. Kebijakan Kisah Islami tetap berada di paket
  `kisah_islami`; pengujian cerita umum tidak boleh melemahkan penjaga adab/dalil.
- Tidak memakai LLM untuk menutupi kekurangan algoritme deterministik.
- Tidak mengubah naskah referensi Nuh, Ya'juj, atau Mahsyar. Referensi dipakai untuk
  membandingkan kedalaman struktur dan detail, bukan untuk menyalin koordinat/adegan.
- Tidak memicu render video referensi yang sudah pernah dijalankan. Tahap pembandingan
  awal berfokus pada JSON; render hanya dilakukan setelah kontrak JSON lulus.

## Urutan tahap bertumpuk dalam satu PR

Seluruh tahap pekerjaan spek JSON berada dalam **satu PR dan satu branch utama**.
Setiap tahap ditambahkan sebagai commit lanjutan di atas tahap sebelumnya; jangan
membuat PR terpisah untuk Tahap 2, 3, atau 4.

1. **Tahap 1 — Kontrak spek JSON dan baseline kelengkapan**: kriteria lapisan,
   audit struktur keluaran aktual, dan tes kontrak.
2. **Tahap 2 — Ketepatan relasi peristiwa**: aktor–aksi–sasaran–tujuan, bukti frasa,
   negasi, kalimat pasif/majemuk, dan diagnostik ambiguitas.
3. **Tahap 3 — Keadaan, blocking, dan kontinuitas**: transisi berbasis peristiwa, lintasan,
   benda, serta kesinambungan antar-beat/shot.
4. **Tahap 4 — Uji referensi lintas cerita**: bandingkan JSON hasil pengarahan dengan contoh
   Nuh, Ya'juj, dan Mahsyar; ukur kelengkapan tiap lapisan dan catat bagian yang belum
   didukung. Jangan mengubah sumber referensi.
5. **Tahap lanjutan — Penyempurnaan**: lengkapi kesenjangan yang ditemukan, jalankan
   pengujian JSON lintas cerita, lalu audit akhir sebelum uji render.

Setiap tahap harus menyertakan tes CI dan ringkasan audit yang membedakan hal yang
terbukti, temuan `periksa`, dan pekerjaan yang belum dilakukan. PR tetap draft dan
tidak digabung ke `main` sebelum seluruh tahap serta audit berurutan selesai.
