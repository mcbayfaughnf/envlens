"""
Parser registry — detect file format and dispatch to the correct parser.
"""

from pathlib import Path
from typing import Dict, Optional

from envlens.parsers.dotenv_parser import parse_dotenv_file
from envlens.parsers.docker_parser import parse_dockerfile_file
from envlens.parsers.github_actions_parser import parse_github_actions_file
from envlens.parsers.circleci_parser import parse_circleci_file
from envlens.parsers.travis_parser import parse_travis_file
from envlens.parsers.gitlab_ci_parser import parse_gitlab_ci_file
from envlens.parsers.bitbucket_parser import parse_bitbucket_pipelines_file
from envlens.parsers.jenkins_parser import parse_jenkins_file
from envlens.parsers.azure_pipelines_parser import parse_azure_pipelines_file
from envlens.parsers.env_substitution import resolve_substitutions

__all__ = ["detect_format", "parse"]

# Maps a canonical format name to its file parser.
_PARSERS = {
    "dotenv": parse_dotenv_file,
    "dockerfile": parse_dockerfile_file,
    "github-actions": parse_github_actions_file,
    "circleci": parse_circleci_file,
    "travis": parse_travis_file,
    "gitlab-ci": parse_gitlab_ci_file,
    "bitbucket-pipelines": parse_bitbucket_pipelines_file,
    "jenkins": parse_jenkins_file,
    "azure-pipelines": parse_azure_pipelines_file,
}

# Heuristic rules: (stem_pattern, suffix) → format
_DETECT_RULES = [
    ("Dockerfile", "", "dockerfile"),
    ("Dockerfile", ".dockerfile", "dockerfile"),
    (".travis", ".yml", "travis"),
    (".travis", ".yaml", "travis"),
    (".circleci/config", ".yml", "circleci"),
    (".circleci/config", ".yaml", "circleci"),
    (".gitlab-ci", ".yml", "gitlab-ci"),
    (".gitlab-ci", ".yaml", "gitlab-ci"),
    ("bitbucket-pipelines", ".yml", "bitbucket-pipelines"),
    ("bitbucket-pipelines", ".yaml", "bitbucket-pipelines"),
    ("Jenkinsfile", "", "jenkins"),
    ("azure-pipelines", ".yml", "azure-pipelines"),
    ("azure-pipelines", ".yaml", "azure-pipelines"),
]


def detect_format(path: str) -> Optional[str]:
    """Return the canonical format name for *path*, or *None* if unknown."""
    p = Path(path)
    name = p.name
    suffix = p.suffix
    stem = p.stem

    for pattern, ext, fmt in _DETECT_RULES:
        if pattern in name and (ext == "" or suffix == ext):
            return fmt

    # GitHub Actions: .github/workflows/*.yml
    parts = p.parts
    if ".github" in parts and "workflows" in parts and suffix in (".yml", ".yaml"):
        return "github-actions"

    # .env files: .env, .env.*, *.env
    if name == ".env" or name.startswith(".env.") or suffix == ".env":
        return "dotenv"

    return None


def parse(
    path: str,
    fmt: Optional[str] = None,
    resolve: bool = False,
    fallback: Optional[Dict[str, str]] = None,
    strict: bool = False,
) -> Dict[str, str]:
    """Parse *path* and return an environment map.

    Parameters
    ----------
    path:
        Path to the file to parse.
    fmt:
        Force a specific format instead of auto-detecting.
    resolve:
        When *True*, expand variable references in values via
        :func:`~envlens.parsers.env_substitution.resolve_substitutions`.
    fallback:
        Passed through to :func:`resolve_substitutions` when *resolve* is
        *True*.
    strict:
        Passed through to :func:`resolve_substitutions`.
    """
    format_name = fmt or detect_format(path)
    if format_name is None:
        raise ValueError(
            f"Cannot detect format for '{path}'. "
            "Pass fmt= to specify it explicitly."
        )
    if format_name not in _PARSERS:
        raise ValueError(
            f"Unknown format '{format_name}'. "
            f"Supported: {', '.join(sorted(_PARSERS))}"
        )
    env = _PARSERS[format_name](path)
    if resolve:
        env = resolve_substitutions(env, fallback=fallback, strict=strict)
    return env
