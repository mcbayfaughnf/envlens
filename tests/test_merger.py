"""Tests for envlens.merger."""

import pytest

from envlens.merger import (
    MergeConflictError,
    MergeResult,
    MergeStrategy,
    merge_envs,
)


# ---------------------------------------------------------------------------
# Basic happy-path tests
# ---------------------------------------------------------------------------

def test_single_source_returned_unchanged():
    src = {"A": "1", "B": "2"}
    result = merge_envs([src])
    assert result.merged == src
    assert not result.has_conflicts


def test_disjoint_sources_merged():
    result = merge_envs([{"A": "1"}, {"B": "2"}, {"C": "3"}])
    assert result.merged == {"A": "1", "B": "2", "C": "3"}
    assert not result.has_conflicts


def test_empty_sources_returns_empty():
    result = merge_envs([])
    assert result.merged == {}
    assert not result.has_conflicts


# ---------------------------------------------------------------------------
# Strategy: LAST (default)
# ---------------------------------------------------------------------------

def test_last_strategy_keeps_latest_value():
    result = merge_envs([{"X": "first"}, {"X": "second"}])
    assert result.merged["X"] == "second"
    assert result.has_conflicts


def test_last_strategy_three_sources():
    result = merge_envs(
        [{"X": "a"}, {"X": "b"}, {"X": "c"}],
        strategy=MergeStrategy.LAST,
    )
    assert result.merged["X"] == "c"
    assert len(result.conflicts["X"]) == 3


# ---------------------------------------------------------------------------
# Strategy: FIRST
# ---------------------------------------------------------------------------

def test_first_strategy_keeps_earliest_value():
    result = merge_envs(
        [{"X": "original"}, {"X": "override"}],
        strategy=MergeStrategy.FIRST,
    )
    assert result.merged["X"] == "original"
    assert result.has_conflicts


# ---------------------------------------------------------------------------
# Strategy: ERROR
# ---------------------------------------------------------------------------

def test_error_strategy_raises_on_conflict():
    with pytest.raises(MergeConflictError) as exc_info:
        merge_envs([{"X": "a"}, {"X": "b"}], strategy=MergeStrategy.ERROR)
    assert exc_info.value.key == "X"


def test_error_strategy_no_conflict_succeeds():
    result = merge_envs([{"A": "1"}, {"B": "2"}], strategy=MergeStrategy.ERROR)
    assert result.merged == {"A": "1", "B": "2"}


# ---------------------------------------------------------------------------
# ignore_keys
# ---------------------------------------------------------------------------

def test_ignore_keys_excluded_from_merged():
    result = merge_envs([{"A": "1", "SECRET": "x"}, {"B": "2", "SECRET": "y"}],
                        ignore_keys=["SECRET"])
    assert "SECRET" not in result.merged
    assert result.merged == {"A": "1", "B": "2"}


def test_ignore_keys_prevents_false_conflicts():
    result = merge_envs([{"A": "1"}, {"A": "2"}], ignore_keys=["A"])
    assert not result.has_conflicts
    assert result.merged == {}


# ---------------------------------------------------------------------------
# MergeResult helpers
# ---------------------------------------------------------------------------

def test_conflict_summary_no_conflicts():
    result = merge_envs([{"A": "1"}])
    assert result.conflict_summary() == "No conflicts."


def test_conflict_summary_lists_keys():
    result = merge_envs([{"A": "old"}, {"A": "new"}])
    summary = result.conflict_summary()
    assert "A" in summary
    assert "old" in summary
    assert "new" in summary
