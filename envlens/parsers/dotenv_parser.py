"""Parser for .env files into a normalized key-value dictionary."""

import re
from pathlib import Path
from typing import Dict, Optional


class DotEnvParseError(Exception):
    """Raised when a .env file cannot be parsed."""
    pass


_LINE_RE = re.compile(
    r"^\s*(?:export\s+)?"
    r"([A-Za-z_][A-Za-z0-9_]*)"
    r"\s*=\s*"
    r"(.*?)\s*$"
)

_QUOTED_RE = re.compile(r'^([\'"])(.*?)\1$', re.DOTALL)


def _strip_inline_comment(value: str) -> str:
    """Remove unquoted inline comments (# ...) from a value."""
    if value and value[0] not in ('"', "'"):
        idx = value.find(" #")
        if idx != -1:
            value = value[:idx].rstrip()
    return value


def _unescape_value(value: str) -> str:
    """Strip surrounding quotes and unescape basic escape sequences."""
    match = _QUOTED_RE.match(value)
    if match:
        quote_char, inner = match.group(1), match.group(2)
        if quote_char == '"':
            inner = inner.replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"')
        return inner
    return value


def parse_dotenv(source: str, filepath: Optional[str] = None) -> Dict[str, str]:
    """
    Parse the contents of a .env file and return a dict of env vars.

    Args:
        source:   Raw text content of the .env file.
        filepath: Optional path hint used in error messages.

    Returns:
        Dictionary mapping variable names to their string values.
    """
    env: Dict[str, str] = {}
    location = filepath or "<string>"

    for lineno, raw_line in enumerate(source.splitlines(), start=1):
        line = raw_line.strip()

        # Skip blanks and comments
        if not line or line.startswith("#"):
            continue

        match = _LINE_RE.match(line)
        if not match:
            raise DotEnvParseError(
                f"{location}:{lineno}: invalid syntax — {raw_line!r}"
            )

        key, value = match.group(1), match.group(2)
        value = _strip_inline_comment(value)
        value = _unescape_value(value)
        env[key] = value

    return env


def parse_dotenv_file(path: str | Path) -> Dict[str, str]:
    """
    Read a .env file from disk and parse it.

    Args:
        path: Filesystem path to the .env file.

    Returns:
        Dictionary mapping variable names to their string values.
    """
    path = Path(path)
    try:
        source = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise DotEnvParseError(f"Cannot read file {path}: {exc}") from exc
    return parse_dotenv(source, filepath=str(path))
