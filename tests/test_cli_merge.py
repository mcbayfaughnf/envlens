"""Tests for envlens.cli_merge."""

import argparse
import json
from io import StringIO
from unittest.mock import patch

import pytest

from envlens.cli_merge import build_merge_parser, run_merge_command


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_args(**kwargs) -> argparse.Namespace:
    defaults = {
        "sources": [],
        "strategy": "last",
        "ignore": [],
        "output_format": "dotenv",
        "show_conflicts": False,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


_ENV_A = {"APP_ENV": "production", "DB_HOST": "db.prod"}
_ENV_B = {"APP_ENV": "staging", "REDIS_URL": "redis://localhost"}


# ---------------------------------------------------------------------------
# Parser construction
# ---------------------------------------------------------------------------

def test_build_merge_parser_returns_parser():
    p = build_merge_parser()
    assert isinstance(p, argparse.ArgumentParser)


def test_parser_defaults():
    p = build_merge_parser()
    ns = p.parse_args(["a.env", "b.env"])
    assert ns.strategy == "last"
    assert ns.output_format == "dotenv"
    assert ns.show_conflicts is False


# ---------------------------------------------------------------------------
# run_merge_command — dotenv output
# ---------------------------------------------------------------------------

def test_dotenv_output_last_strategy(capsys):
    args = _make_args(sources=["a.env", "b.env"], strategy="last")
    with patch("envlens.cli_merge.detect_format", return_value="dotenv"), \
         patch("envlens.cli_merge.parse", side_effect=[_ENV_A, _ENV_B]):
        code = run_merge_command(args)
    assert code == 0
    out = capsys.readouterr().out
    assert "APP_ENV=staging" in out          # LAST wins
    assert "DB_HOST=db.prod" in out
    assert "REDIS_URL=redis://localhost" in out


def test_dotenv_output_first_strategy(capsys):
    args = _make_args(sources=["a.env", "b.env"], strategy="first")
    with patch("envlens.cli_merge.detect_format", return_value="dotenv"), \
         patch("envlens.cli_merge.parse", side_effect=[_ENV_A, _ENV_B]):
        run_merge_command(args)
    out = capsys.readouterr().out
    assert "APP_ENV=production" in out        # FIRST wins


# ---------------------------------------------------------------------------
# run_merge_command — JSON output
# ---------------------------------------------------------------------------

def test_json_output_is_valid_json(capsys):
    args = _make_args(sources=["a.env", "b.env"], output_format="json")
    with patch("envlens.cli_merge.detect_format", return_value="dotenv"), \
         patch("envlens.cli_merge.parse", side_effect=[_ENV_A, _ENV_B]):
        code = run_merge_command(args)
    assert code == 0
    data = json.loads(capsys.readouterr().out)
    assert isinstance(data, dict)
    assert "APP_ENV" in data


# ---------------------------------------------------------------------------
# Error / conflict paths
# ---------------------------------------------------------------------------

def test_error_strategy_returns_exit_2(capsys):
    args = _make_args(sources=["a.env", "b.env"], strategy="error")
    with patch("envlens.cli_merge.detect_format", return_value="dotenv"), \
         patch("envlens.cli_merge.parse", side_effect=[_ENV_A, _ENV_B]):
        code = run_merge_command(args)
    assert code == 2


def test_unreadable_source_returns_exit_1(capsys):
    args = _make_args(sources=["missing.env"])
    with patch("envlens.cli_merge.detect_format", side_effect=FileNotFoundError("gone")):
        code = run_merge_command(args)
    assert code == 1


def test_show_conflicts_writes_to_stderr(capsys):
    args = _make_args(sources=["a.env", "b.env"], show_conflicts=True)
    with patch("envlens.cli_merge.detect_format", return_value="dotenv"), \
         patch("envlens.cli_merge.parse", side_effect=[_ENV_A, _ENV_B]):
        run_merge_command(args)
    err = capsys.readouterr().err
    assert "APP_ENV" in err
