"""Uji batas paket genre terhadap inti NewMotion."""

from pathlib import Path

import pytest

from newmotion.domain.genre import (
    PaketGenre,
    ambil,
    daftar,
    daftarkan,
    dari_rencana,
    nama_dari_rencana,
    nama_genre_untuk_naskah,
    konteks_konten_untuk_naskah,
    memakai_kebijakan_islami,
)


def test_rencana_lama_tetap_memakai_kisah_islami():
    assert nama_dari_rencana({}) == "kisah_islami"
    assert dari_rencana({}).nama == "kisah_islami"


def test_manifest_kisah_islami_memuat_referensi_kompatibilitas():
    paket = ambil("kisah_islami")
    assert paket.nama == "kisah_islami"
    assert set(paket.modul_legacy) == {
        "pengarah", "arah_visual", "penjaga_dalil", "penjaga_tokoh_suci"
    }


def test_paket_genre_tiruan_dapat_didaftarkan_tanpa_mengubah_inti():
    nama = "genre_tiruan_uji"

    def komponen_tiruan(*args, **kwargs):
        return {"hasil": "siap"}

    paket = PaketGenre(
        nama=nama,
        komponen_visual={"benda.lingkaran": komponen_tiruan},
        bawaan={"warna": "biru"},
    )
    daftarkan(paket)
    try:
        assert nama in daftar()
        assert ambil(nama).komponen_visual["benda.lingkaran"]() == {"hasil": "siap"}
    finally:
        from newmotion.domain import genre
        genre._PAKET.pop(nama, None)


def test_paket_genre_tiruan_dapat_dimuat_dari_rencana():
    nama = "genre_rencana_uji"
    paket = PaketGenre(nama=nama, bawaan={"mode": "uji"})
    daftarkan(paket)
    try:
        assert dari_rencana({"genre": nama}) is paket
    finally:
        from newmotion.domain import genre
        genre._PAKET.pop(nama, None)


def test_manifest_dibekukan_setelah_dibuat():
    bawaan = {"tema": {"warna": "biru"}}
    paket = PaketGenre(nama="genre_beku_uji", bawaan=bawaan)
    bawaan["tema"]["warna"] = "merah"
    assert paket.bawaan["tema"]["warna"] == "biru"
    with pytest.raises(TypeError):
        paket.bawaan["tema"]["warna"] = "hijau"


@pytest.mark.parametrize("nama", ["", "../keluar", "Kisah Islami", "genre-baru"])
def test_nama_genre_tidak_boleh_mengandung_path_atau_spasi(nama):
    with pytest.raises(ValueError, match="nama genre"):
        PaketGenre(nama=nama, bawaan={"mode": "uji"})


def test_genre_tidak_dikenal_ditolak():
    with pytest.raises(ValueError, match="genre tidak dikenal"):
        ambil("genre_yang_tidak_ada")


def test_inti_tidak_mengimpor_paket_kisah_islami_secara_langsung():
    akar = Path(__file__).resolve().parents[1] / "newmotion"
    sumber = (akar / "domain" / "genre.py").read_text(encoding="utf-8")
    assert "newmotion.paket_genre.kisah_islami" not in sumber
    assert "import newmotion.paket_genre.kisah_islami" not in sumber


def test_validasi_job_memilih_genre_dari_spesifikasi(tmp_path):
    from newmotion.application.validasi_job import validasi_job

    spesifikasi = tmp_path / "cerita.json"
    spesifikasi.write_text('{"genre": "kisah_islami"}', encoding="utf-8")
    validasi_job(spesifikasi, tmp_path / "hasil.mp4")


def test_validasi_job_menolak_genre_yang_tidak_tersedia(tmp_path):
    from newmotion.application.validasi_job import GalatValidasiJob, validasi_job

    spesifikasi = tmp_path / "cerita.json"
    spesifikasi.write_text('{"genre": "genre_tidak_tersedia"}', encoding="utf-8")
    with pytest.raises(GalatValidasiJob, match="Genre pada spesifikasi tidak valid"):
        validasi_job(spesifikasi, tmp_path / "hasil.mp4")



