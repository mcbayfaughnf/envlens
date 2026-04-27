"""Unit tests for envlens.parsers.dotenv_parser."""

import textwrap
from pathlib import Path

import pytest

from envlens.parsers.dotenv_parser import (
    DotEnvParseError,
    parse_dotenv,
    parse_dotenv_file,
)


def test_basic_key_value():
    result = parse_dotenv("FOO=bar\nBAZ=qux\n")
    assert result == {"FOO": "bar", "BAZ": "qux"}


def test_empty_value():
    assert parse_dotenv("EMPTY=") == {"EMPTY": ""}


def test_blank_lines_and_comments_skipped():
    source = textwrap.dedent("""\
        # This is a comment
        FOO=1

        # Another comment
        BAR=2
    """)
    assert parse_dotenv(source) == {"FOO": "1", "BAR": "2"}


def test_export_prefix_stripped():
    assert parse_dotenv("export MY_VAR=hello") == {"MY_VAR": "hello"}


def test_double_quoted_value():
    assert parse_dotenv('GREETING="hello world"') == {"GREETING": "hello world"}


def test_single_quoted_value():
    assert parse_dotenv("MSG='it works'") == {"MSG": "it works"}


def test_double_quoted_escape_sequences():
    result = parse_dotenv('MULTI="line1\\nline2"')
    assert result["MULTI"] == "line1\nline2"


def test_single_quoted_no_escape():
    result = parse_dotenv("RAW='no\\nescape'")
    assert result["RAW"] == "no\\nescape"


def test_inline_comment_stripped():
    result = parse_dotenv("HOST=localhost # the host")
    assert result["HOST"] == "localhost"


def test_inline_comment_not_stripped_inside_quotes():
    result = parse_dotenv('NOTE="keep # this"')
    assert result["NOTE"] == "keep # this"


def test_whitespace_around_equals():
    result = parse_dotenv("KEY  =  value  ")
    assert result["KEY"] == "value"


def test_invalid_line_raises():
    with pytest.raises(DotEnvParseError, match="invalid syntax"):
        parse_dotenv("THIS IS INVALID")


def test_parse_dotenv_file_reads_from_disk(tmp_path: Path):
    env_file = tmp_path / ".env"
    env_file.write_text("DB_HOST=postgres\nDB_PORT=5432\n", encoding="utf-8")
    result = parse_dotenv_file(env_file)
    assert result == {"DB_HOST": "postgres", "DB_PORT": "5432"}


def test_parse_dotenv_file_missing_raises(tmp_path: Path):
    with pytest.raises(DotEnvParseError, match="Cannot read file"):
        parse_dotenv_file(tmp_path / "nonexistent.env")


def test_error_message_includes_filepath():
    with pytest.raises(DotEnvParseError, match="myfile.env:2"):
        parse_dotenv("GOOD=ok\nBAD LINE\n", filepath="myfile.env")
