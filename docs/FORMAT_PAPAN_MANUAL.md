# Papan manual — JSON lengkap ditulis sesi chat AI, dirender tanpa LLM

Jalur paling irit: sesi chat (Claude/GPT) menulis SATU berkas JSON yang berisi visual **dan** narasi.
Mesin hanya membuat suara (satu permintaan ElevenLabs), mencocokkan waktu, merender, memeriksa, lalu mengirim video.
Tidak ada naskah/sutradara/periksa visual LLM di jalur ini.

Kirim: unggah berkas `.json` ke bot Mesin KONTEN, atau simpan di `mesin-video/papan/kisah/<nama>.json` lalu `/papan <nama>`.
Bekal lengkap untuk sesi chat (dokumen ini + katalog benda/tokoh/suara terbaru): `docs/BEKAL_PAPAN_MANUAL.md`
(diperbarui otomatis oleh CI; bot mengirimkannya lewat `/bekal`). Prompt siap pakai: `docs/PROMPT_JSON_LENGKAP.md`.

## Contoh referensi
`mesin-video/papan/kisah/mahsyar1.json`, `nuh1.json`, `yajuj1.json`, `yajuj2.json` — kunci shot yang dipakai di sana
(`langit`, `horizon`, `malam`, `debu`, `palet`, `kamera`, `benda`, `teks`, `boneka`, `kerumunan`, `matahari`, `hujan`,
`panas`, `retak`, `naungan`, `ruang`, `tanah`, ...) dibaca oleh `mesin-video/papan/cerita.js`.
Bedanya: di contoh itu waktu sudah angka karena rekamannya sudah ada. Di papan manual, waktu boleh mengikuti narasi.

## Kerangka
```json
{
  "latar": "gelap",
  "narator": "UdQDnhmw5mrED2XYPXhu",
  "cerita": {"label": "JUDUL SERI", "shot": [
    {"narasi": "Kamu akan dibangkitkan tanpa alas kaki.", "intonasi": "berat",
     "langit": 1, "horizon": 1350, "kamera": {"z": [1.0, 1.12], "x": 540, "y": 1000},
     "teks": [{"at": "@dibangkitkan", "teks": "DIBANGKITKAN", "sub": "HR Bukhari 6527", "y": 380, "ukuran": 96}],
     "boneka": [{"x": 540, "y": 1900, "s": 1.5, "utama": true, "wajah": [[0, "netral"], ["@kaki", "takut"]]}]},
    {"durasi": 2.0, "langit": 0.2},
    {"narasi": "Lalu semua manusia dikumpulkan.", "jeda": 0.9, "kerumunan": {"n": 300, "y0": 4, "y1": 400}}
  ]},
  "rekaman": [{"berkas": "../../aset/suara/braam.mp3", "at": "@dibangkitkan", "vol": 0.5}]
}
```

## Narasi dan waktu
- `narasi` per shot: kalimat yang dibacakan saat shot itu tampil. Semua narasi dibacakan dalam satu permintaan (suara konsisten).
- `intonasi` (opsional): `tenang`, `berat`, `tegang`, `bisik`, `tegas`, `haru`, `lega`.
- `jeda` (opsional, detik): diam setelah narasi shot itu (bawaan 0,45).
- Shot tanpa `narasi` = layar tenang; wajib `durasi` (detik). Shot pertama harus bernarasi.
- `at` shot diisi otomatis (awal narasinya). Isi shot (teks, kunci boneka, dll.) memakai detik **relatif awal shot**,
  atau `"@kata"` / `"@kata#2"` (kemunculan ke-2) / `"@kata-0.3"` (geser) = saat kata itu diucapkan. `rekaman` (efek suara) memakai detik mutlak atau `"@kata"`.
- Subtitle dibuat otomatis dari narasi. Narator bawaan Ozhy; `narator` hanya bila ingin suara lain.
- Audio disimpan dan dipakai ulang selama teks narasi tidak berubah: memperbaiki visual saja tidak memakan kredit ElevenLabs.
- Bila papan sudah merujuk rekaman sendiri (`suara` + `waktu`, seperti mahsyar1.json), narasi tidak dibuat.

## Batas wajib (dicek mesin; papan ditolak bila dilanggar)
- Allah tidak digambar; nabi dan malaikat tidak digambar (cahaya/nur + nama). Sahabat tidak digambar berwajah.
- Bacaan Arab tidak disuarakan: huruf Arab dilarang di `narasi`; tulis Arab + latin + arti di `teks` layar.
- Hanya dalil sahih/hasan, sumber tampil di layar (`sub`), nomor dicek oleh penulis JSON. Jalur ini tidak memverifikasi dalil.
- Tanpa watermark. Label AI tetap aktif saat unggah.

## Resep tokoh yang sering dipakai
- **Raja Mesir kuno / Firaun:** `"penutup_kepala": "nemes", "janggut": true, "janggut_model": "firaun",
  "pakaian": {"jenis": "jubah", "warna": "#f4ecd8", "bisht": "#3a2a1e", "kalung": "usekh"}`.
- **Rombongan Arab:** `"cerita": {"suku": "arab", ...}` lalu figuran `{"npc": <angka acak tetap>}`; membelakangi kamera: `"belakang": true`.
- **Nabi:** benda `{"jenis": "nur", "nama": "Nabi Musa ﷺ", "nama_letak": "atas"}`, tidak pernah boneka.
- **Kartu dalil tembus pandang:** benda `kartu_dalil` dengan `"latar": 0.4` (1 = kartu penuh); tampilkan di beat kutipan saja.
- **Jasad tanpa luka:** boneka `"pose": "rebahan", "mata": "tutup"` di benda `pantai`.
- **Laut terbelah:** benda `{"jenis": "laut_terbelah", "belah": [[0, 0], [2.5, 1]]}` (turunkan lagi = laut menutup).

## Yang dikirim balik
Lembar kontak + video + hasil `periksa.py`. GAGAL = kerusakan teknis atau batas wajib; PERIKSA = pedoman, keputusan Anda.
