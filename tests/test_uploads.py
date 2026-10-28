from pathlib import Path

import pytest

from tools.uploads import MAX_UPLOAD_BYTES, safe_upload_path


def test_safe_upload_strips_path_and_uuid(tmp_path: Path):
    dest = safe_upload_path(tmp_path, r"..\..\etc\passwd.csv", 100)
    assert dest.parent == tmp_path
    assert dest.suffix == ".csv"
    assert ".." not in dest.name
    assert dest.name.endswith("passwd.csv")


def test_rejects_bad_extension(tmp_path: Path):
    with pytest.raises(ValueError, match="extensao"):
        safe_upload_path(tmp_path, "malware.exe", 10)


def test_rejects_oversize(tmp_path: Path):
    with pytest.raises(ValueError, match="maior"):
        safe_upload_path(tmp_path, "huge.csv", MAX_UPLOAD_BYTES + 1)
