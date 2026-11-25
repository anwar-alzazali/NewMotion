"""Konfigurasi logging terpusat."""

import logging


def siapkan_logging(tingkat="INFO"):
    logging.basicConfig(level=getattr(logging, tingkat.upper()),
                        format="%(asctime)s %(levelname)s %(name)s %(message)s")
    return logging.getLogger("newmotion")
