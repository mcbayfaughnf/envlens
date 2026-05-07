import pytest
from envlens.parsers.env_substitution import (
    SubstitutionError,
    resolve_substitutions,
)


def test_no_references_unchanged():
    env = {"FOO": "bar", "BAZ": "qux"}
    assert resolve_substitutions(env) == {"FOO": "bar", "BAZ": "qux"}


def test_braced_reference_resolved():
    env = {"BASE": "/app", "PATH": "${BASE}/bin"}
    result = resolve_substitutions(env)
    assert result["PATH"] == "/app/bin"


def test_bare_reference_resolved():
    env = {"HOST": "localhost", "URL": "http://$HOST:8080"}
    result = resolve_substitutions(env)
    assert result["URL"] == "http://localhost:8080"


def test_default_used_when_name_missing():
    env = {"GREETING": "${NAME:-world}"}
    result = resolve_substitutions(env)
    assert result["GREETING"] == "world"


def test_defined_value_beats_default():
    env = {"NAME": "Alice", "GREETING": "${NAME:-world}"}
    result = resolve_substitutions(env)
    assert result["GREETING"] == "Alice"


def test_fallback_dict_consulted():
    env = {"MSG": "Hello $USER"}
    fallback = {"USER": "bob"}
    result = resolve_substitutions(env, fallback=fallback)
    assert result["MSG"] == "Hello bob"


def test_env_beats_fallback():
    env = {"USER": "alice", "MSG": "Hello $USER"}
    fallback = {"USER": "bob"}
    result = resolve_substitutions(env, fallback=fallback)
    assert result["MSG"] == "Hello alice"


def test_unresolved_left_intact_by_default():
    env = {"MSG": "Hello ${UNKNOWN}"}
    result = resolve_substitutions(env)
    assert result["MSG"] == "Hello ${UNKNOWN}"


def test_strict_mode_raises_on_unresolved_braced():
    env = {"MSG": "Hello ${UNKNOWN}"}
    with pytest.raises(SubstitutionError, match="UNKNOWN"):
        resolve_substitutions(env, strict=True)


def test_strict_mode_raises_on_unresolved_bare():
    env = {"MSG": "Hello $UNKNOWN"}
    with pytest.raises(SubstitutionError, match="UNKNOWN"):
        resolve_substitutions(env, strict=True)


def test_multiple_references_in_one_value():
    env = {"PROTO": "https", "HOST": "example.com", "PORT": "443",
           "URL": "${PROTO}://${HOST}:${PORT}"}
    result = resolve_substitutions(env)
    assert result["URL"] == "https://example.com:443"


def test_empty_default_allowed():
    env = {"VAL": "${MISSING:-}"}
    result = resolve_substitutions(env)
    assert result["VAL"] == ""


def test_original_dict_not_mutated():
    env = {"A": "1", "B": "${A}"}
    original = dict(env)
    resolve_substitutions(env)
    assert env == original
