from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from iracing_telemetry.balance import compute_balance
from iracing_telemetry.metadata import SessionMetadata
from iracing_telemetry.sectors import compute_sector_times, theoretical_best
from iracing_telemetry.utils import (
    Units,
    convert_speed,
    format_lap_time,
    get_valid_laps,
    load_config,
    rate_smoothness,
    speed_label,
)

logger = logging.getLogger("iracing_telemetry")


def analyze_telemetry(
    filtered_csv_path: Path,
    base_name: str,
    plots_dir: Path | None = None,
    units: Units = "mph",
    metadata: SessionMetadata | None = None,
) -> None:
    """Write the summary CSV and markdown report for a filtered CSV.

    Args:
        filtered_csv_path: Path to the filtered CSV file.
        base_name: Base name for output files (without extension).
        plots_dir: Where the markdown report goes (default ./plots). The summary
            CSV is written next to the input CSV.
        units: Speed units for the report ("mph" or "kph").
        metadata: Optional session metadata for the report header.
    """
    df = pd.read_csv(filtered_csv_path)

    if plots_dir is None:
        plots_dir = Path.cwd() / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)

    lap_stats = _calculate_lap_statistics(df, units)
    summary_path = filtered_csv_path.parent / f"{base_name}_summary.csv"
    lap_stats.to_csv(summary_path, index=False)

    report = build_report(df, base_name, units, metadata, lap_stats=lap_stats)
    report_path = plots_dir / "report.md"
    report_path.write_text(report, encoding="utf-8")
    logger.info("Report written: %s", report_path.name)


