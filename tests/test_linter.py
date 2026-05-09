"""Tests for envlens.linter."""
import pytest
from envlens.linter import lint_env, LintResult, LintIssue


def _codes(result: LintResult) -> list:
    return [i.code for i in result.issues]


# ---------------------------------------------------------------------------
# L001 – key naming
# ---------------------------------------------------------------------------

def test_valid_upper_snake_key_no_l001():
    result = lint_env({"MY_KEY": "value"})
    assert "L001" not in _codes(result)


def test_lowercase_key_triggers_l001():
    result = lint_env({"my_key": "value"})
    assert "L001" in _codes(result)
    issue = next(i for i in result.issues if i.code == "L001")
    assert issue.severity == "warning"


def test_lowercase_key_allowed_when_flag_set():
    result = lint_env({"my_key": "value"}, allow_lowercase_keys=True)
    assert "L001" not in _codes(result)


def test_key_starting_with_digit_triggers_l001():
    result = lint_env({"1BAD": "val"})
    assert "L001" in _codes(result)


# ---------------------------------------------------------------------------
# L002 – empty sensitive value
# ---------------------------------------------------------------------------

def test_empty_password_triggers_l002():
    result = lint_env({"DB_PASSWORD": ""})
    assert "L002" in _codes(result)
    issue = next(i for i in result.issues if i.code == "L002")
    assert issue.severity == "error"


def test_empty_token_triggers_l002():
    result = lint_env({"GITHUB_TOKEN": ""})
    assert "L002" in _codes(result)


def test_empty_non_sensitive_key_no_l002():
    result = lint_env({"OPTIONAL_FEATURE": ""})
    assert "L002" not in _codes(result)


def test_non_empty_secret_no_l002():
    result = lint_env({"API_SECRET": "abc123"})
    assert "L002" not in _codes(result)


# ---------------------------------------------------------------------------
# L003 – suspicious placeholder value
# ---------------------------------------------------------------------------

def test_changeme_triggers_l003():
    result = lint_env({"DB_HOST": "changeme"})
    assert "L003" in _codes(result)
    issue = next(i for i in result.issues if i.code == "L003")
    assert issue.severity == "warning"


def test_todo_triggers_l003():
    result = lint_env({"SOME_URL": "todo"})
    assert "L003" in _codes(result)


def test_real_value_no_l003():
    result = lint_env({"DB_HOST": "postgres://localhost/mydb"})
    assert "L003" not in _codes(result)


# ---------------------------------------------------------------------------
# L004 – value length
# ---------------------------------------------------------------------------

def test_long_value_triggers_l004():
    result = lint_env({"BIG": "x" * 300}, max_value_length=256)
    assert "L004" in _codes(result)
    issue = next(i for i in result.issues if i.code == "L004")
    assert issue.severity == "warning"


def test_value_at_limit_no_l004():
    result = lint_env({"BIG": "x" * 256}, max_value_length=256)
    assert "L004" not in _codes(result)


def test_no_max_length_no_l004():
    result = lint_env({"BIG": "x" * 10_000})
    assert "L004" not in _codes(result)


# ---------------------------------------------------------------------------
# Aggregation helpers
# ---------------------------------------------------------------------------

def test_has_errors_true_when_error_present():
    result = lint_env({"API_KEY": ""})
    assert result.has_errors


def test_has_warnings_true_when_warning_present():
    result = lint_env({"bad_key": "hello"})
    assert result.has_warnings


def test_clean_env_no_issues():
    result = lint_env({"PORT": "8080", "DEBUG": "false"})
    assert not result.issues
