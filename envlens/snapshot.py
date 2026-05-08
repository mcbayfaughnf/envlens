"""Snapshot support: save and load named env snapshots for later diffing."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

DEFAULT_SNAPSHOT_DIR = Path(".envlens_snapshots")


class SnapshotError(Exception):
    """Raised when a snapshot operation fails."""


def _snapshot_path(name: str, directory: Path) -> Path:
    safe_name = name.replace(os.sep, "_").replace("/", "_")
    return directory / f"{safe_name}.json"


def save_snapshot(
    name: str,
    env: Dict[str, str],
    directory: Path = DEFAULT_SNAPSHOT_DIR,
    metadata: Optional[Dict] = None,
) -> Path:
    """Persist *env* as a named snapshot under *directory*.

    Returns the path of the written file.
    """
    directory.mkdir(parents=True, exist_ok=True)
    path = _snapshot_path(name, directory)
    payload = {
        "name": name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "metadata": metadata or {},
        "env": env,
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def load_snapshot(
    name: str,
    directory: Path = DEFAULT_SNAPSHOT_DIR,
) -> Dict[str, str]:
    """Load a previously saved snapshot by *name*.

    Raises :class:`SnapshotError` if the snapshot does not exist or is corrupt.
    """
    path = _snapshot_path(name, directory)
    if not path.exists():
        raise SnapshotError(f"Snapshot '{name}' not found in {directory}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload["env"]
    except (json.JSONDecodeError, KeyError) as exc:
        raise SnapshotError(f"Snapshot '{name}' is corrupt: {exc}") from exc


def list_snapshots(directory: Path = DEFAULT_SNAPSHOT_DIR) -> list[str]:
    """Return snapshot names available in *directory*, sorted alphabetically."""
    if not directory.exists():
        return []
    return sorted(
        p.stem
        for p in directory.iterdir()
        if p.suffix == ".json" and p.is_file()
    )


def delete_snapshot(
    name: str,
    directory: Path = DEFAULT_SNAPSHOT_DIR,
) -> None:
    """Remove a snapshot by *name*. Raises :class:`SnapshotError` if missing."""
    path = _snapshot_path(name, directory)
    if not path.exists():
        raise SnapshotError(f"Snapshot '{name}' not found in {directory}")
    path.unlink()
