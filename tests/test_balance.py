"""Tests for the understeer / oversteer balance heuristic."""

from __future__ import annotations

import numpy as np
import pandas as pd

from iracing_telemetry.balance import (
    balance_trace,
    compute_balance,
    compute_lap_balance,
)


def _lap(steer: list[float], latg: list[float], lap: int = 1) -> pd.DataFrame:
    n = len(steer)
    return pd.DataFrame(
        {
            "Lap": lap,
            "LapDistPct": np.linspace(0.0, 1.0, n),
            "SteeringWheelAngle": steer,
            "LatAccel": latg,
        }
    )


# Fixed thresholds so the tests do not depend on constants.json.
THRESH, NEUTRAL, SAMPLE = 10.0, 0.05, 0.1


class TestComputeLapBalance:
    def test_understeer(self):
        # Lots of steering, comparatively little lateral grip.
        lap = _lap([1, 1, 1, 1], [20, 11, 11, 11])
        result = compute_lap_balance(lap, 1, THRESH, NEUTRAL, SAMPLE)
        assert result.tendency == "Understeer"
        assert result.balance_index > 0

    def test_oversteer(self):
        # High lateral grip with little steering held.
        lap = _lap([0.5, 0.2, 0.2, 0.2], [20, 20, 20, 20])
        result = compute_lap_balance(lap, 1, THRESH, NEUTRAL, SAMPLE)
        assert result.tendency == "Oversteer"
        assert result.balance_index < 0

    def test_neutral_when_proportional(self):
        lap = _lap([1.0, 0.55, 0.75], [20.0, 11.0, 15.0])
        result = compute_lap_balance(lap, 1, THRESH, NEUTRAL, SAMPLE)
        assert result.tendency == "Neutral"

    def test_no_cornering_is_neutral(self):
        # All below the lateral-G threshold -> nothing to judge.
        lap = _lap([1, 1, 1], [1, 2, 3])
        result = compute_lap_balance(lap, 7, THRESH, NEUTRAL, SAMPLE)
        assert result.tendency == "Neutral"
        assert result.lap == 7


class TestComputeBalance:
    def test_missing_columns_returns_empty(self):
        df = pd.DataFrame({"Lap": [1], "LapDistPct": [0.0], "Speed": [10.0]})
        assert compute_balance(df, [1]) == []

    def test_one_result_per_lap(self, telemetry_df):
        results = compute_balance(telemetry_df, [1, 2])
        assert [b.lap for b in results] == [1, 2]


class TestBalanceTrace:
    def test_nan_outside_cornering(self):
        lap = _lap([1, 1, 1, 1], [30, 2, 30, 2])
        trace = balance_trace(lap, 1, latg_threshold=10.0)
        # Samples 2 and 4 are below threshold -> NaN.
        assert np.isnan(trace["Balance"].to_numpy()[1])
        assert not np.isnan(trace["Balance"].to_numpy()[0])
