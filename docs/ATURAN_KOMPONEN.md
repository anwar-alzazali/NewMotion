# Aturan membuat komponen renderer yang belum tersedia — dari naskah pemilik

Untuk sesi AI pengembang (ChatGPT/Codex) yang menerima **naskah** dari pemilik (Anwar Alzazali) dan
diminta menyiapkan komponen visual yang dibutuhkan naskah itu. Bahasa kerja: Indonesia.
Aturan ini melengkapi `docs/TUGAS_GPT.md` (protokol sesi, batas wajib, CI) — baca keduanya.

## Alur kerja

1. **Baca naskah** beat demi beat. Untuk tiap beat tulis visual yang dibutuhkan agar penonton mengerti
   tanpa membaca subtitle: tempat, benda inti, tokoh/figuran dan gerak mereka, keadaan yang berubah.
2. **Cocokkan dengan kemampuan yang sudah ada**, jangan menebak:
   ```
   python -c "from newmotion.application.katalog_renderer import teks_katalog; print(teks_katalog())"
   python -c "from newmotion.application.kemampuan_tokoh import teks_kemampuan_tokoh; print(teks_kemampuan_tokoh())"
   python -m newmotion.application.kebutuhan_renderer      # antrean kebutuhan dari produksi sebelumnya
   ```
   Juga ruang (latar dalam ruangan) di fungsi `ruang()` `mesin-video/papan/cerita.js`.
3. **Tulis tabel kebutuhan** (wajib, masuk ke deskripsi PR):

   | Beat | Visual yang dibutuhkan | Sudah ada? | Keputusan |
   |---|---|---|---|
   | 3 | sumur tua di padang | `sumur` | pakai yang ada |
   | 5 | unta berlutut | `unta` tanpa pose berlutut | tambah parameter `lutut` ke `unta` |
   | 7 | kafilah dagang berjalan | tidak ada | benda baru `kafilah` |

4. **Putuskan** dengan urutan di bawah (bagian "Kapan membuat"), lalu buat.
5. **Buktikan** (bagian "Bukti"), catat kebutuhan di antrean kebutuhan, buka PR (bagian "Penyerahan").

## Kapan membuat, dan apa yang dibuat (urut dari yang paling diutamakan)

1. **Pakai yang ada** bila benda/kombinasi benda + parameter + figuran sudah bisa menceritakan beat itu.
   Contoh: "pasar ramai" = `kios_pasar` + figuran berpindah, bukan benda baru "pasar_ramai".
2. **Tambah parameter** ke benda yang ada bila yang kurang hanya keadaannya (terbuka/tertutup, penuh/kosong,
   rusak, menyala). Bawaan parameter baru = tampilan lama persis (video lama tidak boleh berubah).
3. **Benda baru** hanya bila 1 dan 2 tidak cukup.
4. **Kemampuan tokoh** (pose, aksi, pegang, kait) hanya bila beat tak terbaca tanpa gerak itu.

**Manusia selalu lewat boneka/figuran, bukan benda baru.** Tokoh biasa (Firaun, raja, prajurit, penduduk,
jasad) digambar dengan `boneka`/figuran yang sudah dijaga penjaga adab dan punya wajah, pose, dan gerak.
Kebutuhan manusia yang belum ada = **kemampuan tokoh**: aksesori/pakaian (mis. mahkota raja, jubah kebesaran),
pose (mis. terbaring tak bernyawa, tanpa luka), atau aksi. Larangan "bentuk manusia" di prompt
`skill/pembuat_komponen.md` itu benar dan tetap: yang dilarang adalah **benda** bersosok manusia, karena
benda tidak melewati aturan wajah/adab boneka. Contoh naskah Firaun: Firaun = boneka + aksesori raja;
jasad Firaun = boneka pose terbaring di tepi air (+ benda `ombak`/pantai); laut terbelah = benda baru yang sah.

Batas per naskah: **paling banyak 5 komponen baru/diubah**. Sisanya catat di antrean kebutuhan dan
sebutkan pengganti terdekat di tabel; pemilik yang memutuskan bila ingin lebih.

