"""Core diffing logic for comparing environment variable sets."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set


@dataclass
class EnvDiffResult:
    """Holds the result of comparing two environment variable mappings."""

    source_name: str
    target_name: str
    only_in_source: Dict[str, str] = field(default_factory=dict)
    only_in_target: Dict[str, str] = field(default_factory=dict)
    value_mismatches: Dict[str, tuple[str, str]] = field(default_factory=dict)
    matching: Set[str] = field(default_factory=set)

    @property
    def has_differences(self) -> bool:
        """Return True if any differences were found."""
        return bool(self.only_in_source or self.only_in_target or self.value_mismatches)

    def summary(self) -> str:
        """Return a human-readable summary of the diff."""
        lines: List[str] = [
            f"Diff: {self.source_name!r} vs {self.target_name!r}",
            f"  Matching keys      : {len(self.matching)}",
            f"  Only in source     : {len(self.only_in_source)}",
            f"  Only in target     : {len(self.only_in_target)}",
            f"  Value mismatches   : {len(self.value_mismatches)}",
        ]
        if self.only_in_source:
            lines.append("  [+] Only in source:")
            for k, v in sorted(self.only_in_source.items()):
                lines.append(f"      {k}={v!r}")
        if self.only_in_target:
            lines.append("  [-] Only in target:")
            for k, v in sorted(self.only_in_target.items()):
                lines.append(f"      {k}={v!r}")
        if self.value_mismatches:
            lines.append("  [~] Value mismatches:")
            for k, (sv, tv) in sorted(self.value_mismatches.items()):
                lines.append(f"      {k}: {sv!r} -> {tv!r}")
        return '\n'.join(lines)


def diff_envs(
    source: Dict[str, str],
    target: Dict[str, str],
    source_name: str = 'source',
    target_name: str = 'target',
    ignore_keys: Optional[List[str]] = None,
) -> EnvDiffResult:
    """Compare two environment variable mappings and return a diff result.

    Args:
        source: The baseline environment variable mapping.
        target: The environment variable mapping to compare against.
        source_name: Label for the source (used in output).
        target_name: Label for the target (used in output).
        ignore_keys: Optional list of keys to exclude from comparison.

    Returns:
        An EnvDiffResult describing all differences.
    """
    ignored: Set[str] = set(ignore_keys or [])
    source_keys = {k for k in source if k not in ignored}
    target_keys = {k for k in target if k not in ignored}

    result = EnvDiffResult(source_name=source_name, target_name=target_name)
    result.only_in_source = {k: source[k] for k in source_keys - target_keys}
    result.only_in_target = {k: target[k] for k in target_keys - source_keys}

    for key in source_keys & target_keys:
        if source[key] == target[key]:
            result.matching.add(key)
        else:
            result.value_mismatches[key] = (source[key], target[key])

    return result
