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
        peristiwa = papan["rencana_cerita"]["adegan"][1]["peristiwa"][0]
        sumber = naskah["adegan"][1]["peristiwa"][0]
        assert {k: peristiwa[k] for k in sumber} == sumber
        assert peristiwa["aktor_id"] == "tokoh-penolong"
        assert peristiwa["sasaran_tokoh_id"] == "tokoh-pengendara"
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


def test_rencana_semantik_mengaitkan_aktor_dan_sasaran_ke_id_tokoh():
    from newmotion.application.pengarah_inti import arahkan_naskah

    nama = "sutradara_tautan_peristiwa_uji"
    paket = PaketGenre(
        nama=nama,
        pengarah_naskah=lambda data: {
            "cerita": {"shot": [{"at": 0, "_adegan": 0}]}
        },
    )
    daftarkan(paket)
    try:
        papan, _, _ = arahkan_naskah({
            "judul": "Penolong",
            "genre": nama,
            "konteks_konten": "umum",
            "tokoh": [
                {"id": "tokoh-penolong", "nama": "Penolong"},
                {"id": "tokoh-korban", "nama": "Pengendara"},
            ],
            "adegan": [{
                "id": "beat-001",
                "teks": "Penolong menghampiri pengendara.",
                "tokoh_ids": ["tokoh-penolong", "tokoh-korban"],
                "peristiwa": [{
                    "id": "peristiwa-1",
                    "aktor": "  PENOLONG ",
                    "aksi": "menghampiri",
                    "sasaran": "Pengendara",
                }],
            }],
        })
        peristiwa = papan["rencana_cerita"]["adegan"][0]["peristiwa"][0]
        assert peristiwa["aktor"] == "  PENOLONG "
        assert peristiwa["aktor_id"] == "tokoh-penolong"
        assert peristiwa["sasaran_tokoh_id"] == "tokoh-korban"
        assert papan["rencana_cerita"]["diagnostik"] == []
    finally:
        from newmotion.domain import genre as modul_genre
        modul_genre._PAKET.pop(nama, None)


def test_rencana_semantik_tidak_mengarang_id_untuk_sasaran_benda():
    from newmotion.application.pengarah_inti import arahkan_naskah

    nama = "sutradara_sasaran_benda_uji"
    paket = PaketGenre(
        nama=nama,
        pengarah_naskah=lambda data: {
            "cerita": {"shot": [{"at": 0, "_adegan": 0}]}
        },
    )
    daftarkan(paket)
    try:
        papan, _, _ = arahkan_naskah({
            "judul": "Motor tergelincir",
            "genre": nama,
            "konteks_konten": "umum",
            "tokoh": [{"id": "tokoh-pengendara", "nama": "Pengendara"}],
            "adegan": [{
                "id": "beat-001",
                "teks": "Pengendara mengendalikan motor.",
                "tokoh_ids": ["tokoh-pengendara"],
                "peristiwa": [{
                    "aktor": "Pengendara",
                    "aksi": "mengendarai",
                    "sasaran": "motor",
                }],
            }],
        })
        peristiwa = papan["rencana_cerita"]["adegan"][0]["peristiwa"][0]
        assert peristiwa["aktor_id"] == "tokoh-pengendara"
        assert "sasaran_tokoh_id" not in peristiwa
        assert peristiwa["sasaran"] == "motor"
    finally:
        from newmotion.domain import genre as modul_genre
        modul_genre._PAKET.pop(nama, None)


def test_rencana_semantik_mencatat_aktor_yang_belum_terpetakan():
    from newmotion.application.pengarah_inti import arahkan_naskah

    nama = "sutradara_aktor_belum_terpetakan_uji"
    paket = PaketGenre(
        nama=nama,
        pengarah_naskah=lambda data: {
            "cerita": {"shot": [{"at": 0, "_adegan": 0}]}
        },
    )
    daftarkan(paket)
    try:
        papan, _, _ = arahkan_naskah({
            "judul": "Aktor belum ada",
            "genre": nama,
            "konteks_konten": "umum",
            "tokoh": [],
            "adegan": [{
                "id": "beat-001",
                "teks": "Seseorang menolong.",
                "peristiwa": [{"aktor": "Orang asing", "aksi": "menolong"}],
            }],
        })
        assert papan["rencana_cerita"]["diagnostik"] == [{
            "kode": "aktor_belum_terpetakan",
            "beat_id": "beat-001",
            "peristiwa": None,
            "nilai": "Orang asing",
        }]
        assert "aktor_id" not in papan["rencana_cerita"]["adegan"][0]["peristiwa"][0]
    finally:
        from newmotion.domain import genre as modul_genre
        modul_genre._PAKET.pop(nama, None)


