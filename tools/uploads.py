from __future__ import annotations

import re
import uuid
from pathlib import Path

ALLOWED_SUFFIXES = {".csv", ".xlsx", ".xls", ".parquet"}
MAX_UPLOAD_BYTES = 20 * 1024 * 1024
_SAFE_STEM = re.compile(r"[^A-Za-z0-9._-]+")


def safe_upload_path(dest_dir: Path, original_name: str, size: int) -> Path:
    if size > MAX_UPLOAD_BYTES:
        raise ValueError(f"arquivo maior que {MAX_UPLOAD_BYTES // (1024 * 1024)} MB")
    name = Path(original_name.replace("\\", "/")).name
    if not name or name in {".", ".."}:
        raise ValueError("nome de arquivo invalido")
    suffix = Path(name).suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise ValueError(f"extensao nao permitida: {suffix or '(vazia)'}")
    stem = _SAFE_STEM.sub("_", Path(name).stem).strip("._")[:80] or "upload"
    dest_dir.mkdir(parents=True, exist_ok=True)
    return dest_dir / f"{uuid.uuid4().hex}_{stem}{suffix}"
