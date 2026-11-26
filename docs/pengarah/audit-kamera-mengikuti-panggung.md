# Tahap 11 — Kamera mengikuti lintasan panggung

## Tujuan

Menghasilkan keyframe kamera `x/y` dari posisi tokoh yang sudah diterjemahkan
adapter visual. Kamera tidak boleh menciptakan lintasan aktor dan tidak boleh
mengubah sumbu yang dikunci eksplisit oleh naskah.

## Integrasi arsitektur

- Kontrak `PaketGenre` mendapat kait opsional `pengarah_kamera`.
- Paket cerita umum mengaktifkan kait tersebut; paket Kisah Islami tidak diubah.
- Orkestrator memanggil pengarah kamera setelah adapter visual selesai mengisi
  `cerita.shot.boneka`.
- Pengarah kamera membaca `fokus_tokoh_ids` dan lintasan posisi yang sudah ada.
  Ia tidak mengubah rencana blocking, pose, atau lintasan aktor.

## Algoritme

1. Ambil tokoh pada shot yang termasuk fokus pengarahan.
2. Gabungkan waktu keyframe posisi x/y seluruh tokoh fokus.
3. Pada setiap waktu, hitung pusat bounding-box kelompok tokoh.
4. Gunakan pusat tersebut sebagai keyframe kamera x/y.
5. Jika sumbu x atau y diberikan eksplisit oleh naskah, sumbu itu tidak ditimpa;
   sumbu lain tetap boleh mengikuti panggung.
6. Jika tidak ada lintasan dinamis, pertahankan profil kamera dasar.
7. Catat status kamera dan hasil keyframe pada `rencana_kamera`.

Kamera z, efek hentak, dan guncang tetap berasal dari profil/metadata kamera
sebelumnya. Tidak ada nilai acak atau lintasan aktor baru yang dibuat.

## Tes

- Kamera mengikuti pusat kelompok aktor pada lintasan berjalan.
- Sumbu kamera yang dikunci naskah tetap utuh.
- Aksi statis tidak menghasilkan gerak kamera palsu.
- Hasil deterministik pada input yang sama.

## Batas yang belum diselesaikan

- Pusat bounding-box belum mempertimbangkan ukuran visual, kedalaman z, foreground,
  occlusion, atau ruang kosong untuk arah gerak.
- Belum ada shot/reverse-shot, over-the-shoulder, atau pemilihan lensa/komposisi
  berdasarkan dialog dan relasi blocking.
- Pelacakan hanya berjalan bila adapter sudah menyediakan lintasan tokoh yang sah.
- Belum ada render visual; penerimaan tahap ini hanya pada kontrak JSON dan CI.
