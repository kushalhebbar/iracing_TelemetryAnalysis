"""Tests for mini-sector timing and the theoretical best lap."""

from __future__ import annotations

import numpy as np
import pandas as pd

from iracing_telemetry.sectors import compute_sector_times, theoretical_best


def _make_lap(lap: int, sector_durations: list[float], start: float = 0.0) -> pd.DataFrame:
    """A lap whose interpolated sector times exactly match ``sector_durations``."""
    dist = np.linspace(0.0, 1.0, len(sector_durations) + 1)
    elapsed = np.concatenate([[0.0], np.cumsum(sector_durations)])
    return pd.DataFrame({"Lap": lap, "LapDistPct": dist, "SessionTime": start + elapsed})


class TestComputeSectorTimes:
    def test_shape_and_index(self):
        df = _make_lap(1, [2.0] * 10)
        result = compute_sector_times(df, [1], n_sectors=10)
        assert result.shape == (10, 1)
        assert result.index.name == "Sector"
        assert list(result.columns) == [1]

    def test_sector_times_match_input(self):
        durations = [1.0, 2.0, 3.0, 2.0, 1.0]
        df = _make_lap(1, durations)
        result = compute_sector_times(df, [1], n_sectors=5)
        np.testing.assert_allclose(result[1].to_numpy(), durations, atol=1e-6)

    def test_sector_sum_equals_lap_time(self):
        durations = [1.5] * 8
        df = _make_lap(1, durations)
        result = compute_sector_times(df, [1], n_sectors=8)
        assert abs(result[1].sum() - sum(durations)) < 1e-6


class TestTheoreticalBest:
    def test_stitches_fastest_sectors(self):
        lap1 = _make_lap(1, [1.0] + [2.0] * 9)  # fastest in sector 1
        lap2 = _make_lap(2, [2.0] * 9 + [1.0], start=100.0)  # fastest in sector 10
        df = pd.concat([lap1, lap2], ignore_index=True)

        sector_times = compute_sector_times(df, [1, 2], n_sectors=10)
        best = theoretical_best(sector_times)

        assert best is not None
        # 1 + 2*8 + 1 = 18, faster than either actual lap (19).
        assert abs(best.theoretical_best - 18.0) < 1e-6
        assert abs(best.actual_best_time - 19.0) < 1e-6
        assert abs(best.time_to_gain - 1.0) < 1e-6

    def test_best_sector_ownership(self):
        lap1 = _make_lap(1, [1.0] + [2.0] * 9)
        lap2 = _make_lap(2, [2.0] * 9 + [1.0], start=100.0)
        df = pd.concat([lap1, lap2], ignore_index=True)

        best = theoretical_best(compute_sector_times(df, [1, 2], n_sectors=10))
        assert int(best.best_sector_lap.loc[1]) == 1
        assert int(best.best_sector_lap.loc[10]) == 2

    def test_single_lap_theoretical_equals_actual(self):
        df = _make_lap(3, [2.0] * 10)
        best = theoretical_best(compute_sector_times(df, [3], n_sectors=10))
        assert best.time_to_gain == 0.0
        assert best.actual_best_lap == 3

    def test_empty_returns_none(self):
        empty = compute_sector_times(pd.DataFrame(columns=["Lap", "LapDistPct", "SessionTime"]), [])
        assert theoretical_best(empty) is None
