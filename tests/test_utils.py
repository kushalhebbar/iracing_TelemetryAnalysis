"""Tests for pure utility helpers."""

from __future__ import annotations

import pandas as pd

from iracing_telemetry.utils import (
    convert_speed,
    convert_speed_to_mph,
    format_lap_time,
    get_valid_laps,
    is_lap_complete,
    load_config,
    ms_to_mph,
    rate_smoothness,
    speed_factor,
    speed_label,
)


class TestFormatLapTime:
    def test_formats_sub_minute(self):
        assert format_lap_time(45.678) == "0:45.678"

    def test_formats_minutes_and_seconds(self):
        assert format_lap_time(95.123) == "1:35.123"

    def test_pads_seconds(self):
        assert format_lap_time(61.5) == "1:01.500"

    def test_zero(self):
        assert format_lap_time(0) == "0:00.000"


class TestRateSmoothness:
    def test_smooth(self):
        assert rate_smoothness(0.01, 0.05, 0.10) == "Smooth"

    def test_fair(self):
        assert rate_smoothness(0.07, 0.05, 0.10) == "Fair"

    def test_rough(self):
        assert rate_smoothness(0.20, 0.05, 0.10) == "Rough"

    def test_boundary_is_exclusive(self):
        # Exactly at the smooth threshold is not "Smooth".
        assert rate_smoothness(0.05, 0.05, 0.10) == "Fair"


class TestConvertSpeed:
    def test_converts_and_returns_copy(self):
        df = pd.DataFrame({"Speed": [10.0, 20.0]})
        result = convert_speed_to_mph(df)
        assert result["Speed"].tolist() == [10.0 * ms_to_mph(), 20.0 * ms_to_mph()]
        # Original is untouched.
        assert df["Speed"].tolist() == [10.0, 20.0]


class TestUnits:
    def test_mph_factor(self):
        assert speed_factor("mph") == 2.237

    def test_kph_factor(self):
        assert speed_factor("kph") == 3.6

    def test_labels(self):
        assert speed_label("mph") == "mph"
        assert speed_label("kph") == "kph"

    def test_convert_speed_kph(self):
        df = pd.DataFrame({"Speed": [10.0]})
        assert convert_speed(df, "kph")["Speed"].iloc[0] == 36.0

    def test_convert_speed_defaults_to_mph(self):
        df = pd.DataFrame({"Speed": [10.0]})
        assert convert_speed(df)["Speed"].iloc[0] == 10.0 * 2.237


class TestLoadConfig:
    def test_returns_expected_keys(self):
        config = load_config()
        assert "speed_conversion" in config
        assert "lap_validation" in config

    def test_is_cached(self):
        assert load_config() is load_config()


class TestLapCompleteness:
    def test_complete_lap_is_complete(self, complete_lap_df):
        assert is_lap_complete(complete_lap_df) is True

    def test_partial_lap_is_incomplete(self, partial_lap_df):
        assert is_lap_complete(partial_lap_df) is False

    def test_valid_laps_excludes_partial(self, telemetry_df):
        assert get_valid_laps(telemetry_df) == [1, 2]
