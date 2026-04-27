"""Parser for CircleCI config files (.circleci/config.yml)."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise ImportError("PyYAML is required for CircleCI parsing: pip install pyyaml") from exc


class CircleCIParseError(Exception):
    """Raised when a CircleCI config cannot be parsed."""


def _collect_env_blocks(data: object, results: Dict[str, str]) -> None:
    """Recursively walk the YAML structure and collect environment key/value pairs."""
    if isinstance(data, dict):
        if "environment" in data:
            env_block = data["environment"]
            if isinstance(env_block, dict):
                for key, value in env_block.items():
                    results[str(key)] = str(value) if value is not None else ""
        for value in data.values():
            _collect_env_blocks(value, results)
    elif isinstance(data, list):
        for item in data:
            _collect_env_blocks(item, results)


def parse_circleci(content: str) -> Dict[str, str]:
    """Parse a CircleCI config YAML string and return a dict of environment variables.

    Args:
        content: Raw YAML content of a CircleCI config file.

    Returns:
        A dict mapping environment variable names to their string values.

    Raises:
        CircleCIParseError: If the YAML cannot be loaded or has unexpected structure.
    """
    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError as exc:
        raise CircleCIParseError(f"Invalid YAML: {exc}") from exc

    if data is None:
        return {}

    if not isinstance(data, dict):
        raise CircleCIParseError("CircleCI config must be a YAML mapping at the top level.")

    env: Dict[str, str] = {}
    _collect_env_blocks(data, env)
    return env


def parse_circleci_file(path: str | Path) -> Dict[str, str]:
    """Parse a CircleCI config file from disk.

    Args:
        path: Path to the CircleCI config YAML file.

    Returns:
        A dict mapping environment variable names to their string values.

    Raises:
        CircleCIParseError: If the file cannot be read or parsed.
    """
    try:
        content = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        raise CircleCIParseError(f"Cannot read file '{path}': {exc}") from exc
    return parse_circleci(content)