def test_rencana_semantik_menolak_peristiwa_non_objek():
    from newmotion.application.pengarah_inti import GalatPengarahan, arahkan_naskah

    nama = "sutradara_peristiwa_tidak_valid_uji"
    paket = PaketGenre(
        nama=nama,
        pengarah_naskah=lambda data: {
            "cerita": {"shot": [{"at": 0, "_adegan": 0}]}
        },
    )
    daftarkan(paket)
    try:
        with pytest.raises(GalatPengarahan, match="harus berupa objek"):
            arahkan_naskah({
                "judul": "Peristiwa rusak",
                "genre": nama,
                "konteks_konten": "umum",
                "adegan": [{
                    "id": "beat-001",
                    "teks": "Adegan.",
                    "peristiwa": ["teks bukan objek"],
                }],
            })
    finally:
        from newmotion.domain import genre as modul_genre
        modul_genre._PAKET.pop(nama, None)

def test_sutradara_meneruskan_peristiwa_semantik_ke_rencana_blocking():
    from newmotion.application.pengarah_inti import arahkan_naskah

    nama = "sutradara_blocking_semantik_uji"
    paket = PaketGenre(
        nama=nama,
        pengarah_naskah=lambda data: {
            "cerita": {"shot": [{"at": 0, "_adegan": 0, "boneka": [], "benda": []}]}
        },
    )
    daftarkan(paket)
    try:
        papan, _, _ = arahkan_naskah({
            "judul": "Penolong",
            "genre": nama,
            "konteks_konten": "umum",
            "tokoh": [{"id": "tokoh-a", "nama": "Penolong"}],
            "adegan": [{
                "id": "beat-001",
                "teks": "Penolong menghampiri korban.",
                "peristiwa": [{
                    "id": "peristiwa-1",
                    "aktor": "Penolong",
                    "aksi": "menghampiri",
                    "sasaran": "motor",
                }],
            }],
        })
        rencana = papan["rencana_blocking"]
        assert rencana["tahap"] == "kontrak_semantik"
        assert rencana["peristiwa"][0]["aktor_id"] == "tokoh-a"
        assert rencana["peristiwa"][0]["sasaran"] == "motor"
        assert rencana["shot"][0]["beat_id"] == "beat-001"
        assert rencana["shot"][0]["peristiwa_ids"] == ["peristiwa-1"]
        assert papan["cerita"]["shot"][0]["boneka"] == []
    finally:
        from newmotion.domain import genre as modul_genre
        modul_genre._PAKET.pop(nama, None)



def test_penjaga_kisah_islami_memeriksa_roster_tokoh_semantik():
    from newmotion.paket_genre.kisah_islami.penjaga_tokoh import periksa_adab_tokoh

    hasil = periksa_adab_tokoh({
        "rencana_cerita": {
            "tokoh": [{
                "id": "pengendara-01",
                "nama": "Pengendara",
                "kategori": "tokoh_umum",
                "tampil": "tubuh",
            }]
        }
    })
    assert hasil == []


