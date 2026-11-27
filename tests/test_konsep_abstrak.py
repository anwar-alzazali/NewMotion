"""Kontrak visual untuk empat konsep abstrak Kisah Islami."""
from newmotion.application.katalog_renderer import katalog_subjek
from newmotion.paket_genre.kisah_islami.rencana_sutradara import validasi_rencana


KONSEP = {
    "genangan_tubuh": {"tinggi": [35, 440], "riak": [0, 1]},
    "resapan_tanah": {"kedalaman": [0.2, 1], "alir": [0, 1]},
    "naungan_kelompok": {"luas": [0.2, 1], "kuat": [0, 1]},
    "timbangan": {"miring": [-18, 18]},
}


def test_katalog_mencatat_semua_konsep_dan_parameter_animasi():
    kat = katalog_subjek()
    assert set(KONSEP) <= set(kat)
    for jenis, parameter in KONSEP.items():
        assert set(parameter) <= set(kat[jenis]["parameter"])
        assert set(parameter) <= set(kat[jenis]["animasi"])


def test_rencana_sutradara_bisa_memilih_dan_menganimasikan_konsep():
    for jenis, keadaan in KONSEP.items():
        rencana = {
            "beat": [{
                "beat": 1,
                "bukti": "Konsep ini berubah sepanjang adegan",
                "subjek": [{"jenis": jenis, "tempat": "tengah", "keadaan": keadaan}],
                "kamu": "tidak",
                "kamera": {"bidikan": "lebar", "aksen": None},
                "klimaks": False,
            }]
        }
        assert validasi_rencana(rencana, ["Konsep ini berubah sepanjang adegan"]) == []


def test_siluet_manusia_umum_dilarang_untuk_tokoh_sakral():
    for jenis in ("genangan_tubuh", "naungan_kelompok"):
        rencana = {
            "beat": [{
                "beat": 1,
                "bukti": "Nabi berdiri di tengah kaum",
                "subjek": [{"jenis": jenis, "tempat": "tengah", "keadaan": {}}],
                "kamu": "tidak",
                "kamera": {"bidikan": "lebar", "aksen": None},
                "klimaks": False,
            }]
        }
        galat = validasi_rencana(rencana, ["Nabi berdiri di tengah kaum"])
        assert any("tokoh sakral" in x for x in galat)
