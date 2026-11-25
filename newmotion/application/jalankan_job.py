"""Orkestrasi satu job render secara lokal."""

import logging
from pathlib import Path

from newmotion.application.validasi_job import validasi_job
from newmotion.domain.job import Job
from newmotion.domain.status_job import StatusJob
from newmotion.infrastructure.render.papan_lama import AdapterPapanLama


class LayananJalankanJob:
    def __init__(self, konfigurasi, log=None):
        self.konfigurasi = konfigurasi
        self.log = log or logging.getLogger("newmotion.job")

    def jalankan_render(self, spesifikasi, keluaran, argumen_tambahan=()):
        sumber, tujuan = validasi_job(spesifikasi, keluaran)
        tujuan.parent.mkdir(parents=True, exist_ok=True)
        job = Job(spesifikasi=sumber, keluaran=tujuan)
        self.log.info("Job dibuat id=%s sumber=%s", job.id, sumber)
        job.ubah_status(StatusJob.BERJALAN)
        self.log.info("Job berjalan id=%s", job.id)
        adapter = AdapterPapanLama(
            self.konfigurasi.akar_proyek,
            self.konfigurasi.batas_waktu_subproses,
            self.log,
        )
        try:
            hasil = adapter.render(sumber, tujuan, argumen_tambahan)
            if hasil.kode_keluar != 0:
                job.pesan_gagal = hasil.stderr[-2000:] or f"Renderer keluar dengan kode {hasil.kode_keluar}"
                job.ubah_status(StatusJob.GAGAL)
            else:
                job.ubah_status(StatusJob.BERHASIL)
            self.log.info("Job selesai id=%s status=%s", job.id, job.status)
            return job, hasil
        except Exception as galat:
            job.pesan_gagal = str(galat)
            job.ubah_status(StatusJob.GAGAL)
            self.log.exception("Job gagal id=%s", job.id)
            raise
