"""Uji pengarah subjek dengan narasi generik dan cerita di luar empat tolok ukur."""
from newmotion.paket_genre.kisah_islami.pengarah_subjek import arahkan_subjek


def _jenis(teks):
    return {benda["jenis"] for benda in arahkan_subjek(teks, 4.0)["benda"]}


def test_kapal_yang_berlayar_harus_tampak_dan_bergerak():
    hasil = arahkan_subjek("Kapal itu berlayar di tengah ombak.", 5.0)
    jenis = {benda["jenis"] for benda in hasil["benda"]}
    assert {"bahtera", "ombak"} <= jenis
    kapal = next(b for b in hasil["benda"] if b["jenis"] == "bahtera")
    assert isinstance(kapal["x"], list)
    assert kapal["goyang"] > 1


def test_dinding_berkembang_dari_retak_ke_lubang_hingga_jebol():
    retak = arahkan_subjek("Dinding mulai retak.", 4.0)["benda"][0]
    lubang = arahkan_subjek("Lubang pada dinding semakin membesar.", 4.0)["benda"][0]
    jebol = arahkan_subjek("Dinding itu akhirnya jebol.", 4.0)["benda"][0]
    assert retak["jenis"] == lubang["jenis"] == jebol["jenis"] == "ngarai"
    assert retak["lubang"] < lubang["lubang"] < jebol["lubang"]
    assert jebol["jebol"] == 1


def test_penggali_dan_pemimpin_ditampilkan_sebagai_subjek_terpisah():
    jenis = _jenis("Para penggali bekerja, sementara pemimpin mereka mengangkat tangan.")
    assert {"penggali", "pemimpin"} <= jenis


def test_narasi_nuh2_di_luar_tolok_ukur_memunculkan_bahtera():
    # Diambil dari papan/kisah/nuh2_naskah.py, bukan dari empat fixture tolok ukur.
    assert "bahtera" in _jenis("Kapal itu berlayar, di tengah ombak laksana gunung.")


def test_narasi_dabbah2_tidak_mengarang_wujud_makhluk_tanpa_rincian():
    # Dabbah2_naskah.py secara eksplisit menyatakan tidak ada rincian sahih tentang wujudnya.
    assert _jenis("Namanya, Dabbatul Ard. Makhluk dari bumi.") == set()


def test_narasi_kubur1_tidak_menggambar_malaikat():
    # Naskah kubur1.txt memerintahkan malaikat tidak digambar; pengarah tidak menebak wujud.
    assert _jenis("Lalu dua malaikat datang dan mendudukkanmu.") == set()


def test_angka_dan_momen_klimaks_mendapat_teks_dan_aksen_kamera():
    hasil = arahkan_subjek("Sembilan ratus lima puluh tahun berlalu, lalu dinding itu jebol.", 5.0)
    # Kata angka yang ditulis huruf tidak ditebak menjadi angka; kata klimaks tetap ditandai.
    assert hasil["klimaks"] is True
    assert any(b["jenis"] == "ngarai" and b["jebol"] == 1 for b in hasil["benda"])


def test_hasil_deterministik_tanpa_judul_cerita():
    teks = "Kapal berlayar di tengah ombak."
    assert arahkan_subjek(teks, 5.0) == arahkan_subjek(teks, 5.0)



def test_kata_kerja_menggali_memunculkan_penggali():
    assert "penggali" in _jenis("Mereka menggali dinding setiap hari.")


def test_efek_keringat_resapan_dan_naungan_masuk_ke_shot():
    from newmotion.paket_genre.kisah_islami.pengarah_naskah import arahkan

    spek = arahkan({
        "judul": "Perubahan keadaan lingkungan",
        "adegan": [
            {"nama": "keringat", "teks": "Keringat meresap ke dalam tanah."},
            {"nama": "naungan", "teks": "Tujuh golongan mendapat naungan."},
        ],
    })
    pertama, kedua = spek["cerita"]["shot"]
    assert pertama["resap"]["p"] > 0
    assert pertama["boneka"][0]["keringat"] == 1
    assert pertama["boneka"][0]["genangan"] > 0
    assert kedua["naungan"]["kuat"] == 1



def test_kata_angka_dalam_narasi_muncul_sebagai_teks_layar():
    hasil = arahkan_subjek("Sembilan ratus lima puluh tahun telah berlalu.", 4.0)
    assert any("SEMBILAN RATUS LIMA PULUH TAHUN" in item["teks"] for item in hasil["teks"])


def test_dinding_yang_digali_dan_kaum_dikenali_tanpa_judul_khusus():
    jenis = _jenis("Dinding yang digali setiap hari dijaga oleh kaum itu.")
    assert {"ngarai", "penggali", "kerumunan"} <= jenis
