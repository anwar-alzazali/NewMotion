"""Shim kompatibilitas; penjaga tokoh kini dimiliki paket genre Kisah Islami."""
from pathlib import Path
import sys

AKAR_REPO = Path(__file__).resolve().parents[2]
if str(AKAR_REPO) not in sys.path:
    sys.path.insert(0, str(AKAR_REPO))

from newmotion.paket_genre.kisah_islami.penjaga_tokoh_legacy import (  # noqa: E402,F401
    ALLAH,
    NABI_MALAIKAT,
    SAHABAT,
    NAMA_TINGKAT,
    Pelanggaran,
    TokohSuciDigambarError,
    periksa_tokoh_suci,
    tingkat_suci,
    wajib_lulus_tokoh_suci,
)
