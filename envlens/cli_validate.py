"""CLI sub-command: validate an env file against a YAML schema."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

from envlens.parsers import parse
from envlens.validator import EnvSchema, ValidationError, validate


def _dir_arg(value: str) -> Path:
    p = Path(value)
    if not p.exists():
        raise argparse.ArgumentTypeError(f"Path does not exist: {value}")
    return p


def build_validate_parser(subparsers: "argparse._SubParsersAction") -> argparse.ArgumentParser:  # type: ignore[type-arg]
    parser = subparsers.add_parser(
        "validate",
        help="Validate an env file against a YAML schema of required/optional keys.",
    )
    parser.add_argument(
        "env_file",
        type=Path,
        help="Path to the env file to validate (dotenv, Dockerfile, CI config, …).",
    )
    parser.add_argument(
        "schema_file",
        type=Path,
        help="Path to a YAML schema file with 'required' and/or 'optional' key lists.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        default=False,
        help="Fail on keys not listed in the schema (unknown keys).",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="output_format",
        help="Output format (default: text).",
    )
    return parser


def run_validate_command(args: argparse.Namespace) -> int:
    """Execute the validate sub-command.  Returns an exit code."""
    # Load schema
    try:
        raw = yaml.safe_load(args.schema_file.read_text(encoding="utf-8")) or {}
        schema = EnvSchema.from_dict(raw)
    except (yaml.YAMLError, ValidationError) as exc:
        print(f"Schema error: {exc}", file=sys.stderr)
        return 2

    # Parse env file
    try:
        env = parse(str(args.env_file))
    except Exception as exc:  # noqa: BLE001
        print(f"Parse error: {exc}", file=sys.stderr)
        return 2

    result = validate(env, schema, allow_unknown=not args.strict)

    if args.output_format == "json":
        import json

        print(
            json.dumps(
                {
                    "valid": result.is_valid,
                    "missing_required": sorted(result.missing_required),
                    "unknown_keys": sorted(result.unknown_keys),
                },
                indent=2,
            )
        )
    else:
        print(result.summary())

    return 0 if result.is_valid else 1
