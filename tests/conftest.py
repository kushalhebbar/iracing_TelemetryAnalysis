"""Shared pytest fixtures for the iRacing telemetry test suite."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest


def _make_lap(lap_number: int, n_samples: int, start_time: float, coverage: float) -> pd.DataFrame:
    """Build a single synthetic lap of telemetry data.

    Args:
        lap_number: Value for the ``Lap`` column.
        n_samples: Number of rows in the lap.
        start_time: Session time (seconds) at the start of the lap.
        coverage: Fraction of the track the lap covers (0-1). Values below the
            completion threshold produce a "partial" lap.
    """
    dist = np.linspace(0.0, coverage, n_samples)
    # A simple speed profile: fast on straights, slower mid-lap (a "corner").
    speed = 60.0 + 20.0 * np.cos(dist * 2 * np.pi)  # m/s
    throttle = np.clip(0.5 + 0.5 * np.cos(dist * 2 * np.pi), 0, 1)
    brake = np.clip(0.5 - 0.5 * np.cos(dist * 2 * np.pi), 0, 1)
    gear = np.where(speed > 65, 4, 3)
    rpm = 6000 + speed * 20

    return pd.DataFrame(
        {
            "SessionTime": start_time + np.linspace(0, 90 + lap_number, n_samples),
            "Lap": lap_number,
            "LapDistPct": dist,
            "Speed": speed,
            "Throttle": throttle,
            "Brake": brake,
            "SteeringWheelAngle": 0.3 * np.sin(dist * 2 * np.pi),
            "Gear": gear,
            "RPM": rpm,
            "LatAccel": 1.5 * np.sin(dist * 2 * np.pi),
            "LongAccel": 0.5 * np.cos(dist * 2 * np.pi),
            "Lat": 45.6 + dist * 0.01,
            "Lon": 9.28 + dist * 0.01,
        }
    )


@pytest.fixture
def telemetry_df() -> pd.DataFrame:
    """Two complete laps plus one partial lap of synthetic telemetry."""
    laps = [
        _make_lap(1, n_samples=200, start_time=0.0, coverage=0.99),
        _make_lap(2, n_samples=200, start_time=100.0, coverage=0.99),
        _make_lap(3, n_samples=50, start_time=200.0, coverage=0.40),  # partial
    ]
    return pd.concat(laps, ignore_index=True)


@pytest.fixture
def complete_lap_df(telemetry_df: pd.DataFrame) -> pd.DataFrame:
    """A single complete lap (lap 1)."""
    return telemetry_df[telemetry_df["Lap"] == 1].reset_index(drop=True)


@pytest.fixture
def partial_lap_df(telemetry_df: pd.DataFrame) -> pd.DataFrame:
    """A single partial lap (lap 3)."""
    return telemetry_df[telemetry_df["Lap"] == 3].reset_index(drop=True)
