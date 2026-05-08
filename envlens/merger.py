"""Merge multiple env dicts with configurable conflict resolution."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple


class MergeStrategy(str, Enum):
    """How to resolve a key that appears in more than one source."""

    FIRST = "first"   # keep the value from the earliest source
    LAST = "last"     # keep the value from the latest source (default)
    ERROR = "error"   # raise MergeConflictError on any conflict


class MergeConflictError(Exception):
    """Raised when MergeStrategy.ERROR is used and a conflict is detected."""

    def __init__(self, key: str, values: List[Tuple[int, str]]) -> None:
        detail = ", ".join(f"source[{i}]={v!r}" for i, v in values)
        super().__init__(f"Conflict for key {key!r}: {detail}")
        self.key = key
        self.conflicting_values = values


@dataclass
class MergeResult:
    """Outcome of a merge operation."""

    merged: Dict[str, str]
    conflicts: Dict[str, List[Tuple[int, str]]] = field(default_factory=dict)

    @property
    def has_conflicts(self) -> bool:
        return bool(self.conflicts)

    def conflict_summary(self) -> str:
        if not self.conflicts:
            return "No conflicts."
        lines = []
        for key, pairs in self.conflicts.items():
            detail = ", ".join(f"source[{i}]={v!r}" for i, v in pairs)
            lines.append(f"  {key}: {detail}")
        return "Conflicts:\n" + "\n".join(lines)


def merge_envs(
    sources: List[Dict[str, str]],
    strategy: MergeStrategy = MergeStrategy.LAST,
    ignore_keys: Optional[List[str]] = None,
) -> MergeResult:
    """Merge *sources* into a single env dict using *strategy*.

    Parameters
    ----------
    sources:
        Ordered list of env dicts (index 0 is the "first" / lowest priority).
    strategy:
        Conflict resolution policy.
    ignore_keys:
        Keys to exclude from the merge entirely.
    """
    skip = set(ignore_keys or [])
    merged: Dict[str, str] = {}
    conflicts: Dict[str, List[Tuple[int, str]]] = {}

    for idx, env in enumerate(sources):
        for key, value in env.items():
            if key in skip:
                continue

            if key not in merged:
                merged[key] = value
                continue

            # Key already present — record the conflict.
            if key not in conflicts:
                # Locate which earlier source first set this key.
                first_idx = next(
                    i for i, s in enumerate(sources[:idx]) if key in s
                )
                conflicts[key] = [(first_idx, merged[key])]
            conflicts[key].append((idx, value))

            if strategy is MergeStrategy.ERROR:
                raise MergeConflictError(key, conflicts[key])
            elif strategy is MergeStrategy.LAST:
                merged[key] = value
            # MergeStrategy.FIRST: keep existing value, do nothing.

    return MergeResult(merged=merged, conflicts=conflicts)
