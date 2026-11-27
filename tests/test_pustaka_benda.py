"""Kontrak pustaka benda baru: semua jenis terdaftar dan punya parameter keadaan."""
from newmotion.application.katalog_renderer import katalog, katalog_subjek

BARU = {
    "tenda_badui": "buka", "sumur": "air", "kebun_kurma": "buah",
    "ladang_gandum": "matang", "sungai": "arus", "perahu_kecil": "goyang",
    "lentera": "nyala", "api_unggun": "nyala", "pintu_kota_kuno": "buka",
    "karung": "penuh", "keranjang": "penuh", "kambing": "jalan",
    "domba": "jalan", "burung_kawanan": "terbang", "ular_siluet": "gerak",
    "kapal_dagang": "muatan", "menara_pengawas": "penjaga", "rak_kitab": "isi",
    "jam_pasir": "sisa", "rantai_belenggu": "tegang", "pedang_tersarung": "ornamen",
    "awan_badai": "hujan", "kios_pasar": "dagangan", "awan_gelap": "kilat",
}


def test_pustaka_benda_baru_terdaftar_dan_memiliki_parameter_keadaan():
    semua = katalog()
    subjek = katalog_subjek()
    for nama, parameter in BARU.items():
        assert nama in semua, f"{nama} tidak terbaca dari cerita.js"
        assert nama in subjek, f"{nama} tidak boleh dipilih sutradara"
        assert parameter in semua[nama]["parameter"], f"{nama}: parameter {parameter} tidak dibaca"
        assert parameter in semua[nama]["animasi"], f"{nama}: parameter {parameter} tidak dianimasikan"


def test_pustaka_benda_baru_tidak_menghapus_katalog_lama():
    semua = katalog()
    for nama in ("bahtera", "nur", "timbangan", "rumah_kampung", "hewan", "zaqqum"):
        assert nama in semua
