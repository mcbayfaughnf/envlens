"""Tests for envlens.normalizer."""

import pytest

from envlens.normalizer import (
    KeyCase,
    NormalizeOptions,
    normalize_env,
    normalize_keys,
    normalize_values,
)


# ---------------------------------------------------------------------------
# normalize_keys
# ---------------------------------------------------------------------------

def test_preserve_keys_unchanged():
    env = {"Foo": "bar", "BAZ": "qux"}
    assert normalize_keys(env, KeyCase.PRESERVE) == {"Foo": "bar", "BAZ": "qux"}


def test_upper_keys():
    env = {"foo": "1", "Bar": "2"}
    assert normalize_keys(env, KeyCase.UPPER) == {"FOO": "1", "BAR": "2"}


def test_lower_keys():
    env = {"FOO": "1", "Bar": "2"}
    assert normalize_keys(env, KeyCase.LOWER) == {"foo": "1", "bar": "2"}


def test_collision_last_value_wins():
    # "foo" and "FOO" both map to "FOO" under UPPER — last wins
    env = {"foo": "first", "FOO": "second"}
    result = normalize_keys(env, KeyCase.UPPER)
    assert result == {"FOO": "second"}


# ---------------------------------------------------------------------------
# normalize_values
# ---------------------------------------------------------------------------

def test_strip_values_removes_whitespace():
    env = {"KEY": "  hello  "}
    result = normalize_values(env, strip=True, collapse_empty=False)
    assert result["KEY"] == "hello"


def test_strip_false_preserves_whitespace():
    env = {"KEY": "  hello  "}
    result = normalize_values(env, strip=False, collapse_empty=False)
    assert result["KEY"] == "  hello  "


def test_collapse_empty_whitespace_only_becomes_empty():
    env = {"KEY": "   "}
    result = normalize_values(env, strip=False, collapse_empty=True)
    assert result["KEY"] == ""


def test_collapse_empty_false_preserves_whitespace_only():
    env = {"KEY": "   "}
    result = normalize_values(env, strip=False, collapse_empty=False)
    assert result["KEY"] == "   "


# ---------------------------------------------------------------------------
# normalize_env (integration)
# ---------------------------------------------------------------------------

def test_default_options_strips_values():
    env = {"FOO": "  bar  "}
    result = normalize_env(env)
    assert result == {"FOO": "bar"}


def test_default_options_preserves_keys():
    env = {"Foo": "bar"}
    result = normalize_env(env)
    assert "Foo" in result


def test_upper_case_and_strip():
    env = {"foo": "  value  ", "bar": "other"}
    opts = NormalizeOptions(key_case=KeyCase.UPPER, strip_values=True)
    result = normalize_env(env, opts)
    assert result == {"FOO": "value", "BAR": "other"}


def test_lower_case_collapse_empty():
    env = {"FOO": "   ", "BAR": "real"}
    opts = NormalizeOptions(key_case=KeyCase.LOWER, strip_values=False, collapse_empty=True)
    result = normalize_env(env, opts)
    assert result["foo"] == ""
    assert result["bar"] == "real"


def test_original_env_not_mutated():
    env = {"KEY": "  val  "}
    original = dict(env)
    normalize_env(env)
    assert env == original


def test_none_options_uses_defaults():
    env = {"X": "  y  "}
    assert normalize_env(env, None) == normalize_env(env, NormalizeOptions())
