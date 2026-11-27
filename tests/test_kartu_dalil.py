from pathlib import Path

from newmotion.paket_genre.kisah_islami import kartu_dalil as K
from newmotion.paket_genre.kisah_islami import pengarah_naskah as P
from newmotion.paket_genre.kisah_islami.sutradara_llm import (
    pesan_sutradara,
    validasi_lengkap,
)

PENDEK = "قَالَ كَلَّآ ۖ إِنَّ مَعِىَ رَبِّى سَيَهْدِينِ"
PANJANG = PENDEK * 6


def test_arab_pendek_satu_baris_panjang_ditolak():
    uk, baris = K.tata_arab(PENDEK)
    assert uk >= K.ARAB_MIN_1 and len(baris) == 1
    assert K.tata_arab(PANJANG) is None
    assert K.alasan_tidak_layak("Musa menjawab, sekali-kali tidak.", PENDEK) is None
    assert "Arab" in K.alasan_tidak_layak("x", PANJANG)
    assert "huruf" in K.alasan_tidak_layak("x" * 300, PENDEK)


def test_kartu_muat_di_zona_aman():
    k = K.buat_kartu({"kitab": "QS 26:62", "teks": "Musa menjawab: sekali-kali tidak, sesungguhnya Tuhanku bersamaku.",
                      "arab": PENDEK, "label": "QUR'AN"}, at=1.2)
    _, tinggi = K.tata_kartu(k["teks"], True)
    assert K.ZONA_ATAS <= k["y"] - tinggi * k["s"] / 2 and k["y"] + tinggi * k["s"] / 2 <= K.ZONA_ATAS + K.ZONA_TINGGI + 1
    assert k["arab_baris"] and k["arab_at"] == 0.15 and k["at"] == 1.2


def _naskah(kartu: bool, arab: str):
    rencana = {"beat": 1, "bukti": "Musa menjawab", "subjek": [{"jenis": "pantai", "tempat": "tengah"}], "kamu": "tidak",
               "kamera": {"bidikan": "lebar", "aksen": None}, "teks_layar": "TIDAK GOYAH", "klimaks": False, "kartu_dalil": kartu}
    return {"judul": "Uji", "adegan": [{"nama": "adegan_1", "teks": "Musa menjawab dengan yakin bahwa Tuhannya bersamanya.",
                                        "rencana": rencana}],
            "dalil_dipakai": [{"surah": 26, "ayat": "62", "di_adegan": "adegan_1", "label": "QS ASY-SYU'ARA 62"}]}, arab


def _arahkan(monkeypatch, kartu: bool, arab: str):
    naskah, arab = _naskah(kartu, arab)
    monkeypatch.setattr(P, "_ambil_dalil_untuk_adegan", lambda nama, dd: {
        "kitab": "QS 26:62", "arab": arab, "teks": "Musa menjawab: sekali-kali tidak.", "label": "QUR'AN",
        "sumber": "QS ASY-SYU'ARA 62"} if dd else None)
    return P.arahkan(naskah)["cerita"]["shot"]


def test_dalil_rencana_tidak_menggantikan_adegan_dan_sumber_tampil(monkeypatch):
    shots = _arahkan(monkeypatch, False, PENDEK)
    benda = [b["jenis"] for s in shots for b in s.get("benda", [])]
    assert "kartu_dalil" not in benda and "pantai" in benda
    assert any(t.get("sub") == "QS ASY-SYU'ARA 62" for s in shots for t in s.get("teks", []))


def test_kartu_dipilih_sutradara_muncul_di_atas_adegan(monkeypatch):
    shots = _arahkan(monkeypatch, True, PENDEK)
    benda = [b for s in shots for b in s.get("benda", [])]
    kartu = [b for b in benda if b["jenis"] == "kartu_dalil"]
    assert len(kartu) == 1 and kartu[0]["at"] > 0 and any(b["jenis"] == "pantai" for b in benda)


def test_kartu_yang_tak_terbaca_jadi_label(monkeypatch):
    shots = _arahkan(monkeypatch, True, PANJANG)
    assert not any(b["jenis"] == "kartu_dalil" for s in shots for b in s.get("benda", []))
    assert any(t.get("sub") for s in shots for t in s.get("teks", []))


def test_sutradara_tahu_beat_berdalil_dan_kartu_dibatasi():
    naskah = {"judul": "U", "genre": "kisah_islami", "konteks_konten": "islami",
              "adegan": [{"nama": f"adegan_{i}", "teks": f"kalimat {i} di sini."} for i in range(1, 5)],
              "dalil_dipakai": [{"surah": 1, "ayat": "1", "di_adegan": "adegan_2", "label": "QS AL-FATIHAH 1"}]}
    assert "[dalil: QS AL-FATIHAH 1]" in pesan_sutradara(naskah)
    beat = [{"beat": i, "bukti": f"kalimat {i}", "subjek": [], "kamu": "tidak", "kamera": {"bidikan": "lebar", "aksen": None},
             "teks_layar": None, "klimaks": False, "kartu_dalil": i == 1} for i in range(1, 5)]
    r = {"objek_inti": None, "beat": beat}
    assert validasi_lengkap(r, naskah) == []          # diperbaiki mesin, bukan ditolak
    assert not r["beat"][0]["kartu_dalil"] and any("kartu_dalil" in c for c in r["_perbaikan_mesin"])


