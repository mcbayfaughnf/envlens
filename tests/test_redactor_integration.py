"""Integration tests: redactor working with real parsed env data."""

from __future__ import annotations

import textwrap

from envlens.parsers.dotenv_parser import parse_dotenv
from envlens.redactor import REDACTED_PLACEHOLDER, RedactOptions, redact_env


_DOTENV_CONTENT = textwrap.dedent("""\
    HOST=db.example.com
    PORT=5432
    DB_PASSWORD=supersecret
    API_KEY=abc123
    APP_NAME=myapp
    SECRET_SAUCE=spicy
""")


def _parsed() -> dict:
    return parse_dotenv(_DOTENV_CONTENT)


def test_plain_values_survive_round_trip():
    env = _parsed()
    result = redact_env(env)
    assert result["HOST"] == "db.example.com"
    assert result["PORT"] == "5432"
    assert result["APP_NAME"] == "myapp"


def test_sensitive_values_redacted():
    env = _parsed()
    result = redact_env(env)
    assert result["DB_PASSWORD"] == REDACTED_PLACEHOLDER
    assert result["API_KEY"] == REDACTED_PLACEHOLDER
    assert result["SECRET_SAUCE"] == REDACTED_PLACEHOLDER


def test_custom_placeholder_applied():
    env = _parsed()
    opts = RedactOptions(placeholder="[HIDDEN]")
    result = redact_env(env, opts)
    assert result["DB_PASSWORD"] == "[HIDDEN]"


def test_allow_list_exposes_sensitive_value():
    env = _parsed()
    opts = RedactOptions(allow_keys=frozenset({"API_KEY"}))
    result = redact_env(env, opts)
    assert result["API_KEY"] == "abc123"
    # Others still redacted
    assert result["DB_PASSWORD"] == REDACTED_PLACEHOLDER


def test_extra_keys_redact_non_sensitive():
    env = _parsed()
    opts = RedactOptions(extra_keys=frozenset({"HOST", "PORT"}))
    result = redact_env(env, opts)
    assert result["HOST"] == REDACTED_PLACEHOLDER
    assert result["PORT"] == REDACTED_PLACEHOLDER
    assert result["APP_NAME"] == "myapp"


def test_all_keys_present_in_output():
    env = _parsed()
    result = redact_env(env)
    assert set(result.keys()) == set(env.keys())
