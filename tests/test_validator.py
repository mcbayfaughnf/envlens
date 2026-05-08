"""Tests for envlens.validator."""

import pytest

from envlens.validator import (
    EnvSchema,
    ValidationError,
    ValidationResult,
    validate,
)


# ---------------------------------------------------------------------------
# EnvSchema construction
# ---------------------------------------------------------------------------

def test_schema_from_dict_basic():
    schema = EnvSchema.from_dict({"required": ["A", "B"], "optional": ["C"]})
    assert schema.required == frozenset({"A", "B"})
    assert schema.optional == frozenset({"C"})


def test_schema_empty_defaults():
    schema = EnvSchema()
    assert schema.required == frozenset()
    assert schema.optional == frozenset()


def test_schema_overlap_raises():
    with pytest.raises(ValidationError, match="both required and optional"):
        EnvSchema(required=frozenset({"X"}), optional=frozenset({"X"}))


def test_schema_from_dict_missing_sections():
    schema = EnvSchema.from_dict({})
    assert schema.required == frozenset()
    assert schema.optional == frozenset()


# ---------------------------------------------------------------------------
# validate — happy paths
# ---------------------------------------------------------------------------

def test_all_required_present_is_valid():
    schema = EnvSchema(required=frozenset({"HOST", "PORT"}))
    result = validate({"HOST": "localhost", "PORT": "5432"}, schema)
    assert result.is_valid


def test_extra_keys_allowed_by_default():
    schema = EnvSchema(required=frozenset({"HOST"}))
    result = validate({"HOST": "localhost", "EXTRA": "value"}, schema)
    assert result.is_valid
    assert result.unknown_keys == frozenset()


def test_optional_keys_not_required():
    schema = EnvSchema(required=frozenset({"A"}), optional=frozenset({"B"}))
    result = validate({"A": "1"}, schema)
    assert result.is_valid


# ---------------------------------------------------------------------------
# validate — missing required
# ---------------------------------------------------------------------------

def test_missing_required_key_reported():
    schema = EnvSchema(required=frozenset({"DB_URL", "SECRET_KEY"}))
    result = validate({"DB_URL": "sqlite://"}, schema)
    assert not result.is_valid
    assert result.missing_required == frozenset({"SECRET_KEY"})


def test_all_required_missing():
    schema = EnvSchema(required=frozenset({"A", "B"}))
    result = validate({}, schema)
    assert result.missing_required == frozenset({"A", "B"})


# ---------------------------------------------------------------------------
# validate — unknown keys
# ---------------------------------------------------------------------------

def test_unknown_keys_reported_when_strict():
    schema = EnvSchema(required=frozenset({"A"}), optional=frozenset({"B"}))
    result = validate({"A": "1", "C": "3"}, schema, allow_unknown=False)
    assert not result.is_valid
    assert result.unknown_keys == frozenset({"C"})


def test_unknown_keys_ignored_when_allow_unknown():
    schema = EnvSchema(required=frozenset({"A"}))
    result = validate({"A": "1", "Z": "99"}, schema, allow_unknown=True)
    assert result.unknown_keys == frozenset()


# ---------------------------------------------------------------------------
# ValidationResult.summary
# ---------------------------------------------------------------------------

def test_summary_ok():
    result = ValidationResult()
    assert result.summary() == "OK"


def test_summary_missing_required():
    result = ValidationResult(missing_required=frozenset({"FOO"}))
    assert "Missing required keys" in result.summary()
    assert "FOO" in result.summary()


def test_summary_unknown_keys():
    result = ValidationResult(unknown_keys=frozenset({"BAR"}))
    assert "Unknown keys" in result.summary()
    assert "BAR" in result.summary()


def test_summary_both_issues():
    result = ValidationResult(
        missing_required=frozenset({"A"}),
        unknown_keys=frozenset({"Z"}),
    )
    summary = result.summary()
    assert "Missing required keys" in summary
    assert "Unknown keys" in summary
