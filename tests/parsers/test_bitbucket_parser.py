"""Tests for envlens.parsers.bitbucket_parser."""

import pytest

from envlens.parsers.bitbucket_parser import (
    BitbucketParseError,
    parse_bitbucket_pipelines,
)


DEFINITIONS_ONLY = """
definitions:
  variables:
    APP_ENV: production
    LOG_LEVEL: info

pipelines:
  default:
    - step:
        name: Build
        script:
          - echo hello
        variables: {}
"""

STEP_VARIABLES = """
pipelines:
  default:
    - step:
        name: Deploy
        script:
          - ./deploy.sh
        variables:
          DEPLOY_TARGET: staging
          TIMEOUT: "30"
"""

MERGED_DEFINITIONS_AND_STEP = """
definitions:
  variables:
    APP_ENV: production
    SHARED_KEY: base

pipelines:
  default:
    - step:
        name: Test
        script: [echo test]
        variables:
          SHARED_KEY: overridden
          STEP_ONLY: yes
"""

PARALLEL_STEPS = """
pipelines:
  default:
    - parallel:
        - step:
            name: Unit
            script: [echo unit]
            variables:
              TEST_SUITE: unit
        - step:
            name: Integration
            script: [echo int]
            variables:
              TEST_SUITE: integration
"""


def test_definitions_variables_parsed():
    result = parse_bitbucket_pipelines(DEFINITIONS_ONLY)
    assert result == {"APP_ENV": "production", "LOG_LEVEL": "info"}


def test_step_variables_parsed():
    result = parse_bitbucket_pipelines(STEP_VARIABLES)
    assert result == {"DEPLOY_TARGET": "staging", "TIMEOUT": "30"}


def test_step_variables_override_definitions():
    result = parse_bitbucket_pipelines(MERGED_DEFINITIONS_AND_STEP)
    assert result["SHARED_KEY"] == "overridden"
    assert result["APP_ENV"] == "production"
    assert result["STEP_ONLY"] == "yes"


def test_parallel_steps_last_value_wins():
    result = parse_bitbucket_pipelines(PARALLEL_STEPS)
    # Both steps define TEST_SUITE; last one processed wins
    assert "TEST_SUITE" in result


def test_empty_string_returns_empty():
    assert parse_bitbucket_pipelines("") == {}


def test_blank_whitespace_returns_empty():
    assert parse_bitbucket_pipelines("   \n  ") == {}


def test_no_variables_returns_empty():
    yaml_text = """
pipelines:
  default:
    - step:
        name: Build
        script:
          - echo hi
"""
    assert parse_bitbucket_pipelines(yaml_text) == {}


def test_invalid_yaml_raises():
    with pytest.raises(BitbucketParseError, match="Invalid YAML"):
        parse_bitbucket_pipelines("{bad: yaml: here:")


def test_non_mapping_yaml_returns_empty():
    assert parse_bitbucket_pipelines("- just\n- a\n- list") == {}