def test_manifest_kisah_islami_mendaftarkan_kedua_penjaga():
    paket = ambil("kisah_islami")
    assert callable(paket.penjaga_tokoh)
    assert callable(paket.penjaga_dalil)
    assert paket.penjaga_dalil({}) == []


def test_kontrak_menolak_penjaga_dalil_yang_bukan_fungsi():
    with pytest.raises(TypeError, match="penjaga_dalil"):
        PaketGenre(nama="genre_penjaga_salah_uji", penjaga_dalil="bukan-fungsi")


def test_renderer_menjadi_satu_satunya_gerbang_penjaga_genre():
    akar = Path(__file__).resolve().parents[1]
    sumber = (akar / "mesin-video" / "papan_buat.py").read_text(encoding="utf-8")
    awal = sumber.index("def jaga_spek(spec):")
    akhir = sumber.index("\ndef buat_html", awal)
    gerbang = sumber[awal:akhir]
    assert "for penjaga in penjaga_tokoh:" in gerbang
    assert "for penjaga in penjaga_dalil:" in gerbang
    assert "dict.fromkeys(" in gerbang
    assert 'ambil("kisah_islami")' in gerbang
    assert 'if paket.nama == "kisah_islami"' not in gerbang

    validasi = (akar / "newmotion" / "application" / "validasi_job.py").read_text(encoding="utf-8")
    assert "paket.penjaga_tokoh(" not in validasi
    assert "paket.penjaga_dalil(" not in validasi



def test_manifest_mendaftarkan_pengarah_dan_kebijakan_visual_kisah_islami():
    paket = ambil("kisah_islami")
    assert callable(paket.pengarah_naskah)
    assert {
        "pilih_tema", "tema_lokal", "pilih_tampilan", "pilih_pose",
        "rencana_framing", "ruang_untuk", "atmosfer",
    } <= set(paket.komponen_visual)


def test_modul_lama_hanya_menjadi_shim_ke_paket_genre():
    akar = Path(__file__).resolve().parents[1]
    for nama, target in (
        ("direktur.py", "pengarah_naskah.py"),
        ("arah_visual.py", "arah_visual.py"),
    ):
        sumber = (akar / "mesin-video" / "papan" / nama).read_text(encoding="utf-8")
        assert "newmotion.paket_genre.kisah_islami" in sumber
        assert target.removesuffix(".py") in sumber


def test_workflow_render_mahsyar_tidak_terpicu_perubahan_paket_genre():
    akar = Path(__file__).resolve().parents[1]
    sumber = (akar / ".github" / "workflows" / "uji-mahsyar1.yml").read_text(encoding="utf-8")
    assert "'newmotion/**'" not in sumber
    assert "'mesin-video/papan/cerita.js'" in sumber
    assert "workflow_dispatch:" in sumber
    assert "github.head_ref != 'feature/pemisahan-pengarah-kisah-islami'" in sumber



def test_pengarah_kisah_islami_menghasilkan_shot_dari_naskah():
    paket = ambil("kisah_islami")
    hasil = paket.pengarah_naskah({
        "judul": "Uji pengarah",
        "adegan": [{"nama": "awal", "teks": "Seorang pengendara melintasi jembatan."}],
    })
    assert isinstance(hasil, dict)
    assert isinstance(hasil.get("cerita"), dict)
    assert len(hasil["cerita"].get("shot", [])) >= 1



def test_naskah_baru_wajib_memiliki_genre_eksplisit():
    with pytest.raises(ValueError, match="Genre naskah belum ditentukan"):
        nama_genre_untuk_naskah({"judul": "Cerita tanpa genre", "adegan": []})


