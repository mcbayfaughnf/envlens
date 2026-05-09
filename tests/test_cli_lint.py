"""Tests for envlens.cli_lint."""
from __future__ import annotations

import json
import types
from unittest.mock import patch

import pytest

from envlens.cli_lint import build_lint_parser, run_lint_command


def _make_args(**kwargs) -> types.SimpleNamespace:
    defaults = {
        "file": "dummy.env",
        "output_format": "text",
        "allow_lowercase_keys": False,
        "max_value_length": None,
        "strict": False,
    }
    defaults.update(kwargs)
    return types.SimpleNamespace(**defaults)


# ---------------------------------------------------------------------------
# Parser construction
# ---------------------------------------------------------------------------

def test_build_lint_parser_returns_parser():
    parser = build_lint_parser()
    assert parser is not None


def test_parser_defaults():
    parser = build_lint_parser()
    args = parser.parse_args(["myfile.env"])
    assert args.output_format == "text"
    assert args.allow_lowercase_keys is False
    assert args.max_value_length is None
    assert args.strict is False


# ---------------------------------------------------------------------------
# run_lint_command – text output
# ---------------------------------------------------------------------------

def test_clean_env_exits_zero(capsys):
    with patch("envlens.cli_lint.parse", return_value={"PORT": "8080"}):
        code = run_lint_command(_make_args())
    assert code == 0
    out = capsys.readouterr().out
    assert "No lint issues found" in out


def test_error_exits_two(capsys):
    with patch("envlens.cli_lint.parse", return_value={"API_KEY": ""}):
        code = run_lint_command(_make_args())
    assert code == 2
    out = capsys.readouterr().out
    assert "L002" in out
    assert "ERROR" in out


def test_warning_exits_zero_without_strict(capsys):
    with patch("envlens.cli_lint.parse", return_value={"bad_key": "hello"}):
        code = run_lint_command(_make_args(strict=False))
    assert code == 0


def test_warning_exits_two_with_strict(capsys):
    with patch("envlens.cli_lint.parse", return_value={"bad_key": "hello"}):
        code = run_lint_command(_make_args(strict=True))
    assert code == 2


# ---------------------------------------------------------------------------
# run_lint_command – json output
# ---------------------------------------------------------------------------

def test_json_output_is_valid_json(capsys):
    with patch("envlens.cli_lint.parse", return_value={"bad_key": "changeme"}):
        run_lint_command(_make_args(output_format="json"))
    out = capsys.readouterr().out
    data = json.loads(out)
    assert isinstance(data, list)
    codes = [item["code"] for item in data]
    assert "L001" in codes
    assert "L003" in codes


def test_json_clean_env_empty_list(capsys):
    with patch("envlens.cli_lint.parse", return_value={"PORT": "8080"}):
        run_lint_command(_make_args(output_format="json"))
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data == []


# ---------------------------------------------------------------------------
# run_lint_command – parse error
# ---------------------------------------------------------------------------

def test_parse_error_exits_one(capsys):
    with patch("envlens.cli_lint.parse", side_effect=ValueError("bad file")):
        code = run_lint_command(_make_args())
    assert code == 1
    err = capsys.readouterr().err
    assert "bad file" in err