@pytest.mark.parametrize(
    ("tokoh", "kode"),
    [
        ({"id": "nabi-01", "nama": "Nabi Hud", "kategori": "nabi", "tampil": "tubuh"},
         "CARA_TAMPIL_TOKOH_SUCI"),
        ({"id": "malaikat-01", "nama": "Malaikat", "kategori": "malaikat", "tampil": "tubuh"},
         "CARA_TAMPIL_TOKOH_SUCI"),
        ({"id": "sahabat-01", "nama": "Sahabat", "kategori": "sahabat", "tampil": "tubuh"},
         "CARA_TAMPIL_TOKOH_SUCI"),
        ({"id": "allah-01", "nama": "Allah", "kategori": "tokoh_umum", "tampil": "tubuh"},
         "ALLAH_TIDAK_DIVISUALKAN"),
        ({"id": "orang-01", "nama": "Orang biasa", "kategori": "tokoh_umum", "tampil": "wajah_cahaya"},
         "BENTUK_CAHAYA_SALAH"),
    ],
)
def test_penjaga_roster_semantik_menolak_pelanggaran_adab(tokoh, kode):
    from newmotion.paket_genre.kisah_islami.penjaga_tokoh import periksa_adab_tokoh

    temuan = periksa_adab_tokoh({"rencana_cerita": {"tokoh": [tokoh]}})
    assert kode in {item.kode for item in temuan}


@pytest.mark.parametrize(
    ("kategori", "tampil"),
    [
        ("nabi", "nur"),
        ("rasul", "nur"),
        ("malaikat", "cahaya_malaikat"),
        ("sahabat", "wajah_cahaya"),
    ],
)
def test_penjaga_roster_semantik_menerima_tampilan_sakral_yang_diizinkan(kategori, tampil):
    from newmotion.paket_genre.kisah_islami.penjaga_tokoh import periksa_adab_tokoh

    hasil = periksa_adab_tokoh({
        "rencana_cerita": {
            "tokoh": [{
                "id": "tokoh-sakral",
                "nama": "Tokoh",
                "kategori": kategori,
                "tampil": tampil,
            }]
        }
    })
    assert hasil == []


def test_gerbang_renderer_memblokir_roster_semantik_yang_melanggar_adab(monkeypatch):
    import importlib.util

    akar = Path(__file__).resolve().parents[1]
    sumber = akar / "mesin-video" / "papan_buat.py"
    spec_modul = importlib.util.spec_from_file_location("newmotion_uji_papan_buat_roster", sumber)
    modul_render = importlib.util.module_from_spec(spec_modul)
    spec_modul.loader.exec_module(modul_render)

    with pytest.raises(modul_render.SpekDitolak):
        modul_render.jaga_spek({
            "genre": "kisah_islami",
            "konteks_konten": "islami",
            "rencana_cerita": {
                "tokoh": [{
                    "id": "nabi-01",
                    "nama": "Nabi Hud",
                    "kategori": "nabi",
                    "tampil": "tubuh",
                }]
            },
        })


def test_paket_tanpa_kait_visual_tokoh_menahan_roster_dari_renderer():
    from newmotion.application.pengarah_inti import arahkan_naskah

    nama = "genre_tanpa_visual_tokoh_uji"
    paket = PaketGenre(
        nama=nama,
        pengarah_naskah=lambda data: {
            "cerita": {"shot": [{"at": 0, "_adegan": 0, "boneka": [], "benda": []}]}
        },
    )
    daftarkan(paket)
    try:
        papan, _, _ = arahkan_naskah({
            "judul": "Pemeran belum didukung",
            "genre": nama,
            "konteks_konten": "umum",
            "tokoh": [{"id": "tokoh-a", "nama": "Aktor"}],
            "adegan": [{"id": "beat-001", "teks": "Aktor masuk.", "tokoh_ids": ["tokoh-a"]}],
        })
        assert papan["rencana_visual_tokoh"]["status"] == "belum_didukung_paket"
        assert papan["rencana_visual_tokoh"]["shot"] == []
        assert papan["rencana_visual_tokoh"]["diagnostik"][0]["kode"] == (
            "paket_belum_menyediakan_pengarah_tokoh_visual"
        )
        assert papan["cerita"]["shot"][0]["boneka"] == []
    finally:
        from newmotion.domain import genre as modul_genre
        modul_genre._PAKET.pop(nama, None)


