"""Round-trip test for the synthetic .ibt writer in tools/make_sample_ibt.py."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import irsdk
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location(
    "make_sample_ibt", ROOT / "tools" / "make_sample_ibt.py"
)
make_sample_ibt = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(make_sample_ibt)


def _tiny_frame(rows: int = 4) -> pd.DataFrame:
    dist = np.linspace(0.0, 1.0, rows)
    return pd.DataFrame(
        {
            "SessionTime": np.linspace(0.0, 10.0, rows),
            "Lap": [1] * rows,
            "LapDistPct": dist,
            "Speed": np.linspace(40.0, 80.0, rows),
            "Throttle": np.linspace(0.0, 1.0, rows),
            "Brake": np.linspace(1.0, 0.0, rows),
            "SteeringWheelAngle": np.linspace(-0.5, 0.5, rows),
            "Gear": [3, 4, 4, 5],
            "RPM": np.linspace(6000.0, 8000.0, rows),
            "LatAccel": np.linspace(-10.0, 10.0, rows),
            "LongAccel": np.linspace(-5.0, 5.0, rows),
            "Lat": np.linspace(45.61, 45.62, rows),
            "Lon": np.linspace(9.28, 9.29, rows),
        }
    )


def test_write_ibt_is_readable_by_irsdk(tmp_path):
    df = _tiny_frame()
    out = tmp_path / "roundtrip.ibt"
    make_sample_ibt.write_ibt(out, df, make_sample_ibt.SESSION_YAML)

    ibt = irsdk.IBT()
    ibt.open(str(out))
    try:
        assert ibt.var_headers_names[:3] == ["SessionTime", "Lap", "LapDistPct"]
        assert ibt.get_all("Lap") == [1, 1, 1, 1]
        # Doubles round-trip exactly; floats within float32 precision.
        np.testing.assert_allclose(ibt.get_all("SessionTime"), df["SessionTime"], rtol=1e-9)
        np.testing.assert_allclose(ibt.get_all("Speed"), df["Speed"], rtol=1e-5)
        np.testing.assert_allclose(ibt.get_all("Lon"), df["Lon"], rtol=1e-12)
    finally:
        ibt.close()


def test_written_file_flows_through_pipeline(tmp_path):
    from iracing_telemetry import get_valid_laps, load_filtered_frame, read_session_metadata

    df = make_sample_ibt._synthesise(_full_lap(), n_per_lap=300, n_laps=2)
    out = tmp_path / "session.ibt"
    make_sample_ibt.write_ibt(out, df, make_sample_ibt.SESSION_YAML)

    loaded = load_filtered_frame(out)
    assert get_valid_laps(loaded) == [1, 2]
    assert read_session_metadata(out).car == "Porsche 911 GT3 R (992)"


def _full_lap() -> pd.DataFrame:
    """A single dense lap the synthesiser can use as a template."""
    n = 400
    dist = np.linspace(0.0, 0.99, n)
    return pd.DataFrame(
        {
            "SessionTime": np.linspace(0.0, 108.0, n),
            "Lap": [1] * n,
            "LapDistPct": dist,
            "Speed": 40.0 + 30.0 * np.abs(np.cos(dist * 2 * np.pi)),
            "Throttle": np.clip(np.cos(dist * 2 * np.pi), 0, 1),
            "Brake": np.clip(-np.cos(dist * 2 * np.pi), 0, 1),
            "SteeringWheelAngle": 0.4 * np.sin(dist * 2 * np.pi),
            "Gear": np.full(n, 4),
            "RPM": 7000.0 + 1000.0 * np.cos(dist * 2 * np.pi),
            "LatAccel": 20.0 * np.sin(dist * 2 * np.pi),
            "LongAccel": 5.0 * np.cos(dist * 2 * np.pi),
            "Lat": 45.61 + dist * 0.01,
            "Lon": 9.28 + dist * 0.01,
        }
    )
