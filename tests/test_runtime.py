import sys

import pytest

from newmotion.runtime.konfigurasi import Konfigurasi
from newmotion.runtime.lingkungan import periksa_lingkungan
from newmotion.infrastructure.proses.subprocess import PelaksanaProses


def test_konfigurasi_profil_test(tmp_path):
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "test.toml").write_text(
        """[runtime]
direktori_hasil = "keluaran"
tingkat_log = "WARNING"
batas_waktu_subproses = 30
""",
        encoding="utf-8",
    )
    konfigurasi = Konfigurasi.muat("test", tmp_path)
    assert konfigurasi.profil == "test"
    assert konfigurasi.direktori_hasil == (tmp_path / "keluaran").resolve()
    assert konfigurasi.batas_waktu_subproses == 30


def test_batas_waktu_tidak_valid(tmp_path, monkeypatch):
    monkeypatch.setenv("NEWMOTION_SUBPROCESS_TIMEOUT", "0")
    with pytest.raises(ValueError):
        Konfigurasi.muat("test", tmp_path)


def test_pemeriksaan_lingkungan_memuat_python():
    hasil = periksa_lingkungan()
    assert hasil[0].nama == "Python"
    assert hasil[0].tersedia is True


def test_pelaksana_proses_mengembalikan_kode_keluar(tmp_path):
    hasil = PelaksanaProses(10).jalankan(
        [sys.executable, "-c", "print('berhasil')"], tmp_path
    )
    assert hasil.kode_keluar == 0
    assert hasil.stdout.strip() == "berhasil"


def test_pelaksana_proses_menghormati_timeout(tmp_path):
    with pytest.raises(TimeoutError):
        PelaksanaProses(0.05).jalankan(
            [sys.executable, "-c", "import time; time.sleep(1)"], tmp_path
        )


from newmotion.application.validasi_job import GalatValidasiJob, validasi_job
from newmotion.domain.job import Job
from newmotion.domain.status_job import StatusJob


def test_transisi_status_job_hanya_mengizinkan_alur_valid(tmp_path):
    job = Job(tmp_path / "spec.json", tmp_path / "hasil.mp4")
    job.ubah_status(StatusJob.BERJALAN)
    job.ubah_status(StatusJob.BERHASIL)
    assert job.status == StatusJob.BERHASIL
    assert job.dimulai_pada is not None
    assert job.selesai_pada is not None
    with pytest.raises(ValueError):
        job.ubah_status(StatusJob.BERJALAN)


def test_validasi_job_menerima_json_objek_dan_mp4(tmp_path):
    spesifikasi = tmp_path / "cerita.json"
    spesifikasi.write_text('{"judul": "Uji", "adegan": []}', encoding="utf-8")
    sumber, keluaran = validasi_job(spesifikasi, tmp_path / "hasil.mp4")
    assert sumber == spesifikasi.resolve()
    assert keluaran == (tmp_path / "hasil.mp4").resolve()


def test_validasi_job_menolak_json_tidak_valid(tmp_path):
    spesifikasi = tmp_path / "rusak.json"
    spesifikasi.write_text("{bukan json}", encoding="utf-8")
    with pytest.raises(GalatValidasiJob):
        validasi_job(spesifikasi, tmp_path / "hasil.mp4")


def test_validasi_job_menolak_ekstensi_keluaran_salah(tmp_path):
    spesifikasi = tmp_path / "cerita.json"
    spesifikasi.write_text("{}", encoding="utf-8")
    with pytest.raises(GalatValidasiJob):
        validasi_job(spesifikasi, tmp_path / "hasil.mov")


from types import SimpleNamespace

from newmotion.application import jalankan_job as modul_job
from newmotion.application.jalankan_job import LayananJalankanJob


def test_layanan_job_mengorkestrasi_render_berhasil(tmp_path, monkeypatch):
    spesifikasi = tmp_path / "cerita.json"
    spesifikasi.write_text("{}", encoding="utf-8")

    class AdapterPalsu:
        def __init__(self, *args):
            pass

        def render(self, *args):
            return SimpleNamespace(kode_keluar=0, stdout="selesai", stderr="")

    monkeypatch.setattr(modul_job, "AdapterPapanLama", AdapterPalsu)
    konfigurasi = SimpleNamespace(akar_proyek=tmp_path, batas_waktu_subproses=10)
    job, hasil = LayananJalankanJob(konfigurasi).jalankan_render(
        spesifikasi, tmp_path / "hasil.mp4"
    )
    assert job.status == StatusJob.BERHASIL
    assert hasil.stdout == "selesai"


def test_layanan_job_mencatat_kegagalan_renderer(tmp_path, monkeypatch):
    spesifikasi = tmp_path / "cerita.json"
    spesifikasi.write_text("{}", encoding="utf-8")

    class AdapterPalsu:
        def __init__(self, *args):
            pass

        def render(self, *args):
            return SimpleNamespace(kode_keluar=3, stdout="", stderr="render gagal")

    monkeypatch.setattr(modul_job, "AdapterPapanLama", AdapterPalsu)
    konfigurasi = SimpleNamespace(akar_proyek=tmp_path, batas_waktu_subproses=10)
    job, _ = LayananJalankanJob(konfigurasi).jalankan_render(
        spesifikasi, tmp_path / "hasil.mp4"
    )
    assert job.status == StatusJob.GAGAL
    assert job.pesan_gagal == "render gagal"



def test_cli_menerima_lokasi_keluaran_setelah_spesifikasi():
    from newmotion.cli import buat_parser

    args = buat_parser().parse_args([
        "render", "mesin-video/papan/kisah/yajuj2_visual3_gabungan.json",
        "-o", "yajuj2-visual3-gabungan.mp4",
    ])
    assert args.perintah == "render"
    assert args.spesifikasi.endswith("yajuj2_visual3_gabungan.json")
    assert args.keluaran == "yajuj2-visual3-gabungan.mp4"
    assert args.tanpa_suara is False


def test_cli_meneruskan_opsi_render_terbatas():
    from newmotion.cli import buat_parser

    args = buat_parser().parse_args([
        "render", "spec.json", "--tanpa-suara", "-d", "12.5", "-o", "hasil.mp4",
    ])
    assert args.tanpa_suara is True
    assert args.durasi == 12.5