def test_paket_dapat_mengarahkan_rencana_visual_tokoh_secara_opt_in():
    from newmotion.application.pengarah_inti import arahkan_naskah

    nama = "genre_dengan_visual_tokoh_uji"
    diterima = []

    def pengarah_visual(rencana_cerita, rencana_blocking, cerita):
        diterima.append((rencana_cerita, rencana_blocking, cerita))
        return {
            "status": "siap_diterjemahkan",
            "shot": [{
                "indeks": 0,
                "tokoh": [{
                    "tokoh_id": "tokoh-penolong",
                    "aksi": "jalan",
                    "x": [[0, 200], [2, 500]],
                    "y": 1450,
                }],
            }],
            "diagnostik": [],
        }

    paket = PaketGenre(
        nama=nama,
        pengarah_naskah=lambda data: {
            "cerita": {"shot": [{"at": 0, "_adegan": 0, "boneka": [], "benda": []}]}
        },
        pengarah_tokoh_visual=pengarah_visual,
    )
    daftarkan(paket)
    try:
        papan, _, _ = arahkan_naskah({
            "judul": "Penolong",
            "genre": nama,
            "konteks_konten": "umum",
            "tokoh": [{"id": "tokoh-penolong", "nama": "Penolong"}],
            "adegan": [{
                "id": "beat-001",
                "teks": "Penolong berjalan.",
                "tokoh_ids": ["tokoh-penolong"],
                "peristiwa": [{
                    "aktor": "Penolong",
                    "aksi": "jalan",
                }],
            }],
        })
        assert diterima
        assert diterima[0][0]["tokoh"][0]["id"] == "tokoh-penolong"
        assert diterima[0][1]["peristiwa"][0]["aktor_id"] == "tokoh-penolong"
        assert papan["rencana_visual_tokoh"]["status"] == "siap_diterjemahkan"
        assert papan["rencana_visual_tokoh"]["shot"][0]["tokoh"][0]["aksi"] == "jalan"
        # Kait visual mengeluarkan rencana, bukan menyisipkan boneka secara diam-diam.
        assert papan["cerita"]["shot"][0]["boneka"] == []
    finally:
        from newmotion.domain import genre as modul_genre
        modul_genre._PAKET.pop(nama, None)


def test_paket_menolak_kait_pengarah_visual_tokoh_bukan_fungsi():
    with pytest.raises(TypeError, match="pengarah_tokoh_visual"):
        PaketGenre(
            nama="genre_visual_tokoh_salah_uji",
            pengarah_tokoh_visual="bukan-fungsi",
        )


def test_pengarah_visual_tokoh_menolak_hasil_dengan_kontrak_tidak_lengkap():
    from newmotion.application.pengarah_inti import GalatPengarahan, arahkan_naskah

    nama = "genre_visual_tokoh_tidak_valid_uji"
    paket = PaketGenre(
        nama=nama,
        pengarah_naskah=lambda data: {
            "cerita": {"shot": [{"at": 0, "_adegan": 0, "boneka": [], "benda": []}]}
        },
        pengarah_tokoh_visual=lambda *args: {"status": "siap", "shot": "bukan-daftar"},
    )
    daftarkan(paket)
    try:
        with pytest.raises(GalatPengarahan, match="daftar shot dan diagnostik"):
            arahkan_naskah({
                "judul": "Kontrak visual salah",
                "genre": nama,
                "konteks_konten": "umum",
                "adegan": [{"id": "beat-001", "teks": "Tokoh hadir."}],
            })
    finally:
        from newmotion.domain import genre as modul_genre
        modul_genre._PAKET.pop(nama, None)


def test_kisah_islami_tidak_mengaktifkan_pengarah_pemeran_cerita_otomatis():
    from newmotion.application.pengarah_inti import arahkan_naskah

    papan, _, _ = arahkan_naskah({
        "judul": "Avatar tetap",
        "genre": "kisah_islami",
        "konteks_konten": "islami",
        "tokoh": [{"id": "tokoh-umum", "nama": "Pengendara", "kategori": "tokoh_umum"}],
        "adegan": [{
            "id": "beat-001",
            "teks": "Pengendara melintas.",
            "tokoh_ids": ["tokoh-umum"],
        }],
    })
    assert papan["rencana_visual_tokoh"]["status"] == "belum_didukung_paket"
    assert papan["rencana_visual_tokoh"]["shot"] == []
    assert all(
        boneka.get("id") == "kamu"
        for shot in papan["cerita"]["shot"]
        for boneka in shot.get("boneka", [])
    )
