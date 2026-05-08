"""Tests for envlens.snapshot."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envlens.snapshot import (
    SnapshotError,
    delete_snapshot,
    list_snapshots,
    load_snapshot,
    save_snapshot,
)


@pytest.fixture()
def snap_dir(tmp_path: Path) -> Path:
    return tmp_path / "snaps"


ENV = {"APP_ENV": "production", "DB_HOST": "db.example.com", "PORT": "5432"}


def test_save_creates_file(snap_dir):
    path = save_snapshot("prod", ENV, directory=snap_dir)
    assert path.exists()
    assert path.suffix == ".json"


def test_save_and_load_roundtrip(snap_dir):
    save_snapshot("prod", ENV, directory=snap_dir)
    loaded = load_snapshot("prod", directory=snap_dir)
    assert loaded == ENV


def test_load_missing_raises(snap_dir):
    with pytest.raises(SnapshotError, match="not found"):
        load_snapshot("ghost", directory=snap_dir)


def test_load_corrupt_file_raises(snap_dir):
    snap_dir.mkdir(parents=True)
    (snap_dir / "bad.json").write_text("not json", encoding="utf-8")
    with pytest.raises(SnapshotError, match="corrupt"):
        load_snapshot("bad", directory=snap_dir)


def test_load_missing_env_key_raises(snap_dir):
    snap_dir.mkdir(parents=True)
    (snap_dir / "noenv.json").write_text(json.dumps({"name": "noenv"}), encoding="utf-8")
    with pytest.raises(SnapshotError, match="corrupt"):
        load_snapshot("noenv", directory=snap_dir)


def test_list_empty_when_directory_absent(snap_dir):
    assert list_snapshots(snap_dir) == []


def test_list_returns_names(snap_dir):
    save_snapshot("alpha", ENV, directory=snap_dir)
    save_snapshot("beta", ENV, directory=snap_dir)
    assert list_snapshots(snap_dir) == ["alpha", "beta"]


def test_delete_removes_snapshot(snap_dir):
    save_snapshot("temp", ENV, directory=snap_dir)
    delete_snapshot("temp", directory=snap_dir)
    assert "temp" not in list_snapshots(snap_dir)


def test_delete_missing_raises(snap_dir):
    with pytest.raises(SnapshotError, match="not found"):
        delete_snapshot("ghost", directory=snap_dir)


def test_metadata_stored_in_file(snap_dir):
    meta = {"source": "production", "author": "ci-bot"}
    path = save_snapshot("with-meta", ENV, directory=snap_dir, metadata=meta)
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["metadata"] == meta


def test_created_at_present(snap_dir):
    path = save_snapshot("ts", ENV, directory=snap_dir)
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert "created_at" in payload
    assert payload["created_at"].endswith("+00:00")


def test_name_with_path_separator_sanitised(snap_dir):
    save_snapshot("a/b", ENV, directory=snap_dir)
    names = list_snapshots(snap_dir)
    assert any("a" in n for n in names)
    # Must not have created a sub-directory
    assert not (snap_dir / "a").is_dir()
