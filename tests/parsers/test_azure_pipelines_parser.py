"""Tests for envlens.parsers.azure_pipelines_parser."""

import pytest

from envlens.parsers.azure_pipelines_parser import (
    AzurePipelinesParseError,
    parse_azure_pipelines,
)


def test_top_level_variables_dict():
    yaml_text = """
Variables:
  APP_ENV: production
  LOG_LEVEL: info
variables:
  APP_ENV: production
  LOG_LEVEL: info
"""
    result = parse_azure_pipelines(yaml_text)
    assert result == {"APP_ENV": "production", "LOG_LEVEL": "info"}


def test_top_level_variables_list_form():
    yaml_text = """
variables:
  - name: DB_HOST
    value: localhost
  - name: DB_PORT
    value: 5432
"""
    result = parse_azure_pipelines(yaml_text)
    assert result == {"DB_HOST": "localhost", "DB_PORT": "5432"}


def test_job_level_variables_override_top_level():
    yaml_text = """
variables:
  APP_ENV: staging
jobs:
  - job: Build
    variables:
      APP_ENV: production
    steps: []
"""
    result = parse_azure_pipelines(yaml_text)
    assert result["APP_ENV"] == "production"


def test_step_level_env_block():
    yaml_text = """
steps:
  - script: echo hello
    env:
      SECRET_KEY: abc123
      DEBUG: "false"
"""
    result = parse_azure_pipelines(yaml_text)
    assert result == {"SECRET_KEY": "abc123", "DEBUG": "false"}


def test_stage_level_variables():
    yaml_text = """
stages:
  - stage: Deploy
    variables:
      DEPLOY_ENV: prod
    jobs: []
"""
    result = parse_azure_pipelines(yaml_text)
    assert result == {"DEPLOY_ENV": "prod"}


def test_multiple_stages_last_value_wins():
    yaml_text = """
stages:
  - stage: A
    variables:
      REGION: us-east-1
  - stage: B
    variables:
      REGION: eu-west-1
    jobs: []
"""
    result = parse_azure_pipelines(yaml_text)
    assert result["REGION"] == "eu-west-1"


def test_empty_string_returns_empty():
    assert parse_azure_pipelines("") == {}


def test_blank_whitespace_returns_empty():
    assert parse_azure_pipelines("   \n\n  ") == {}


def test_no_variables_block_returns_empty():
    yaml_text = """
trigger:
  - main
pool:
  vmImage: ubuntu-latest
"""
    result = parse_azure_pipelines(yaml_text)
    assert result == {}


def test_invalid_yaml_raises_error():
    with pytest.raises(AzurePipelinesParseError):
        parse_azure_pipelines("key: [unclosed")


def test_none_value_becomes_empty_string():
    yaml_text = """
variables:
  OPTIONAL_VAR:
"""
    result = parse_azure_pipelines(yaml_text)
    assert result == {"OPTIONAL_VAR": ""}
