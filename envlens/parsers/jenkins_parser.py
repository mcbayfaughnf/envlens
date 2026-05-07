"""Parser for Jenkinsfile environment blocks."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict


class JenkinsParseError(ValueError):
    """Raised when a Jenkinsfile cannot be parsed."""


# Matches: environment { KEY = 'value' } or environment { KEY = "value" }
_ENV_BLOCK_RE = re.compile(r"environment\s*\{([^}]*)\}", re.DOTALL)
_KV_RE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*['\"]?(.*?)['\"]?\s*$")


def _collect_env_blocks(text: str) -> Dict[str, str]:
    """Extract all key=value pairs from every environment { } block.

    Later declarations win (last-value-wins semantics).
    """
    result: Dict[str, str] = {}
    for block_match in _ENV_BLOCK_RE.finditer(text):
        block_body = block_match.group(1)
        for line in block_body.splitlines():
            line = line.strip()
            if not line or line.startswith("//"):
                continue
            m = _KV_RE.match(line)
            if m:
                key, value = m.group(1), m.group(2)
                # Strip surrounding quotes that the loose regex may have kept
                for quote in ('"', "'"):
                    if value.startswith(quote) and value.endswith(quote) and len(value) >= 2:
                        value = value[1:-1]
                        break
                result[key] = value
    return result


def parse_jenkins(text: str) -> Dict[str, str]:
    """Parse a Jenkinsfile string and return a flat env-var mapping.

    Args:
        text: Raw Jenkinsfile content.

    Returns:
        Dict mapping variable names to their string values.

    Raises:
        JenkinsParseError: If *text* is not a string.
    """
    if not isinstance(text, str):
        raise JenkinsParseError(f"Expected str, got {type(text).__name__}")
    if not text.strip():
        return {}
    return _collect_env_blocks(text)


def parse_jenkins_file(path: str | Path) -> Dict[str, str]:
    """Read *path* and delegate to :func:`parse_jenkins`.

    Raises:
        JenkinsParseError: If the file cannot be read.
    """
    try:
        content = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        raise JenkinsParseError(f"Cannot read file {path!r}: {exc}") from exc
    return parse_jenkins(content)