**Nama harus umum dan bisa dipakai ulang** kisah lain: `sumur`, `kafilah`, `gua_batu`, bukan
`sumur_nabi_yusuf` atau `gua_ashabul_kahfi`. Satu komponen = satu bentuk yang jelas; variasi lewat parameter.

## Batas wajib (tidak boleh dilanggar walau naskah memintanya)

- **Adab:** Allah tidak digambar dalam bentuk apa pun (termasuk simbol tangan, mata, cahaya bersosok).
  Nabi/rasul hanya pilar cahaya `nur`; malaikat cahaya bentuk lain; sahabat bertubuh manusia berwajah cahaya.
  Komponen baru **tidak boleh** bisa dipakai sebagai wujud mereka: tidak ada benda bersosok manusia yang
  dinamai/ditujukan untuk tokoh mulia. Bila beat menyebut tokoh mulia, kebutuhan visualnya dipenuhi dengan
  cahaya, benda di sekitar (tongkat, bahtera, mimbar), atau tempat, bukan sosok.
- **Tidak menakutkan berlebihan / tidak sadis:** azab, neraka, kematian digambar tegas tetapi tanpa darah,
  luka, atau penyiksaan rinci. Simbol, cahaya, api, kegelapan, dan reaksi tokoh lebih kuat dari gore.
- **Tidak ada gambar AI atau foto.** Bentuk-bentuk digambar vektor di `cerita.js`. Logo/merek: lihat
  bagian "Logo dan merek" (boleh, dengan berkas resmi; tidak digambar ulang).
- **Tidak ada tulisan Arab di dalam komponen** (ayat/teks ditampilkan oleh kartu dalil, bukan benda).
- **Video lama tidak berubah:** benda/parameter lama tidak diubah tampilannya kecuali parameter baru diberi
  nilai; `tests/test_referensi_kisah.py` harus tetap lulus.

## Logo dan merek (untuk video tutorial/edukasi)

Video tutorial butuh logo asli (WhatsApp, Excel, ChatGPT, Google, Supabase, dll.) agar penonton langsung
mengenali aplikasinya. Aturannya:

- **Pakai berkas logo resmi, jangan menggambar ulang.** Logo buatan tangan (vektor tiruan, warna/bentuk
  dikira-kira) terlihat palsu dan bisa salah. Berkas resmi diambil dari halaman *brand/press kit* resmi
  pemiliknya dan disediakan pemilik di `mesin-video/aset/logo/<nama>.svg` (atau `.png`, latar transparan),
  dengan nama sederhana: `whatsapp.svg`, `excel.svg`, `chatgpt.svg`.
- **Ditampilkan lewat komponen gambar yang sudah ada**: kartu Papan `gambar` dengan `logo: true`
  (`mesin-video/papan/papan.js`), atau komponen kecil di `cerita.js` yang memuat berkas dari
  `aset/logo/` bila logo harus menempel di adegan bertokoh (mis. di layar HP yang dipegang tokoh).
  Komponen pemuat logo dibuat **sekali** dan dipakai untuk semua logo; jangan satu komponen per merek.
- **Bila berkas belum ada**, jangan menunggu dan jangan menggambar tiruan: pakai tempat-kosong netral
  (kotak membulat abu-abu berisi nama aplikasi) dan tulis di PR daftar berkas logo yang perlu disiapkan pemilik.
- **Pemakaian yang wajar:** logo dipakai untuk menunjuk aplikasi yang sedang dibahas, ukuran dan warnanya
  tidak diubah-ubah, tidak dipotong/didistorsi, tidak ditempel seolah-olah video itu dibuat/disponsori merek itu.
- **Kisah Islami tidak memakai logo/merek** (penjaga konten akun itu tetap berlaku).

## Standar gambar

- **Gaya:** garis tinta `INK` (tebal 4–8 pada skala 1), warna datar + satu bayangan/kilau lembut, proporsi
  kartun yang sama dengan benda lain. Lihat `domba`, `rumah`, `bahtera`, `kios_pasar` sebagai patokan gaya.
