"""Tests for filename normalization and CSV conversion helpers."""

from __future__ import annotations

import pandas as pd

import iracing_telemetry.convert as convert_mod
from iracing_telemetry.convert import (
    _normalize_filename,
    _write_per_lap_csvs,
    convert_batch,
    iter_ibt_files,
)


class TestNormalizeFilename:
    def test_strips_car_and_time(self):
        name = "porsche992rgt3_monza full 2026-02-18 20-06-55.ibt"
        assert _normalize_filename(name) == "monza_full_2026-02-18"

    def test_without_car_prefix(self):
        assert _normalize_filename("monza 2026-02-18.ibt") == "monza_2026-02-18"

    def test_strips_compact_time_suffix(self):
        name = "car_spa 2026-01-01_123456.ibt"
        assert _normalize_filename(name) == "spa_2026-01-01"

    def test_handles_missing_extension_gracefully(self):
        # No .ibt still normalizes spaces.
        assert _normalize_filename("car_track name") == "track_name"


class TestWritePerLapCsvs:
    def test_writes_only_complete_laps(self, telemetry_df, tmp_path):
        full_output = tmp_path / "session.csv"
        _write_per_lap_csvs(telemetry_df, full_output)

        assert (tmp_path / "session_lap1.csv").exists()
        assert (tmp_path / "session_lap2.csv").exists()
        # Lap 3 is partial and must be skipped.
        assert not (tmp_path / "session_lap3.csv").exists()

    def test_no_lap_column_is_noop(self, tmp_path):
        df = pd.DataFrame({"Speed": [1, 2, 3]})
        _write_per_lap_csvs(df, tmp_path / "session.csv")
        assert list(tmp_path.iterdir()) == []


class TestIterIbtFiles:
    def test_single_file(self, tmp_path):
        f = tmp_path / "a.ibt"
        f.write_text("")
        assert iter_ibt_files(f) == [f]

    def test_directory_globs_sorted_ibt_only(self, tmp_path):
        (tmp_path / "b.ibt").write_text("")
        (tmp_path / "a.ibt").write_text("")
        (tmp_path / "notes.txt").write_text("")
        assert iter_ibt_files(tmp_path) == [tmp_path / "a.ibt", tmp_path / "b.ibt"]

    def test_empty_directory(self, tmp_path):
        assert iter_ibt_files(tmp_path) == []


class TestConvertBatch:
    def test_records_failures_and_continues(self, tmp_path, monkeypatch):
        good = tmp_path / "good.ibt"
        bad = tmp_path / "bad.ibt"

        def fake_convert(path, output_dir=None, generate_plots=True, units="mph"):
            if path.name == "bad.ibt":
                raise ValueError("boom")

        monkeypatch.setattr(convert_mod, "convert_ibt_to_csv", fake_convert)
        results = convert_batch([good, bad])

        assert results[good] is None
        assert isinstance(results[bad], ValueError)

