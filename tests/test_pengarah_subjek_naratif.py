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
    retak = arahkan_subjek("Dinding besi di celah dua gunung mulai retak.", 4.0)["benda"][0]
    lubang = arahkan_subjek("Lubang pada dinding besi di celah dua gunung semakin membesar.", 4.0)["benda"][0]
    jebol = arahkan_subjek("Dinding besi di celah dua gunung itu akhirnya jebol.", 4.0)["benda"][0]
    assert retak["jenis"] == lubang["jenis"] == jebol["jenis"] == "ngarai"
    assert retak["lubang"] < lubang["lubang"] < jebol["lubang"]
    assert jebol["jebol"] == 1


def test_penggali_dan_pemimpin_ditampilkan_sebagai_subjek_terpisah():
    jenis = _jenis("Para penggali mengikis dinding besi di celah dua gunung. Pemimpin mereka mengangkat tangan.")
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
    hasil = arahkan_subjek("Sembilan ratus lima puluh tahun berlalu, lalu dinding besi di celah dua gunung itu jebol.", 5.0)
    # Kata angka yang ditulis huruf tidak ditebak menjadi angka; kata klimaks tetap ditandai.
    assert hasil["klimaks"] is True
    assert any(b["jenis"] == "ngarai" and b["jebol"] == 1 for b in hasil["benda"])


def test_hasil_deterministik_tanpa_judul_cerita():
    teks = "Kapal berlayar di tengah ombak."
    assert arahkan_subjek(teks, 5.0) == arahkan_subjek(teks, 5.0)



def test_kata_kerja_menggali_memunculkan_penggali():
    assert "penggali" in _jenis("Mereka menggali dinding besi di celah dua gunung setiap hari.")


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
    jenis = _jenis("Dinding besi di celah dua gunung digali setiap hari dan dijaga oleh kaum itu.")
    assert {"ngarai", "penggali", "kerumunan"} <= jenis


def test_air_tidak_pernah_dipetakan_ke_kerumunan_berlari():
    assert "arus" not in _jenis("Mereka meminum habis air.")
    assert "arus" not in _jenis("Air mata mengalir di pipinya.")
    assert "arus" not in _jenis("Mata air memancar dari bumi.")


def test_mata_air_memakai_renderer_pancar_bukan_kerumunan():
    jenis = _jenis("Mata air memancar dari bumi.")
    assert "pancar" in jenis
    assert "arus" not in jenis
    assert "kerumunan" not in jenis


def test_lubang_dan_dinding_kubur_tidak_memakai_dinding_zulkarnain():
    assert "ngarai" not in _jenis("Lubang kubur itu sempit.")
    assert "ngarai" not in _jenis("Dinding kubur menghimpitnya.")
    assert "penggali" not in _jenis("Mereka menggali kubur.")


def test_kabah_tidak_digambar_sebagai_rumah_biasa():
    assert "rumah" not in _jenis("Rumah Allah, Ka'bah, menjadi arah kiblat.")


def test_pemimpin_yang_merujuk_rasulullah_tidak_menjadi_sosok_manusia():
    jenis = _jenis("Rasulullah, pemimpin umat ini, berdiri di depan para sahabat.")
    assert "pemimpin" not in jenis
    assert "kerumunan" not in jenis
    assert "arus" not in jenis


def test_sosok_pemuka_kaum_di_kalimat_terpisah_tetap_dapat_diarahkan():
    jenis = _jenis("Nabi Nuh membuat kapal. Pemuka kaumnya lewat dan mengejek.")
    assert "pemimpin" in jenis


def test_dinding_generik_tanpa_konteks_besi_dua_gunung_tidak_ditebak():
    assert "ngarai" not in _jenis("Dinding rumah itu mulai retak.")
    assert "ngarai" not in _jenis("Lubang pada tembok itu membesar.")



def test_segmen_yang_menyebut_sahabat_tidak_menyisipkan_siluet_di_kalimat_lain():
    jenis = _jenis("Para sahabat berkumpul. Rasulullah kemudian menyampaikan nasihat.")
    assert "kerumunan" not in jenis
    assert "arus" not in jenis


def test_air_biasa_tidak_diberi_visual_kerumunan_atau_mata_air():
    for teks in (
        "Mereka meminum habis air.",
        "Air mengalir di sungai.",
        "Air mata mengalir di pipinya.",
        "Hujan membawa aliran air ke lembah.",
    ):
        assert not ({"arus", "kerumunan", "pancar"} & _jenis(teks))


