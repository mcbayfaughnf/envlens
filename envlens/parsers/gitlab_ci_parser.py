"""Parser for GitLab CI (.gitlab-ci.yml) environment variable blocks."""

from __future__ import annotations

from typing import Dict

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore


class GitLabCIParseError(Exception):
    """Raised when a .gitlab-ci.yml file cannot be parsed."""


def _collect_env_blocks(data: dict) -> Dict[str, str]:
    """Walk a parsed GitLab CI structure and collect all *variables* blocks.

    Precedence (last write wins, mirrors runtime override order):
      1. Top-level ``variables``
      2. Per-job ``variables``
    """
    result: Dict[str, str] = {}

    # Top-level variables block
    top_vars = data.get("variables", {})
    if isinstance(top_vars, dict):
        for k, v in top_vars.items():
            result[str(k)] = str(v) if v is not None else ""

    # Job-level variables blocks (any mapping key that contains a 'variables' dict)
    for key, value in data.items():
        if key == "variables" or not isinstance(value, dict):
            continue
        job_vars = value.get("variables", {})
        if isinstance(job_vars, dict):
            for k, v in job_vars.items():
                result[str(k)] = str(v) if v is not None else ""

    return result


def parse_gitlab_ci(text: str) -> Dict[str, str]:
    """Parse *text* as a GitLab CI YAML document and return env vars.

    Parameters
    ----------
    text:
        Raw YAML content of a ``.gitlab-ci.yml`` file.

    Returns
    -------
    dict
        Mapping of variable name to value.
    """
    if yaml is None:  # pragma: no cover
        raise GitLabCIParseError("PyYAML is required to parse GitLab CI files.")

    if not text or not text.strip():
        return {}

    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise GitLabCIParseError(f"YAML parse error: {exc}") from exc

    if not isinstance(data, dict):
        return {}

    return _collect_env_blocks(data)


def parse_gitlab_ci_file(path: str) -> Dict[str, str]:
    """Read *path* and delegate to :func:`parse_gitlab_ci`."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return parse_gitlab_ci(fh.read())
    except OSError as exc:
        raise GitLabCIParseError(f"Cannot read file '{path}': {exc}") from exc
