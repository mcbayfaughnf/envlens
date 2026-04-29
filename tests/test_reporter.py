"""Tests for envlens.reporter."""

from __future__ import annotations

import json
import io

import pytest

from envlens.diff import EnvDiffResult
from envlens.reporter import OutputFormat, render


@pytest.fixture()
def clean_result() -> EnvDiffResult:
    return EnvDiffResult(
        only_in_source={},
        only_in_target={},
        value_mismatches={},
    )


@pytest.fixture()
def mixed_result() -> EnvDiffResult:
    return EnvDiffResult(
        only_in_source={"REMOVED_KEY": "old_val"},
        only_in_target={"NEW_KEY": "new_val"},
        value_mismatches={"SHARED": ("v1", "v2")},
    )


# --- TEXT format ---

def test_text_no_differences(clean_result):
    out = render(clean_result, OutputFormat.TEXT, stream=io.StringIO())
    assert "No differences found." in out


def test_text_only_in_source(mixed_result):
    out = render(mixed_result, OutputFormat.TEXT, source_label="src", target_label="tgt", stream=io.StringIO())
    assert "Only in src:" in out
    assert "REMOVED_KEY=old_val" in out


def test_text_only_in_target(mixed_result):
    out = render(mixed_result, OutputFormat.TEXT, source_label="src", target_label="tgt", stream=io.StringIO())
    assert "Only in tgt:" in out
    assert "NEW_KEY=new_val" in out


def test_text_value_mismatch(mixed_result):
    out = render(mixed_result, OutputFormat.TEXT, source_label="src", target_label="tgt", stream=io.StringIO())
    assert "Value mismatches:" in out
    assert "SHARED" in out
    assert "src: v1" in out
    assert "tgt: v2" in out


# --- JSON format ---

def test_json_structure(mixed_result):
    out = render(mixed_result, OutputFormat.JSON, source_label="src", target_label="tgt", stream=io.StringIO())
    data = json.loads(out)
    assert data["source"] == "src"
    assert data["target"] == "tgt"
    assert data["only_in_source"] == {"REMOVED_KEY": "old_val"}
    assert data["only_in_target"] == {"NEW_KEY": "new_val"}
    assert data["value_mismatches"]["SHARED"] == {"src": "v1", "tgt": "v2"}


def test_json_no_differences(clean_result):
    out = render(clean_result, OutputFormat.JSON, stream=io.StringIO())
    data = json.loads(out)
    assert data["only_in_source"] == {}
    assert data["only_in_target"] == {}
    assert data["value_mismatches"] == {}


# --- Markdown format ---

def test_markdown_header(mixed_result):
    out = render(mixed_result, OutputFormat.MARKDOWN, source_label="dev", target_label="prod", stream=io.StringIO())
    assert "## Env Diff: `dev` vs `prod`" in out


def test_markdown_table_row(mixed_result):
    out = render(mixed_result, OutputFormat.MARKDOWN, source_label="dev", target_label="prod", stream=io.StringIO())
    assert "| `SHARED` | `v1` | `v2` |" in out


def test_markdown_no_differences(clean_result):
    out = render(clean_result, OutputFormat.MARKDOWN, stream=io.StringIO())
    assert "_No differences found._" in out


# --- stream output ---

def test_render_writes_to_stream(mixed_result):
    buf = io.StringIO()
    render(mixed_result, OutputFormat.TEXT, stream=buf)
    buf.seek(0)
    assert "REMOVED_KEY" in buf.read()
