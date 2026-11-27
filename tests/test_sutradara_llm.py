"""Rencana sutradara (LLM) -> validator -> papan: format, adab, katalog, dan integrasi pengarah."""
import copy
import json
from pathlib import Path

import pytest

from newmotion.application.katalog_renderer import katalog, katalog_subjek
from newmotion.application.pengarah_inti import arahkan_naskah
from newmotion.paket_genre.kisah_islami import sutradara_llm as S
from newmotion.paket_genre.kisah_islami.rencana_sutradara import (
    terapkan_rencana,
    validasi_rencana,
)

DATA = Path(__file__).parent / "data"
NASKAH = json.loads((DATA / "tolok_ukur" / "yajuj1.json").read_text(encoding="utf-8"))
RENCANA = json.loads((DATA / "rencana" / "yajuj1.json").read_text(encoding="utf-8"))
NARASI = [a["teks"] for a in NASKAH["adegan"]]


def _shots(rencana=RENCANA, naskah=NASKAH):
    spek, _, _ = arahkan_naskah(terapkan_rencana(naskah, rencana))
    return spek["cerita"]["shot"]


def test_katalog_dibaca_dari_renderer():
    k = katalog()
    assert {"ngarai", "penggali", "bahtera", "arus"} <= set(k)
    assert {"lubang", "jebol"} <= set(k["ngarai"]["parameter"])
    assert "kartu_dalil" in k and "kartu_dalil" not in katalog_subjek()


def test_skill_memuat_katalog_dan_tanpa_contoh_tolok_ukur():
    skill = S.skill_sutradara()
    assert "{KATALOG}" not in skill and "- ngarai:" in skill
    contoh = skill[skill.index("## Contoh"):]
    for nama in ("Ya'juj", "Nuh", "Mahsyar", "Dabbah", "kubur"):
        assert nama.lower() not in contoh.lower()  # contoh tidak boleh membocorkan cerita uji


def test_rencana_contoh_lolos_validator_lengkap():
    assert S.validasi_lengkap(RENCANA, NASKAH) == []


def test_rencana_diterjemahkan_ke_papan():
    shots = _shots()
    jebol = [b for s in shots for b in s["benda"] if b["jenis"] == "ngarai" and b.get("jebol")]
    assert jebol and jebol[0]["jebol"][-1][1] == 1.0          # [awal, akhir] -> kunci waktu
    pertama = shots[0]
    assert pertama["boneka"] == []                              # kamu: tidak
    assert any(t["teks"] == "DIGALI\nSETIAP HARI" for t in pertama["teks"])
    gali = next(b for b in pertama["benda"] if b["jenis"] == "penggali")
    dinding = next(b for b in pertama["benda"] if b["jenis"] == "ngarai")
    assert gali["y"] < dinding["y"]                              # di lubang dinding, bukan di tanah
    assert "_di_lubang" not in gali
    assert any("guncang" in s["kamera"] for s in shots)


def test_validator_menolak_kesalahan_umum():
    r = copy.deepcopy(RENCANA)
    r["beat"][0]["subjek"].append({"jenis": "naga", "tempat": "tengah"})
    r["beat"][1]["bukti"] = "kalimat karangan yang tidak ada di narasi"
    r["beat"][2]["subjek"][0]["keadaan"] = {"terbang": 1}
    r["beat"][3]["kamu"] = "pahlawan"
    r["beat"].pop()
    galat = "\n".join(validasi_rencana(r, NARASI))
    for kata in ("naga", "bukti", "terbang", "kamu harus", "tepat satu entri"):
        assert kata in galat


def test_validator_menolak_sosok_manusia_untuk_rasulullah():
    naskah = {"judul": "uji", "genre": "kisah_islami", "konteks_konten": "islami",
              "adegan": [{"nama": "a1", "teks": "Rasulullah, pemimpin umat ini, berdiri di atas bukit."}]}
    r = {"objek_inti": None, "beat": [{"beat": 1, "bukti": "Rasulullah, pemimpin umat ini", "kamu": "tidak",
                                       "subjek": [{"jenis": "pemimpin", "tempat": "tengah"}],
                                       "kamera": {"bidikan": "lebar", "aksen": None}, "teks_layar": None, "klimaks": False}]}
    assert any(g.startswith("adab:") for g in S.validasi_lengkap(r, naskah))