def test_pilihan_pengguna_mengungguli_metadata_genre_naskah():
    assert nama_genre_untuk_naskah(
        {"genre": "kisah_islami"}, pilihan="genre_tiruan"
    ) == "genre_tiruan"


def test_sutradara_inti_mendispatch_ke_paket_genre_tanpa_asumsi_genre():
    from newmotion.application.pengarah_inti import arahkan_naskah

    nama = "sutradara_tiruan_uji"
    panggilan = []

    def pengarah(data):
        panggilan.append(data["judul"])
        return {"cerita": {"shot": [{"at": 0, "benda": [], "boneka": []}]}}

    paket = PaketGenre(nama=nama, pengarah_naskah=pengarah)
    daftarkan(paket)
    try:
        papan, genre, jumlah = arahkan_naskah({
            "judul": "Uji lintas genre",
            "genre": nama,
            "konteks_konten": "umum",
            "adegan": [{"teks": "Tokoh membuka pintu."}],
        })
        assert genre == nama
        assert papan["genre"] == nama
        assert jumlah == 1
        assert panggilan == ["Uji lintas genre"]
    finally:
        from newmotion.domain import genre as modul_genre
        modul_genre._PAKET.pop(nama, None)


def test_sutradara_inti_menolak_naskah_tanpa_genre():
    from newmotion.application.pengarah_inti import GalatPengarahan, arahkan_naskah

    with pytest.raises(GalatPengarahan, match="Genre naskah belum ditentukan"):
        arahkan_naskah({
            "judul": "Tanpa genre",
            "adegan": [{"teks": "Tokoh berjalan."}],
        })


def test_validasi_mode_naskah_menolak_genre_yang_tidak_dipilih(tmp_path):
    from newmotion.application.validasi_job import GalatValidasiJob, validasi_job

    naskah = tmp_path / "naskah.json"
    naskah.write_text(
        '{"judul":"Belum dipilih","adegan":[{"teks":"Tokoh berjalan."}]}',
        encoding="utf-8",
    )
    with pytest.raises(GalatValidasiJob, match="Genre naskah belum ditentukan"):
        validasi_job(naskah, tmp_path / "hasil.mp4", wajib_genre=True)


def test_validasi_mode_naskah_menerima_pilihan_genre_cli(tmp_path):
    from newmotion.application.validasi_job import validasi_job

    naskah = tmp_path / "naskah.json"
    naskah.write_text(
        '{"judul":"Pilihan CLI","konteks_konten":"islami","adegan":[{"teks":"Tokoh berjalan."}]}',
        encoding="utf-8",
    )
    validasi_job(
        naskah, tmp_path / "hasil.mp4",
        wajib_genre=True, genre_pilihan="kisah_islami",
    )



def test_genre_komedi_dapat_memakai_konteks_islami():
    konteks = konteks_konten_untuk_naskah(
        {"genre": "komedi", "konteks_konten": "islami"},
        genre="komedi",
    )
    assert konteks == "islami"
    assert memakai_kebijakan_islami(konteks)


def test_genre_umum_tidak_otomatis_mendapat_kebijakan_islami():
    konteks = konteks_konten_untuk_naskah({"genre": "komedi"}, genre="komedi")
    assert konteks == "umum"
    assert not memakai_kebijakan_islami(konteks)


def test_kisah_islami_mewarisi_konteks_islami_untuk_kompatibilitas():
    assert konteks_konten_untuk_naskah(
        {"genre": "kisah_islami"}, genre="kisah_islami"
    ) == "islami"


def test_kisah_islami_tidak_boleh_diberi_konteks_umum():
    with pytest.raises(ValueError, match="wajib memakai konteks konten Islami"):
        konteks_konten_untuk_naskah(
            {"genre": "kisah_islami", "konteks_konten": "umum"},
            genre="kisah_islami",
        )


