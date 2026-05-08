"""CLI sub-command: redact — print a redacted view of an env file."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

from envlens.parsers import parse
from envlens.redactor import RedactOptions, redact_env


def _dir_arg(value: str) -> str:  # pragma: no cover
    return value


def build_redact_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "redact",
        help="Print a redacted view of an env file, hiding sensitive values.",
    )
    p.add_argument("file", help="Path to the env file to redact.")
    p.add_argument(
        "--format",
        choices=["dotenv", "dockerfile", "github-actions", "gitlab-ci",
                 "circleci", "travis", "bitbucket", "jenkins", "azure-pipelines"],
        default=None,
        help="Force a specific parser (auto-detected by default).",
    )
    p.add_argument(
        "--extra-keys",
        metavar="KEY",
        nargs="+",
        default=[],
        help="Additional keys to always redact.",
    )
    p.add_argument(
        "--allow-keys",
        metavar="KEY",
        nargs="+",
        default=[],
        help="Keys to never redact even if they look sensitive.",
    )
    p.add_argument(
        "--placeholder",
        default="***REDACTED***",
        help="Replacement string for redacted values.",
    )
    p.add_argument(
        "--output",
        choices=["dotenv", "json"],
        default="dotenv",
        help="Output format (default: dotenv).",
    )
    return p


def _print_dotenv(redacted: dict) -> None:
    """Print redacted key/value pairs in dotenv format, quoting values that contain spaces."""
    for key, value in sorted(redacted.items()):
        # Quote the value if it contains whitespace so the output remains
        # parseable as a valid dotenv file.
        if any(c in value for c in (" ", "\t")):
            print(f'{key}="{value}"')
        else:
            print(f"{key}={value}")


def run_redact_command(args: argparse.Namespace) -> int:
    """Execute the redact sub-command.  Returns an exit code."""
    try:
        env = parse(args.file, fmt=args.format)
    except FileNotFoundError:
        print(f"error: file not found: {args.file}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 1

    opts = RedactOptions(
        placeholder=args.placeholder,
        extra_keys=frozenset(args.extra_keys),
        allow_keys=frozenset(args.allow_keys),
    )
    redacted = redact_env(env, opts)

    if args.output == "json":
        print(json.dumps(redacted, indent=2))
    else:
        _print_dotenv(redacted)

    return 0
