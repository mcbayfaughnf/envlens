"""Tests for envlens.parsers.gitlab_ci_parser."""

import pytest

from envlens.parsers.gitlab_ci_parser import (
    GitLabCIParseError,
    parse_gitlab_ci,
)


def test_top_level_variables_block():
    yaml_text = """
variables:
  APP_ENV: production
  LOG_LEVEL: info
"""
    result = parse_gitlab_ci(yaml_text)
    assert result == {"APP_ENV": "production", "LOG_LEVEL": "info"}


def test_job_level_variables_block():
    yaml_text = """
build:
  stage: build
  variables:
    BUILD_MODE: release
  script:
    - make build
"""
    result = parse_gitlab_ci(yaml_text)
    assert result == {"BUILD_MODE": "release"}


def test_top_and_job_level_job_wins():
    yaml_text = """
variables:
  APP_ENV: staging
  SHARED: common

deploy:
  stage: deploy
  variables:
    APP_ENV: production
"""
    result = parse_gitlab_ci(yaml_text)
    assert result["APP_ENV"] == "production"
    assert result["SHARED"] == "common"


def test_multiple_jobs_last_value_wins():
    yaml_text = """
job_a:
  variables:
    KEY: first

job_b:
  variables:
    KEY: second
"""
    result = parse_gitlab_ci(yaml_text)
    assert result["KEY"] == "second"


def test_no_variables_returns_empty():
    yaml_text = """
stages:
  - build
  - test

build_job:
  stage: build
  script:
    - echo hello
"""
    result = parse_gitlab_ci(yaml_text)
    assert result == {}


def test_empty_string_returns_empty():
    assert parse_gitlab_ci("") == {}


def test_blank_whitespace_returns_empty():
    assert parse_gitlab_ci("   \n  \t  ") == {}


def test_numeric_value_coerced_to_string():
    yaml_text = """
variables:
  PORT: 8080
  TIMEOUT: 30
"""
    result = parse_gitlab_ci(yaml_text)
    assert result["PORT"] == "8080"
    assert result["TIMEOUT"] == "30"


def test_null_value_becomes_empty_string():
    yaml_text = """
variables:
  OPTIONAL_VAR: ~
"""
    result = parse_gitlab_ci(yaml_text)
    assert result["OPTIONAL_VAR"] == ""


def test_invalid_yaml_raises_error():
    with pytest.raises(GitLabCIParseError, match="YAML parse error"):
        parse_gitlab_ci("{invalid: yaml: content:")
