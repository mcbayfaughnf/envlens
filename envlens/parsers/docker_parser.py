"""Parser for extracting environment variables from Dockerfiles."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Tuple


class DockerParseError(Exception):
    """Raised when a Dockerfile cannot be parsed."""


# Matches: ENV KEY=VALUE, ENV KEY VALUE (legacy), or multi-line ENV blocks
_ENV_SINGLE_RE = re.compile(
    r'^ENV\s+([A-Za-z_][A-Za-z0-9_]*)(?:=(.*)|(.*))$'
)
_ENV_KV_RE = re.compile(r'([A-Za-z_][A-Za-z0-9_]*)=([^\s]*)\s*')


def _strip_quotes(value: str) -> str:
    """Remove surrounding single or double quotes from a value."""
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
        return value[1:-1]
    return value


def _parse_env_line(line: str) -> List[Tuple[str, str]]:
    """Parse a single ENV instruction and return (key, value) pairs."""
    line = line.strip()
    if not line.upper().startswith('ENV '):
        return []

    rest = line[4:].strip()

    # Multi-value form: ENV KEY1=VAL1 KEY2=VAL2
    if '=' in rest:
        pairs = []
        for match in _ENV_KV_RE.finditer(rest):
            key = match.group(1)
            value = _strip_quotes(match.group(2))
            pairs.append((key, value))
        return pairs

    # Legacy single-value form: ENV KEY VALUE
    parts = rest.split(None, 1)
    if len(parts) == 2:
        return [(parts[0], _strip_quotes(parts[1]))]
    if len(parts) == 1:
        return [(parts[0], '')]
    return []


def parse_dockerfile(content: str) -> Dict[str, str]:
    """Parse ENV instructions from Dockerfile content.

    Args:
        content: Raw Dockerfile text.

    Returns:
        Mapping of environment variable names to their values.

    Raises:
        DockerParseError: If content is not a string.
    """
    if not isinstance(content, str):
        raise DockerParseError("Dockerfile content must be a string")

    env_vars: Dict[str, str] = {}
    # Join continuation lines (backslash at end)
    joined_lines: List[str] = []
    buffer = ''
    for raw_line in content.splitlines():
        stripped = raw_line.rstrip()
        if stripped.endswith('\\'):
            buffer += stripped[:-1] + ' '
        else:
            buffer += stripped
            joined_lines.append(buffer)
            buffer = ''
    if buffer:
        joined_lines.append(buffer)

    for line in joined_lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        pairs = _parse_env_line(line)
        for key, value in pairs:
            env_vars[key] = value

    return env_vars


def parse_dockerfile_file(path: str | Path) -> Dict[str, str]:
    """Read a Dockerfile from disk and parse its ENV instructions."""
    path = Path(path)
    try:
        content = path.read_text(encoding='utf-8')
    except OSError as exc:
        raise DockerParseError(f"Cannot read Dockerfile at {path}: {exc}") from exc
    return parse_dockerfile(content)
