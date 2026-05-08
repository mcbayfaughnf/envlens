"""Tests for envlens.cli_redact."""

from __future__ import annotations

import argparse
import json
from unittest.mock import patch

import pytest

from envlens.cli_redact import build_redact_parser, run_redact_command
from envlens.redactor import REDACTED_PLACEHOLDER


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_args(**kwargs) -> argparse.Namespace:
    defaults = dict(
        file="dummy.env",
        format=None,
        extra_keys=[],
        allow_keys=[],
        placeholder=REDACTED_PLACEHOLDER,
        output="dotenv",
    )
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


_SAMPLE_ENV = {
    "HOST": "localhost",
    "DB_PASSWORD": "s3cr3t",
    "PORT": "5432",
}


# ---------------------------------------------------------------------------
# build_redact_parser
# ---------------------------------------------------------------------------

def test_build_redact_parser_returns_parser():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers()
    p = build_redact_parser(sub)
    assert p is not None


# ---------------------------------------------------------------------------
# run_redact_command — dotenv output
# ---------------------------------------------------------------------------

def test_dotenv_output_sensitive_redacted(capsys):
    args = _make_args()
    with patch("envlens.cli_redact.parse", return_value=_SAMPLE_ENV):
        rc = run_redact_command(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert REDACTED_PLACEHOLDER in out
    assert "s3cr3t" not in out
    assert "localhost" in out


def test_dotenv_output_plain_keys_visible(capsys):
    args = _make_args()
    with patch("envlens.cli_redact.parse", return_value=_SAMPLE_ENV):
        run_redact_command(args)
    out = capsys.readouterr().out
    assert "HOST=localhost" in out


# ---------------------------------------------------------------------------
# run_redact_command — json output
# ---------------------------------------------------------------------------

def test_json_output_is_valid_json(capsys):
    args = _make_args(output="json")
    with patch("envlens.cli_redact.parse", return_value=_SAMPLE_ENV):
        rc = run_redact_command(args)
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert isinstance(data, dict)
    assert data["DB_PASSWORD"] == REDACTED_PLACEHOLDER


# ---------------------------------------------------------------------------
# run_redact_command — extra / allow keys
# ---------------------------------------------------------------------------

def test_extra_key_redacted(capsys):
    args = _make_args(extra_keys=["HOST"])
    with patch("envlens.cli_redact.parse", return_value=_SAMPLE_ENV):
        run_redact_command(args)
    out = capsys.readouterr().out
    assert "HOST=" + REDACTED_PLACEHOLDER in out


def test_allow_key_not_redacted(capsys):
    args = _make_args(allow_keys=["DB_PASSWORD"])
    with patch("envlens.cli_redact.parse", return_value=_SAMPLE_ENV):
        run_redact_command(args)
    out = capsys.readouterr().out
    assert "s3cr3t" in out


# ---------------------------------------------------------------------------
# run_redact_command — parse error
# ---------------------------------------------------------------------------

def test_parse_error_returns_nonzero(capsys):
    args = _make_args()
    with patch("envlens.cli_redact.parse", side_effect=ValueError("bad file")):
        rc = run_redact_command(args)
    assert rc == 1
    assert "bad file" in capsys.readouterr().err