def build_report(
    df: pd.DataFrame,
    base_name: str = "session",
    units: Units = "mph",
    metadata: SessionMetadata | None = None,
    lap_stats: pd.DataFrame | None = None,
) -> str:
    """Return the full markdown analysis report for a filtered telemetry frame."""
    if lap_stats is None:
        lap_stats = _calculate_lap_statistics(df, units)
    slabel = speed_label(units)

    report_lines = ["# Telemetry Analysis Report"]
    report_lines.extend(_session_header(base_name, metadata))
    report_lines.append(
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    report_lines.append("\n---\n")

    report_lines.append("## Lap Times\n")
    lap_table = f"| Lap | Time | Avg Speed ({slabel}) | Max Speed ({slabel}) | Status |\n"
    lap_table += "|-----|------|-----------------|-----------------|--------|\n"
    for _, row in lap_stats.iterrows():
        minutes = int(row["LapTime"] // 60)
        seconds = row["LapTime"] % 60
        time_str = f"{minutes}:{seconds:06.3f}"

        status_md = ""
        if row.get("IsPartial", False):
            status_md = "Partial"
        elif row.get("is_fastest", False):
            status_md = "Fastest"

        lap_table += (
            f"| {int(row['Lap'])} | {time_str} | {row['AvgSpeed']:.1f} | "
            f"{row['MaxSpeed']:.1f} | {status_md} |\n"
        )
    report_lines.append(lap_table)

    report_lines.extend(_analyze_gear_shifts(df))

    valid_laps = get_valid_laps(df)
    if len(valid_laps) == 0:
        return "\n".join(report_lines)

    report_lines.extend(_analyze_input_smoothness(df, valid_laps))

    report_lines.extend(_sector_report(df, valid_laps))

    report_lines.extend(_balance_report(df, valid_laps))

    if len(valid_laps) >= 2:
        report_lines.extend(_compare_laps(df, lap_stats, valid_laps, units))

    report_lines.extend(_run_advanced_analysis(df, lap_stats, valid_laps, units))

    return "\n".join(report_lines)


def _balance_report(df: pd.DataFrame, valid_laps: list) -> list[str]:
    """Understeer / oversteer balance tendency per lap."""
    results = compute_balance(df, valid_laps)
    lines = ["\n## Balance (Understeer / Oversteer)\n"]
    if not results:
        lines.append("Steering or lateral-acceleration data not available.\n")
        return lines

    lines.append("| Lap | Balance index | Understeer % | Oversteer % | Tendency |")
    lines.append("|-----|---------------|--------------|-------------|----------|")
    for bal in results:
        lines.append(
            f"| {bal.lap} | {bal.balance_index:+.3f} | {bal.understeer_pct:.0f}% | "
            f"{bal.oversteer_pct:.0f}% | {bal.tendency} |"
        )
    lines.append("")
    lines.append(
        "Positive index leans understeer, negative leans oversteer. Heuristic from "
        "steering angle versus lateral grip in corners.\n"
    )
    return lines


def _sector_report(df: pd.DataFrame, valid_laps: list, n_sectors: int | None = None) -> list[str]:
    """Mini-sector times and the theoretical best lap."""
    sector_times = compute_sector_times(df, valid_laps, n_sectors)
    best = theoretical_best(sector_times)
    lines = [f"\n## Sector Analysis ({len(sector_times)} mini-sectors)\n"]
    if best is None:
        return lines

    lines.append(f"**Theoretical best lap:** {format_lap_time(best.theoretical_best)}")
    if len(valid_laps) >= 2 and best.time_to_gain > 0.0005:
        lines.append(
            f"That is **{best.time_to_gain:.3f}s** quicker than your best actual lap "
            f"(Lap {best.actual_best_lap}, {format_lap_time(best.actual_best_time)}).\n"
        )
    else:
        lines.append("")

    lines.append("| Sector | Best time (s) | From |")
    lines.append("|--------|---------------|------|")
    for sector in sector_times.index:
        lines.append(
            f"| {sector} | {best.best_sector_times[sector]:.3f} | "
            f"Lap {int(best.best_sector_lap[sector])} |"
        )
    lines.append("")
    return lines


def _session_header(base_name: str, metadata: SessionMetadata | None) -> list[str]:
    """Report header lines describing the session (track, car, driver)."""
    if metadata is None:
        return [f"\n**Session:** {base_name}"]

    lines = [f"\n**Track:** {metadata.track_label}"]
    if metadata.location:
        lines[0] += f"  —  {metadata.location}"
    if metadata.car:
        lines.append(f"**Car:** {metadata.car}")
    if metadata.driver:
        lines.append(f"**Driver:** {metadata.driver}")
    if metadata.num_turns:
        lines.append(f"**Turns:** {metadata.num_turns}")
    lines.append(f"**Session file:** {base_name}")
    return lines


def _calculate_lap_statistics(df: pd.DataFrame, units: Units = "mph") -> pd.DataFrame:
    """Calculate lap times and statistics for each lap."""
    stats = []

    df = convert_speed(df, units)

    config = load_config()
    min_lap_samples = config['lap_validation']['min_lap_samples']
    completion_threshold = config['lap_validation']['completion_threshold']
    
    for lap in sorted(df['Lap'].unique()):
        lap_data = df[df['Lap'] == lap]
        
        if len(lap_data) < min_lap_samples:
            continue
        
        # Check if lap is complete (should cover ~95%+ of track)
        lap_dist_range = lap_data['LapDistPct'].max() - lap_data['LapDistPct'].min()
        is_partial = lap_dist_range < (completion_threshold - 0.05)
        
        # Calculate lap time
        lap_time = lap_data['SessionTime'].max() - lap_data['SessionTime'].min()
        
        # Calculate speeds
        avg_speed = lap_data['Speed'].mean()
        max_speed = lap_data['Speed'].max()
        
        # Throttle/Brake usage
        avg_throttle = lap_data['Throttle'].mean() * 100
        avg_brake = lap_data['Brake'].mean() * 100
        
        # Count braking events (transitions from 0 to >0)
        brake_events = ((lap_data['Brake'].shift(1) == 0) & (lap_data['Brake'] > 0)).sum()
        
        stats.append({
            'Lap': int(lap),
            'LapTime': lap_time,
            'AvgSpeed': avg_speed,
            'MaxSpeed': max_speed,
            'AvgThrottle': avg_throttle,
            'AvgBrake': avg_brake,
            'BrakeEvents': brake_events,
            'IsPartial': is_partial,
        })
    
    stats_df = pd.DataFrame(stats)
    
    if len(stats_df) > 0:
        # Mark fastest lap (only among complete laps)
        complete_laps = stats_df[~stats_df['IsPartial']]
        if len(complete_laps) > 0:
            fastest_idx = complete_laps['LapTime'].idxmin()
            stats_df['is_fastest'] = False
            stats_df.loc[fastest_idx, 'is_fastest'] = True
        else:
            stats_df['is_fastest'] = False
    
    return stats_df


def _analyze_gear_shifts(df: pd.DataFrame) -> list[str]:
    """Summarise up/downshift counts and shift RPM by gear."""
    report_lines = ["\n## Gear Shift Analysis\n"]

    has_rpm = 'RPM' in df.columns

    if not has_rpm:
        report_lines.append("**RPM data not available** - add 'RPM' to the channels for shift analysis.\n")
        return report_lines
    
    # Detect gear shifts (where gear changes from one value to another)
    df_copy = df.copy()
    df_copy['GearShift'] = df_copy['Gear'] != df_copy['Gear'].shift(1)
    df_copy['UpShift'] = (df_copy['Gear'] > df_copy['Gear'].shift(1)) & df_copy['GearShift']
    df_copy['DownShift'] = (df_copy['Gear'] < df_copy['Gear'].shift(1)) & df_copy['GearShift']
    
    upshifts = df_copy[df_copy['UpShift']]
    downshifts = df_copy[df_copy['DownShift']]

    report_lines.append(f"**Total upshifts:** {len(upshifts)}")
    report_lines.append(f"**Total downshifts:** {len(downshifts)}\n")
    
    if has_rpm and len(upshifts) > 0:
        report_lines.append("### Upshift RPM by Gear\n")
        report_lines.append("| Upshift | Avg RPM | Min RPM | Max RPM |")
        report_lines.append("|---------|---------|---------|---------|")
        
        for gear in sorted(upshifts['Gear'].shift(1).dropna().unique()):
            gear_shifts = upshifts[upshifts['Gear'].shift(1) == gear]
            if len(gear_shifts) > 0:
                avg_rpm = gear_shifts['RPM'].mean()
                min_rpm = gear_shifts['RPM'].min()
                max_rpm = gear_shifts['RPM'].max()
                report_lines.append(f"| {int(gear)} → {int(gear+1)} | {avg_rpm:.0f} | {min_rpm:.0f} | {max_rpm:.0f} |")
        
        report_lines.append("")
        upshift_rpm = upshifts['RPM'].mean()
        upshift_std = upshifts['RPM'].std()
        
        config = load_config()
        gear_shift_config = config['gear_shift']
        
        report_lines.append(f"Average upshift RPM: {upshift_rpm:.0f} ± {upshift_std:.0f}\n")
        
        if upshift_std > gear_shift_config['variance_high']:
            feedback = f"High variance in shift RPM. Target: <{gear_shift_config['variance_moderate']} RPM variation per gear."
        elif upshift_std > gear_shift_config['variance_moderate']:
            feedback = "Moderate shift RPM variance."
        else:
            feedback = "Consistent shift points."
        
        report_lines.append(f"{feedback}\n")

    return report_lines


def _analyze_input_smoothness(df: pd.DataFrame, valid_laps: list) -> list[str]:
    """Rate per-lap throttle and brake input smoothness."""
    report_lines = ["\n## Input Smoothness Analysis\n"]
    
    config = load_config()
    smoothness_config = config['input_smoothness']

    report_lines.append("| Lap | Throttle Smoothness | Throttle Variation | Brake Smoothness | Brake Variation |")
    report_lines.append("|-----|---------------------|--------------------|--------------------|-----------------|")
    
    for lap in valid_laps:
        lap_data = df[df['Lap'] == lap].sort_values('LapDistPct')
        
        # Calculate throttle smoothness (lower variation = smoother)
        throttle_changes = lap_data['Throttle'].diff().abs()
        throttle_variation = throttle_changes.std()

        # Calculate brake smoothness
        brake_changes = lap_data['Brake'].diff().abs()
        brake_variation = brake_changes.std()

        throttle_rating_md = rate_smoothness(
            throttle_variation,
            smoothness_config['throttle_smooth_threshold'],
            smoothness_config['throttle_fair_threshold'],
        )
        brake_rating_md = rate_smoothness(
            brake_variation,
            smoothness_config['brake_smooth_threshold'],
            smoothness_config['brake_fair_threshold'],
        )

        report_lines.append(f"| {int(lap)} | {throttle_rating_md} | {throttle_variation:.4f} | {brake_rating_md} | {brake_variation:.4f} |")
    
    report_lines.append("")
    report_lines.append(f"Target: <{smoothness_config['throttle_smooth_threshold']} throttle variation, <{smoothness_config['brake_smooth_threshold']} brake variation. Lower values indicate smoother inputs.\n")
    
    return report_lines


def _compare_laps(df: pd.DataFrame, lap_stats: pd.DataFrame, valid_laps: list,
                 units: Units = "mph") -> list[str]:
    """Compare the fastest and slowest complete laps."""
    report_lines = ["\n## Fastest Lap Analysis\n"]
    slabel = speed_label(units)

    df = convert_speed(df, units)
    
    # Only compare complete laps
    complete_laps = lap_stats[~lap_stats['IsPartial']]
    if len(complete_laps) < 2:
        report_lines.append("Not enough complete laps for comparison.\n")
        return report_lines
    
    laps_by_time = complete_laps.sort_values('LapTime')
    fastest_lap = int(laps_by_time.iloc[0]['Lap'])
    slowest_lap = int(laps_by_time.iloc[-1]['Lap'])

    time_diff = complete_laps.loc[complete_laps['Lap'] == slowest_lap, 'LapTime'].values[0] - \
                complete_laps.loc[complete_laps['Lap'] == fastest_lap, 'LapTime'].values[0]
    
    fastest_avg_speed = complete_laps.loc[complete_laps['Lap'] == fastest_lap, 'AvgSpeed'].values[0]
    slowest_avg_speed = complete_laps.loc[complete_laps['Lap'] == slowest_lap, 'AvgSpeed'].values[0]
    
    fastest_throttle = complete_laps.loc[complete_laps['Lap'] == fastest_lap, 'AvgThrottle'].values[0]
    slowest_throttle = complete_laps.loc[complete_laps['Lap'] == slowest_lap, 'AvgThrottle'].values[0]

    report_lines.append(f"Fastest lap (Lap {fastest_lap}) was **{time_diff:.3f}s faster** than slowest (Lap {slowest_lap}).\n")
    report_lines.append("### Key Differences\n")
    report_lines.append(f"- **Average speed:** {fastest_avg_speed:.1f} {slabel} vs {slowest_avg_speed:.1f} {slabel}")
    report_lines.append(f"- **Average throttle:** {fastest_throttle:.1f}% vs {slowest_throttle:.1f}%\n")
    
    if fastest_throttle > slowest_throttle + 2:
        report_lines.append("More aggressive throttle application on the fastest lap.")
    if fastest_avg_speed > slowest_avg_speed + 2:
        report_lines.append("Better corner exit speed or earlier throttle application.\n")
    
    return report_lines


def _run_advanced_analysis(df: pd.DataFrame, lap_stats: pd.DataFrame, valid_laps: list, units: Units = "mph") -> list[str]:
    """Run all advanced analysis features and return report lines."""
    report_lines = ["\n---\n", "\n# Advanced Analysis\n"]

    if len(valid_laps) == 0:
        return report_lines

    df_speed = convert_speed(df, units)

    if len(valid_laps) >= 2:
        lap_times = {}
        for lap in valid_laps:
            lap_data = df[df['Lap'] == lap]
            lap_times[lap] = lap_data['SessionTime'].max() - lap_data['SessionTime'].min()
        fastest_lap = min(lap_times, key=lambda lap: lap_times[lap])
        report_lines.append("\n## Delta Time Analysis\n")
        report_lines.append(f"Reference lap: {int(fastest_lap)}\n")

    report_lines.extend(_corner_analysis(df_speed, valid_laps, units))

    if len(valid_laps) >= 2:
        report_lines.extend(_consistency_analysis(df_speed, valid_laps, units))

    report_lines.extend(_steering_analysis(df_speed, valid_laps))
    report_lines.extend(_trail_braking_analysis(df_speed, valid_laps))

    if 'Lat' in df.columns and 'Lon' in df.columns:
        report_lines.append("\n## Track Map Visualization\n")
        report_lines.append("GPS-based racing line colored by speed.\n")

    return report_lines


def _corner_analysis(df: pd.DataFrame, valid_laps: list, units: Units = "mph") -> list[str]:
    """Detect corners and analyze performance through each."""
    report_lines = ["\n## Corner-by-Corner Breakdown\n"]
    slabel = speed_label(units)
    
    config = load_config()
    corner_config = config['corner_detection']
    
    # Use first lap to detect corners
    reference_lap = valid_laps[0]
    ref_data = df[df['Lap'] == reference_lap].sort_values('LapDistPct').reset_index(drop=True)
    
    # Detect corners
    max_speed = ref_data['Speed'].max()
    speed_threshold = max_speed * corner_config['speed_threshold']
    brake_active = ref_data['Brake'] > corner_config['brake_threshold']
    slow_points = ref_data['Speed'] < speed_threshold
    corner_zones = brake_active & slow_points
    
    # Find corner apexes
    corners = []
    in_corner = False
    corner_start = 0
    
    for idx in range(len(corner_zones)):
        if corner_zones.iloc[idx] and not in_corner:
            corner_start = idx
            in_corner = True
        elif not corner_zones.iloc[idx] and in_corner:
            corner_segment = ref_data.iloc[corner_start:idx]
            if len(corner_segment) > 0:
                apex_idx = corner_segment['Speed'].idxmin()
                corners.append(apex_idx)
            in_corner = False

    report_lines.append(f"**{len(corners)} corners detected**\n")
    if len(corners) == 0:
        return report_lines
    
    report_lines.append("| Corner | Entry Speed | Apex Speed | Exit Speed | Brake Point | Consistency |")
    report_lines.append("|--------|-------------|------------|------------|-------------|-------------|")
    
    for corner_num, corner_idx in enumerate(corners, 1):
        corner_dist = ref_data.loc[corner_idx, 'LapDistPct']
        window = corner_config['window_size']
        corner_start = max(0, corner_dist - window)
        corner_end = min(1, corner_dist + window)
        
        entry_speeds = []
        apex_speeds = []
        exit_speeds = []
        brake_points = []
        
        for lap in valid_laps:
            lap_data = df[df['Lap'] == lap]
            corner_data = lap_data[
                (lap_data['LapDistPct'] >= corner_start) &
                (lap_data['LapDistPct'] <= corner_end)
            ].sort_values('LapDistPct')
            
            if len(corner_data) < 10:
                continue
            
            entry = corner_data.head(int(len(corner_data) * 0.2))
            if len(entry) > 0:
                entry_speeds.append(entry['Speed'].mean())
            
            apex_speeds.append(corner_data['Speed'].min())
            
            exit = corner_data.tail(int(len(corner_data) * 0.2))
            if len(exit) > 0:
                exit_speeds.append(exit['Speed'].mean())
            
            brake_in_corner = corner_data[corner_data['Brake'] > 0.1]
            if len(brake_in_corner) > 0:
                brake_points.append(brake_in_corner.iloc[0]['LapDistPct'] * 100)
        
        avg_entry = np.mean(entry_speeds) if entry_speeds else 0
        avg_apex = np.mean(apex_speeds) if apex_speeds else 0
        avg_exit = np.mean(exit_speeds) if exit_speeds else 0
        avg_brake_pt = np.mean(brake_points) if brake_points else 0
        consistency = np.std(apex_speeds) if len(apex_speeds) > 1 else 0
        consistency_rating = f"±{consistency:.1f} {slabel}"
        
        report_lines.append(
            f"| {corner_num} | {avg_entry:.1f} {slabel} | {avg_apex:.1f} {slabel} | {avg_exit:.1f} {slabel} | "
            f"{avg_brake_pt:.1f}% | {consistency_rating} |"
        )
    
    report_lines.append("")
    return report_lines


def _consistency_analysis(df: pd.DataFrame, valid_laps: list, units: Units = "mph") -> list[str]:
    """Calculate consistency metrics across laps."""
    report_lines = ["\n## Consistency Metrics\n"]
    slabel = speed_label(units)
    
    lap_times = []
    avg_speeds = []

    for lap in valid_laps:
        lap_data = df[df['Lap'] == lap]
        lap_time = lap_data['SessionTime'].max() - lap_data['SessionTime'].min()
        lap_times.append(lap_time)
        avg_speeds.append(lap_data['Speed'].mean())
    
    lap_time_std = np.std(lap_times)
    speed_std = np.std(avg_speeds)
    
    consistency_score = max(0, 100 - (lap_time_std * 40))
    
    config = load_config()
    consistency_config = config['consistency_rating']
    
    report_lines.append(f"**Consistency Score:** {consistency_score:.1f}/100\n")
    report_lines.append("| Metric | Std Deviation | Rating |")
    report_lines.append("|--------|---------------|--------|")
    
    time_rating = "Good" if lap_time_std < consistency_config['good_lap_time'] else "Fair" if lap_time_std < consistency_config['fair_lap_time'] else "High"
    speed_rating = "Good" if speed_std < consistency_config['good_speed'] else "Fair" if speed_std < consistency_config['fair_speed'] else "High"
    
    report_lines.append(f"| Lap Time | ±{lap_time_std:.3f}s | {time_rating} |")
    report_lines.append(f"| Avg Speed | ±{speed_std:.2f} {slabel} | {speed_rating} |")
    report_lines.append("")

    return report_lines


def _steering_analysis(df: pd.DataFrame, valid_laps: list) -> list[str]:
    """Analyze steering smoothness and corrections."""
    report_lines = ["\n## Steering Analysis\n"]
    
    if 'SteeringWheelAngle' not in df.columns:
        report_lines.append("Steering data not available.\n")
        return report_lines
    
    config = load_config()
    steering_config = config['steering_analysis']

    report_lines.append("| Lap | Smoothness | Corrections/Lap | Max Angle | Rating |")
    report_lines.append("|-----|------------|-----------------|-----------|--------|")
    
    for lap in valid_laps:
        lap_data = df[df['Lap'] == lap].sort_values('LapDistPct')
        steering = lap_data['SteeringWheelAngle']
        
        steering_changes = steering.diff().abs()
        smoothness = 1 - (steering_changes.mean() / 0.1)
        smoothness_pct = max(0, min(100, smoothness * 100))
        
        steering_diff = steering.diff()
        direction_changes = ((steering_diff.shift(1) * steering_diff) < 0).sum()
        corrections = direction_changes / 2
        
        max_angle = steering.abs().max()
        
        if smoothness_pct > steering_config['excellent_smoothness'] and corrections < steering_config['excellent_corrections']:
            rating = "Good"
        elif smoothness_pct > steering_config['good_smoothness'] and corrections < steering_config['good_corrections']:
            rating = "Fair"
        else:
            rating = "High"
        
        report_lines.append(
            f"| {int(lap)} | {smoothness_pct:.1f}% | {int(corrections)} | {max_angle:.3f} rad | {rating} |"
        )

    report_lines.append(f"\nTarget: >{steering_config['excellent_smoothness']}% smoothness, <{steering_config['excellent_corrections']} corrections/lap.\n")
    
    return report_lines


def _trail_braking_analysis(df: pd.DataFrame, valid_laps: list) -> list[str]:
    """Detect and analyze trail braking technique."""
    report_lines = ["\n## Trail Braking Analysis\n"]
    
    config = load_config()
    trail_config = config['trail_braking']

    for lap in valid_laps:
        lap_data = df[df['Lap'] == lap].sort_values('LapDistPct')
        
        brake_on = lap_data['Brake'] > trail_config['brake_threshold']
        throttle_on = lap_data['Throttle'] > trail_config['throttle_threshold']
        
        if 'SteeringWheelAngle' in lap_data.columns:
            turning = lap_data['SteeringWheelAngle'].abs() > trail_config['steering_threshold']
            trail_braking = brake_on & turning
        else:
            trail_braking = brake_on & throttle_on
        
        trail_pct = (trail_braking.sum() / len(lap_data)) * 100
        
        brake_releases = lap_data[brake_on]['Brake'].diff()
        release_rate = brake_releases[brake_releases < 0].mean()
        
        report_lines.append(f"**Lap {int(lap)}:**")
        report_lines.append(f"- Trail braking: {trail_pct:.1f}% of lap")
        report_lines.append(f"- Brake release rate: {abs(release_rate):.4f}\n")

    report_lines.append("\nTypical range: 15-25% of lap. Progressive release rate maintains weight transfer.\n")
    
    return report_lines