def test_konteks_konten_tidak_dikenal_ditolak():
    with pytest.raises(ValueError, match="konteks_konten tidak dikenal"):
        konteks_konten_untuk_naskah(
            {"konteks_konten": "campuran_tidak_jelas"}, genre="komedi"
        )



def test_gerbang_renderer_menerapkan_penjaga_islami_pada_genre_lain(monkeypatch):
    import importlib.util
    from types import SimpleNamespace
    from newmotion.domain import genre as modul_genre

    akar = Path(__file__).resolve().parents[1]
    sumber = akar / "mesin-video" / "papan_buat.py"
    spec_modul = importlib.util.spec_from_file_location("newmotion_uji_papan_buat", sumber)
    modul_render = importlib.util.module_from_spec(spec_modul)
    spec_modul.loader.exec_module(modul_render)

    panggilan = []
    def penjaga_tokoh(spec):
        panggilan.append(("tokoh", spec["genre"]))
        return []

    def penjaga_dalil(spec):
        panggilan.append(("dalil", spec["genre"]))
        return []

    paket_komedi = SimpleNamespace(
        nama="komedi", penjaga_tokoh=None, penjaga_dalil=None
    )
    paket_islami = SimpleNamespace(
        nama="kisah_islami",
        penjaga_tokoh=penjaga_tokoh,
        penjaga_dalil=penjaga_dalil,
    )
    monkeypatch.setattr(modul_genre, "dari_rencana", lambda spec: paket_komedi)
    monkeypatch.setattr(
        modul_genre, "ambil",
        lambda nama: paket_islami if nama == "kisah_islami" else None,
    )

    modul_render.jaga_spek({
        "genre": "komedi",
        "konteks_konten": "islami",
    })

    assert panggilan == [("tokoh", "komedi"), ("dalil", "komedi")]



def test_validasi_job_menolak_konteks_konten_tidak_dikenal(tmp_path):
    from newmotion.application.validasi_job import GalatValidasiJob, validasi_job

    naskah = tmp_path / "naskah.json"
    naskah.write_text(
        '{"genre":"kisah_islami","konteks_konten":"bebas_tanpa_batas","adegan":[]}',
        encoding="utf-8",
    )
    with pytest.raises(GalatValidasiJob, match="konteks_konten tidak dikenal"):
        validasi_job(naskah, tmp_path / "hasil.mp4", wajib_genre=True)


def test_validasi_job_menolak_kisah_islami_dengan_konteks_umum(tmp_path):
    from newmotion.application.validasi_job import GalatValidasiJob, validasi_job

    naskah = tmp_path / "naskah.json"
    naskah.write_text(
        '{"genre":"kisah_islami","konteks_konten":"umum","adegan":[]}',
        encoding="utf-8",
    )
    with pytest.raises(GalatValidasiJob, match="wajib memakai konteks konten Islami"):
        validasi_job(naskah, tmp_path / "hasil.mp4", wajib_genre=True)



def test_naskah_baru_dari_genre_non_islami_wajib_menyatakan_konteks():
    with pytest.raises(ValueError, match="Konteks konten belum ditentukan"):
        konteks_konten_untuk_naskah(
            {"genre": "komedi"}, genre="komedi", wajib_eksplisit=True
        )


