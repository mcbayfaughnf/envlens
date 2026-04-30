"""Tests for the envlens.parsers registry (detect_format + parse)."""

import pytest

from envlens.parsers import detect_format, parse


# ---------------------------------------------------------------------------
# detect_format
# ---------------------------------------------------------------------------


def test_detect_dotenv():
    assert detect_format(".env") == "dotenv"


def test_detect_dotenv_suffixed():
    assert detect_format(".env.production") == "dotenv"


def test_detect_dockerfile():
    assert detect_format("Dockerfile") == "dockerfile"


def test_detect_travis():
    assert detect_format(".travis.yml") == "travis"


def test_detect_circleci():
    assert detect_format(".circleci/config.yml") == "circleci"


def test_detect_github_actions():
    assert detect_format(".github/workflows/ci.yml") == "github_actions"


def test_detect_unknown_returns_none():
    assert detect_format("random.txt") is None


# ---------------------------------------------------------------------------
# parse — happy paths via tmp files
# ---------------------------------------------------------------------------


def test_parse_dotenv(tmp_path):
    f = tmp_path / ".env"
    f.write_text("KEY=value\n")
    result = parse(str(f))
    assert result == {"KEY": "value"}


def test_parse_dockerfile(tmp_path):
    f = tmp_path / "Dockerfile"
    f.write_text("FROM python:3.11\nENV APP_ENV=production\n")
    result = parse(str(f))
    assert result == {"APP_ENV": "production"}


def test_parse_travis(tmp_path):
    f = tmp_path / ".travis.yml"
    f.write_text("env:\n  global:\n    - CI=true\n")
    result = parse(str(f))
    assert result == {"CI": "true"}


def test_parse_with_explicit_fmt(tmp_path):
    f = tmp_path / "weird_name.cfg"
    f.write_text("HELLO=world\n")
    result = parse(str(f), fmt="dotenv")
    assert result == {"HELLO": "world"}


def test_parse_unknown_raises_without_fmt(tmp_path):
    f = tmp_path / "unknown.cfg"
    f.write_text("X=1\n")
    with pytest.raises(ValueError, match="Cannot detect format"):
        parse(str(f))


def test_parse_unsupported_fmt_raises(tmp_path):
    f = tmp_path / ".env"
    f.write_text("X=1\n")
    with pytest.raises(ValueError, match="Unsupported format"):
        parse(str(f), fmt="toml")
