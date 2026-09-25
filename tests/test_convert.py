"""Tests for filename normalization and CSV conversion helpers."""

from __future__ import annotations

import pandas as pd

from iracing_telemetry.convert import _normalize_filename, _write_per_lap_csvs


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
