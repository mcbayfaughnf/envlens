"""Parser registry for envlens.

Exports a unified ``parse`` entry point that selects the correct parser
based on the file path or an explicit *format* hint.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from .dotenv_parser import parse_dotenv_file
from .docker_parser import parse_dockerfile_file
from .github_actions_parser import parse_github_actions_file
from .circleci_parser import parse_circleci_file
from .travis_parser import parse_travis_file

__all__ = [
    "parse_dotenv_file",
    "parse_dockerfile_file",
    "parse_github_actions_file",
    "parse_circleci_file",
    "parse_travis_file",
    "detect_format",
    "parse",
]

_EXTENSION_MAP: Dict[str, str] = {
    ".env": "dotenv",
    "dockerfile": "dockerfile",
    ".yml": "yaml",
    ".yaml": "yaml",
}

_NAME_MAP: Dict[str, str] = {
    "dockerfile": "dockerfile",
    ".travis.yml": "travis",
    ".travis.yaml": "travis",
    ".circleci/config.yml": "circleci",
    ".circleci/config.yaml": "circleci",
}


def detect_format(path: str) -> Optional[str]:
    """Infer the config format from the file path.

    Returns one of ``'dotenv'``, ``'dockerfile'``, ``'github_actions'``,
    ``'circleci'``, ``'travis'``, or ``None`` if unknown.
    """
    p = Path(path)
    name_lower = p.name.lower()

    # Exact name matches take priority
    if name_lower in _NAME_MAP:
        return _NAME_MAP[name_lower]

    # Check if any parent directory is .github/workflows
    parts_lower = [part.lower() for part in p.parts]
    if ".github" in parts_lower and "workflows" in parts_lower:
        return "github_actions"

    if ".circleci" in parts_lower:
        return "circleci"

    # Extension-based fallback
    suffix = p.suffix.lower()
    if suffix in _EXTENSION_MAP:
        return _EXTENSION_MAP[suffix]

    if name_lower.startswith(".env"):
        return "dotenv"

    return None


_PARSERS = {
    "dotenv": parse_dotenv_file,
    "dockerfile": parse_dockerfile_file,
    "github_actions": parse_github_actions_file,
    "circleci": parse_circleci_file,
    "travis": parse_travis_file,
}


def parse(path: str, fmt: Optional[str] = None) -> Dict[str, str]:
    """Parse *path* and return a flat ``{key: value}`` dict.

    Parameters
    ----------
    path:
        Path to the config file.
    fmt:
        Optional format override. When omitted, :func:`detect_format` is used.

    Raises
    ------
    ValueError
        If the format cannot be detected or is not supported.
    """
    resolved = fmt or detect_format(path)
    if resolved is None:
        raise ValueError(
            f"Cannot detect format for '{path}'. "
            "Pass fmt= explicitly (dotenv, dockerfile, github_actions, circleci, travis)."
        )
    if resolved not in _PARSERS:
        raise ValueError(f"Unsupported format '{resolved}'.")
    return _PARSERS[resolved](path)
