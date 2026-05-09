"""CLI sub-command: envlens lint <file>"""
from __future__ import annotations

import argparse
import json
import sys
from typing import List

from envlens.linter import LintIssue, LintResult, lint_env
from envlens.parsers import parse


def _dir_arg(raw: str) -> str:  # pragma: no cover
    return raw


def build_lint_parser(subparsers=None) -> argparse.ArgumentParser:
    description = "Lint an env file for common issues."
    if subparsers is not None:
        parser = subparsers.add_parser("lint", help=description)
    else:
        parser = argparse.ArgumentParser(prog="envlens lint", description=description)

    parser.add_argument("file", help="Path to the env file to lint.")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="output_format",
        help="Output format (default: text).",
    )
    parser.add_argument(
        "--allow-lowercase-keys",
        action="store_true",
        default=False,
        help="Suppress L001 warnings for lowercase keys.",
    )
    parser.add_argument(
        "--max-value-length",
        type=int,
        default=None,
        metavar="N",
        help="Warn when a value exceeds N characters (L004).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        default=False,
        help="Exit with code 2 if any warnings are present (in addition to errors).",
    )
    return parser


def _render_text(issues: List[LintIssue]) -> str:
    if not issues:
        return "No lint issues found."
    lines = []
    for issue in issues:
        lines.append(f"[{issue.severity.upper()}] {issue.code}: {issue.message}")
    return "\n".join(lines)


def _render_json(issues: List[LintIssue]) -> str:
    return json.dumps(
        [
            {
                "key": i.key,
                "code": i.code,
                "severity": i.severity,
                "message": i.message,
            }
            for i in issues
        ],
        indent=2,
    )


def run_lint_command(args: argparse.Namespace) -> int:
    """Execute the lint sub-command. Returns an exit code."""
    try:
        env = parse(args.file)
    except Exception as exc:  # noqa: BLE001
        print(f"Error reading '{args.file}': {exc}", file=sys.stderr)
        return 1

    result: LintResult = lint_env(
        env,
        allow_lowercase_keys=args.allow_lowercase_keys,
        max_value_length=args.max_value_length,
    )

    if args.output_format == "json":
        print(_render_json(result.issues))
    else:
        print(_render_text(result.issues))

    if result.has_errors:
        return 2
    if args.strict and result.has_warnings:
        return 2
    return 0