def test_llm_tiruan_dipakai_lewat_rantai_model(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "uji")
    monkeypatch.setenv("NEWMOTION_MODEL_SUTRADARA", "claude-sonnet-5-5")
    terkirim = {}

    def http(url, badan, kepala, batas):
        terkirim["badan"] = badan
        return {"content": [{"type": "text", "text": json.dumps(RENCANA)}],
                "usage": {"input_tokens": 9000, "output_tokens": 4000}}

    j = S.buat_rencana(NASKAH, http=http)
    assert j.data == RENCANA and j.biaya_usd == pytest.approx((9000 * 2 + 4000 * 10) / 1e6)
    assert "1. Ada satu dinding" in terkirim["badan"]["messages"][0]["content"][-1]["text"]


def test_tanpa_rencana_pengarah_aturan_tidak_berubah():
    tanpa, _, _ = arahkan_naskah(NASKAH)
    assert all("rencana" not in a for a in NASKAH["adegan"])
    assert tanpa["cerita"]["shot"][0]["boneka"]  # pengarah aturan tetap menaruh tokoh "kamu"


def test_gunung_subjek_tidak_dibuang_bersama_latar():
    naskah = {"judul": "uji", "genre": "kisah_islami", "konteks_konten": "islami",
              "adegan": [{"nama": "a1", "teks": "Anaknya berkata: aku akan berlindung ke gunung, sementara kapal berlayar."}]}
    r = {"objek_inti": None, "beat": [{"beat": 1, "bukti": "aku akan berlindung ke gunung", "kamu": "tidak",
                                       "subjek": [{"jenis": "bahtera", "tempat": "kiri"}, {"jenis": "gunung", "tempat": "kanan"}],
                                       "kamera": {"bidikan": "lebar", "aksen": None}, "teks_layar": None, "klimaks": False}]}
    assert S.validasi_lengkap(r, naskah) == []
    spek, _, _ = arahkan_naskah(terapkan_rencana(naskah, r))
    gunung = [b for s in spek["cerita"]["shot"] for b in s["benda"] if b["jenis"] == "gunung"]
    assert gunung and all(g["x"] == 780 for g in gunung)  # hanya gunung subjek (kanan) yang tersisa


def test_suara_rencana_jadi_rekaman():
    spek, _, _ = arahkan_naskah(terapkan_rencana(NASKAH, RENCANA))
    assert spek["musik"] is False and spek["volume_efek"] == 0
    rek = spek["rekaman"]
    drone = [r for r in rek if r["berkas"].endswith("drone_gelap.mp3")]
    assert len(drone) == 1 and drone[0]["ulang"] and drone[0]["sampai"]  # suasana sama digabung, lalu berhenti
    assert sum(r["berkas"].endswith("braam.mp3") for r in rek) == 2
    gali = sorted(r["at"] for r in rek if r["berkas"].endswith("timbangan_denting.mp3") and r["at"] < 6)
    assert len(gali) == 6 and round(gali[1] - gali[0], 2) == 0.6           # ritme ulang
    assert all(r["at"] == sorted(x["at"] for x in rek)[i] for i, r in enumerate(rek))
    assert terapkan_rencana(NASKAH, RENCANA)["adegan"][10]["intonasi"] == "haru"


def test_suara_ditolak_bila_tidak_di_katalog_atau_kata_tidak_ada():
    r = copy.deepcopy(RENCANA)
    r["beat"][0]["suara"] = {"suasana": "musik_pop", "efek": [{"nama": "rimshot"}, {"nama": "braam", "pada": "meledak"}],
                             "intonasi": "ceria"}
    galat = validasi_rencana(r, NARASI)
    assert any("suasana" in g for g in galat) and any("rimshot" in g for g in galat)
    assert any("efek.pada" in g for g in galat) and any("intonasi" in g for g in galat)


def test_waktu_efek_memakai_waktu_kata_tts_bila_ada():
    from newmotion.paket_genre.kisah_islami.rencana_sutradara import (
        rekaman_dari_rencana,
    )

    adegan = [{"teks": "Mereka menembusnya, dan keluar.",
               "rencana": {"suara": {"efek": [{"nama": "braam", "pada": "menembusnya"}]}}}]
    kira = rekaman_dari_rencana(adegan, [(10.0, 4.0)])[0]["at"]
    pasti = rekaman_dari_rencana(adegan, [(10.0, 4.0)], [[[10.0, "Mereka"], [10.7, "menembusnya,"]]])[0]["at"]
    assert 10.0 < kira < 12.0 and pasti == 10.7


