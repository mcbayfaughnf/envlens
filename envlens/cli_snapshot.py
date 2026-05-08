"""CLI sub-commands for snapshot management (save / load / list / delete)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envlens.diff import diff_envs
from envlens.parsers import parse
from envlens.reporter import OutputFormat, render
from envlens.snapshot import SnapshotError, delete_snapshot, list_snapshots, load_snapshot, save_snapshot

DEFAULT_DIR = Path(".envlens_snapshots")


def _dir_arg(value: str) -> Path:
    return Path(value)


def build_snapshot_parser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Register 'snapshot' sub-commands onto an existing subparsers group."""
    snap = subparsers.add_parser("snapshot", help="Manage env snapshots")
    snap_sub = snap.add_subparsers(dest="snap_cmd", required=True)

    # save
    p_save = snap_sub.add_parser("save", help="Save current env as a snapshot")
    p_save.add_argument("name", help="Snapshot name")
    p_save.add_argument("source", help="Env file or config path to snapshot")
    p_save.add_argument("--dir", type=_dir_arg, default=DEFAULT_DIR, dest="directory")

    # load / diff
    p_diff = snap_sub.add_parser("diff", help="Diff a snapshot against a live file")
    p_diff.add_argument("name", help="Snapshot name to use as source")
    p_diff.add_argument("target", help="Live env file or config path")
    p_diff.add_argument("--dir", type=_dir_arg, default=DEFAULT_DIR, dest="directory")
    p_diff.add_argument("--format", choices=[f.value for f in OutputFormat], default="text", dest="fmt")

    # list
    p_list = snap_sub.add_parser("list", help="List available snapshots")
    p_list.add_argument("--dir", type=_dir_arg, default=DEFAULT_DIR, dest="directory")

    # delete
    p_del = snap_sub.add_parser("delete", help="Delete a snapshot")
    p_del.add_argument("name", help="Snapshot name")
    p_del.add_argument("--dir", type=_dir_arg, default=DEFAULT_DIR, dest="directory")


def run_snapshot_command(args: argparse.Namespace) -> int:
    """Dispatch snapshot sub-command; returns exit code."""
    try:
        if args.snap_cmd == "save":
            env = parse(args.source)
            path = save_snapshot(args.name, env, directory=args.directory)
            print(f"Snapshot '{args.name}' saved to {path}")

        elif args.snap_cmd == "diff":
            source_env = load_snapshot(args.name, directory=args.directory)
            target_env = parse(args.target)
            result = diff_envs(source_env, target_env)
            fmt = OutputFormat(args.fmt)
            print(render(result, fmt, source_label=f"snapshot:{args.name}", target_label=args.target))
            return 1 if result.has_differences() else 0

        elif args.snap_cmd == "list":
            names = list_snapshots(args.directory)
            if names:
                print("\n".join(names))
            else:
                print("No snapshots found.")

        elif args.snap_cmd == "delete":
            delete_snapshot(args.name, directory=args.directory)
            print(f"Snapshot '{args.name}' deleted.")

    except SnapshotError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001
        print(f"Unexpected error: {exc}", file=sys.stderr)
        return 3

    return 0
