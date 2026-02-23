from __future__ import annotations

import re
from pathlib import Path

import irsdk
import pandas as pd

from .analysis import analyze_telemetry
from .utils import is_lap_complete, load_config


def _normalize_filename(ibt_filename: str) -> str:
    """Extract track name and date from .ibt filename, removing car name and time.
    
    Example:
        'porsche992rgt3_monza full 2026-02-18 20-06-55.ibt' 
        -> 'monza_full_2026-02-18'
    """
    # Remove the .ibt extension
    base_name = ibt_filename.replace('.ibt', '')
    
    # Try to find the pattern: carname_trackname date time
    # Look for underscore followed by track name (letters/spaces) and date pattern
    match = re.match(r'^[^_]+_(.+)$', base_name)
    
    if match:
        extracted = match.group(1)
    else:
        extracted = base_name
    
    # Replace spaces with underscores
    normalized = extracted.replace(' ', '_')
    
    # Remove time portion: strip anything after the date pattern (YYYY-MM-DD)
    # Pattern: keep everything up to and including YYYY-MM-DD, remove HH-MM-SS or _HHMMSS
    normalized = re.sub(r'_\d{2}-\d{2}-\d{2}$', '', normalized)
    normalized = re.sub(r'_\d{6}$', '', normalized)
    
    return normalized


def convert_ibt_to_csv(input_path: Path, output_path: Path | None = None) -> None:
    """Convert an iRacing `.ibt` telemetry file to CSV files.

    Generates:
    - Full CSV with all telemetry channels
    - Filtered CSV with essential channels
    - Per-lap CSV files (filtered data only)

    All outputs are saved to csv_output/ directory in the workspace root.

    Args:
        input_path: Path to the .ibt file
        output_path: Optional custom output path (auto-generated if None)
    """
    # Generate standardized output name
    base_name = _normalize_filename(input_path.name)
    
    # Create csv_output directory at workspace root (not relative to input file)
    # Navigate up from src/iracing_telemetry/ to workspace root
    workspace_root = Path.cwd()
    output_dir = workspace_root / "csv_output"
    output_dir.mkdir(exist_ok=True)
    
    if output_path is None:
        output_path = output_dir / f"{base_name}.csv"
    
    # Open the IBT file
    ibt = irsdk.IBT()
    ibt.open(str(input_path))

    # Get all available telemetry channels
    channels = ibt.var_headers_names

    # Build a dictionary of {channel_name: [values]}
    data = {}
    for channel in channels:
        try:
            values = ibt.get_all(channel)
            data[channel] = values
        except Exception as e:
            # Skip channels that can't be read
            print(f"Warning: Could not read channel '{channel}': {e}")
            continue

    # Create DataFrame and export full CSV
    df = pd.DataFrame(data)
    df.to_csv(output_path, index=False)

    ibt.close()

    print(f"✓ Full CSV: {output_path.name}")
    print(f"  Rows: {len(df):,} | Columns: {len(df.columns)}")

    # Define essential channels for filtered output
    desired_channels = [
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

    # Handle LapDistPct/LapDist fallback
    available_channels = []
    for channel in desired_channels:
        if channel in df.columns:
            available_channels.append(channel)
        elif channel == "LapDistPct" and "LapDist" in df.columns:
            available_channels.append("LapDist")
            print(f"  Note: Using 'LapDist' instead of 'LapDistPct'")

    # Create filtered DataFrame
    df_filtered = df[available_channels]

    # Save filtered CSV
    filtered_output = output_path.with_stem(f"{output_path.stem}_filtered")
    df_filtered.to_csv(filtered_output, index=False)

    print(f"\n✓ Filtered CSV: {filtered_output.name}")
    print(f"  Rows: {len(df_filtered):,} | Columns: {len(df_filtered.columns)}")

    # Generate per-lap CSV files (only for complete laps)
    if "Lap" in df_filtered.columns:
        unique_laps = sorted(df_filtered["Lap"].unique())
        print(f"\n✓ Per-lap CSVs:")
        
        config = load_config()
        min_lap_samples = config['lap_validation']['min_lap_samples']
        
        for lap_num in unique_laps:
            lap_df = df_filtered[df_filtered["Lap"] == lap_num]
            
            # Skip laps with insufficient data or incomplete coverage
            if not is_lap_complete(lap_df):
                if len(lap_df) < min_lap_samples:
                    print(f"  Lap {int(lap_num)}: Skipped ({len(lap_df):,} rows - insufficient data)")
                else:
                    lap_dist_range = lap_df['LapDistPct'].max() - lap_df['LapDistPct'].min()
                    coverage_pct = lap_dist_range * 100
                    print(f"  Lap {int(lap_num)}: Skipped (partial lap - {coverage_pct:.0f}% coverage)")
                continue
            
            lap_output = output_path.with_stem(f"{output_path.stem}_lap{int(lap_num)}")
            lap_df.to_csv(lap_output, index=False)
            print(f"  Lap {int(lap_num)}: {lap_output.name} ({len(lap_df):,} rows)")
    else:
        print("\n⚠ Warning: 'Lap' column not found, skipping per-lap CSV generation")
    
    # Perform telemetry analysis
    try:
        analyze_telemetry(filtered_output, base_name)
    except Exception as e:
        print(f"\n⚠ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
