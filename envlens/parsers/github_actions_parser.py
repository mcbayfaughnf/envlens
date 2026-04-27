"""Parser for extracting environment variables from GitHub Actions workflow files."""

from __future__ import annotations

from pathlib import Path
from typing import Dict

try:
    import yaml
except ImportError as _exc:  # pragma: no cover
    raise ImportError("PyYAML is required for GitHub Actions parsing: pip install pyyaml") from _exc


class GitHubActionsParseError(Exception):
    """Raised when a workflow file cannot be parsed."""


def _collect_env_blocks(node: object, collected: Dict[str, str]) -> None:
    """Recursively walk a parsed YAML structure and collect 'env' mappings."""
    if isinstance(node, dict):
        if 'env' in node and isinstance(node['env'], dict):
            for key, value in node['env'].items():
                collected[str(key)] = str(value) if value is not None else ''
        for child in node.values():
            _collect_env_blocks(child, collected)
    elif isinstance(node, list):
        for item in node:
            _collect_env_blocks(item, collected)


def parse_github_actions(content: str) -> Dict[str, str]:
    """Parse environment variables from a GitHub Actions workflow YAML string.

    Collects all 'env' blocks at any nesting level (workflow, job, step).
    Later definitions override earlier ones (deepest scope wins if duplicate keys).

    Args:
        content: Raw YAML text of the workflow file.

    Returns:
        Mapping of environment variable names to their string values.

    Raises:
        GitHubActionsParseError: If YAML parsing fails.
    """
    if not isinstance(content, str):
        raise GitHubActionsParseError("Workflow content must be a string")
    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError as exc:
        raise GitHubActionsParseError(f"Invalid YAML: {exc}") from exc

    if data is None:
        return {}

    env_vars: Dict[str, str] = {}
    _collect_env_blocks(data, env_vars)
    return env_vars


def parse_github_actions_file(path: str | Path) -> Dict[str, str]:
    """Read a GitHub Actions workflow file from disk and parse its env vars."""
    path = Path(path)
    try:
        content = path.read_text(encoding='utf-8')
    except OSError as exc:
        raise GitHubActionsParseError(
            f"Cannot read workflow file at {path}: {exc}"
        ) from exc
    return parse_github_actions(content)
