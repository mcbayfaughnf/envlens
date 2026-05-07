"""Tests for envlens.masker."""

from __future__ import annotations

from frozenset import __class_getitem__  # noqa: F401 — just ensure frozenset available

import pytest

from envlens.masker import MASK_PLACEHOLDER, is_sensitive, mask_env


# ---------------------------------------------------------------------------
# is_sensitive
# ---------------------------------------------------------------------------


def test_secret_key_is_sensitive():
    assert is_sensitive("MY_SECRET") is True


def test_password_key_is_sensitive():
    assert is_sensitive("DB_PASSWORD") is True


def test_token_key_is_sensitive():
    assert is_sensitive("GITHUB_TOKEN") is True


def test_api_key_is_sensitive():
    assert is_sensitive("STRIPE_API_KEY") is True


def test_plain_key_not_sensitive():
    assert is_sensitive("APP_ENV") is False


def test_port_not_sensitive():
    assert is_sensitive("PORT") is False


def test_case_insensitive_match():
    assert is_sensitive("db_password") is True


def test_extra_pattern_matches():
    assert is_sensitive("MY_CERT", extra_patterns=(r".*CERT.*",)) is True


def test_extra_pattern_does_not_affect_unrelated():
    assert is_sensitive("APP_NAME", extra_patterns=(r".*CERT.*",)) is False


def test_explicit_sensitive_keys_set():
    assert is_sensitive("CUSTOM_VAR", sensitive_keys=frozenset({"CUSTOM_VAR"})) is True


def test_explicit_sensitive_keys_case_insensitive():
    assert is_sensitive("custom_var", sensitive_keys=frozenset({"CUSTOM_VAR"})) is True


# ---------------------------------------------------------------------------
# mask_env
# ---------------------------------------------------------------------------


def test_mask_env_replaces_sensitive_values():
    env = {"DB_PASSWORD": "s3cr3t", "APP_ENV": "production"}
    result = mask_env(env)
    assert result["DB_PASSWORD"] == MASK_PLACEHOLDER
    assert result["APP_ENV"] == "production"


def test_mask_env_does_not_mutate_original():
    env = {"API_KEY": "abc123", "PORT": "8080"}
    mask_env(env)
    assert env["API_KEY"] == "abc123"


def test_mask_env_custom_placeholder():
    env = {"SECRET_KEY": "topsecret"}
    result = mask_env(env, placeholder="[REDACTED]")
    assert result["SECRET_KEY"] == "[REDACTED]"


def test_mask_env_with_extra_patterns():
    env = {"SSL_CERT": "cert-data", "HOST": "localhost"}
    result = mask_env(env, extra_patterns=(r".*CERT.*",))
    assert result["SSL_CERT"] == MASK_PLACEHOLDER
    assert result["HOST"] == "localhost"


def test_mask_env_with_explicit_sensitive_keys():
    env = {"DEPLOY_KEY": "xyz", "REGION": "us-east-1"}
    result = mask_env(env, sensitive_keys=frozenset({"DEPLOY_KEY"}))
    assert result["DEPLOY_KEY"] == MASK_PLACEHOLDER
    assert result["REGION"] == "us-east-1"


def test_mask_env_empty_dict():
    assert mask_env({}) == {}
