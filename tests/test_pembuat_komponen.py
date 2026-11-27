"""Uji pembuat draf komponen tanpa panggilan LLM atau GitHub sungguhan."""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from newmotion.application import pembuat_komponen as P
from newmotion.application import penerbit_komponen as R


KODE = '''else if (j === "kendi_besar") { // kendi penyimpanan; isi 0 kosong, 1 penuh
      const isiKendi = v(o.isi, t, d, 0);
      g += `<path d="M -70 -30 Q -110 -150 -45 -250 L 45 -250 Q 110 -150 70 -30 Z" fill="#b87945" stroke="${INK}" stroke-width="8"/><path d="M -45 -160 Q 0 -190 45 -160" fill="none" stroke="#f4d6a4" stroke-width="8" opacity="${isiKendi}"/>`;
    }'''


def test_validator_menerima_satu_cabang_dengan_parameter_animasi():
    data = {"kode": KODE, "nama": "kendi_besar", "parameter": "isi",
            "ringkasan": "kendi besar"}
    assert P.validasi_draf(data, "kendi_besar", daftar={}) == []


@pytest.mark.parametrize("ubah", [
    lambda s: s.replace('j === "kendi_besar"', 'j === "kendi_lain"'),
    lambda s: s.replace("v(o.isi, t, d, 0)", "o.isi"),
    lambda s: s.replace("stroke=\"${INK}\"", 'stroke="#000"'),
    lambda s: s.replace("g +=", "x +="),
    lambda s: s.replace("const isiKendi", "function isiKendi"),
    lambda s: s + '<text x="0">nama</text>',
])
def test_validator_menolak_pelanggaran_kontrak(ubah):
    data = {"kode": ubah(KODE), "nama": "kendi_besar",
            "parameter": "isi", "ringkasan": "kendi"}
    assert P.validasi_draf(data, "kendi_besar", daftar={})


def test_validator_menolak_nama_yang_sudah_ada():
    data = {"kode": KODE, "nama": "kendi_besar", "parameter": "isi"}
    assert any("sudah ada" in x for x in P.validasi_draf(
        data, "kendi_besar", daftar={"kendi_besar": {}}
    ))


def test_buat_draf_memakai_jalur_llm_palsu(monkeypatch):
    monkeypatch.setattr(P, "katalog", lambda: {})
    jawaban = SimpleNamespace(
        data={"kode": KODE, "parameter": "isi", "ringkasan": "kendi"},
        model="model-uji", penyedia="uji", token_masuk=10,
        token_keluar=20, biaya_usd=0.0,
    )
    panggilan = {}

    def palsu(tahap, sistem, pesan, **kwargs):
        panggilan.update(tahap=tahap, sistem=sistem, pesan=pesan, kwargs=kwargs)
        return jawaban

    monkeypatch.setattr(P, "panggil", palsu)
    hasil = P.buat_draf("kendi_besar", "wadah air belum ada", "mengisi kendi besar")
    assert hasil["status"] == "draf_kode_belum_diverifikasi"
    assert hasil["model"] == "model-uji"
    assert panggilan["tahap"] == "komponen_renderer"
    assert panggilan["kwargs"]["json"] is True
    assert callable(panggilan["kwargs"]["validasi"])


def test_simpan_draf_tidak_mengubah_renderer_dan_tidak_menimpa(tmp_path):
    data = {"nama": "kendi_besar", "kode": KODE, "parameter": "isi",
            "ringkasan": "kendi", "status": "draf_kode_belum_diverifikasi"}
    jalur = P.simpan_draf(data, tmp_path)
    assert jalur.exists()
    assert "kendi_besar" in jalur.read_text(encoding="utf-8")
    with pytest.raises(FileExistsError):
        P.simpan_draf(data, tmp_path)


def test_skill_pembuat_melarang_wujud_tokoh_mulia_dan_raster():
    isi = P.SKILL.read_text(encoding="utf-8")
    assert "Allah" in isi and "nabi/rasul" in isi
    assert "gambar raster" in isi
    assert "parameter" in isi



def test_penerbit_menyisipkan_cabang_baru_sebelum_return_tanpa_mengubah_cabang_lama():
    sumber = '''function benda(o, t, d) {
    if (j === "cahaya") { // cabang lama
      g = "cahaya";
    }
    return `<g data-j="${j}">${g}</g>`;
  }

  // ---- TITIK KAIT
'''
    hasil = R.sisipkan_cabang(sumber, KODE, "kendi_besar")
    assert 'if (j === "cahaya")' in hasil
    assert '} else if (j === "kendi_besar") {' in hasil
    assert hasil.index('j === "kendi_besar"') < hasil.index("return `<g")
    with pytest.raises(ValueError, match="sudah ada"):
        R.sisipkan_cabang(hasil, KODE, "kendi_besar")



def test_antrean_menandai_kebutuhan_sebagai_draf(tmp_path):
    from newmotion.application import kebutuhan_renderer as K

    berkas = tmp_path / "kebutuhan_renderer.json"
    K.catat(
        [{"nama": "kafilah", "alasan": "rombongan belum tersedia",
          "bukti": "kafilah berjalan"}],
        sumber="sutradara", kisah="Kisah dagang", jalur=berkas,
    )
    antrean = K.tandai_draf({
        "nama": "kafilah", "alasan": "rombongan belum tersedia",
        "bukti_narasi": "kafilah berjalan",
    }, jalur=berkas)
    assert antrean["kebutuhan"]["kafilah"]["status"] == "draf"
    assert "pembuat_komponen" in antrean["kebutuhan"]["kafilah"]["sumber"]
    assert K.STATUS == ("menunggu", "draf", "dibuat")