def test_skill_memuat_katalog_suara():
    skill = S.skill_sutradara()
    assert "{KATALOG_SUARA}" not in skill and "- drone_gelap:" in skill and "rimshot" not in skill


def test_figuran_rencana_jadi_boneka_dan_dijaga_adab():
    from newmotion.paket_genre.kisah_islami.penjaga_tokoh import periksa_adab_tokoh

    r = copy.deepcopy(RENCANA)
    r["suku"] = "arab"
    r["beat"][8]["figuran"] = [{"jumlah": 3, "tempat": "kanan", "gerak": "lari", "hadap": "kiri"}]
    assert S.validasi_lengkap(r, NASKAH) == []
    spek, _, _ = arahkan_naskah(terapkan_rencana(NASKAH, r))
    assert spek["cerita"]["suku"] == "arab"
    fig = [b for sh in spek["cerita"]["shot"] if sh["_adegan"] == 8 for b in sh["boneka"] if "npc" in b]
    assert len(fig) >= 3 and all(b["pose"] == "lari" and b["profil"] == "kiri" for b in fig)
    # penjaga: figuran di shot yang menyebut nabi -> gagal
    sh = copy.deepcopy(spek["cerita"]["shot"][8])
    sh["_narasi"] = "Nabi Musa berdiri di tepi laut."
    assert any(t.kode == "FIGURAN_TOKOH_SAKRAL" for t in periksa_adab_tokoh({"cerita": {"shot": [sh]}}))


def test_figuran_ditolak_bila_beat_menyebut_tokoh_sakral_atau_gerak_tak_dikenal():
    naskah = copy.deepcopy(NASKAH)
    naskah["adegan"][1]["teks"] = "Nabi Musa berdiri di tepi laut. " + naskah["adegan"][1]["teks"]
    r = copy.deepcopy(RENCANA)
    r["beat"][1]["figuran"] = [{"jumlah": 2, "gerak": "terbang"}]
    galat = validasi_rencana(r, [a["teks"] for a in naskah["adegan"]])
    assert any("adab" in g for g in galat)
    r["beat"][2]["figuran"] = [{"jumlah": 2, "gerak": "terbang", "naik": "motor"}]
    galat = validasi_rencana(r, NARASI)
    assert any("gerak" in g for g in galat) and any("naik" in g for g in galat)


def test_figuran_naik_benda_menempel_lewat_kait():
    from newmotion.paket_genre.kisah_islami.rencana_sutradara import figuran_dari_rencana

    benda = [{"jenis": "motor", "x": 540, "y": 1600}]
    [o] = figuran_dari_rencana({"figuran": [{"naik": "motor", "suku": "arab"}]}, benda, 3)
    assert o["kait"] == benda[0]["id"] and o["suku"] == "arab"


def test_skill_memuat_kemampuan_tokoh():
    skill = S.skill_sutradara()
    assert "{KEMAMPUAN_TOKOH}" not in skill and "motor (samping)" in skill and "- aksi berulang:" in skill and "benda yang dapat dipegang" in skill


def test_figuran_berpencar_saling_menjauh():
    from newmotion.paket_genre.kisah_islami.rencana_sutradara import figuran_dari_rencana

    fig = figuran_dari_rencana({"figuran": [{"jumlah": 4, "pindah": "berpencar"}]}, [], 1, ds=4.0)
    arah = [(f["x"][-1][1] - f["x"][0][1], f["profil"]) for f in fig]
    assert [a < 0 for a, _ in arah] == [True, True, False, False]
    assert [p for _, p in arah] == ["kiri", "kiri", "kanan", "kanan"] and all(f["pose"] == "jalan" for f in fig)
    r = copy.deepcopy(RENCANA)
    r["beat"][2]["figuran"] = [{"jumlah": 2, "pindah": "terbang"}]
    assert any("pindah" in g for g in validasi_rencana(r, NARASI))


def test_variasi_dan_tanah_per_tema():
    spek, _, _ = arahkan_naskah(terapkan_rencana(NASKAH, RENCANA))
    assert spek["cerita"]["variasi"] == NASKAH["judul"]


