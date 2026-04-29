"""Formats and renders EnvDiffResult output for CLI and programmatic use."""

from __future__ import annotations

from enum import Enum
from typing import TextIO
import sys

from envlens.diff import EnvDiffResult


class OutputFormat(str, Enum):
    TEXT = "text"
    JSON = "json"
    MARKDOWN = "markdown"


def _render_text(result: EnvDiffResult, source_label: str, target_label: str) -> str:
    lines: list[str] = []

    if result.only_in_source:
        lines.append(f"Only in {source_label}:")
        for key in sorted(result.only_in_source):
            lines.append(f"  - {key}={result.only_in_source[key]}")

    if result.only_in_target:
        lines.append(f"Only in {target_label}:")
        for key in sorted(result.only_in_target):
            lines.append(f"  + {key}={result.only_in_target[key]}")

    if result.value_mismatches:
        lines.append("Value mismatches:")
        for key in sorted(result.value_mismatches):
            src_val, tgt_val = result.value_mismatches[key]
            lines.append(f"  ~ {key}")
            lines.append(f"      {source_label}: {src_val}")
            lines.append(f"      {target_label}: {tgt_val}")

    if not lines:
        lines.append("No differences found.")

    return "\n".join(lines)


def _render_json(result: EnvDiffResult, source_label: str, target_label: str) -> str:
    import json

    payload = {
        "source": source_label,
        "target": target_label,
        "only_in_source": result.only_in_source,
        "only_in_target": result.only_in_target,
        "value_mismatches": {
            k: {source_label: v[0], target_label: v[1]}
            for k, v in result.value_mismatches.items()
        },
    }
    return json.dumps(payload, indent=2)


def _render_markdown(result: EnvDiffResult, source_label: str, target_label: str) -> str:
    lines: list[str] = [f"## Env Diff: `{source_label}` vs `{target_label}`", ""]

    if result.only_in_source:
        lines.append(f"### Only in `{source_label}`")
        for key in sorted(result.only_in_source):
            lines.append(f"- `{key}` = `{result.only_in_source[key]}`")
        lines.append("")

    if result.only_in_target:
        lines.append(f"### Only in `{target_label}`")
        for key in sorted(result.only_in_target):
            lines.append(f"- `{key}` = `{result.only_in_target[key]}`")
        lines.append("")

    if result.value_mismatches:
        lines.append("### Value Mismatches")
        lines.append(f"| Key | `{source_label}` | `{target_label}` |")
        lines.append("|-----|------|------|")
        for key in sorted(result.value_mismatches):
            src_val, tgt_val = result.value_mismatches[key]
            lines.append(f"| `{key}` | `{src_val}` | `{tgt_val}` |")
        lines.append("")

    if not result.only_in_source and not result.only_in_target and not result.value_mismatches:
        lines.append("_No differences found._")

    return "\n".join(lines)


def render(
    result: EnvDiffResult,
    fmt: OutputFormat = OutputFormat.TEXT,
    source_label: str = "source",
    target_label: str = "target",
    stream: TextIO | None = None,
) -> str:
    """Render a diff result to a string and optionally write it to *stream*."""
    if stream is None:
        stream = sys.stdout

    renderers = {
        OutputFormat.TEXT: _render_text,
        OutputFormat.JSON: _render_json,
        OutputFormat.MARKDOWN: _render_markdown,
    }
    output = renderers[fmt](result, source_label, target_label)
    print(output, file=stream)
    return output
