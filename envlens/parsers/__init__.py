"""Parser registry — detect format and dispatch to the right parser."""

from __future__ import annotations

import os
from typing import Dict

from envlens.parsers.dotenv_parser import parse_dotenv_file
from envlens.parsers.docker_parser import parse_dockerfile_file
from envlens.parsers.github_actions_parser import parse_github_actions_file
from envlens.parsers.circleci_parser import parse_circleci_file
from envlens.parsers.travis_parser import parse_travis_file
from envlens.parsers.gitlab_ci_parser import parse_gitlab_ci_file
from envlens.parsers.bitbucket_parser import parse_bitbucket_pipelines_file
from envlens.parsers.jenkins_parser import parse_jenkins_file
from envlens.parsers.azure_pipelines_parser import parse_azure_pipelines_file

# ---------------------------------------------------------------------------
# Format detection
# ---------------------------------------------------------------------------

_BASENAME_MAP: Dict[str, str] = {
    "dockerfile": "dockerfile",
    ".travis.yml": "travis",
    ".circleci/config.yml": "circleci",
    ".gitlab-ci.yml": "gitlab_ci",
    "bitbucket-pipelines.yml": "bitbucket",
    "jenkinsfile": "jenkins",
    "azure-pipelines.yml": "azure_pipelines",
}

_SUFFIX_MAP: Dict[str, str] = {
    ".env": "dotenv",
}

# Subpath fragments that identify CI configs by directory/filename patterns
_SUBPATH_FRAGMENTS: Dict[str, str] = {
    ".github/workflows": "github_actions",
    ".circleci/config": "circleci",
}


def detect_format(path: str) -> str:
    """Return a format identifier string for *path*.

    Raises :class:`ValueError` if the format cannot be determined.
    """
    normalised = path.replace("\\", "/").lower()
    basename = os.path.basename(normalised)

    # Exact basename matches
    if basename in _BASENAME_MAP:
        return _BASENAME_MAP[basename]

    # Suffix matches (.env, .env.local, etc.)
    for suffix, fmt in _SUFFIX_MAP.items():
        if basename == suffix or basename.endswith(suffix):
            return fmt

    # Subpath fragment matches
    for fragment, fmt in _SUBPATH_FRAGMENTS.items():
        if fragment in normalised:
            return fmt

    # GitHub Actions — any .yml/.yaml under .github/workflows
    if ".github/workflows" in normalised and normalised.endswith((".yml", ".yaml")):
        return "github_actions"

    # GitLab CI variants
    if basename == ".gitlab-ci.yml":
        return "gitlab_ci"

    # Azure Pipelines common alternative names
    if basename in ("azure-pipelines.yaml", "azure_pipelines.yml", "azure_pipelines.yaml"):
        return "azure_pipelines"

    raise ValueError(
        f"Cannot detect environment format for path: {path!r}. "
        "Use --format to specify it explicitly."
    )


# ---------------------------------------------------------------------------
# Unified parse entry-point
# ---------------------------------------------------------------------------

_PARSERS = {
    "dotenv": parse_dotenv_file,
    "dockerfile": parse_dockerfile_file,
    "github_actions": parse_github_actions_file,
    "circleci": parse_circleci_file,
    "travis": parse_travis_file,
    "gitlab_ci": parse_gitlab_ci_file,
    "bitbucket": parse_bitbucket_pipelines_file,
    "jenkins": parse_jenkins_file,
    "azure_pipelines": parse_azure_pipelines_file,
}


def parse(path: str, fmt: str | None = None) -> Dict[str, str]:
    """Parse *path* and return a ``{key: value}`` mapping.

    If *fmt* is ``None``, the format is auto-detected via :func:`detect_format`.
    """
    resolved_fmt = fmt or detect_format(path)
    if resolved_fmt not in _PARSERS:
        raise ValueError(
            f"Unsupported format {resolved_fmt!r}. "
            f"Valid options: {sorted(_PARSERS)}"
        )
    return _PARSERS[resolved_fmt](path)