def test_konteks_zulkarnain_harus_eksplisit_sebelum_dinding_digambar():
    assert "ngarai" not in _jenis("Dinding batu itu retak dan mulai runtuh.")
    assert "ngarai" not in _jenis("Mereka menggali lubang besar di tanah.")
    assert "ngarai" in _jenis("Zulkarnain membangun dinding besi di celah dua gunung.")


def test_pengarah_menyimpan_narasi_sumber_untuk_penjaga_adab():
    from newmotion.paket_genre.kisah_islami.pengarah_naskah import arahkan

    spek = arahkan({
        "judul": "Nasihat Rasulullah",
        "adegan": [{
            "nama": "nasihat",
            "teks": "Rasulullah, pemimpin umat ini, berdiri di depan para sahabat.",
        }],
    })
    shot = spek["cerita"]["shot"][0]
    assert shot["_narasi"] == "Rasulullah, pemimpin umat ini, berdiri di depan para sahabat."
    assert not any(
        benda.get("jenis") in {"pemimpin", "penggali", "kerumunan", "arus"}
        for benda in shot.get("benda", [])
    )



def test_konteks_dinding_zulkarnain_dapat_diteruskan_lintas_adegan():
    from newmotion.paket_genre.kisah_islami.pengarah_subjek import arahkan_subjek

    konteks = (
        "Zulkarnain membangun dinding besi di celah dua gunung. "
        "Ya'juj dan Ma'juj menggali dinding itu setiap hari."
    )
    hasil = arahkan_subjek("Mereka menggali setiap hari sampai hampir tembus.", 4.0, konteks=konteks)
    jenis = {benda["jenis"] for benda in hasil["benda"]}
    assert {"ngarai", "penggali"} <= jenis


def test_konteks_yajuj_mengizinkan_dinding_disebut_kembali_tanpa_mengarang_bentuk_lain():
    from newmotion.paket_genre.kisah_islami.pengarah_subjek import arahkan_subjek

    konteks = "Zulkarnain membangun dinding besi di celah dua gunung untuk menahan Ya'juj dan Ma'juj."
    jenis = {
        benda["jenis"]
        for benda in arahkan_subjek("Dinding itu kembali utuh keesokan harinya.", 4.0, konteks=konteks)["benda"]
    }
    assert "ngarai" in jenis
    assert "rumah" not in jenis


def test_pemimpin_yajuj_tetap_dapat_diarahkan_meski_allah_disebut_di_kalimat_berdekatan():
    from newmotion.paket_genre.kisah_islami.pengarah_subjek import arahkan_subjek

    jenis = _jenis("Allah menetapkan waktunya. Hari itu pemimpin mereka berkata: pulanglah.")
    assert "pemimpin" in jenis


def test_penggalian_kubur_tetap_tidak_diarahkan_meski_konteks_kisah_menyebut_zulkarnain():
    from newmotion.paket_genre.kisah_islami.pengarah_subjek import arahkan_subjek

    konteks = "Zulkarnain membangun dinding besi di celah dua gunung. Kemudian mereka menggali kubur."
    jenis = {
        benda["jenis"]
        for benda in arahkan_subjek("Mereka menggali kubur.", 4.0, konteks=konteks)["benda"]
    }
    assert "ngarai" not in jenis
    assert "penggali" not in jenis



def test_satu_shot_yang_menyebut_sahabat_tidak_menyisipkan_siluet_kelompok_di_kalimat_lain():
    jenis = _jenis("Para sahabat berkumpul. Orang-orang berlarian di kejauhan.")
    assert "kerumunan" not in jenis
    assert "arus" not in jenis


def _arahkan_satu(teks):
    from newmotion.application.pengarah_inti import arahkan_naskah
    spek, _, _ = arahkan_naskah({"judul": "uji", "genre": "kisah_islami", "konteks_konten": "islami",
                                 "adegan": [{"nama": "a1", "teks": teks}]})
    return spek["cerita"]["shot"]


