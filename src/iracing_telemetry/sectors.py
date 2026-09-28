"""Mini-sector timing and the theoretical best lap.

Each lap is split into a fixed number of equal-distance sectors. Comparing the
same sector across laps shows exactly where time is won or lost, and stitching
together the fastest version of every sector gives the "theoretical best" lap.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from iracing_telemetry.utils import load_config


def _sector_count(n_sectors: int | None) -> int:
    if n_sectors is not None:
        return n_sectors
    return int(load_config()["sectors"]["count"])


def compute_sector_times(
    df: pd.DataFrame, valid_laps: list, n_sectors: int | None = None
) -> pd.DataFrame:
    """Per-sector times for each lap.

    Returns a DataFrame indexed by sector number (1..N) with one column per lap
    (the column label is the lap number) and values in seconds.
    """
    count = _sector_count(n_sectors)
    boundaries = np.linspace(0.0, 1.0, count + 1)

    data: dict[int, np.ndarray] = {}
    for lap in valid_laps:
        lap_data = df[df["Lap"] == lap].sort_values("LapDistPct")
        dist = lap_data["LapDistPct"].to_numpy()
        elapsed = (lap_data["SessionTime"] - lap_data["SessionTime"].min()).to_numpy()
        # Interpolated elapsed time at each sector boundary, then the deltas.
        time_at_boundary = np.interp(boundaries, dist, elapsed)
        data[int(lap)] = np.diff(time_at_boundary)

    index = pd.Index(range(1, count + 1), name="Sector")
    return pd.DataFrame(data, index=index)


@dataclass(frozen=True)
class TheoreticalBest:
    best_sector_times: pd.Series  # fastest time per sector
    best_sector_lap: pd.Series  # lap that owns each sector's best
    theoretical_best: float  # sum of the best sectors
    actual_best_lap: int  # fastest complete lap
    actual_best_time: float  # its total time
    time_to_gain: float  # actual_best_time - theoretical_best


def theoretical_best(sector_times: pd.DataFrame) -> TheoreticalBest | None:
    """Stitch the fastest version of every sector into an ideal-lap summary."""
    if sector_times.empty:
        return None

    best_times = sector_times.min(axis=1)
    best_lap = sector_times.idxmin(axis=1)
    theo = float(best_times.sum())

    lap_totals = sector_times.sum(axis=0)
    best_pos = int(np.asarray(lap_totals).argmin())
    actual_best_lap = int(lap_totals.index[best_pos])
    actual_best_time = float(lap_totals.iloc[best_pos])

    return TheoreticalBest(
        best_sector_times=best_times,
        best_sector_lap=best_lap,
        theoretical_best=theo,
        actual_best_lap=actual_best_lap,
        actual_best_time=actual_best_time,
        time_to_gain=actual_best_time - theo,
    )
