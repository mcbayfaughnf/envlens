"""Parser for Travis CI .travis.yml environment variable blocks."""

from __future__ import annotations

from typing import Dict

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise ImportError("PyYAML is required for Travis CI parsing: pip install pyyaml") from exc


class TravisParseError(Exception):
    """Raised when a .travis.yml file cannot be parsed."""


def _collect_env_blocks(data: dict) -> Dict[str, str]:
    """Extract env vars from a parsed Travis CI config dict.

    Handles both top-level ``env.global`` (list of KEY=VALUE strings or
    dicts with ``secure`` keys) and job-matrix ``env`` entries.
    """
    result: Dict[str, str] = {}

    env_section = data.get("env")
    if not env_section:
        return result

    # env.global is the canonical place for shared env vars
    global_entries = []
    if isinstance(env_section, dict):
        global_entries = env_section.get("global", [])
    elif isinstance(env_section, list):
        global_entries = env_section

    for entry in global_entries:
        if isinstance(entry, str):
            # "KEY=VALUE" or "KEY=VALUE OTHER=VALUE2" on one line
            for token in entry.split():
                if "=" in token:
                    key, _, value = token.partition("=")
                    result[key.strip()] = value.strip()
        elif isinstance(entry, dict):
            # secure encrypted values — record key with placeholder
            for k, v in entry.items():
                if k != "secure":
                    result[k] = str(v)

    return result


def parse_travis(content: str) -> Dict[str, str]:
    """Parse a Travis CI YAML string and return a flat env var dict."""
    if not content or not content.strip():
        return {}
    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError as exc:
        raise TravisParseError(f"Invalid YAML: {exc}") from exc

    if not isinstance(data, dict):
        return {}

    return _collect_env_blocks(data)


def parse_travis_file(path: str) -> Dict[str, str]:
    """Read a .travis.yml file and return a flat env var dict."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return parse_travis(fh.read())
    except OSError as exc:
        raise TravisParseError(f"Cannot read file '{path}': {exc}") from exc