- **Titik jangkar (0, 0) = titik pijak di tanah** (tengah bawah). Benda langit/terbang: jangkar di tengah.
- **Skala acuan:** tokoh boneka skala 1 tingginya ±640 px dari kaki ke ubun-ubun. Benda berukuran
  dunia nyata mengikuti itu (pintu ±1,1× tinggi orang, kambing setinggi pinggang, dst.).
- **Terbaca di ponsel:** bentuk dikenali dari siluetnya saja pada ukuran seperempat layar. Hindari detail
  halus yang hilang saat kecil (garis < 3 px, teks kecil).
- **Parameter keadaan** dibaca lewat `v(o.nama, t, d, bawaan)` agar sutradara bisa menganimasikan
  `[awal, akhir]` (katalog menandai parameter seperti ini dengan `*`). Nilai 0–1 diutamakan.
  Minimal satu parameter yang bermakna bagi cerita.
- **Gerak hidup ringan** (api berkedip, air beriak, kain berkibar) memakai waktu `t`, halus, tidak membuat
  pusing; tidak berkedip cepat.
- **Komentar keterangan** di cabang `} else if (j === "nama") { // keterangan singkat; param 0-1 artinya ...`
  Komentar inilah yang dibaca sutradara LLM; tulis untuk apa benda dipakai dan arti tiap parameter.
- Bila benda bisa dinaiki/diduduki/ditumpangi: tambahkan entri di `KAIT` (dudukan, pegangan, pijakan, sudut)
  dan adegan di `ADEGAN_KAIT` `uji_tokoh.py`; A6 harus lulus.
- Ringan: tanpa filter berat per frame, tanpa ribuan elemen; render pratinjau tetap cepat.

## Bukti (wajib di PR)

- **Lembar dua keadaan** tiap komponen (parameter awal dan akhir), ukuran penuh dan ukuran seperempat
  layar, berdampingan dengan **tokoh skala acuan** agar ukurannya bisa dinilai. Pakai/kembangkan
  `mesin-video/papan/lembar_benda_baru.py`; lembar ada di artefak run CI.
- **Satu frame beat naskah** yang memakai komponen itu (spek kecil berisi beat tersebut), supaya terlihat
  komponen benar-benar menceritakan beatnya, bukan hanya bagus sendirian.
- CI `test-runtime.yml` hijau (ukuran benda diukur ulang otomatis, pytest, uji tokoh 0 temuan).

## Penyerahan

- Branch `tugas-komponen-<judul-ringkas-naskah>`. PR berisi: tabel kebutuhan, daftar komponen yang dibuat
  atau diubah beserta parameternya, lembar bukti, dan kebutuhan yang sengaja ditunda.
- Catat setiap kebutuhan (dibuat atau ditunda) di antrean kebutuhan (`kebutuhan_renderer`), status
  `dibuat` untuk yang dibuat.
- **Tujuan PR:** `gpt/integrasi` (disamakan dengan `main` setiap kali Claude menggabungkan). Komponen dari naskah pemilik **tidak di-merge sendiri**: pemilik melihat lembar buktinya lalu
  merge (cepat, hanya menilai gambar). Tulis log kerja sebagai berkas baru di `docs/log_kerja/`.
- Jangan mengubah naskah. Bila naskah meminta sesuatu yang melanggar batas wajib, tulis di PR bagian mana
  dan usulan penggantinya; jangan dibuat.

## Pesan pembuka untuk pemilik (salin ke sesi GPT bersama naskahnya)

```
Repo: anwar-alzazali/NewMotion. Baca docs/ATURAN_KOMPONEN.md dan docs/TUGAS_GPT.md
(protokol, batas wajib, CI). Siapkan komponen renderer yang dibutuhkan naskah di bawah
sesuai aturan itu: tabel kebutuhan per beat, maksimal 5 komponen, lembar bukti, PR
tanpa merge sendiri.

NASKAH:
<tempel naskah di sini>
```
