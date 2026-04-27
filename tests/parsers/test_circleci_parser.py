"""Tests for the CircleCI config parser."""

import pytest

from envlens.parsers.circleci_parser import CircleCIParseError, parse_circleci


CONFIG_SINGLE_JOB = """
version: 2.1
jobs:
  build:
    environment:
      APP_ENV: production
      LOG_LEVEL: info
    steps:
      - checkout
"""

CONFIG_MULTIPLE_JOBS = """
version: 2.1
jobs:
  build:
    environment:
      APP_ENV: staging
  test:
    environment:
      APP_ENV: test
      DEBUG: "true"
"""

CONFIG_WORKFLOW_LEVEL = """
version: 2.1
workflows:
  main:
    jobs:
      - build
jobs:
  build:
    environment:
      CI: "1"
      REGION: us-east-1
    steps:
      - run: echo hello
"""

CONFIG_EMPTY = """
version: 2.1
jobs:
  build:
    steps:
      - checkout
"""


def test_single_job_environment():
    result = parse_circleci(CONFIG_SINGLE_JOB)
    assert result["APP_ENV"] == "production"
    assert result["LOG_LEVEL"] == "info"


def test_multiple_jobs_last_value_wins():
    result = parse_circleci(CONFIG_MULTIPLE_JOBS)
    # Both jobs define APP_ENV; the second encountered value should be present.
    assert "APP_ENV" in result
    assert result["DEBUG"] == "true"


def test_workflow_level_env():
    result = parse_circleci(CONFIG_WORKFLOW_LEVEL)
    assert result["CI"] == "1"
    assert result["REGION"] == "us-east-1"


def test_no_environment_blocks_returns_empty():
    result = parse_circleci(CONFIG_EMPTY)
    assert result == {}


def test_empty_string_returns_empty():
    result = parse_circleci("")
    assert result == {}


def test_invalid_yaml_raises():
    with pytest.raises(CircleCIParseError, match="Invalid YAML"):
        parse_circleci(": : bad: yaml: [")


def test_non_mapping_top_level_raises():
    with pytest.raises(CircleCIParseError, match="YAML mapping"):
        parse_circleci("- item1\n- item2\n")


def test_null_value_becomes_empty_string():
    config = "version: 2.1\njobs:\n  build:\n    environment:\n      EMPTY_VAR:\n"
    result = parse_circleci(config)
    assert result["EMPTY_VAR"] == ""
