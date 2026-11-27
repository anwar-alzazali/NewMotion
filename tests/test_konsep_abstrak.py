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


def test_pengarah_aturan_mengenali_semua_jenis_konsep_abstrak():
    from newmotion.paket_genre.kisah_islami.pengarah_naskah import _validasi_benda

    for jenis in KONSEP:
        spek = {"cerita": {"shot": [{"benda": [{"jenis": jenis}], "boneka": []}]}}
        assert _validasi_benda(spek) == []


def test_penjaga_adab_menolak_siluet_konsep_abstrak_di_shot_tokoh_sakral():
    from newmotion.paket_genre.kisah_islami.penjaga_tokoh import periksa_adab_tokoh

    for jenis in ("genangan_tubuh", "naungan_kelompok"):
        spek = {"cerita": {"shot": [{
            "_narasi": "Nabi Musa berdiri di tengah kaum.",
            "benda": [{"jenis": jenis}],
        }]}}
        temuan = periksa_adab_tokoh(spek)
        assert any(x.kode == "BENDA_MANUSIA_TOKOH_SAKRAL" for x in temuan)


def test_penjaga_adab_tidak_melarang_konsep_abstrak_pada_narasi_umum():
    from newmotion.paket_genre.kisah_islami.penjaga_tokoh import periksa_adab_tokoh

    spek = {"cerita": {"shot": [{
        "_narasi": "Orang-orang berkumpul di padang terbuka.",
        "benda": [{"jenis": "naungan_kelompok"}],
    }]}}
    assert not any(
        x.kode == "BENDA_MANUSIA_TOKOH_SAKRAL"
        for x in periksa_adab_tokoh(spek)
    )


def test_genangan_menampilkan_lima_label_ketinggian():
    from pathlib import Path

    renderer = Path(__file__).resolve().parents[1] / "mesin-video" / "papan" / "cerita.js"
    sumber = renderer.read_text(encoding="utf-8")
    for label in ("mata kaki", "lutut", "pinggang", "dada", "mulut"):
        assert f'"{label}"' in sumber
