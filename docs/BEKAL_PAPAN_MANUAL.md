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
- Bacaan Arab tidak disuarakan: huruf Arab dilarang di `narasi`. Teks Arab dalil hanya lewat `kartu_dalil` (kolom `arab`),
  supaya dicocokkan dengan sumbernya; teks layar biasa memuat latin/arti dan sumber.
- Hanya dalil sahih/hasan, sumber tampil di layar (`sub`). Kartu dalil dicocokkan mesin dengan Al-Qur'an/dataset hadis;
  yang tidak cocok satu huruf pun ditolak. Sumber di `sub` teks biasa tetap tanggung jawab penulis JSON.
- Tanpa watermark. Label AI tetap aktif saat unggah.

## Resep tokoh yang sering dipakai
- **Raja Mesir kuno / Firaun:** `"penutup_kepala": "nemes", "janggut": true, "janggut_model": "firaun",
  "pakaian": {"jenis": "jubah", "warna": "#f4ecd8", "bisht": "#3a2a1e", "kalung": "usekh"}`.
- **Rombongan Arab:** `"cerita": {"suku": "arab", ...}` lalu figuran `{"npc": <angka acak tetap>}`; membelakangi kamera: `"belakang": true`.
- **Nabi:** benda `{"jenis": "nur", "nama": "Nabi Musa a.s.", "nama_letak": "atas"}`, tidak pernah boneka.
- **Kartu dalil tembus pandang** (tampilkan di beat kutipan saja; `latar` 1 = kartu penuh):
  `{"jenis": "kartu_dalil", "label": "QUR'AN", "kitab": "QS 26:62", "teks": "<terjemahan Indonesia>", "arab": "<teks Arab persis dari mushaf>", "latar": 0.4, "x": 540, "y": 700, "at": "@menjawab"}`
  Hadis: `"label": "HADIS", "kitab": "HR. Tirmidzi", "no": "3537"`. `teks` = terjemahan (bukan Arab); opsional `sorot` (frasa yang disorot kuning).
- **Jasad tanpa luka:** boneka `"pose": "rebahan", "mata": "tutup"` di benda `pantai`.
- **Laut terbelah:** benda `{"jenis": "laut_terbelah", "belah": [[0, 0], [2.5, 1]]}` (turunkan lagi = laut menutup).

## Aturan penulisan yang sering salah (dicek validator sebelum narasi dibuat)
- **Parameter benda ditulis langsung**, tidak dibungkus: `{"jenis": "surya", "x": 790, "y": 840, "r": 115, "terang": 1}`.
  Bukan `{"jenis": "surya", "o": {"r": 115}}`: isi `o` diabaikan renderer.
- **Semua benda masuk daftar `benda`**, termasuk matahari (`surya`). Kunci shot hanya yang tercantum di kerangka/contoh
  (`langit`, `horizon`, `malam`, `palet`, `kamera`, `benda`, `boneka`, `teks`, ...).
- **Teks layar tidak dipecah otomatis.** Pecah sendiri dengan `"\n"`: di ukuran 72 muat ±16 huruf kapital per baris,
  di ukuran 90 ±13. Teks yang lebih lebar dari layar ditolak. `sub` cukup sumber singkat (mis. `"QS Yunus 10:92"`).
- **`@kata` = kata persis di narasi tanpa tanda baca/tanda hubung:** "sekali-kali" ditulis `@sekalikali`.
  Waktu dicari dari kemunculan pertama di seluruh narasi; bila kata itu sudah muncul di shot sebelumnya, pakai `@kata#2`.
- **Efek suara hanya dari katalog** (`../../aset/suara/<nama>.mp3`); nama yang tidak ada ditolak.
- **Benda berlabel KHUSUS** di katalog hanya untuk kisahnya (mis. `genangan_tubuh` = keringat Padang Mahsyar).
- Bila ditolak, mesin mengirim daftar kesalahan bernomor; salin daftar itu ke sesi chat penulis JSON lalu kirim ulang.
  Narasi belum dibuat saat itu, jadi kredit ElevenLabs tidak terpakai.

## Yang dikirim balik
Lembar kontak + video + hasil `periksa.py`. GAGAL = kerusakan teknis atau batas wajib; PERIKSA = pedoman, keputusan Anda.


