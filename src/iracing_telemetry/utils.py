"""Utility functions shared across analysis modules."""

from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Literal

import pandas as pd

logger = logging.getLogger("iracing_telemetry")

Units = Literal["mph", "kph"]


@lru_cache(maxsize=1)
def load_config() -> dict:
    """Load the tuning constants from constants.json (read once, then cached)."""
    config_path = Path(__file__).parent / "constants.json"
    with open(config_path, encoding="utf-8") as f:
        return json.load(f)


def speed_factor(units: Units = "mph") -> float:
    """m/s conversion factor for the requested speed units."""
    key = "ms_to_kph" if units == "kph" else "ms_to_mph"
    return load_config()["speed_conversion"][key]


def speed_label(units: Units = "mph") -> str:
    """Axis/legend label for the requested speed units."""
    return "kph" if units == "kph" else "mph"


def ms_to_mph() -> float:
    """m/s to mph conversion factor."""
    return speed_factor("mph")


def convert_speed(df: pd.DataFrame, units: Units = "mph") -> pd.DataFrame:
    """Return a copy of df with Speed converted from m/s to the given units."""
    df_copy = df.copy()
    df_copy["Speed"] = df_copy["Speed"] * speed_factor(units)
    return df_copy


def convert_speed_to_mph(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of df with the Speed column converted from m/s to mph."""
    return convert_speed(df, "mph")


def is_lap_complete(lap_data: pd.DataFrame) -> bool:
    """True if the lap has enough samples and covers most of the track."""
    config = load_config()
    if len(lap_data) < config["lap_validation"]["min_lap_samples"]:
        return False

    lap_dist_range = lap_data["LapDistPct"].max() - lap_data["LapDistPct"].min()
    return bool(lap_dist_range >= config["lap_validation"]["completion_threshold"])


def get_valid_laps(df: pd.DataFrame) -> list[int]:
    """Sorted lap numbers that pass the completeness check."""
    valid_laps: list[int] = []
    for lap in sorted(df["Lap"].unique()):
        lap_data = df[df["Lap"] == lap]
        if is_lap_complete(lap_data):
            valid_laps.append(int(lap))
    return valid_laps


def format_lap_time(seconds: float) -> str:
    """Format seconds as M:SS.sss (e.g. 95.12 -> '1:35.120')."""
    minutes = int(seconds // 60)
    remaining_seconds = seconds % 60
    return f"{minutes}:{remaining_seconds:06.3f}"


def rate_smoothness(
    variation: float, smooth_threshold: float, fair_threshold: float
) -> str:
    """Bucket an input-variation value into Smooth / Fair / Rough."""
    if variation < smooth_threshold:
        return "Smooth"
    if variation < fair_threshold:
        return "Fair"
    return "Rough"
