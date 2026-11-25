"""Orkestrasi satu job render secara lokal."""

import json
import logging
import os
from pathlib import Path

from newmotion.application.validasi_job import validasi_job
from newmotion.application.pengarah_inti import arahkan_naskah
from newmotion.domain.job import Job
from newmotion.domain.status_job import StatusJob
from newmotion.infrastructure.render.papan_lama import AdapterPapanLama


class LayananJalankanJob:
    def __init__(self, konfigurasi, log=None):
        self.konfigurasi = konfigurasi
        self.log = log or logging.getLogger("newmotion.job")

    @staticmethod
    def _siapkan_papan_dari_naskah(sumber, tujuan, genre_pilihan=None):
        """Jalankan sutradara inti dan simpan papan hasil pengarahan."""
        with sumber.open("r", encoding="utf-8") as berkas:
            naskah = json.load(berkas)

        spesifikasi, nama_genre, jumlah_shot = arahkan_naskah(
            naskah, genre_pilihan=genre_pilihan
        )
        berkas_papan = tujuan.with_suffix(".papan.json")
        sementara = berkas_papan.with_name(berkas_papan.name + ".tmp")
        try:
            sementara.write_text(
                json.dumps(spesifikasi, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            os.replace(sementara, berkas_papan)
        finally:
            if sementara.exists():
                sementara.unlink()
        return berkas_papan, nama_genre, jumlah_shot

    def jalankan_render(self, spesifikasi, keluaran, argumen_tambahan=(), *, naskah=False, genre_pilihan=None):
        sumber, tujuan = validasi_job(
            spesifikasi, keluaran, wajib_genre=naskah, genre_pilihan=genre_pilihan
        )
        berkas_render = sumber
        if naskah:
            berkas_render, nama_genre, jumlah_shot = self._siapkan_papan_dari_naskah(
                sumber, tujuan, genre_pilihan=genre_pilihan
            )
            self.log.info(
                "Sutradara inti memakai paket %s dan menghasilkan %s shot; papan=%s",
                nama_genre,
                jumlah_shot,
                berkas_render,
            )
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
            hasil = adapter.render(berkas_render, tujuan, argumen_tambahan)
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