def test_figuran_saling_menghadap_dan_memegang_benda():
    from newmotion.paket_genre.kisah_islami.rencana_sutradara import figuran_dari_rencana

    r = {"figuran": [
        {"nama": "pemberi", "hadap_ke": "penerima", "pegang": "surat", "tempat": "kiri"},
        {"nama": "penerima", "hadap_ke": "pemberi", "pegang": "kendi", "tempat": "kanan"},
    ]}
    assert S.validasi_rencana({**copy.deepcopy(RENCANA), "beat": [
        {**copy.deepcopy(RENCANA["beat"][0]), "figuran": r["figuran"]}
    ] + copy.deepcopy(RENCANA["beat"][1:])}, NARASI) == []
    tokoh = figuran_dari_rencana(r, [], 7)
    assert tokoh[0]["profil"] == "kanan" and tokoh[1]["profil"] == "kiri"
    assert tokoh[0]["pose"] == "pegang_surat"
    assert tokoh[1]["pose"] == "pegang_kendi"
    assert tokoh[0]["id"] != tokoh[1]["id"]


def test_figuran_interaksi_menolak_rujukan_dan_benda_tidak_dikenal():
    from newmotion.paket_genre.kisah_islami.rencana_sutradara import _validasi_figuran

    jenis = {"penduduk"}
    narasi = "Dua penduduk saling menyerahkan surat."
    galat = _validasi_figuran([
        {"nama": "a", "hadap_ke": "hilang", "pegang": "senjata_api", "tempat": "kiri"},
        {"nama": "a", "hadap_ke": "a", "tempat": "kanan"},
    ], jenis, narasi, "beat 1")
    assert any("nama figuran harus unik" in e for e in galat)
    assert any("hadap_ke" in e for e in galat)
    assert any("pegang" in e for e in galat)


def test_validasi_interaksi_menolak_tipe_data_tidak_sah_tanpa_crash():
    from newmotion.paket_genre.kisah_islami.rencana_sutradara import _validasi_figuran

    galat = _validasi_figuran([
        {"nama": ["bukan", "teks"], "hadap_ke": [], "pegang": ["surat"], "tempat": "kiri"},
        {"nama": "penerima", "tempat": "tempat_tidak_ada"},
    ], set(), "Dua orang bertemu.", "beat 1")
    assert any("nama" in e for e in galat)
    assert any("hadap_ke" in e for e in galat)
    assert any("pegang" in e for e in galat)


def test_katalog_benda_genggam_dibaca_dari_renderer():
    from newmotion.application.kemampuan_tokoh import kemampuan, teks_kemampuan_tokoh

    k = kemampuan()
    assert {"tongkat", "kendi", "lentera", "keranjang", "tasbih", "surat", "gulungan", "karung_kecil"} <= set(k["pegang"])
    teks = teks_kemampuan_tokoh()
    assert "- benda yang dapat dipegang: " in teks
    assert "karung_kecil" in teks


def test_rencana_serah_terima_diterjemahkan_ke_papan():
    r = copy.deepcopy(RENCANA)
    r["beat"][8]["figuran"] = [
        {"nama": "pemberi", "hadap_ke": "penerima", "pegang": "surat",
         "serahkan_ke": "penerima", "tempat": "kiri"},
        {"nama": "penerima", "hadap_ke": "pemberi", "tempat": "kanan"},
    ]
    assert S.validasi_lengkap(r, NASKAH) == []
    spek, _, _ = arahkan_naskah(terapkan_rencana(NASKAH, r))
    adegan = [sh for sh in spek["cerita"]["shot"] if sh.get("serah_terima")]
    assert adegan
    transfer = adegan[0]["serah_terima"]
    assert transfer["benda"] == "surat" and transfer["dari"] != transfer["ke"]
    tokoh = adegan[0]["boneka"]
    assert tokoh[transfer["dari"]]["pose"] == "pegang_surat"
    assert tokoh[transfer["ke"]]["_nama_interaksi"] == "penerima"


def test_serah_terima_ditolak_bila_penerima_tidak_ada_atau_benda_tidak_sah():
    r = copy.deepcopy(RENCANA)
    r["beat"][8]["figuran"] = [
        {"nama": "pemberi", "pegang": "pedang", "serahkan_ke": "orang_hilang", "tempat": "kiri"}
    ]
    galat = validasi_rencana(r, NARASI)
    assert any("serahkan_ke" in e for e in galat)
    assert any("serah-terima" in e for e in galat)
