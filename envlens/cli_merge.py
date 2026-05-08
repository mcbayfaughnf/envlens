"""CLI sub-command: merge two or more env sources into one."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

from envlens.merger import MergeConflictError, MergeStrategy, merge_envs
from envlens.parsers import detect_format, parse


def _dir_arg(raw: str) -> str:  # pragma: no cover
    return raw


def build_merge_parser(parent: Optional[argparse.ArgumentParser] = None) -> argparse.ArgumentParser:
    p = parent or argparse.ArgumentParser(
        prog="envlens merge",
        description="Merge multiple env sources into a single env dict.",
    )
    p.add_argument(
        "sources",
        nargs="+",
        metavar="SOURCE",
        help="Paths to .env / Dockerfile / CI config files (at least two).",
    )
    p.add_argument(
        "--strategy",
        choices=[s.value for s in MergeStrategy],
        default=MergeStrategy.LAST.value,
        help="Conflict resolution strategy (default: last).",
    )
    p.add_argument(
        "--ignore",
        metavar="KEY",
        nargs="*",
        default=[],
        help="Keys to exclude from the merge.",
    )
    p.add_argument(
        "--format",
        choices=["dotenv", "json"],
        default="dotenv",
        dest="output_format",
        help="Output format (default: dotenv).",
    )
    p.add_argument(
        "--show-conflicts",
        action="store_true",
        help="Print a conflict summary to stderr.",
    )
    return p


def run_merge_command(args: argparse.Namespace) -> int:
    """Execute the merge sub-command.  Returns an exit code."""
    envs = []
    for path in args.sources:
        try:
            fmt = detect_format(path)
            envs.append(parse(path, fmt))
        except Exception as exc:  # noqa: BLE001
            print(f"envlens merge: error reading {path!r}: {exc}", file=sys.stderr)
            return 1

    strategy = MergeStrategy(args.strategy)

    try:
        result = merge_envs(envs, strategy=strategy, ignore_keys=args.ignore or [])
    except MergeConflictError as exc:
        print(f"envlens merge: conflict error: {exc}", file=sys.stderr)
        return 2

    if args.show_conflicts and result.has_conflicts:
        print(result.conflict_summary(), file=sys.stderr)

    if args.output_format == "json":
        print(json.dumps(result.merged, indent=2))
    else:
        for key, value in sorted(result.merged.items()):
            print(f"{key}={value}")

    return 0