def test_dinding_zulkarnain_tidak_tertutup_latar_gunung():
    # Renderer menggambar benda `belakang` lebih dulu; gunung latar akan menimpa dinding.
    for shot in _arahkan_satu("Dinding besi Zulkarnain digali setiap hari oleh Ya'juj dan Ma'juj."):
        jenis = [b["jenis"] for b in shot["benda"]]
        if "ngarai" in jenis:
            assert not {"gunung", "tebing", "kota"} & set(jenis)


def test_tokoh_kamu_menjadi_saksi_saat_pelaku_cerita_tampil():
    for shot in _arahkan_satu("Setiap hari mereka menggali dinding besi Zulkarnain, sampai hampir tembus."):
        if any(b["jenis"] == "penggali" for b in shot["benda"]):
            kamu = shot["boneka"][0]
            assert kamu["belakang"] is True and kamu["s"] <= 0.6 and kamu["y"] >= 1900
            assert shot["kamera"]["x"] == 540 and shot["kamera"]["z"][0] == 1.0
            batu = [b for b in shot["benda"] if b["jenis"] == "batu" and b.get("depan")]
            assert all((b["x"] > 540) != (kamu["x"] > 540) for b in batu)


def test_kamu_tetap_tokoh_utama_bila_subjek_hanya_suasana():
    # Mahsyar: "kamu" adalah pelaku; kerumunan latar tidak membuatnya mundur.
    for shot in _arahkan_satu("Manusia tenggelam dalam keringatnya, dan keringatmu sampai mana?"):
        assert not shot["boneka"][0].get("belakang") or shot["boneka"][0]["s"] > 0.55


def test_dinding_kembali_utuh_tanpa_lubang():
    from newmotion.paket_genre.kisah_islami.pengarah_subjek import arahkan_subjek
    konteks = "Dinding besi itu dibangun Zulkarnain untuk mengurung Ya'juj dan Ma'juj."
    teks = "Esoknya, dinding itu sudah kembali utuh."
    ngarai = [b for b in arahkan_subjek(teks, 4.0, 0, konteks=konteks + " " + teks)["benda"] if b["jenis"] == "ngarai"]
    assert ngarai and ngarai[0]["lubang"] == 0.0


def test_penggali_menggali_di_lubang_dinding():
    # Papan Ya'juj 1: kaki dinding di cakrawala, titik gali = lubang (kaki - 190 * s).
    shots = _arahkan_satu("Setiap hari mereka menggali dinding besi Zulkarnain, sampai hampir tembus.")
    shot = next(s for s in shots if any(b["jenis"] == "penggali" for b in s["benda"]))
    dinding = next(b for b in shot["benda"] if b["jenis"] == "ngarai")
    gali = next(b for b in shot["benda"] if b["jenis"] == "penggali")
    assert dinding["y"] == shot["horizon"]
    assert gali["x"] == dinding["x"] + (dinding.get("lx") or 0) * dinding["s"]
    assert gali["y"] == round(dinding["y"] + dinding.get("ly", -190) * dinding["s"])


def test_surya_subjek_rencana_di_langit_dan_bisa_membesar():
    """Temuan pemeriksa visual Mahsyar: matahari subjek jatuh di tanah (tertutup), dan r
    berkunci waktu tidak digambar. Kini duduk di atas cakrawala dan r dianimasikan renderer."""
    import json
    from pathlib import Path

    from newmotion.application.katalog_renderer import katalog
    from newmotion.application.pengarah_inti import arahkan_naskah
    from newmotion.paket_genre.kisah_islami.rencana_sutradara import terapkan_rencana

    naskah = json.loads((Path(__file__).parent / "data" / "tolok_ukur" / "mahsyar1.json").read_text(encoding="utf-8"))
    n = len(naskah["adegan"])
    rencana = {"beat": [{"beat": i, "bukti": naskah["adegan"][i - 1]["teks"].split()[0], "kamu": "tidak",
                         "subjek": [{"jenis": "surya", "tempat": "tengah", "keadaan": {"r": [120, 300]}}]}
                        for i in range(1, n + 1)]}
    spek, _, _ = arahkan_naskah(terapkan_rencana(naskah, rencana))
    dicek = 0
    for sh in spek["cerita"]["shot"]:
        for b in sh["benda"]:
            if b["jenis"] == "surya" and isinstance(b.get("r"), list):
                assert b["y"] + 300 * 0.2 <= sh["horizon"] and not b.get("belakang")
                dicek += 1
    assert dicek >= n
    assert "r" in katalog()["surya"]["animasi"]
