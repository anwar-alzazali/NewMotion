from newmotion.application.antrean_naskah import _rapikan_suasana
from newmotion.paket_genre.kisah_islami.pengarah_naskah import _waktu_dan_air


def test_suasana_tanpa_dasar_jadi_waktu_terakhir_atau_siang():
    n = {"dalil": [], "beat": [
        {"narasi": "Firaun hampir tenggelam.", "suasana": "malam"},          # tanpa dasar, belum ada waktu -> siang
        {"narasi": "Saat matahari terbit, mereka tersusul.", "suasana": "dhuha"},
        {"narasi": "Laut terbelah.", "suasana": "senja"},                    # tanpa dasar -> berlanjut dhuha
        {"narasi": "Di padang Mahsyar semua dibangkitkan."},                 # alam akhirat disebut
        {"narasi": "Jangan putus asa."},                                     # akhirat tidak berlanjut -> dhuha
    ]}
    _rapikan_suasana(n)
    assert [b["suasana"] for b in n["beat"]] == ["siang", "dhuha", "dhuha", "mahsyar", "dhuha"]
    assert len(n["peringatan"]) == 2


def _shot():
    return {"palet": "malam", "malam": 1, "horizon": 1430, "benda": [{"jenis": "bintang"}]}


def test_bawaan_siang_dan_air_satu_palet():
    s = _shot()
    laut = {"jenis": "laut_terbelah", "x": 540, "y": 1320, "s": 0.82}
    _waktu_dan_air(s, [laut], None, "laut terbelah", "laut")
    assert s["palet"] == "pantai_siang" and s["malam"] == 0 and not any(o["jenis"] == "bintang" for o in s["benda"])
    assert laut["warna"][1] == "#3f8ac9" and s["horizon"] < 1000
    p = {"jenis": "pantai", "y": 1450, "tinggi": 330}
    _waktu_dan_air(_shot(), [p], "dhuha", "jasad di pantai", "laut")
    assert p["warna"] == ["#3f8ac9", "#6ac9d9"]


def test_akhirat_tetap_khas():
    s = {"palet": "neraka", "malam": 0, "horizon": 1000, "benda": []}
    _waktu_dan_air(s, [], "neraka", "api neraka", "neraka")
    assert s["palet"] == "neraka"
    s2 = {"palet": None, "horizon": 1000, "benda": []}
    _waktu_dan_air(s2, [], None, "padang mahsyar", "mahsyar")
    assert s2["palet"] is None
