"""Tests for the command-line interface argument handling."""

from __future__ import annotations

import pytest

from iracing_telemetry.cli import main


def test_missing_file_exits_with_error(tmp_path):
    missing = tmp_path / "nope.ibt"
    with pytest.raises(SystemExit) as exc:
        main([str(missing)])
    assert exc.value.code == 2


def test_non_ibt_suffix_exits_with_error(tmp_path):
    not_ibt = tmp_path / "data.csv"
    not_ibt.write_text("x")
    with pytest.raises(SystemExit) as exc:
        main([str(not_ibt)])
    assert exc.value.code == 2


def test_empty_directory_exits_with_error(tmp_path):
    with pytest.raises(SystemExit) as exc:
        main([str(tmp_path)])
    assert exc.value.code == 2
