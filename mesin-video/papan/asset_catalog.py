"""Inventaris aset lokal yang deterministik dan read-only.

Modul ini hanya mencatat berkas yang benar-benar tersedia. Ia tidak menebak
makna aset, tidak mengunduh, tidak mengubah katalog sumber, dan tidak
memberikan persetujuan produksi.
"""
from __future__ import annotations

import hashlib
import mimetypes
from pathlib import Path
from typing import Any


CATALOG_CONTRACT = "motion-studio.asset-catalog@1.0.0"

_EXTENSIONS = {
    ".png": "image",
    ".jpg": "image",
    ".jpeg": "image",
    ".webp": "image",
    ".gif": "image",
    ".bmp": "image",
    ".tif": "image",
    ".tiff": "image",
    ".svg": "vector",
    ".mp3": "audio",
    ".wav": "audio",
    ".ogg": "audio",
    ".m4a": "audio",
    ".aac": "audio",
    ".flac": "audio",
    ".mp4": "video",
    ".mov": "video",
    ".webm": "video",
    ".mkv": "video",
    ".glb": "model_3d",
    ".gltf": "model_3d",
    ".obj": "model_3d",
    ".fbx": "model_3d",
    ".ttf": "font",
    ".otf": "font",
    ".woff": "font",
    ".woff2": "font",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _visible(path: Path, root: Path) -> bool:
    return not any(part.startswith(".") for part in path.relative_to(root).parts)


def scan_asset_catalog(
    asset_root: str | Path,
    *,
    include_hidden: bool = False,
) -> dict[str, Any]:
    """Lakukan inventaris read-only atas file di asset_root.

    ID bersifat stabil terhadap pemindaian ulang selama path relatif tidak
    berubah. Hash mengidentifikasi isi file; ID tidak berubah ketika isi file
    pada path yang sama diperbarui. File symlink dan file di luar root diabaikan.
    """
    root = Path(asset_root).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError(f"Direktori aset tidak ditemukan: {asset_root}")

    assets: list[dict[str, Any]] = []
    warnings: list[dict[str, str]] = []

    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix().casefold()):
        try:
            if path.is_symlink() or not path.is_file():
                continue
            if not include_hidden and not _visible(path, root):
                continue

            resolved = path.resolve(strict=True)
            if not resolved.is_relative_to(root):
                warnings.append({
                    "path": path.relative_to(root).as_posix(),
                    "reason": "outside_asset_root",
                })
                continue

            relative = path.relative_to(root).as_posix()
            extension = path.suffix.lower()
            stat = path.stat()
            assets.append({
                "asset_id": f"local:{relative}",
                "source": "local",
                "relative_path": relative,
                "file_name": path.name,
                "extension": extension,
                "asset_type": _EXTENSIONS.get(extension, "other"),
                "mime_type": mimetypes.guess_type(path.name)[0],
                "size_bytes": stat.st_size,
                "sha256": _sha256(path),
                "approval_status": "unreviewed",
                "production_usable": False,
            })
        except OSError as exc:
            warnings.append({
                "path": path.relative_to(root).as_posix(),
                "reason": f"unreadable:{exc.__class__.__name__}",
            })

    counts: dict[str, int] = {}
    for asset in assets:
        kind = asset["asset_type"]
        counts[kind] = counts.get(kind, 0) + 1

    return {
        "contract": CATALOG_CONTRACT,
        "asset_root": str(root),
        "assets": assets,
        "summary": {
            "total_assets": len(assets),
            "by_type": dict(sorted(counts.items())),
            "unreviewed": len(assets),
            "production_usable": 0,
        },
        "warnings": warnings,
    }
