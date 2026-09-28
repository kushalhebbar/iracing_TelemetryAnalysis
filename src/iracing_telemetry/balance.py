"""Understeer / oversteer balance estimation.

This is a heuristic, not a physics model. In cornering, we compare how much
steering the driver is holding against how much lateral grip the car is actually
producing. Both are normalised to their per-lap maxima, and the difference

    balance = |steering| / max|steering|  -  |LatAccel| / max|LatAccel|

is read as: positive means more steering than the car's rotation is rewarding
(understeer tendency), negative means the car rotates more than the steering
input implies (oversteer tendency). It is a relative indicator for spotting
where a lap leans one way or the other, not an absolute understeer gradient.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from iracing_telemetry.utils import load_config

REQUIRED_COLUMNS = ("SteeringWheelAngle", "LatAccel")


@dataclass(frozen=True)
class LapBalance:
    lap: int
    balance_index: float  # mean balance over cornering samples
    understeer_pct: float  # % of cornering samples leaning understeer
    oversteer_pct: float  # % leaning oversteer
    tendency: str  # "Understeer" / "Oversteer" / "Neutral"


def _tendency(index: float, band: float) -> str:
    if index > band:
        return "Understeer"
    if index < -band:
        return "Oversteer"
    return "Neutral"


def _balance_series(lap_data: pd.DataFrame, latg_threshold: float) -> pd.Series:
    """Per-sample balance value, NaN outside cornering (or when data is flat)."""
    steer = lap_data["SteeringWheelAngle"].abs()
    latg = lap_data["LatAccel"].abs()
    if steer.max() == 0 or latg.max() == 0:
        return pd.Series(np.nan, index=lap_data.index)

    balance = steer / steer.max() - latg / latg.max()
    return balance.where(latg > latg_threshold)


def compute_lap_balance(
    lap_data: pd.DataFrame,
    lap: int,
    latg_threshold: float,
    neutral_band: float,
    sample_band: float,
) -> LapBalance:
    """Balance summary for a single lap."""
    balance = _balance_series(lap_data, latg_threshold).dropna()
    if balance.empty:
        return LapBalance(lap, 0.0, 0.0, 0.0, "Neutral")

    index = float(balance.mean())
    understeer_pct = float((balance > sample_band).mean() * 100)
    oversteer_pct = float((balance < -sample_band).mean() * 100)
    return LapBalance(lap, index, understeer_pct, oversteer_pct, _tendency(index, neutral_band))


def compute_balance(df: pd.DataFrame, valid_laps: list) -> list[LapBalance]:
    """Balance summary for every lap (empty if steering/lat-G is unavailable)."""
    if not all(col in df.columns for col in REQUIRED_COLUMNS):
        return []

    config = load_config()["balance"]
    results = []
    for lap in valid_laps:
        lap_data = df[df["Lap"] == lap].sort_values("LapDistPct")
        results.append(
            compute_lap_balance(
                lap_data,
                int(lap),
                config["latg_threshold"],
                config["neutral_band"],
                config["sample_band"],
            )
        )
    return results


def balance_trace(df: pd.DataFrame, lap: int, latg_threshold: float | None = None) -> pd.DataFrame:
    """Distance-vs-balance trace for one lap, for plotting (NaN outside corners)."""
    if latg_threshold is None:
        latg_threshold = load_config()["balance"]["latg_threshold"]
    lap_data = df[df["Lap"] == lap].sort_values("LapDistPct")
    return pd.DataFrame(
        {
            "LapDistPct": lap_data["LapDistPct"].to_numpy(),
            "Balance": _balance_series(lap_data, latg_threshold).to_numpy(),
        }
    )
