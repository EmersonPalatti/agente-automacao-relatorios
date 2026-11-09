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


def test_prune_older_than_keeps_recent(tmp_path: Path):
    import os
    import time

    from tools.uploads import prune_older_than

    old_dir = tmp_path / "old_run"
    old_dir.mkdir()
    (old_dir / "report.md").write_text("x")
    old_file = tmp_path / "old.csv"
    old_file.write_text("x")
    recent = tmp_path / "recent_run"
    recent.mkdir()
    past = time.time() - 10_000
    os.utime(old_dir, (past, past))
    os.utime(old_file, (past, past))

    assert prune_older_than(tmp_path, 3600) == 2
    assert [p.name for p in tmp_path.iterdir()] == ["recent_run"]
