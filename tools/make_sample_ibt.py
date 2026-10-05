"""Generate a small, synthetic multi-lap .ibt file for the demo.

It reuses the shape of a real recorded lap (speed profile, racing line, inputs)
as a template, then synthesises several laps with slightly different pacing so
the multi-lap features - delta time, sector comparison, theoretical best,
consistency - have something to chew on. The output is a compact, self-contained
.ibt that the app and the CLI read through the normal pipeline.

Usage:
    poetry run python tools/make_sample_ibt.py
"""

from __future__ import annotations

import struct
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from iracing_telemetry import get_valid_laps, load_filtered_frame  # noqa: E402

# (channel name, struct char, iRacing type index, unit)
CHANNELS: list[tuple[str, str, int, str]] = [
    ("SessionTime", "d", 5, "s"),
    ("Lap", "i", 2, ""),
    ("LapDistPct", "f", 4, "%"),
    ("Speed", "f", 4, "m/s"),
    ("Throttle", "f", 4, "%"),
    ("Brake", "f", 4, "%"),
    ("SteeringWheelAngle", "f", 4, "rad"),
    ("Gear", "i", 2, ""),
    ("RPM", "f", 4, "revs/min"),
    ("LatAccel", "f", 4, "m/s^2"),
    ("LongAccel", "f", 4, "m/s^2"),
    ("Lat", "d", 5, "deg"),
    ("Lon", "d", 5, "deg"),
]

SIZE = {"c": 1, "?": 1, "i": 4, "I": 4, "f": 4, "d": 8}

SESSION_YAML = """---
WeekendInfo:
 TrackName: monza full
 TrackID: 239
 TrackLength: 5.7508 km
 TrackDisplayName: Autodromo Nazionale Monza
 TrackConfigName:
 TrackCity: Monza
 TrackCountry: Italy
 TrackNumTurns: 11
DriverInfo:
 DriverCarIdx: 0
 Drivers:
 - CarIdx: 0
   UserName: Kushal Hebbar
   CarScreenName: Porsche 911 GT3 R (992)
...
"""


def _synthesise(df_real: pd.DataFrame, n_per_lap: int = 6000, n_laps: int = 4) -> pd.DataFrame:
    """Build an n_laps synthetic session from the first complete real lap."""
    template = df_real[df_real["Lap"] == get_valid_laps(df_real)[0]].sort_values("LapDistPct")
    grid = np.linspace(template["LapDistPct"].min(), template["LapDistPct"].max(), n_per_lap)

    def interp(col: str) -> np.ndarray:
        return np.interp(grid, template["LapDistPct"], template[col])

    base = {col: interp(col) for col in df_real.columns if col not in ("Lap",)}
    elapsed_template = interp("SessionTime") - float(template["SessionTime"].min())
    base_lap_time = float(elapsed_template[-1])
    d_template = np.gradient(elapsed_template, grid)

    rng = np.random.default_rng(7)
    # Each lap is a touch quicker/slower overall, and fast in different places.
    overall = [1.006, 1.000, 1.010, 1.003]
    frames = []
    t_offset = 0.0
    for lap_idx in range(n_laps):
        redistribute = 0.004 * base_lap_time * np.sin(2 * np.pi * grid + lap_idx * np.pi / 2)
        elapsed = elapsed_template * overall[lap_idx % len(overall)]
        elapsed = elapsed + (redistribute - redistribute[0])
        elapsed = np.maximum.accumulate(elapsed)

        pace = d_template / np.where(np.gradient(elapsed, grid) == 0, 1e-9, np.gradient(elapsed, grid))
        frames.append(
            pd.DataFrame(
                {
                    "SessionTime": t_offset + elapsed,
                    "Lap": lap_idx + 1,
                    "LapDistPct": grid,
                    "Speed": base["Speed"] * pace,
                    "Throttle": np.clip(base["Throttle"] + rng.normal(0, 0.003, n_per_lap), 0, 1),
                    "Brake": np.clip(base["Brake"] + rng.normal(0, 0.003, n_per_lap), 0, 1),
                    "SteeringWheelAngle": base["SteeringWheelAngle"] + rng.normal(0, 0.003, n_per_lap),
                    "Gear": np.round(base["Gear"]).astype(int),
                    "RPM": base["RPM"] * pace,
                    "LatAccel": base["LatAccel"],
                    "LongAccel": base["LongAccel"],
                    "Lat": base["Lat"] + 1e-5 * lap_idx,
                    "Lon": base["Lon"] + 1e-5 * lap_idx,
                }
            )
        )
        t_offset += float(elapsed[-1]) + 1.0

    return pd.concat(frames, ignore_index=True)


def write_ibt(path: Path, df: pd.DataFrame, session_yaml: str, tick_rate: int = 60) -> None:
    """Pack a DataFrame of the demo channels into a minimal, valid .ibt file."""
    layout = []
    record_offset = 0
    for name, char, type_idx, unit in CHANNELS:
        layout.append((name, char, type_idx, unit, record_offset))
        record_offset += SIZE[char]
    buf_len = record_offset
    num_vars = len(CHANNELS)

    var_header_offset = 144
    session_info_offset = var_header_offset + num_vars * 144
    yaml_bytes = session_yaml.encode("latin-1")
    buf_offset = session_info_offset + len(yaml_bytes)
    n_records = len(df)

    data = bytearray(buf_offset + n_records * buf_len)

    # Header
    struct.pack_into("<iii", data, 0, 2, 1, tick_rate)  # version, status, tick_rate
    struct.pack_into("<iii", data, 12, 0, len(yaml_bytes), session_info_offset)
    struct.pack_into("<ii", data, 24, num_vars, var_header_offset)
    struct.pack_into("<ii", data, 32, 1, buf_len)  # num_buf, buf_len
    struct.pack_into("<ii", data, 48, n_records, buf_offset)  # VarBuffer[0]

    # DiskSubHeader at 112
    struct.pack_into(
        "<Qddii", data, 112, 0, 0.0, float(df["SessionTime"].max()), int(df["Lap"].max()), n_records
    )

    # Variable headers
    for i, (name, _char, type_idx, unit, rec_off) in enumerate(layout):
        base = var_header_offset + i * 144
        struct.pack_into("<iii?", data, base, type_idx, rec_off, 1, False)
        struct.pack_into("<32s", data, base + 16, name.encode("latin-1"))
        struct.pack_into("<32s", data, base + 112, unit.encode("latin-1"))

    # Session info YAML
    data[session_info_offset : session_info_offset + len(yaml_bytes)] = yaml_bytes

    # Telemetry records
    for row_idx in range(n_records):
        row = df.iloc[row_idx]
        record = buf_offset + row_idx * buf_len
        for name, char, _type_idx, _unit, rec_off in layout:
            value = int(round(row[name])) if char in ("i", "I") else float(row[name])
            struct.pack_into("<" + char, data, record + rec_off, value)

    path.write_bytes(data)


def main() -> None:
    source = next((ROOT / "ibt_input").glob("*.ibt"), None)
    if source is None:
        raise SystemExit("No source .ibt found in ibt_input/ to use as a template.")

    df_real = load_filtered_frame(source)
    synthetic = _synthesise(df_real)

    out_dir = ROOT / "examples" / "samples"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "monza_demo_4laps.ibt"
    write_ibt(out_path, synthetic, SESSION_YAML)

    size_kb = out_path.stat().st_size / 1024
    print(f"Wrote {out_path.relative_to(ROOT)} ({size_kb:.0f} KB, {len(synthetic)} records)")


if __name__ == "__main__":
    main()