## Katalog benda (shot.benda[].jenis)
- amplop: amplop uang [keadaan: uang]
- api: (16 Nov, diperhalus) api unggun: lidah api bergradasi berkedip + kayu + pendar lembut
- api_unggun: api unggun dan kayu; nyala 0-1 mengatur besar api [keadaan: nyala*]
- arus: kerumunan siluet bergerak. mode lereng (turun dari dua punggung bukit ke (0,0)), cahaya (berlari masuk ke cahaya di (0,0)), lari (mendatar ke kanan), lorong (masuk menjauh ke ujung lorong laut_terbelah; otomatis menempel [keadaan: jauh, maju*, mode, n, rebah*, rim, rimwarna, tombak]
- awan: -
- awan_badai: awan badai; hujan 0-1 mengatur hujan dan gelap 0-1 warna awan [keadaan: gelap*, hujan*]
- awan_gelap: awan gelap; kilat 0-1 mengatur kilatan [keadaan: kilat*]
- bahtera: kapal Nabi Nuh dari papan dan pasak (QS 54:13), tampak samping; (0,0) = lunas. jadi 0-1 (rusuk -> papan -> rumah geladak), goyang (derajat), cahaya 0-1, orang n (siluet kecil di geladak), pintu 0-1 (+titian), darat (peny [keadaan: cahaya*, darat, goyang*, jadi*, orang, pintu*]
- bambu: rumpun bambu
- batu: batu gelap latar depan (pakai kabur:true agar tampak dekat kamera)
- bawah_laut: kedalaman laut: berkas cahaya samar, gelembung naik, partikel [keadaan: terang*]
- bayang_misteri: massa gelap ambigu: bentuk TIDAK dipastikan (bukan tokoh/monster) - hanya siluet bergeser, berdenyut, dikelilingi cahaya retakan. besar skala, nafas amplitudo denyut, cahaya warna rim [keadaan: besar*, cahaya, nafas]
- belah: (16 Nov) bumi terbelah dalam PERSPEKTIF (tampak samping): (0,0) = ujung celah di cakrawala; celah melebar ke arah kamera sampai y = H. buka 0-1, lebar px di bawah, cahaya warna, goyang px, seed [keadaan: buka*, cahaya, debu, goyang, lebar, tanah, tanah_atas]
- bintang: - [keadaan: n, tinggi]
- buku: kitab terbuka + label sumber: {teks (baris di halaman), sub (pil sumber), buka 0-1} [keadaan: buka*, sub, teks, ukuran]
- bulan: -
- burung_kawanan: kawanan burung; terbang 0-1 mengatur kepak sayap [keadaan: n, terbang*]
- cawan: (16 Nov) periuk/bejana berisi cairan mendidih: gelembung + uap (QS 47:15; HR Bukhari 6562 'seperti periuk'). didih 0-1, warna cairan, uap 0-1 [keadaan: didih*, uap*]
- danau: - [keadaan: isi*]
- domba: domba berbulu; jalan 0-1 menggerakkan langkah [keadaan: jalan*]
- dompet: dompet terbuka; isi = jumlah lembar 0-3 (tipis = 1) [keadaan: isi*]
- gapura: gerbang batu (gerbang Ludd): dua tiang + lengkung, cahaya emas dari dalam; cahaya 0-1 [keadaan: cahaya*]
- gedung: deretan gedung pencakar langit; tumbuh 0-1 = gedung naik dari tanah (berlomba meninggikan bangunan) [keadaan: derek, lebar, malam, n, tinggi, tumbuh*]
- genangan_tubuh: KHUSUS keringat Padang Mahsyar: diagram air di tubuh + label mata kaki/lutut/pinggang/dada/mulut (bukan air laut/banjir/tenggelam); tinggi 0-500 dari telapak (35 mata kaki, 110 lutut, 210 pinggang, 320 dada, 440 mulut),  [keadaan: riak*, tinggi*]
- gerbang: gerbang bercahaya (pintu surga): buka 0-1 = daun pintu terbuka [keadaan: buka*, nama]
- gua: -
- gunung: - [keadaan: bentuk, kilau]
- hati: -
- hewan: siluet hewan berpasangan berjalan ke kanan (QS 11:40); macam gajah|jerapah|unta|rusa|burung; pasang:false = satu; jalan 0-1; cahaya dari kiri-atas (garis tepi emas) [keadaan: jalan*, macam, pasang, rim]
- hp: ponsel menyala di tangan
- ikan: ikan besar (paus) siluet berenang pelan; arah -1 = menghadap kiri [keadaan: arah]
- infus: tiang infus dengan kantong cairan menetes
- jalan: jalan aspal + garis tengah putus-putus + trotoar; {w, y_lebar} [keadaan: lebar, w]
- jam_pasir: jam pasir; sisa 0-1 menunjukkan pasir di ruang atas [keadaan: sisa*]
- jembatan: shirath: jembatan sangat tipis di atas jurang api
- jembatan_desa: jembatan desa: badan jembatan kayu/beton melintasi sungai, dengan pagar dan tiang penyangga [keadaan: air, lebar, warna_pagar]
- jenazah: jenazah berkafan putih di atas keranda kayu (sopan, tanpa wajah); kain = warna kain penutup opsional [keadaan: kain]
- jendela: jendela kamar dengan cahaya Subuh masuk; terang 0-1 [keadaan: terang*]
- jurang: (16 Nov) jurang neraka dilihat dari tepi atas: cincin tebing mengecil ke dasar membara. jatuh 0-1 (batu dari atas ke dasar), dasar 0-1 terang, cahaya warna [keadaan: cahaya, dasar*, jatuh*]
- kambing: kambing kampung bertubuh berisi, tanduk pendek, telinga jatuh, berjanggut [keadaan: jalan*]
- kamboja: pohon kamboja (kuburan) berbunga putih-kuning
- kantong: kantong pahala: kain keemasan, tali, koin mengintip, berkilau
- kantor_gedung: gedung kantor kaca (tampak luar) {nama} [keadaan: nama]
- kapal_dagang: kapal dagang layar; muatan 0-1 mengatur peti di geladak [keadaan: layar*, muatan*]
- karung: karung dagangan; penuh 0-1 mengatur volume [keadaan: penuh*]
- kasur: kasur dilihat dari kaki ranjang; permukaan duduk y -130 (pas dengan pose duduk). {w, seprai, selimut, kayu} [keadaan: kayu, selimut, seprai, w]
- kebun_kurma: kebun kurma berbaris; buah 0-1 menampakkan tandan [keadaan: buah*, n]
- kelapa: pohon kelapa melengkung [keadaan: lengkung]
- keranjang: keranjang anyaman; penuh 0-1 mengatur isi [keadaan: isi, penuh*]
- kerumunan: (16 Nov) kerumunan siluet DIAM menghadap cahaya. tombak true = pasukan. n, w sebar, baris, k skala, seed, rim 0-1 (+rimwarna), sisi 1 = cahaya dari kanan / -1 kiri (bawaan: ke arah tengah), pose berdiri|telinga|wajah|ang [keadaan: api*, bara*, baris, hangus*, k, n, pose, rim*]
- kios_pasar: kios pasar beratap kain; dagangan 0-1 mengatur isi meja [keadaan: dagangan*]
- kipas: kipas angin berdiri, baling-baling berputar; {putar 0-1} [keadaan: putar*]
- koin: koin emas (dinar): {n, jatuh 0-1} [keadaan: jatuh*, n]
- kompor: meja dapur + kompor gas; {nyala 0-1} [keadaan: nyala*]
- kota: siluet kota tua (kubah, menara kecil, rumah bertingkat) dengan beberapa jendela menyala; w lebar, seed [keadaan: w]
- kue: kue ulang tahun kecil + lilin menyala: {nyala 0-1} [keadaan: nyala*]
- kulkas: kulkas dua pintu + magnet
- kursi: kursi kayu; dudukan y -125. {warna, sandaran:false} [keadaan: sandaran]
- ladang_gandum: hamparan batang gandum berbulir; matang 0-1, angin mengayunkan malai [keadaan: angin*, matang*, n]
- lahar: (16 Nov) dataran batu hitam berurat lava dalam perspektif: (0,0) = tengah cakrawala, sampai y = H. seed, cahaya warna, kuat 0-1 [keadaan: cahaya, kuat*]
- lapak: lapak pasar: meja + terpal + dagangan; {terpal, isi: buah|sayur|ikan} [keadaan: isi, terpal]
- laut: permukaan laut malam: y = garis permukaan; pantul = x pantulan bulan (relatif) [keadaan: pantul]
- laut_terbelah: laut terbelah dua (QS 26:63), gaya air sama dengan ombak kisah Nuh: lorong dasar laut kering di antara dua dinding air "laksana gunung", dilihat dari pangkal lorong; (0,0) = tengah pangkal lorong. belah 0-1 (0 = laut ber [keadaan: belah*, buih, jauh, lapis, lebar, tinggi]
- lemari: lemari pakaian dua pintu; {w, warna, buka 0-1} [keadaan: buka*, w]
- lentera: lentera minyak; nyala 0-1 mengatur cahaya [keadaan: nyala*]
- makam: gundukan tanah + nisan; n = jumlah makam berjejer, baru = gundukan segar [keadaan: baru, jarak, n]
- mangga: pohon rindang (mangga/beringin kecil), opsional buah [keadaan: buah, lebar]
- masjid: -
- masjid_kampung: masjid kampung berwarna: kubah hijau, menara, pagar [keadaan: dinding, kubah]
- massa_api: (16 Nov) massa api raksasa berdenyut (neraka didatangkan); r jari-jari, kuat 0-1 [keadaan: kuat*, r*]
- meja: meja di depan (pakai depan:true); w lebar [keadaan: w]
- meja_belajar: meja + lampu + buku + laptop; {lampu 0-1, laptop} [keadaan: lampu*, laptop]
- meja_kantor: meja kerja + monitor + kursi kantor; {layar} [keadaan: layar]
- menara: menara putih (pilot tanda kiamat): badan pucat, satu sisi tersinari emas, balkon dua tingkat, kubah kecil; cahaya 0-1 = pendar di sekelilingnya [keadaan: cahaya*]
- menara_pengawas: menara pengawas; penjaga 0-1 membuka celah pengamatan [keadaan: penjaga*]
- mik: mikrofon podcast di meja (7 Nov): {arah ±1 = arah mulut, tinggi}; pangkal di (0,0) = permukaan meja [keadaan: arah, tinggi]
- mobil_luar: mobil taksi online tampak samping + stiker pintu (7 Nov): {warna, aksen, stiker, sub, arah ±1, jalan px/dtk roda berputar} [keadaan: aksen, aksen2, arah, jalan*, stiker, sub]
- monitor: layar besar di dinding (7 Nov): {w, h, judul (layar diam), nama, teks, komentar (detik relatif benda), suka}; komentar muncul membesar + teks diketik [keadaan: h, judul, komentar, nama, suka, teks, ukuran, w]
- motor: motor matic tampak samping; {warna, arah -1}. Titik kait: KAIT.motor (jok, setang, dek kaki) [keadaan: arah]
- naungan_kelompok: awan peneduh + bayangan nyata untuk kelompok; luas 0-1, kuat 0-1 [keadaan: kuat*, luas*]
- ngarai: dinding besi-tembaga Zulkarnain di celah dua gunung (QS 18:93-97). x,y = kaki dinding; lubang 0-1 (galian, inti terang = hampir tembus), jebol 0-1, kilap = detik dinding "utuh kembali" [keadaan: gaya, jebol*, kilap, lubang*, lx, ly]
- nur: cahaya lembut setinggi orang menandai nabi (TIDAK digambar sosoknya): fokus, tidak silau, nama di bawah (nama_letak "atas" = di atas cahaya) [keadaan: nama, nama_letak, nama_s]
- obat: botol obat + strip
- ombak: banjir / laut badai berlapis (15 Nov): y = permukaan air; tinggi = amplitudo px (300 = "laksana gunung"); lapis, jarak, panjang, cepat, warna [atas, bawah], buih [keadaan: buih, cepat, jarak, kilap*, lapis, panjang, tinggi*]
- pagar: pagar besi/kayu sepanjang w; {w, warna, model: kayu|tembok} [keadaan: model, w]
- pancar: mata air memancar dari bumi (QS 54:12): kuat 0-1, tinggi px [keadaan: kuat*, tinggi]
- pantai: pantai: laut dari cakrawala (y=-ting) ke garis pantai (y=0) + pasir; ombak bergerak; {tinggi, warna [jauh, dekat]} [keadaan: tinggi]
- pedang_tersarung: pedang selalu tersarung; tidak menyediakan adegan kekerasan [keadaan: ornamen*]
- pemimpin: siluet pemimpin di atas batu; angkat 0-1 = lengan terangkat [keadaan: angkat*, rim*]
- penggali: siluet mengayun beliung ke satu titik. x,y = titik gali; aktif 0|1, pulang 0-1 (berbalik lalu pergi ke samping-depan), n, rim [keadaan: aktif*, n, pulang*, rim*]
- perahu_kecil: perahu kecil kayu; goyang 0-1 mengatur olengan [keadaan: goyang*, muatan*]
- petir: kilat bercabang + kilasan langit; saat = [detik relatif shot, ...]; (0,0) = pangkal di atas [keadaan: saat]
- pintu_kota_kuno: pintu gerbang kota kuno; buka 0-1 membuka daun pintu [keadaan: buka*, tinggi]
- pisang: pohon pisang [keadaan: buah]
- pohon: -
- ponsel: HP besar (bidikan dekat) dengan notifikasi: {judul, teks, jam, getar 0-1, notif_at (detik relatif shot), merah} [keadaan: aplikasi, getar*, jam, judul, merah, notif, notif_at, tanggal]
- pot: tanaman pot; {jenis: monstera|palem|bunga, warna_pot} [keadaan: tanaman, warna_pot]
- rak_buku: rak buku 4 susun berisi buku warna-warni; {w, warna, seed} [keadaan: w]
- rak_kitab: rak kitab kayu; isi 0-1 mengatur kepadatan kitab [keadaan: isi*]
- ranjang_rs: ranjang rumah sakit + selimut; dudukan/permukaan y -150 [keadaan: pagar]
- rantai: rantai tanggungan (gaya Papan): {node:[{teks,warna}], jeda, loop:true} [keadaan: jeda, node]
- rantai_belenggu: mata rantai besar dan borgol; tegang 0 kendur, 1 lurus [keadaan: n, tegang*]
- rantai_tarik: (16 Nov) puluhan rantai tegang dari luar layar menuju (0,0); tarik = jarak geser mata rantai (px, boleh [[t,v]]); n; malaikat TIDAK digambar [keadaan: n, putar, r0, tarik*]
- resapan_tanah: penampang tanah; kedalaman 0-1, alir 0-1, garis rembesan bergerak [keadaan: alir*, kedalaman*]
- retakan: tanah merekah: celah gelap bercahaya dari dalam + debu naik. buka 0-1 (lebar celah), cahaya warna pijar, goyang getaran halus, seed varian bentuk [keadaan: buka*, cahaya, goyang]
- rumah: -
- rumah_kampung: rumah kampung: dinding, atap genteng, pintu, jendela, teras; {w, dinding, atap, pintu, lampu 0-1, buka 0-1} [keadaan: atap, buka*, dinding, lampu*, pintu, w]
- rumah_sakit_gedung: gedung rumah sakit (tampak luar) [keadaan: nama]
- rumput: rumpun rumput bergoyang; {n, w} [keadaan: n, w]
- saf: barisan orang tampak belakang (siluet, cahaya tepi emas dari depan); n per baris, baris, jarak [keadaan: baris, jarak, n]
- sajadah: -
- sapu: sapu ijuk; rot = sudut (derajat), pangkal di (0,0) [keadaan: rot*]
- sawah: hamparan sawah bertingkat dari cakrawala (y=0) ke depan; {w, gubuk, hijau 0-1 (0 = menguning)} [keadaan: gubuk, hijau*, w]
- sekolah: gedung sekolah dua lantai + tiang bendera + papan nama [keadaan: atap, dinding, nama]
- semak: semak/perdu, opsional bunga [keadaan: bunga, w]
- setir: setir mobil di depan pengemudi (7 Nov): {putar derajat|[[t,v]]} [keadaan: putar*]
- sofa: sofa; dudukan y -125. {w, warna, bantal} [keadaan: bantal, w]
- sumur: sumur batu; air 0-1 mengatur tinggi air [keadaan: air*, timba*]
- sungai: sungai bertepi jelas; arus 0-1 mengatur kecepatan riak yang bergerak [keadaan: arus*, lebar]
- surya: matahari besar di cakrawala (piringan + pendar emas + sinar tipis); r jari-jari, terang 0-1 [keadaan: r*, terang*]
- tebing: puncak batu curam; (0,0) = pijakan di puncak; cahaya dari kiri-atas
- telaga: - [keadaan: h, kilau, w]
- tenda_badui: tenda badui kain bergaris; buka 0-1 membuka tirai [keadaan: buka*]
- tiang_listrik: tiang listrik + kabel menjuntai ke kanan/kiri [keadaan: kabel]
- timbangan: timbangan emas berornamen [keadaan: miring*]
- toko: ruko/toko kota: rolling door, papan nama {nama, warna} [keadaan: nama]
- tv: meja TV + televisi; {nyala 0-1, warna_layar} [keadaan: nyala*, warna_layar]
- uang: tumpukan uang kertas generik dikipas: {n, kipas 0-1, nilai} [keadaan: kipas*, n, nilai]
- ular_siluet: ular berupa siluet sederhana, tidak agresif; gerak 0-1 mengubah gelombang [keadaan: gerak*]
- unta: -
- warung: warung kelontong: etalase, kanopi garis, toples, papan nama {nama} [keadaan: kanopi, nama, w]
- zaqqum: (16 Nov) pohon zaqqum: batang hitam berpilin, dahan berduri, buah bara menyala (QS 44:43-46). tumbuh 0-1, nyala 0-1 [keadaan: nyala*, tumbuh*]

## Kemampuan tokoh (shot.boneka[])
- pose diam: berdiri, duduk, mengendarai_motor, duduk_samping, pegang_tongkat, pegang_kendi, pegang_lentera, pegang_keranjang, pegang_tasbih, pegang_surat, pegang_gulungan, pegang_karung_kecil, pegang_roti, pegang_koin, menolong, peluk_lutut, tutup_wajah, duduk_tutup_wajah, pegang_hp, duduk_hp, telepon, lambai, tangan_dada, doa, tunjuk, berkacak, tepuk, kaget, rebahan, rebahan_hp, jelaskan, angkat_bahu, tunjuk_atas, stop, dua_naik, silang, tepuk_dahi, condong, lemas
- aksi berulang: angkat, bangkit, berdoa, dagu, gali, jalan, joget, kepala, lari, lompat, melambai, menenangkan, menengadah, mengangguk, menggeleng, palu, pinggang, tergelincir, tertawa, tutup, tutup_telinga, ulurkan
- hadap: depan, kanan, kiri (kanan/kiri = tampak samping utuh, badan dan kaki ikut menyamping)
- benda yang dapat dipegang: gulungan, hp, karung_kecil, kendi, keranjang, koin, lentera, roti, surat, tasbih, tongkat
- bisa dinaiki/diduduki (kait): motor (samping), perahu_kecil (samping), kursi (depan), sofa (depan), kasur (depan). Tokoh menempel otomatis: duduk di jok, tangan di setang, kaki di pijakan
- penutup_kepala tokoh: imamah, kain, kopiah, mahkota, nemes (warna_penutup opsional). nemes = kain kepala bergaris raja Mesir kuno (+ kobra kecil di dahi; ureus: false untuk membuang); mahkota = mahkota emas raja. Raja Mesir kuno/Firaun: penutup_kepala "nemes" + janggut true + janggut_model "firaun" + pakaian {"jenis": "jubah", "bisht": true, "kalung": "usekh"}. Jasad/tak bernyawa: pose rebahan + mata "tutup", tanpa luka
- suku figuran: umum, arab. arab = laki-laki berjubah dengan imamah/ghutrah/peci (sebagian berbisht), perempuan berkerudung dan abaya gelap

## Katalog efek suara (rekaman[].berkas = ../../aset/suara/<nama>.mp3)
Suasana (diulang di bawah narasi):
- air_mengalir: aliran air
- angin_gurun: angin padang tandus
- angin_sejuk: angin lembut
- bawah_laut: dalam air, teredam
- detak_jantung: detak jantung, cemas
- dengung_haru: dengung lembut, haru
- didih: air mendidih
- drone_gelap: dengung gelap, mencekam
- gemuruh_api: api besar menyala
- guntur_hujan: hujan badai dan guntur
- jam_dinding: detik jam, waktu berjalan
- jangkrik: malam di desa
- kerumunan_cemas: kerumunan orang gelisah
- laut_malam: ombak laut malam
- malam_hening: malam sunyi
- napas_berat: napas berat, lelah/takut
- panas_naik: panas menyengat
- ratapan_jauh: ratapan dari jauh
- rumah_sore: suasana rumah sore
- senandung_gelap: senandung muram
- senandung_haru: senandung haru
Efek (sekali bunyi):
- braam: hantaman sinematik berat (pembuka/kejutan besar)
- dentum_jauh: dentuman dari jauh
- halaman_buku: halaman dibalik
- hentak_serius: hentakan tegas
- isak_lembut: isak tangis pelan
- kertas_amplop: kertas/surat
- kilau_cahaya: cahaya muncul, berkilau
- koin_jatuh: koin/harta jatuh
- langkah_lari: langkah berlari
- langkah_pelan: langkah pelan
- palu_kayu: palu/ketukan kayu
- pintu_besi: pintu besi berat
- rantai_seret: rantai diseret
- stempel: cap/ketetapan
- tanah_retak: tanah/dinding retak, runtuh
- tetes: tetesan
- timbangan_denting: denting timbangan/logam
- whoosh: sapuan cepat, perpindahan
Intonasi narasi: tenang, berat, tegang, bisik, tegas, haru, lega