def test_sutradara_memisahkan_rencana_semantik_dan_mengaitkan_shot_ke_beat():
    from newmotion.application.pengarah_inti import arahkan_naskah

    nama = "sutradara_rencana_semantik_uji"

    def pengarah(data):
        return {
            "cerita": {
                "shot": [
                    {"at": 0, "_adegan": 0, "boneka": [], "benda": []},
                    {"at": 5, "_adegan": 1, "boneka": [], "benda": []},
                ]
            }
        }

    paket = PaketGenre(nama=nama, pengarah_naskah=pengarah)
    daftarkan(paket)
    naskah = {
        "judul": "Penolong",
        "genre": nama,
        "konteks_konten": "umum",
        "tokoh": [
            {"id": "tokoh-penolong", "nama": "Penolong"},
            {"id": "tokoh-pengendara", "nama": "Pengendara"},
        ],
        "adegan": [
            {
                "id": "beat-001",
                "teks": "Pengendara kehilangan keseimbangan.",
                "peran": ["Pengendara", "Penolong"],
                "tokoh_ids": ["tokoh-pengendara", "tokoh-penolong"],
                "dialog": [],
            },
            {
                "id": "beat-002",
                "teks": "Penolong menghampiri pengendara.",
                "peran": ["Penolong", "Pengendara"],
                "tokoh_ids": ["tokoh-penolong", "tokoh-pengendara"],
                "dialog": [
                    {"pembicara": "Penolong", "ucapan": "Saya bantu.", "penjawab": "Pengendara"}
                ],
                "peristiwa": [{
                    "id": "peristiwa-1",
                    "aktor": "Penolong",
                    "aksi": "menghampiri",
                    "sasaran": "Pengendara",
                    "tujuan": "menolong",
                }],
            },
        ],
    }
    try:
        papan, _, _ = arahkan_naskah(naskah)
        assert papan["rencana_cerita"]["tokoh"] == naskah["tokoh"]
        assert [a["id"] for a in papan["rencana_cerita"]["adegan"]] == [
            "beat-001", "beat-002"
        ]
        assert papan["rencana_cerita"]["adegan"][1]["dialog"] == naskah["adegan"][1]["dialog"]
        assert papan["rencana_cerita"]["adegan"][1]["peristiwa"] == naskah["adegan"][1]["peristiwa"]
        assert [s["_beat_id"] for s in papan["cerita"]["shot"]] == [
            "beat-001", "beat-002"
        ]
        # Instruksi render tetap terpisah; tidak menyisipkan boneka tokoh secara otomatis.
        assert all("boneka" in s and s["boneka"] == [] for s in papan["cerita"]["shot"])
    finally:
        from newmotion.domain import genre as modul_genre
        modul_genre._PAKET.pop(nama, None)


def test_sutradara_menolak_rujukan_tokoh_yang_tidak_terdaftar():
    from newmotion.application.pengarah_inti import GalatPengarahan, arahkan_naskah

    nama = "sutradara_tokoh_tidak_terdaftar_uji"
    paket = PaketGenre(
        nama=nama,
        pengarah_naskah=lambda data: {
            "cerita": {"shot": [{"at": 0, "_adegan": 0}]}
        },
    )
    daftarkan(paket)
    try:
        with pytest.raises(GalatPengarahan, match="ID tokoh yang tidak terdaftar"):
            arahkan_naskah({
                "judul": "Rujukan salah",
                "genre": nama,
                "konteks_konten": "umum",
                "tokoh": [],
                "adegan": [{
                    "id": "beat-001",
                    "teks": "Tokoh hadir.",
                    "tokoh_ids": ["tokoh-hilang"],
                }],
            })
    finally:
        from newmotion.domain import genre as modul_genre
        modul_genre._PAKET.pop(nama, None)


def test_sutradara_menolak_indeks_adegan_shot_di_luar_rencana():
    from newmotion.application.pengarah_inti import GalatPengarahan, arahkan_naskah

    nama = "sutradara_indeks_adegan_salah_uji"
    paket = PaketGenre(
        nama=nama,
        pengarah_naskah=lambda data: {
            "cerita": {"shot": [{"at": 0, "_adegan": 4}]}
        },
    )
    daftarkan(paket)
    try:
        with pytest.raises(GalatPengarahan, match="indeks _adegan di luar daftar beat"):
            arahkan_naskah({
                "judul": "Indeks salah",
                "genre": nama,
                "konteks_konten": "umum",
                "adegan": [{"id": "beat-001", "teks": "Adegan tunggal."}],
            })
    finally:
        from newmotion.domain import genre as modul_genre
        modul_genre._PAKET.pop(nama, None)
