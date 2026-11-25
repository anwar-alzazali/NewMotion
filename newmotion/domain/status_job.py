"""Status dan aturan transisi job produksi."""

from enum import StrEnum


class StatusJob(StrEnum):
    MENUNGGU = "menunggu"
    BERJALAN = "berjalan"
    BERHASIL = "berhasil"
    GAGAL = "gagal"
    DIBATALKAN = "dibatalkan"


TRANSISI_DIIZINKAN = {
    StatusJob.MENUNGGU: {StatusJob.BERJALAN, StatusJob.DIBATALKAN},
    StatusJob.BERJALAN: {StatusJob.BERHASIL, StatusJob.GAGAL, StatusJob.DIBATALKAN},
    StatusJob.BERHASIL: set(),
    StatusJob.GAGAL: set(),
    StatusJob.DIBATALKAN: set(),
}
