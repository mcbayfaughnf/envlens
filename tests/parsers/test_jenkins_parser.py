"""Tests for envlens.parsers.jenkins_parser."""

from __future__ import annotations

import pytest

from envlens.parsers.jenkins_parser import (
    JenkinsParseError,
    parse_jenkins,
    parse_jenkins_file,
)


JENKINSFILE_SINGLE = """
pipeline {
    environment {
        APP_ENV = 'production'
        LOG_LEVEL = "info"
    }
    stages {}
}
"""

JENKINSFILE_MULTI_BLOCK = """
pipeline {
    environment {
        BASE_URL = 'https://example.com'
        TIMEOUT = '30'
    }
    stages {
        stage('Deploy') {
            environment {
                DEPLOY_ENV = 'prod'
                TIMEOUT = '60'
            }
        }
    }
}
"""

JENKINSFILE_WITH_COMMENTS = """
pipeline {
    environment {
        // This is a comment
        API_KEY = 'secret'
        DEBUG = 'false'
    }
}
"""


def test_single_env_block():
    result = parse_jenkins(JENKINSFILE_SINGLE)
    assert result == {"APP_ENV": "production", "LOG_LEVEL": "info"}


def test_multiple_env_blocks_last_value_wins():
    result = parse_jenkins(JENKINSFILE_MULTI_BLOCK)
    assert result["BASE_URL"] == "https://example.com"
    assert result["DEPLOY_ENV"] == "prod"
    # Stage-level TIMEOUT overrides pipeline-level
    assert result["TIMEOUT"] == "60"


def test_comments_ignored():
    result = parse_jenkins(JENKINSFILE_WITH_COMMENTS)
    assert result == {"API_KEY": "secret", "DEBUG": "false"}


def test_no_environment_block_returns_empty():
    result = parse_jenkins("pipeline { stages { stage('Build') {} } }")
    assert result == {}


def test_empty_string_returns_empty():
    assert parse_jenkins("") == {}


def test_blank_whitespace_returns_empty():
    assert parse_jenkins("   \n\t  ") == {}


def test_non_string_raises():
    with pytest.raises(JenkinsParseError, match="Expected str"):
        parse_jenkins(None)  # type: ignore[arg-type]


def test_parse_jenkins_file(tmp_path):
    p = tmp_path / "Jenkinsfile"
    p.write_text(JENKINSFILE_SINGLE, encoding="utf-8")
    result = parse_jenkins_file(p)
    assert result["APP_ENV"] == "production"


def test_parse_jenkins_file_missing_raises(tmp_path):
    with pytest.raises(JenkinsParseError, match="Cannot read file"):
        parse_jenkins_file(tmp_path / "nonexistent_Jenkinsfile")
