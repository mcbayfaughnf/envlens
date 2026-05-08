"""Tests for envlens.redactor."""

from __future__ import annotations

import pytest

from envlens.redactor import (
    REDACTED_PLACEHOLDER,
    RedactOptions,
    redact_diff_values,
    redact_env,
)


# ---------------------------------------------------------------------------
# redact_env
# ---------------------------------------------------------------------------

def test_plain_keys_unchanged():
    env = {"HOST": "localhost", "PORT": "5432"}
    assert redact_env(env) == env


def test_password_key_redacted():
    env = {"DB_PASSWORD": "s3cr3t", "HOST": "localhost"}
    result = redact_env(env)
    assert result["DB_PASSWORD"] == REDACTED_PLACEHOLDER
    assert result["HOST"] == "localhost"


def test_secret_key_redacted():
    env = {"APP_SECRET": "abc123"}
    result = redact_env(env)
    assert result["APP_SECRET"] == REDACTED_PLACEHOLDER


def test_token_key_redacted():
    env = {"GITHUB_TOKEN": "ghp_xyz"}
    result = redact_env(env)
    assert result["GITHUB_TOKEN"] == REDACTED_PLACEHOLDER


def test_custom_placeholder():
    opts = RedactOptions(placeholder="<hidden>")
    env = {"API_KEY": "key123"}
    result = redact_env(env, opts)
    assert result["API_KEY"] == "<hidden>"


def test_extra_keys_always_redacted():
    opts = RedactOptions(extra_keys=frozenset({"MY_CUSTOM_KEY"}))
    env = {"MY_CUSTOM_KEY": "value"}
    result = redact_env(env, opts)
    assert result["MY_CUSTOM_KEY"] == REDACTED_PLACEHOLDER


def test_allow_keys_not_redacted():
    opts = RedactOptions(allow_keys=frozenset({"DB_PASSWORD"}))
    env = {"DB_PASSWORD": "plaintext"}
    result = redact_env(env, opts)
    assert result["DB_PASSWORD"] == "plaintext"


def test_allow_key_beats_extra_key():
    opts = RedactOptions(
        extra_keys=frozenset({"OVERLAP"}),
        allow_keys=frozenset({"OVERLAP"}),
    )
    env = {"OVERLAP": "visible"}
    result = redact_env(env, opts)
    assert result["OVERLAP"] == "visible"


def test_empty_env_returns_empty():
    assert redact_env({}) == {}


def test_original_env_not_mutated():
    env = {"DB_PASSWORD": "secret"}
    original = dict(env)
    redact_env(env)
    assert env == original


# ---------------------------------------------------------------------------
# redact_diff_values
# ---------------------------------------------------------------------------

def test_diff_plain_values_unchanged():
    src = {"HOST": "a"}
    tgt = {"HOST": "b"}
    mis = {"PORT": ("5432", "5433")}
    r_src, r_tgt, r_mis = redact_diff_values(src, tgt, mis)
    assert r_src == src
    assert r_tgt == tgt
    assert r_mis == mis


def test_diff_sensitive_mismatch_redacted():
    mis = {"DB_PASSWORD": ("old", "new")}
    _, _, r_mis = redact_diff_values({}, {}, mis)
    assert r_mis["DB_PASSWORD"] == (REDACTED_PLACEHOLDER, REDACTED_PLACEHOLDER)


def test_diff_allow_key_shows_mismatch():
    opts = RedactOptions(allow_keys=frozenset({"DB_PASSWORD"}))
    mis = {"DB_PASSWORD": ("old", "new")}
    _, _, r_mis = redact_diff_values({}, {}, mis, opts)
    assert r_mis["DB_PASSWORD"] == ("old", "new")
