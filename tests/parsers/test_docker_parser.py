"""Tests for envlens.parsers.docker_parser."""

import pytest

from envlens.parsers.docker_parser import DockerParseError, parse_dockerfile, parse_dockerfile_file


def test_single_env_equals_form():
    content = "FROM python:3.11\nENV APP_ENV=production\n"
    result = parse_dockerfile(content)
    assert result == {'APP_ENV': 'production'}


def test_single_env_legacy_form():
    content = "FROM ubuntu\nENV MY_VAR legacy_value\n"
    result = parse_dockerfile(content)
    assert result == {'MY_VAR': 'legacy_value'}


def test_multiple_env_on_one_line():
    content = "ENV KEY1=val1 KEY2=val2 KEY3=val3\n"
    result = parse_dockerfile(content)
    assert result == {'KEY1': 'val1', 'KEY2': 'val2', 'KEY3': 'val3'}


def test_env_with_quoted_value():
    content = 'ENV GREETING="hello world"\n'
    result = parse_dockerfile(content)
    assert result['GREETING'] == 'hello world'


def test_comments_ignored():
    content = "# This is a comment\nENV DEBUG=true\n"
    result = parse_dockerfile(content)
    assert result == {'DEBUG': 'true'}


def test_empty_content():
    assert parse_dockerfile('') == {}


def test_no_env_instructions():
    content = "FROM alpine\nRUN echo hello\n"
    assert parse_dockerfile(content) == {}


def test_later_env_overrides_earlier():
    content = "ENV PORT=8080\nENV PORT=9090\n"
    result = parse_dockerfile(content)
    assert result['PORT'] == '9090'


def test_invalid_content_type_raises():
    with pytest.raises(DockerParseError):
        parse_dockerfile(None)  # type: ignore


def test_parse_dockerfile_file_not_found(tmp_path):
    with pytest.raises(DockerParseError, match='Cannot read'):
        parse_dockerfile_file(tmp_path / 'nonexistent')


def test_parse_dockerfile_file_reads_file(tmp_path):
    dockerfile = tmp_path / 'Dockerfile'
    dockerfile.write_text('ENV CI=true\n', encoding='utf-8')
    result = parse_dockerfile_file(dockerfile)
    assert result == {'CI': 'true'}
