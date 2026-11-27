"""Uji pengumpulan revisi, contoh, dan usulan pelajaran tanpa layanan berbayar."""
import json

from newmotion.application import pelajaran_naskah as P


def test_pilih_contoh_mengembalikan_maksimal_dua_yang_paling_mirip(tmp_path, monkeypatch):
    monkeypatch.setattr(P, "DATA", tmp_path)
    folder = tmp_path / "contoh_naskah"
    folder.mkdir()
    for nama, judul in [("a", "Nabi Hud dan kaum Ad"), ("b", "Kisah kapal Nabi Nuh"), ("c", "Perjalanan ke pasar")]:
        data = {"judul": judul, "inti": judul, "naskah": {"beat": [{"narasi": judul, "peran": []}]}}
        (folder / f"{nama}.json").write_text(json.dumps(data), encoding="utf-8")
    hasil = P.pilih_contoh("Nabi Hud kaum Ad", batas=2)
    assert len(hasil) == 2
    assert hasil[0]["judul"] == "Nabi Hud dan kaum Ad"


def test_pedoman_hanya_dibaca_dari_berkas_yang_disetujui(tmp_path, monkeypatch):
    target = tmp_path / "pedoman.md"
    monkeypatch.setattr(P, "PEDOMAN", target)
    assert P.pedoman_disetujui() == ""
    target.write_text("Pertimbangan yang disetujui pemilik.", encoding="utf-8")
    assert P.pedoman_disetujui() == "Pertimbangan yang disetujui pemilik."


def test_ringkas_menulis_usulan_dengan_llm_palsu_dan_tidak_mengaktifkannya(tmp_path, monkeypatch):
    monkeypatch.setattr(P, "DATA", tmp_path)
    monkeypatch.setattr(P, "PEDOMAN", tmp_path / "pedoman.md")
    baris = [
        {"id": "a", "catatan_pemilik": "Perkuat hook", "sebelum": {"beat": [{"narasi": "Awal"}]},
         "sesudah": {"beat": [{"narasi": "Hook kuat"}]}},
        {"id": "b", "catatan_pemilik": "Perkuat hook", "sebelum": {"beat": [{"narasi": "Pembuka"}]},
         "sesudah": {"beat": [{"narasi": "Pembuka kuat"}]}},
    ]
    (tmp_path / "pelajaran_naskah.jsonl").write_text(
        "\n".join(json.dumps(x) for x in baris) + "\n", encoding="utf-8")
    class Jawaban:
        data = {"usulan": [{"pola": "Hook spesifik", "alasan": "Muncul berulang",
                            "jumlah_revisi": 2, "contoh_sebelum": "Awal",
                            "contoh_sesudah": "Hook kuat"}]}
    class LLM:
        @staticmethod
        def panggil(*args, **kwargs):
            return Jawaban()
    monkeypatch.setattr("newmotion.infrastructure.llm.panggil", LLM.panggil)
    hasil = P.ringkas()
    assert hasil["jumlah_revisi"] == 2
    assert (tmp_path / "usulan_pedoman_naskah.json").is_file()
    assert not (tmp_path / "pedoman.md").exists()
