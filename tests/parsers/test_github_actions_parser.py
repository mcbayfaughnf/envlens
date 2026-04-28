"""Tests for the GitHub Actions YAML environment variable parser."""

import pytest
from envlens.parsers.github_actions_parser import (
    GitHubActionsParseError,
    parse_github_actions,
    parse_github_actions_file,
)


def test_top_level_env_block():
    content = """
env:
  APP_ENV: production
  DEBUG: "false"

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - run: echo hello
"""
    result = parse_github_actions(content)
    assert result["APP_ENV"] == "production"
    assert result["DEBUG"] == "false"


def test_job_level_env_block():
    content = """
jobs:
  build:
    runs-on: ubuntu-latest
    env:
      DATABASE_URL: postgres://localhost/db
      SECRET_KEY: abc123
    steps:
      - run: echo hello
"""
    result = parse_github_actions(content)
    assert result["DATABASE_URL"] == "postgres://localhost/db"
    assert result["SECRET_KEY"] == "abc123"


def test_step_level_env_block():
    content = """
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Run tests
        run: pytest
        env:
          PYTEST_TIMEOUT: "60"
          LOG_LEVEL: debug
"""
    result = parse_github_actions(content)
    assert result["PYTEST_TIMEOUT"] == "60"
    assert result["LOG_LEVEL"] == "debug"


def test_multiple_env_blocks_last_value_wins():
    """When the same key appears in multiple env blocks, the last one wins."""
    content = """
env:
  APP_ENV: staging

jobs:
  build:
    runs-on: ubuntu-latest
    env:
      APP_ENV: production
    steps:
      - run: echo hello
"""
    result = parse_github_actions(content)
    assert result["APP_ENV"] == "production"


def test_no_env_blocks_returns_empty():
    content = """
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - run: echo hello
"""
    result = parse_github_actions(content)
    assert result == {}


def test_empty_string_returns_empty():
    result = parse_github_actions("")
    assert result == {}


def test_integer_values_coerced_to_string():
    content = """
env:
  PORT: 8080
  WORKERS: 4
"""
    result = parse_github_actions(content)
    assert result["PORT"] == "8080"
    assert result["WORKERS"] == "4"


def test_invalid_yaml_raises_parse_error():
    bad_content = """
env:
  KEY: [unclosed bracket
  OTHER: value
"""
    with pytest.raises(GitHubActionsParseError):
        parse_github_actions(bad_content)


def test_parse_github_actions_file(tmp_path):
    workflow_file = tmp_path / "ci.yml"
    workflow_file.write_text(
        "env:\n  CI: true\n  NODE_ENV: test\n"
    )
    result = parse_github_actions_file(str(workflow_file))
    assert result["CI"] == "true"
    assert result["NODE_ENV"] == "test"


def test_parse_github_actions_file_not_found():
    with pytest.raises(GitHubActionsParseError, match="not found"):
        parse_github_actions_file("/nonexistent/path/workflow.yml")
