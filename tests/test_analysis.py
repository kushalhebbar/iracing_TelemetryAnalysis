"""Tests for the analysis report helpers."""

from __future__ import annotations

from iracing_telemetry.analysis import (
    _analyze_gear_shifts,
    _analyze_input_smoothness,
    _calculate_lap_statistics,
    _compare_laps,
    _consistency_analysis,
    _corner_analysis,
    _steering_analysis,
    _trail_braking_analysis,
)
from iracing_telemetry.utils import ms_to_mph


class TestCalculateLapStatistics:
    def test_excludes_short_laps(self, telemetry_df):
        # Lap 3 has too few samples and should not appear.
        stats = _calculate_lap_statistics(telemetry_df)
        assert sorted(stats["Lap"].tolist()) == [1, 2]

    def test_marks_single_fastest_lap(self, telemetry_df):
        stats = _calculate_lap_statistics(telemetry_df)
        assert stats["is_fastest"].sum() == 1
        fastest_lap = int(stats.loc[stats["is_fastest"], "Lap"].iloc[0])
        assert fastest_lap == 1

    def test_speed_is_converted_to_mph(self, telemetry_df):
        stats = _calculate_lap_statistics(telemetry_df)
        # Peak synthetic speed is ~80 m/s -> ~179 mph.
        assert stats["MaxSpeed"].max() > 80 * ms_to_mph() - 1

    def test_complete_laps_not_partial(self, telemetry_df):
        stats = _calculate_lap_statistics(telemetry_df)
        assert not stats["IsPartial"].any()


class TestAnalyzeGearShifts:
    def test_reports_shift_counts_when_rpm_present(self, telemetry_df):
        lines = _analyze_gear_shifts(telemetry_df)
        text = "\n".join(lines)
        assert "Gear Shift Analysis" in text
        assert "Total upshifts" in text

    def test_warns_when_rpm_missing(self, telemetry_df):
        df = telemetry_df.drop(columns=["RPM"])
        lines = _analyze_gear_shifts(df)
        text = "\n".join(lines)
        assert "RPM data not available" in text


class TestReportSections:
    def test_input_smoothness_has_row_per_lap(self, telemetry_df):
        lines = _analyze_input_smoothness(telemetry_df, [1, 2])
        text = "\n".join(lines)
        assert "Input Smoothness Analysis" in text
        # Table header + separator + one row per lap.
        assert text.count("| 1 |") == 1
        assert text.count("| 2 |") == 1

    def test_compare_laps_reports_delta(self, telemetry_df):
        stats = _calculate_lap_statistics(telemetry_df)
        lines = _compare_laps(telemetry_df, stats, [1, 2], plots_dir=None, base_name="s")
        text = "\n".join(lines)
        assert "Fastest Lap Analysis" in text
        assert "faster" in text

    def test_compare_laps_needs_two_complete_laps(self, telemetry_df):
        stats = _calculate_lap_statistics(telemetry_df)
        one_lap = stats[stats["Lap"] == 1]
        lines = _compare_laps(telemetry_df, one_lap, [1], plots_dir=None, base_name="s")
        assert "Not enough complete laps" in "\n".join(lines)

    def test_corner_analysis_detects_corners(self, telemetry_df):
        lines = _corner_analysis(telemetry_df, [1, 2])
        assert "Corner-by-Corner Breakdown" in "\n".join(lines)

    def test_consistency_reports_score(self, telemetry_df):
        lines = _consistency_analysis(telemetry_df, [1, 2])
        text = "\n".join(lines)
        assert "Consistency Score" in text

    def test_steering_analysis_has_table(self, telemetry_df):
        lines = _steering_analysis(telemetry_df, [1, 2])
        assert "Steering Analysis" in "\n".join(lines)

    def test_steering_missing_column(self, telemetry_df):
        df = telemetry_df.drop(columns=["SteeringWheelAngle"])
        lines = _steering_analysis(df, [1, 2])
        assert "Steering data not available" in "\n".join(lines)

    def test_trail_braking_reports_percentage(self, telemetry_df):
        lines = _trail_braking_analysis(telemetry_df, [1, 2])
        assert "Trail Braking Analysis" in "\n".join(lines)
