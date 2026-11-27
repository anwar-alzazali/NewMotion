# Log kerja — Tugas 5d: belajar dari revisi pemilik

Tanggal: 2026-11-27  
Cabang: `tugas-5d-belajar-revisi-pemilik`  
Basis: `gpt/integrasi`

## Perubahan yang dikerjakan
- Arsip revisi pada `antrean/<id>/revisi/NNNN.json` berisi catatan pemilik, naskah sebelum, dan naskah sesudah.
- Kumpulan revisi ditambahkan ke `newmotion/application/data/pelajaran_naskah.jsonl`.
- Modul `pelajaran_naskah.py` memilih maksimal dua contoh final yang mirip berdasarkan irisan kata topik.
- Alat manual `python -m newmotion.application.pelajaran_naskah --ringkas` membuat usulan pedoman dengan LLM tahap murah `ringkas_pelajaran`; usulan tidak otomatis masuk ke pedoman aktif.
- Penulis membaca pedoman yang telah disetujui dari `pedoman_naskah_pemilik.md` dan contoh final yang tersimpan.
- Contoh naskah disimpan setelah render final selesai, bukan sekadar setelah naskah disetujui.
- Ditambahkan tes LLM palsu untuk pemilihan contoh, pedoman aktif, dan ringkasan usulan.

## Batasan dan pekerjaan lanjutan
- Perlu memastikan pengarsipan revisi dan pemanggilan contoh/pedoman lewat uji runtime penuh.
- Alur persetujuan usulan perlu diuji secara eksplisit; berkas pedoman aktif tetap tidak dibuat otomatis.
- Perlu uji integrasi bahwa contoh hanya tersimpan sekali setelah render final berhasil.

## CI
- Workflow runtime terakhir yang terpantau: [run 45948910414](https://github.com/anwar-alzazali/NewMotion/actions/runs/45948910414), masih berjalan saat log ini dibuat.
