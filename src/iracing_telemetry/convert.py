from __future__ import annotations

import logging
import re
from pathlib import Path

import irsdk
import numpy as np
import pandas as pd

from .analysis import analyze_telemetry
from .metadata import read_session_metadata
from .utils import Units, is_lap_complete, load_config

logger = logging.getLogger("iracing_telemetry")

# Essential channels kept in the filtered CSV / per-lap files.
FILTERED_CHANNELS = [
    "SessionTime",
    "Lap",
    "LapDistPct",
    "Speed",
    "Throttle",
    "Brake",
    "SteeringWheelAngle",
    "Gear",
    "RPM",
    "LatAccel",
    "LongAccel",
    "Lat",  # GPS latitude for track map
    "Lon",  # GPS longitude for track map
]


def _normalize_filename(ibt_filename: str) -> str:
    """Extract track name and date from an .ibt filename, dropping car and time.

    Example:
        'porsche992rgt3_monza full 2026-02-18 20-06-55.ibt'
        -> 'monza_full_2026-02-18'
    """
    base_name = ibt_filename.replace(".ibt", "")

    # Drop the leading car name (everything up to the first underscore).
    match = re.match(r"^[^_]+_(.+)$", base_name)
    extracted = match.group(1) if match else base_name

    normalized = extracted.replace(" ", "_")

    # Strip the trailing time portion, keeping up to the YYYY-MM-DD date.
    normalized = re.sub(r"_\d{2}-\d{2}-\d{2}$", "", normalized)
    normalized = re.sub(r"_\d{6}$", "", normalized)

    return normalized


def _read_ibt(input_path: Path) -> pd.DataFrame:
    """Read every telemetry channel from an .ibt file into a DataFrame."""
    ibt = irsdk.IBT()
    ibt.open(str(input_path))
    try:
        data: dict[str, list] = {}
        for channel in ibt.var_headers_names:
            try:
                values = ibt.get_all(channel)
            except Exception as exc:  # noqa: BLE001 - skip unreadable channels
                logger.warning("Could not read channel '%s': %s", channel, exc)
                continue

            # Collapse array channels (e.g. LatAccel) to their mean value.
            if len(values) > 0 and isinstance(values[0], list | np.ndarray):
                values = [
                    np.mean(v) if isinstance(v, list | np.ndarray) else v
                    for v in values
                ]
            data[channel] = values
        return pd.DataFrame(data)
    finally:
        ibt.close()


def filter_channels(df: pd.DataFrame) -> pd.DataFrame:
    """Keep the essential channels, tolerating a LapDist fallback."""
    available_channels = []
    for channel in FILTERED_CHANNELS:
        if channel in df.columns:
            available_channels.append(channel)
        elif channel == "LapDistPct" and "LapDist" in df.columns:
            available_channels.append("LapDist")
            logger.info("Using 'LapDist' instead of 'LapDistPct'")
    return df[available_channels]


def load_filtered_frame(input_path: Path) -> pd.DataFrame:
    """Read an .ibt file and return the filtered telemetry frame (writes nothing)."""
    return filter_channels(_read_ibt(input_path))


def convert_ibt_to_csv(
    input_path: Path,
    output_dir: Path | None = None,
    generate_plots: bool = True,
    units: Units = "mph",
) -> None:
    """Convert an iRacing .ibt file to CSVs and, optionally, an analysis report.

    Writes a full CSV, a filtered CSV, and one CSV per complete lap. When
    generate_plots is set, it also produces the interactive HTML report and a
    markdown summary.

    Args:
        input_path: Path to the .ibt file.
        output_dir: Base directory for output. CSVs go to <output_dir>/csv_output
            and plots to <output_dir>/plots. Defaults to the current directory.
        generate_plots: Run the analysis and produce plots/report.
        units: Speed units for the report and plots ("mph" or "kph").
    """
    base_name = _normalize_filename(input_path.name)

    metadata = read_session_metadata(input_path)
    if metadata.track_display_name or metadata.car:
        logger.info("Session: %s | %s", metadata.track_label, metadata.car or "unknown car")

    base_dir = output_dir if output_dir is not None else Path.cwd()
    csv_dir = base_dir / "csv_output"
    plots_dir = base_dir / "plots"
    csv_dir.mkdir(parents=True, exist_ok=True)

    full_output = csv_dir / f"{base_name}.csv"

    df = _read_ibt(input_path)
    df.to_csv(full_output, index=False)
    logger.info("Full CSV written: %s", full_output.name)

    df_filtered = filter_channels(df)
    filtered_output = full_output.with_stem(f"{full_output.stem}_filtered")
    df_filtered.to_csv(filtered_output, index=False)
    logger.info("Filtered CSV written: %s", filtered_output.name)

    _write_per_lap_csvs(df_filtered, full_output)

    if not generate_plots:
        logger.info("Skipping plot generation (--no-plots)")
        logger.info("Conversion complete: %s", base_name)
        return

    try:
        analyze_telemetry(
            filtered_output, base_name, plots_dir=plots_dir, units=units, metadata=metadata
        )
        logger.info("Conversion complete: %s", base_name)
    except Exception:
        logger.exception("Analysis failed for %s", base_name)
        raise


def _write_per_lap_csvs(df_filtered: pd.DataFrame, full_output: Path) -> None:
    """Write one CSV per complete lap next to the filtered output."""
    if "Lap" not in df_filtered.columns:
        return

    config = load_config()
    min_lap_samples = config["lap_validation"]["min_lap_samples"]

    for lap_num in sorted(df_filtered["Lap"].unique()):
        lap_df = df_filtered[df_filtered["Lap"] == lap_num]

        if not is_lap_complete(lap_df):
            if len(lap_df) < min_lap_samples:
                logger.debug(
                    "Lap %d skipped (%d rows - insufficient data)",
                    int(lap_num),
                    len(lap_df),
                )
            else:
                coverage = (
                    lap_df["LapDistPct"].max() - lap_df["LapDistPct"].min()
                ) * 100
                logger.debug(
                    "Lap %d skipped (partial lap - %.0f%% coverage)",
                    int(lap_num),
                    coverage,
                )
            continue

        lap_output = full_output.with_stem(f"{full_output.stem}_lap{int(lap_num)}")
        lap_df.to_csv(lap_output, index=False)
        logger.debug("Lap %d written: %s (%d rows)", int(lap_num), lap_output.name, len(lap_df))


def iter_ibt_files(path: Path) -> list[Path]:
    """Resolve a path to the .ibt files it refers to (a single file or a folder)."""
    if path.is_dir():
        return sorted(path.glob("*.ibt"))
    return [path]


def convert_batch(
    paths: list[Path],
    output_dir: Path | None = None,
    generate_plots: bool = True,
    units: Units = "mph",
) -> dict[Path, Exception | None]:
    """Convert several .ibt files, keeping going if one fails.

    Returns a mapping of each input path to ``None`` on success or the raised
    exception on failure.
    """
    results: dict[Path, Exception | None] = {}
    for path in paths:
        try:
            convert_ibt_to_csv(path, output_dir, generate_plots, units)
            results[path] = None
        except Exception as exc:  # noqa: BLE001 - record and continue with the rest
            logger.exception("Failed to convert %s", path.name)
            results[path] = exc
    return results