def test_font_arab_tersedia():
    assert (Path(__file__).resolve().parents[1] / "mesin-video/papan/font/amiri-quran-arabic-400-normal.woff2").is_file()


def test_rencana_tersimpan_dipakai_ulang_hanya_bila_narasi_sama(tmp_path):
    from newmotion.paket_genre.kisah_islami.sutradara_hibrida import (
        kunci_naskah,
        rencana_tersimpan,
    )
    naskah = {"adegan": [{"teks": "Satu."}, {"teks": "Dua."}]}
    (tmp_path / "rencana.json").write_text('{"beat": []}', encoding="utf-8")
    assert rencana_tersimpan(naskah, tmp_path) is None
    (tmp_path / "rencana.kunci").write_text(kunci_naskah(naskah), encoding="utf-8")
    assert rencana_tersimpan(naskah, tmp_path) == {"beat": []}
    assert rencana_tersimpan({"adegan": [{"teks": "Satu."}, {"teks": "Tiga."}]}, tmp_path) is None


def test_figuran_rencana_membawa_tampilan():
    from newmotion.paket_genre.kisah_islami.rencana_sutradara import (
        figuran_dari_rencana,
    )
    o = figuran_dari_rencana({"figuran": [{"jumlah": 1, "tempat": "tengah", "gerak": "rebahan", "mata": "tutup",
                                           "penutup_kepala": "nemes", "janggut": True, "janggut_model": "firaun",
                                           "pakaian": {"jenis": "jubah", "bisht": True, "kalung": "usekh"}}]}, [], 1)[0]
    assert o["penutup_kepala"] == "nemes" and o["janggut_model"] == "firaun" and o["mata"] == "tutup"
    assert o["pakaian"]["bisht"] == "#3a2a1e"


def test_tokoh_di_lorong_tertelan_laut_yang_menutup():
    from newmotion.paket_genre.kisah_islami.rencana_sutradara import (
        figuran_dari_rencana,
        subjek_dari_rencana,
    )
    rb = {"subjek": [{"jenis": "laut_terbelah", "tempat": "tengah", "keadaan": {"belah": [1, 0.1]}}],
          "figuran": [{"jumlah": 3, "tempat": "di_lorong:laut_terbelah", "gerak": "kaget", "jenis_kelamin": "pria"}]}
    benda = subjek_dari_rencana(rb, "tenggelam", 6.0, 1)["benda"]
    orang = figuran_dari_rencana(rb, benda, 1, 6.0)
    assert len(orang) == 3 and all(o["jenis_kelamin"] == "pria" for o in orang)
    depan = [b for b in benda if b.get("lapis") == "tutup"]
    assert len(depan) == 1 and depan[0]["depan"] is True


def test_beat_dipecah_melanjutkan_perubahan():
    from newmotion.paket_genre.kisah_islami.rencana_sutradara import _nilai
    a, b = _nilai([1, 0], 3.0, 0.0, 0.5), _nilai([1, 0], 3.0, 0.5, 1.0)
    assert a[-1][1] == b[0][1] and b[-1][1] == 0


def test_tokoh_yang_terlupa_dilengkapi_mesin():
    from newmotion.paket_genre.kisah_islami.rencana_sutradara import lengkapi_figuran
    naskah = {"judul": "U", "adegan": [{"nama": "adegan_1", "teks": "Firaun dan tentaranya mengejar.",
                                        "peran": ["Nabi Musa", "Firaun", "tentara Firaun"]}]}
    assert "[tokoh: Firaun, tentara Firaun]" in pesan_sutradara(naskah)
    rb = {"subjek": [{"jenis": "laut_terbelah", "tempat": "tengah"}, {"jenis": "nur", "tempat": "kiri"}]}
    fig = lengkapi_figuran(rb, naskah["adegan"][0]["peran"])["figuran"]
    assert [f["tempat"] for f in fig] == ["di_lorong:laut_terbelah"] * 2
    assert fig[0]["penutup_kepala"] == "nemes" and fig[1]["jenis_kelamin"] == "pria" and fig[1]["jumlah"] == 3
    assert "figuran" not in lengkapi_figuran(rb, ["Nabi Musa", "malaikat Jibril"])
    siluet = lengkapi_figuran(rb, ["Bani Israil"], "Nabi Musa dan pengikutnya menyeberang")
    assert "figuran" not in siluet and siluet["subjek"][-1]["jenis"] == "arus"
