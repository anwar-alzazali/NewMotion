"""Entitas job produksi video."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from newmotion.domain.status_job import StatusJob, TRANSISI_DIIZINKAN


@dataclass
class Job:
    spesifikasi: Path
    keluaran: Path
    id: str = field(default_factory=lambda: str(uuid4()))
    status: StatusJob = StatusJob.MENUNGGU
    dibuat_pada: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    dimulai_pada: datetime | None = None
    selesai_pada: datetime | None = None
    pesan_gagal: str | None = None

    def ubah_status(self, status_baru):
        if status_baru not in TRANSISI_DIIZINKAN[self.status]:
            raise ValueError(f"Transisi status job tidak diizinkan: {self.status} -> {status_baru}")
        waktu = datetime.now(timezone.utc)
        self.status = status_baru
        if status_baru == StatusJob.BERJALAN:
            self.dimulai_pada = waktu
        if status_baru in {StatusJob.BERHASIL, StatusJob.GAGAL, StatusJob.DIBATALKAN}:
            self.selesai_pada = waktu
