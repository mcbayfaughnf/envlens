"""Integration tests: lint real .env content via the dotenv parser."""
from __future__ import annotations

import textwrap

import pytest

from envlens.linter import lint_env
from envlens.parsers.dotenv_parser import parse_dotenv


def _parse(raw: str):
    return parse_dotenv(textwrap.dedent(raw))


def test_clean_dotenv_produces_no_issues():
    env = _parse("""
        PORT=8080
        DEBUG=false
        APP_NAME=envlens
    """)
    result = lint_env(env)
    assert not result.issues


def test_lowercase_key_from_dotenv_triggers_l001():
    env = _parse("db_host=localhost")
    result = lint_env(env)
    codes = [i.code for i in result.issues]
    assert "L001" in codes


def test_empty_secret_from_dotenv_triggers_l002():
    env = _parse("DB_PASSWORD=")
    result = lint_env(env)
    codes = [i.code for i in result.issues]
    assert "L002" in codes


def test_placeholder_value_from_dotenv_triggers_l003():
    env = _parse("REDIS_URL=changeme")
    result = lint_env(env)
    codes = [i.code for i in result.issues]
    assert "L003" in codes


def test_multiple_issues_all_reported():
    env = _parse("""
        api_token=
        REDIS_URL=todo
    """)
    result = lint_env(env)
    codes = [i.code for i in result.issues]
    # api_token: L001 (lowercase) + L002 (empty sensitive)
    assert codes.count("L001") >= 1
    assert "L002" in codes
    # REDIS_URL: L003 (placeholder)
    assert "L003" in codes


def test_max_value_length_integration():
    env = _parse(f"LONG_VAL={'a' * 500}")
    result = lint_env(env, max_value_length=256)
    codes = [i.code for i in result.issues]
    assert "L004" in codes


def test_has_errors_reflects_l002():
    env = _parse("SECRET_KEY=")
    result = lint_env(env)
    assert result.has_errors


def test_errors_and_warnings_helpers():
    env = _parse("""
        bad_key=hello
        API_PASSWORD=
    """)
    result = lint_env(env)
    assert result.has_errors
    assert result.has_warnings
    assert any(i.code == "L002" for i in result.errors())
    assert any(i.code == "L001" for i in result.warnings())
