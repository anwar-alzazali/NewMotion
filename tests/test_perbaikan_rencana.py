from newmotion.paket_genre.kisah_islami.perbaikan_rencana import perbaiki_rencana
from newmotion.paket_genre.kisah_islami.rencana_sutradara import validasi_rencana

NARASI = ["Firaun dan tentaranya mengejar sampai ke tepi laut.",
          "Nabi Musa dan pengikutnya menyeberangi dasar laut.",
          "Laut menutup kembali."]


def _rusak():
    return {"objek_inti": {"jenis": "naga_laut"}, "suku": "mesir", "beat": [
        {"beat": 1, "bukti": "Firaun mengejar dengan marah", "kamu": "pahlawan",
         "subjek": [{"jenis": "kereta_perang", "tempat": "tengah"},
                    {"jenis": "laut_terbelah", "tempat": "atas", "keadaan": {"belah": [0, 1], "warna_x": 3, "lebar": [100, 200]}}],
         "kamera": {"bidikan": "ultra", "aksen": "zoom"}, "teks_layar": "FIRAUN MENGEJAR DENGAN SELURUH BALA TENTARANYA SAMPAI KE LAUT",
         "klimaks": "ya", "suara": {"suasana": "badai_salju", "intonasi": "marah",
                                    "efek": [{"nama": "braam", "pada": "tidak ada", "keras": "sangat", "ulang": 99}, {"nama": "x"}]},
         "figuran": [{"jumlah": 40, "tempat": "di_lorong:laut_terbelah", "gerak": "menari_salto", "hadap": "atas",
                      "suku": "mesir", "pegang": "pedang"}]},
        {"beat": 2, "bukti": "menyeberangi dasar laut", "subjek": [{"jenis": "laut_terbelah"}],
         "figuran": [{"jumlah": 3, "tempat": "tengah", "gerak": "jalan"}]},
        {"beat": 2, "bukti": "ganda"},
        {"beat": 9, "bukti": "di luar rentang"},
    ]}


def test_rencana_rusak_diperbaiki_sampai_lolos_validator():
    r = _rusak()
    catat = perbaiki_rencana(r, NARASI)
    assert validasi_rencana(r, NARASI) == []
    assert [b["beat"] for b in r["beat"]] == [1, 2, 3]
    b1, b2 = r["beat"][0], r["beat"][1]
    assert b1["belum_ada"][0]["nama"] == "kereta_perang" and "kereta_perang" not in [s["jenis"] for s in b1["subjek"]]
    assert b1["subjek"][0]["keadaan"] == {"belah": [0, 1], "lebar": 200}   # parameter asing dibuang, lebar tak beranimasi
    assert b1["figuran"][0]["jumlah"] == 6 and b1["figuran"][0]["tempat"] == "di_lorong:laut_terbelah"
    assert "figuran" not in b2 and b2["subjek"][-1]["jenis"] == "arus"       # adab: beat menyebut nabi -> siluet
    assert any("beat 3 hilang" in c for c in catat)


def test_perbaikan_tidak_mengubah_rencana_yang_sudah_benar():
    r = {"objek_inti": None, "beat": [{"beat": i, "bukti": NARASI[i - 1][:10], "subjek": [], "kamu": "tidak",
                                       "kamera": {"bidikan": "lebar", "aksen": None}, "teks_layar": "A\nB",
                                       "klimaks": False} for i in (1, 2, 3)]}
    import copy
    awal = copy.deepcopy(r)
    assert perbaiki_rencana(r, NARASI) == [] and r == awal
