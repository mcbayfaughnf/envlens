"""Minimal CLI entry-point for envlens.

Usage examples:
    envlens diff .env .env.production
    envlens diff --format json .env Dockerfile
    envlens diff --format markdown .env .github/workflows/ci.yml
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envlens.parsers import load_env_file
from envlens.diff import diff_envs
from envlens.reporter import OutputFormat, render


def _detect_and_parse(path: str) -> dict[str, str]:
    """Delegate to the appropriate parser based on file name heuristics."""
    p = Path(path)
    name = p.name.lower()

    if name == "dockerfile" or name.startswith("dockerfile."):
        from envlens.parsers.docker_parser import parse_dockerfile_file
        return parse_dockerfile_file(path)

    if name.endswith(".yml") or name.endswith(".yaml"):
        # Try GitHub Actions first, fall back to CircleCI
        text = p.read_text(encoding="utf-8")
        if "jobs:" in text and "steps:" in text:
            from envlens.parsers.github_actions_parser import parse_github_actions
            return parse_github_actions(text)
        from envlens.parsers.circleci_parser import parse_circleci
        return parse_circleci(text)

    # Default: treat as .env file
    from envlens.parsers.dotenv_parser import parse_dotenv_file
    return parse_dotenv_file(path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envlens",
        description="Diff environment variable sets across .env files, Dockerfiles, and CI configs.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    diff_cmd = sub.add_parser("diff", help="Compare two env sources.")
    diff_cmd.add_argument("source", help="Path to the source env file.")
    diff_cmd.add_argument("target", help="Path to the target env file.")
    diff_cmd.add_argument(
        "--format",
        dest="fmt",
        choices=[f.value for f in OutputFormat],
        default=OutputFormat.TEXT.value,
        help="Output format (default: text).",
    )
    diff_cmd.add_argument(
        "--ignore",
        metavar="KEY",
        nargs="*",
        default=[],
        help="Keys to exclude from the diff.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "diff":
        try:
            source_env = _detect_and_parse(args.source)
            target_env = _detect_and_parse(args.target)
        except Exception as exc:  # noqa: BLE001
            print(f"Error loading files: {exc}", file=sys.stderr)
            return 1

        result = diff_envs(source_env, target_env, ignore_keys=set(args.ignore))
        render(
            result,
            fmt=OutputFormat(args.fmt),
            source_label=args.source,
            target_label=args.target,
        )
        return 1 if result.only_in_source or result.only_in_target or result.value_mismatches else 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
