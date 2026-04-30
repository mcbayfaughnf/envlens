"""Tests for envlens.parsers.travis_parser."""

import pytest

from envlens.parsers.travis_parser import (
    TravisParseError,
    parse_travis,
    parse_travis_file,
)


YAML_GLOBAL_ENV = """
language: python
env:
  global:
    - APP_ENV=production
    - DEBUG=false
"""

YAML_INLINE_ENV = """
language: python
env:
  - APP_ENV=staging DEBUG=false
"""

YAML_NO_ENV = """
language: python
script: pytest
"""

YAML_DICT_ENTRY = """
language: python
env:
  global:
    - APP_ENV=ci
    - MY_KEY: my_value
"""


def test_global_env_block():
    result = parse_travis(YAML_GLOBAL_ENV)
    assert result == {"APP_ENV": "production", "DEBUG": "false"}


def test_inline_list_env():
    result = parse_travis(YAML_INLINE_ENV)
    assert result == {"APP_ENV": "staging", "DEBUG": "false"}


def test_no_env_block_returns_empty():
    result = parse_travis(YAML_NO_ENV)
    assert result == {}


def test_empty_string_returns_empty():
    assert parse_travis("") == {}


def test_blank_whitespace_returns_empty():
    assert parse_travis("   \n  ") == {}


def test_dict_entry_in_global():
    result = parse_travis(YAML_DICT_ENTRY)
    assert result["APP_ENV"] == "ci"
    assert result["MY_KEY"] == "my_value"


def test_invalid_yaml_raises():
    with pytest.raises(TravisParseError, match="Invalid YAML"):
        parse_travis(": : : bad yaml :::")


def test_non_dict_yaml_returns_empty():
    result = parse_travis("- just\n- a\n- list\n")
    assert result == {}


def test_parse_travis_file(tmp_path):
    f = tmp_path / ".travis.yml"
    f.write_text(YAML_GLOBAL_ENV)
    result = parse_travis_file(str(f))
    assert result["APP_ENV"] == "production"


def test_parse_travis_file_missing_raises(tmp_path):
    with pytest.raises(TravisParseError, match="Cannot read file"):
        parse_travis_file(str(tmp_path / "nonexistent.yml"))
