"""Gerbang dalil sebelum pratinjau visual dan dukungan kartu dalil rentang ayat."""
import json

import pytest

from newmotion.application.antrean_naskah import teks_tinjauan, tombol_kartu
from newmotion.application.pratinjau_visual import buat_pratinjau, naskah_untuk_pengarah


def _status(dalil):
    return {"id": "uji", "tahap": {"tinjau": "jalan", "dalil": dalil}, "ket": {}}


def test_tombol_lanjut_hanya_bila_dalil_lolos():
    data = [b["callback_data"] for baris in tombol_kartu(_status("selesai")) for b in baris]
    assert "nl:uji" in data
    for keadaan in ("gagal", "jalan", "belum"):
        data = [b["callback_data"] for baris in tombol_kartu(_status(keadaan)) for b in baris]
        assert "nl:uji" not in data
    data = [b["callback_data"] for baris in tombol_kartu(_status("gagal")) for b in baris]
    assert {"nr:uji", "nb:uji"} <= set(data)


def test_teks_tinjauan_memberi_tahu_dalil_gagal():
    naskah = {"judul": "Uji", "dalil": [{"id": "x", "label": "QS X 1", "status": "belum"}],
              "beat": [{"narasi": "Satu.", "dalil": ["x"]}]}
    teks = "".join(teks_tinjauan(naskah))
    assert "tidak bisa lanjut ke visual" in teks and "QS X 1" in teks


def test_pratinjau_diblokir_bila_dalil_gagal(tmp_path):
    d = tmp_path / "cerita"
    d.mkdir()
    (d / "naskah.json").write_text(json.dumps({"judul": "C", "beat": [{"narasi": "x"}]}), encoding="utf-8")
    (d / "status.json").write_text(json.dumps({"tahap": {"tinjau": "selesai", "dalil": "gagal"}}), encoding="utf-8")
    with pytest.raises(ValueError, match="dalil naskah belum lolos"):
        buat_pratinjau("cerita", folder=tmp_path)


def test_dalil_rentang_ayat_terverifikasi_masuk_kartu():
    naskah = {
        "judul": "Dzulqarnain",
        "dalil": [
            {"id": "kahfi94", "jenis": "quran", "surah": 18, "ayat": "94-95", "status": "terverifikasi"},
            {"id": "kahfi96", "jenis": "quran", "surah": 18, "ayat": "96-97", "status": "belum"},
        ],
        "beat": [{"narasi": "Mereka meminta dibuatkan dinding.", "dalil": ["kahfi94", "kahfi96"]}],
    }
    assert naskah_untuk_pengarah(naskah)["dalil_dipakai"] == [
        {"surah": 18, "ayat": "94-95", "di_adegan": "adegan_1"}
    ]


ARAB = {94: "قَالُوا يَا ذَا الْقَرْنَيْنِ إِنَّ يَأْجُوجَ وَمَأْجُوجَ مُفْسِدُونَ فِي الْأَرْضِ",
        95: "قَالَ مَا مَكَّنِّي فِيهِ رَبِّي خَيْرٌ فَأَعِينُونِي بِقُوَّةٍ"}


def test_kartu_rentang_ayat_digabung_dan_lolos_penjaga_dalil(monkeypatch):
    from newmotion.paket_genre.kisah_islami import pengarah_naskah as P
    from newmotion.paket_genre.kisah_islami.penjaga_dalil import periksa_kartu

    monkeypatch.setattr(P, "ambil_ayat", lambda s, a: {"teks_arab": ARAB[a], "terjemah": f"arti {a}"})
    kartu = P._ambil_dalil_untuk_adegan("a1", [{"surah": 18, "ayat": "94-95", "di_adegan": "a1"}])
    assert kartu["kitab"] == "QS 18:94-95"
    assert kartu["teks"] == "arti 94 arti 95"

    class Sumber:
        def teks_ayat(self, surah, ayat):
            return ARAB[ayat]

    hasil = periksa_kartu({"jenis": "kartu_dalil", **kartu}, "uji", Sumber())
    assert hasil.status == "lulus", hasil


def test_rentang_ayat_tidak_wajar_tidak_membuat_kartu(monkeypatch):
    from newmotion.paket_genre.kisah_islami import pengarah_naskah as P

    monkeypatch.setattr(P, "ambil_ayat", lambda s, a: {"teks_arab": "x", "terjemah": "y"})
    for ayat in ("95-94", "1-30", "abc"):
        assert P._ambil_dalil_untuk_adegan("a1", [{"surah": 2, "ayat": ayat, "di_adegan": "a1"}]) is None
