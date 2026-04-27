"""Tests for envlens.diff module."""

import pytest

from envlens.diff import EnvDiffResult, diff_envs


def test_identical_envs_no_differences():
    src = {'A': '1', 'B': '2'}
    result = diff_envs(src, src.copy())
    assert not result.has_differences
    assert result.matching == {'A', 'B'}


def test_key_only_in_source():
    result = diff_envs({'A': '1', 'B': '2'}, {'A': '1'})
    assert result.only_in_source == {'B': '2'}
    assert result.only_in_target == {}


def test_key_only_in_target():
    result = diff_envs({'A': '1'}, {'A': '1', 'C': '3'})
    assert result.only_in_target == {'C': '3'}
    assert result.only_in_source == {}


def test_value_mismatch():
    result = diff_envs({'PORT': '8080'}, {'PORT': '9090'})
    assert result.value_mismatches == {'PORT': ('8080', '9090')}
    assert result.matching == set()


def test_ignore_keys_excluded_from_diff():
    result = diff_envs({'A': '1', 'SECRET': 'x'}, {'A': '1'}, ignore_keys=['SECRET'])
    assert not result.has_differences


def test_custom_names_in_result():
    result = diff_envs({}, {}, source_name='.env', target_name='docker')
    assert result.source_name == '.env'
    assert result.target_name == 'docker'


def test_summary_contains_labels():
    result = diff_envs({'X': '1'}, {'X': '2'}, source_name='dev', target_name='prod')
    summary = result.summary()
    assert 'dev' in summary
    assert 'prod' in summary
    assert 'X' in summary


def test_summary_no_differences():
    result = diff_envs({'K': 'v'}, {'K': 'v'})
    summary = result.summary()
    assert 'Matching keys      : 1' in summary


def test_empty_envs():
    result = diff_envs({}, {})
    assert not result.has_differences
    assert result.matching == set()


def test_has_differences_flag():
    result = diff_envs({'A': '1'}, {'A': '2'})
    assert result.has_differences is True
