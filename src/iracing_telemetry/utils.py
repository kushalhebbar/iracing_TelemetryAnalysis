"""Utility functions shared across analysis modules."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def load_config() -> dict:
    """Load constants from JSON file."""
    config_path = Path(__file__).parent / "constants.json"
    with open(config_path, 'r') as f:
        return json.load(f)


def convert_speed_to_mph(df: pd.DataFrame) -> pd.DataFrame:
    """Convert speed from m/s to mph. Returns a copy."""
    config = load_config()
    df_copy = df.copy()
    df_copy['Speed'] = df_copy['Speed'] * config['speed_conversion']['ms_to_mph']
    return df_copy


def is_lap_complete(lap_data: pd.DataFrame) -> bool:
    """Check if a lap has sufficient data and track coverage."""
    config = load_config()
    if len(lap_data) < config['lap_validation']['min_lap_samples']:
        return False
    
    lap_dist_range = lap_data['LapDistPct'].max() - lap_data['LapDistPct'].min()
    return lap_dist_range >= config['lap_validation']['completion_threshold']


def get_valid_laps(df: pd.DataFrame) -> list:
    """Get list of lap numbers with complete data."""
    valid_laps = []
    for lap in sorted(df['Lap'].unique()):
        lap_data = df[df['Lap'] == lap]
        if is_lap_complete(lap_data):
            valid_laps.append(lap)
    return valid_laps


def format_lap_time(seconds: float) -> str:
    """Format lap time as MM:SS.sss"""
    minutes = int(seconds // 60)
    remaining_seconds = seconds % 60
    return f"{minutes}:{remaining_seconds:06.3f}"


def rate_smoothness(variation: float, smooth_threshold: float, fair_threshold: float) -> str:
    """Rate input smoothness based on variation."""
    if variation < smooth_threshold:
        return "Smooth"
    elif variation < fair_threshold:
        return "Fair"
    else:
        return "Rough"
