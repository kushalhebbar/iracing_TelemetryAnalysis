from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd

from iracing_telemetry.utils import (
    convert_speed_to_mph,
    format_lap_time,
    get_valid_laps,
    rate_smoothness,
    load_config,
)

# Import Plotly plotting functions
from iracing_telemetry import plotly_plots


def analyze_telemetry(filtered_csv_path: Path, base_name: str) -> None:
    """Perform comprehensive telemetry analysis and generate plots.
    
    Args:
        filtered_csv_path: Path to the filtered CSV file
        base_name: Base name for output files (without extension)
    """
    # Read the filtered telemetry data
    df = pd.read_csv(filtered_csv_path)
    
    # Create plots directory
    workspace_root = Path.cwd()
    plots_dir = workspace_root / "plots"
    plots_dir.mkdir(exist_ok=True)
    
    # Create summary output directory
    summary_dir = workspace_root / "csv_output"
    
    # Calculate lap times and statistics
    lap_stats = _calculate_lap_statistics(df)
    
    # Export summary statistics
    summary_path = summary_dir / f"{base_name}_summary.csv"
    lap_stats.to_csv(summary_path, index=False)
    
    # Start building the markdown report
    report_lines = []
    report_lines.append(f"# Telemetry Analysis Report")
    report_lines.append(f"\n**Session:** {base_name}")
    report_lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"\n---\n")
    
    # Display lap times
    report_lines.append(f"## Lap Times\n")
    
    lap_table = "| Lap | Time | Avg Speed (mph) | Max Speed (mph) | Status |\n"
    lap_table += "|-----|------|-----------------|-----------------|--------|\n"
    
    for _, row in lap_stats.iterrows():
        # Format lap time as MM:SS.mmm
        minutes = int(row['LapTime'] // 60)
        seconds = row['LapTime'] % 60
        time_str = f"{minutes}:{seconds:06.3f}"
        
        status = ""
        if row.get('IsPartial', False):
            status = " (Partial)"
        elif row.get('is_fastest', False):
            status = " (Fastest)"
        
        # Add to markdown report
        status_md = ""
        if row.get('IsPartial', False):
            status_md = "Partial"
        elif row.get('is_fastest', False):
            status_md = "Fastest"
        
        lap_table += f"| {int(row['Lap'])} | {time_str} | {row['AvgSpeed']:.1f} | {row['MaxSpeed']:.1f} | {status_md} |\n"
    
    report_lines.append(lap_table)
    
    # Analyze gear shifts
    gear_shift_report = _analyze_gear_shifts(df)
    report_lines.extend(gear_shift_report)
    
    # Generate plots for valid laps
    valid_laps = get_valid_laps(df)
    
    if len(valid_laps) == 0:
        return
    
    # Collect all figures for combined HTML
    figures_dict = {}
    
    # Plot speed traces (Plotly - interactive)
    figures_dict["Speed Traces"] = plotly_plots.plot_speed_traces(df, valid_laps, plots_dir, base_name)
    
    # Plot throttle/brake inputs (Plotly - interactive)
    figures_dict["Throttle/Brake Inputs"] = plotly_plots.plot_throttle_brake(df, valid_laps, plots_dir, base_name)
    
    # Plot brake trace for each lap
    figures_dict["Brake Traces"] = plotly_plots.plot_brake_trace(df, valid_laps, plots_dir, base_name)
    
    # Consistency analysis - brake/throttle overlays
    brake_consistency = plotly_plots.plot_brake_consistency(df, valid_laps, plots_dir, base_name)
    if brake_consistency:
        figures_dict["Brake Consistency"] = brake_consistency
    
    throttle_consistency = plotly_plots.plot_throttle_consistency(df, valid_laps, plots_dir, base_name)
    if throttle_consistency:
        figures_dict["Throttle Consistency"] = throttle_consistency
    
    # Plot racing line (Plotly - interactive)
    racing_line = plotly_plots.plot_racing_line(df, valid_laps, plots_dir, base_name)
    if racing_line:
        figures_dict["Racing Line"] = racing_line
    
    # Identify braking points (Plotly - interactive)
    figures_dict["Braking Points"] = plotly_plots.plot_braking_points(df, valid_laps, plots_dir, base_name)
    
    # Create combined HTML with all plots
    plotly_plots.create_combined_html(figures_dict, plots_dir, base_name)
    
    # Input smoothness analysis
    smoothness_report = _analyze_input_smoothness(df, valid_laps)
    report_lines.extend(smoothness_report)
    
    # Compare fastest vs slowest lap
    if len(valid_laps) >= 2:
        comparison_report = _compare_laps(df, lap_stats, valid_laps, plots_dir, base_name)
        report_lines.extend(comparison_report)
    
    # Advanced analysis features
    advanced_report = _run_advanced_analysis(df, lap_stats, valid_laps, plots_dir, base_name)
    report_lines.extend(advanced_report)
    
    # Write markdown report
    report_path = plots_dir / "report.md"
    with open(report_path, 'w') as f:
        f.write('\n'.join(report_lines))
    
    print(f"\n✅ Analysis complete: {base_name}_telemetry_report.html")


def _calculate_lap_statistics(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate lap times and statistics for each lap."""
    stats = []
    
    # Convert speed from m/s to mph (iRacing uses m/s)
    df = convert_speed_to_mph(df)
    
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
    """Analyze gear shift patterns and RPM. Returns markdown report lines."""
    report_lines = ["\n## Gear Shift Analysis\n"]
    
    # print("\nGEAR SHIFT ANALYSIS")
    # print("="*60)
    
    # Check if we have RPM data
    has_rpm = 'RPM' in df.columns
    
    if not has_rpm:
        # print("⚠ RPM data not available in telemetry")
        # print("  Add 'RPM' to the channels list in convert.py to analyze shift RPM")
        report_lines.append("⚠️ **RPM data not available** - Add 'RPM' to channels for shift analysis.\n")
        return report_lines
    
    # Detect gear shifts (where gear changes from one value to another)
    df_copy = df.copy()
    df_copy['GearShift'] = df_copy['Gear'] != df_copy['Gear'].shift(1)
    df_copy['UpShift'] = (df_copy['Gear'] > df_copy['Gear'].shift(1)) & df_copy['GearShift']
    df_copy['DownShift'] = (df_copy['Gear'] < df_copy['Gear'].shift(1)) & df_copy['GearShift']
    
    upshifts = df_copy[df_copy['UpShift']]
    downshifts = df_copy[df_copy['DownShift']]
    
    # print(f"\nTotal upshifts: {len(upshifts)}")
    # print(f"Total downshifts: {len(downshifts)}")
    
    report_lines.append(f"**Total upshifts:** {len(upshifts)}")
    report_lines.append(f"**Total downshifts:** {len(downshifts)}\n")
    
    if has_rpm and len(upshifts) > 0:
        # print(f"\n{'Upshift':<15} {'Avg RPM':<12} {'Min RPM':<12} {'Max RPM':<12}")
        # print("-" * 60)
        
        report_lines.append("### Upshift RPM by Gear\n")
        report_lines.append("| Upshift | Avg RPM | Min RPM | Max RPM |")
        report_lines.append("|---------|---------|---------|---------|")
        
        for gear in sorted(upshifts['Gear'].shift(1).dropna().unique()):
            gear_shifts = upshifts[upshifts['Gear'].shift(1) == gear]
            if len(gear_shifts) > 0:
                avg_rpm = gear_shifts['RPM'].mean()
                min_rpm = gear_shifts['RPM'].min()
                max_rpm = gear_shifts['RPM'].max()
                # print(f"{int(gear)} → {int(gear+1):<10} {avg_rpm:<12.0f} {min_rpm:<12.0f} {max_rpm:<12.0f}")
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
        # print(f"  Average shift RPM: {upshift_rpm:.0f} ± {upshift_std:.0f}")
        # print(f"  {feedback}")
    
    return report_lines


def _analyze_input_smoothness(df: pd.DataFrame, valid_laps: list) -> list[str]:
    """Analyze throttle and brake input smoothness. Returns markdown report lines."""
    report_lines = ["\n## Input Smoothness Analysis\n"]
    
    config = load_config()
    smoothness_config = config['input_smoothness']
    
# print("\nINPUT SMOOTHNESS")
    # print("="*60)

    # print(f"\n{'Lap':<6} {'Throttle':<25} {'Brake':<25}")
    # print(f"{'':6} {'Smoothness':<12} {'Variation':<12} {'Smoothness':<12} {'Variation':<12}")
    # print("-" * 60)
    
    report_lines.append("| Lap | Throttle Smoothness | Throttle Variation | Brake Smoothness | Brake Variation |")
    report_lines.append("|-----|---------------------|--------------------|--------------------|-----------------|")
    
    for lap in valid_laps:
        lap_data = df[df['Lap'] == lap].sort_values('LapDistPct')
        
        # Calculate throttle smoothness (lower variation = smoother)
        throttle_changes = lap_data['Throttle'].diff().abs()
        throttle_smoothness = 1 - throttle_changes.mean()  # 0-1 scale
        throttle_variation = throttle_changes.std()
        
        # Calculate brake smoothness
        brake_changes = lap_data['Brake'].diff().abs()
        brake_smoothness = 1 - brake_changes.mean()
        brake_variation = brake_changes.std()
        
        # Format smoothness as percentage
        throttle_smooth_pct = throttle_smoothness * 100
        brake_smooth_pct = brake_smoothness * 100
        
        # Rating
        if throttle_variation < smoothness_config['throttle_smooth_threshold']:
            throttle_rating = "Smooth"
            throttle_rating_md = "Smooth"
        elif throttle_variation < smoothness_config['throttle_fair_threshold']:
            throttle_rating = "Fair"
            throttle_rating_md = "Fair"
        else:
            throttle_rating = "Rough"
            throttle_rating_md = "Rough"
        
        if brake_variation < smoothness_config['brake_smooth_threshold']:
            brake_rating = "Smooth"
            brake_rating_md = "Smooth"
        elif brake_variation < smoothness_config['brake_fair_threshold']:
            brake_rating = "Fair"
            brake_rating_md = "Fair"
        else:
            brake_rating = "Rough"
            brake_rating_md = "Rough"
        
        # print(f"{int(lap):<6} {throttle_rating:<12} {throttle_variation:<12.4f} {brake_rating:<12} {brake_variation:<12.4f}")
        report_lines.append(f"| {int(lap)} | {throttle_rating_md} | {throttle_variation:.4f} | {brake_rating_md} | {brake_variation:.4f} |")
    
    report_lines.append("")
    report_lines.append(f"Target: <{smoothness_config['throttle_smooth_threshold']} throttle variation, <{smoothness_config['brake_smooth_threshold']} brake variation. Lower values indicate smoother inputs.\n")
    
    return report_lines


def _compare_laps(df: pd.DataFrame, lap_stats: pd.DataFrame, valid_laps: list, 
                 plots_dir: Path, base_name: str) -> list[str]:
    """Compare fastest vs slowest lap. Returns markdown report lines."""
    report_lines = ["\n## Fastest Lap Analysis\n"]
    
    df = convert_speed_to_mph(df)
    
    # Only compare complete laps
    complete_laps = lap_stats[~lap_stats['IsPartial']]
    if len(complete_laps) < 2:
        # print("Not enough complete laps for comparison")
        report_lines.append("Not enough complete laps for comparison.\n")
        return report_lines
    
    fastest_lap = complete_laps.loc[complete_laps['LapTime'].idxmin(), 'Lap']
    slowest_lap = complete_laps.loc[complete_laps['LapTime'].idxmax(), 'Lap']
    
    # Print analysis
    # print(f"\n{'='*60}")
    # print("FASTEST LAP ANALYSIS")
    # print("="*60)
    
    time_diff = complete_laps.loc[complete_laps['Lap'] == slowest_lap, 'LapTime'].values[0] - \
                complete_laps.loc[complete_laps['Lap'] == fastest_lap, 'LapTime'].values[0]
    
    fastest_avg_speed = complete_laps.loc[complete_laps['Lap'] == fastest_lap, 'AvgSpeed'].values[0]
    slowest_avg_speed = complete_laps.loc[complete_laps['Lap'] == slowest_lap, 'AvgSpeed'].values[0]
    
    fastest_throttle = complete_laps.loc[complete_laps['Lap'] == fastest_lap, 'AvgThrottle'].values[0]
    slowest_throttle = complete_laps.loc[complete_laps['Lap'] == slowest_lap, 'AvgThrottle'].values[0]
    
    # print(f"\nFastest lap (Lap {int(fastest_lap)}) was {time_diff:.3f}s faster")
    # print(f"\nKey differences:")
    # print(f"  • Average speed: {fastest_avg_speed:.1f} mph vs {slowest_avg_speed:.1f} mph")
    # print(f"  • Average throttle: {fastest_throttle:.1f}% vs {slowest_throttle:.1f}%")
    
    report_lines.append(f"Fastest lap (Lap {int(fastest_lap)}) was **{time_diff:.3f}s faster** than slowest (Lap {int(slowest_lap)}).\n")
    report_lines.append("### Key Differences\n")
    report_lines.append(f"- **Average speed:** {fastest_avg_speed:.1f} mph vs {slowest_avg_speed:.1f} mph")
    report_lines.append(f"- **Average throttle:** {fastest_throttle:.1f}% vs {slowest_throttle:.1f}%\n")
    
    if fastest_throttle > slowest_throttle + 2:
        # print(f"  💡 More aggressive throttle application on fastest lap")
        report_lines.append("💡 More aggressive throttle application on fastest lap")
    if fastest_avg_speed > slowest_avg_speed + 2:
        # print(f"  💡 Better corner exit speed or earlier throttle application")
        report_lines.append("💡 Better corner exit speed or earlier throttle application\n")
    
    return report_lines


def _run_advanced_analysis(df: pd.DataFrame, lap_stats: pd.DataFrame, valid_laps: list, plots_dir: Path, base_name: str) -> list[str]:
    """Run all advanced analysis features and return report lines."""
    import numpy as np
    from scipy import interpolate
    from scipy.signal import find_peaks
    
    report_lines = ["\n---\n", "\n# Advanced Analysis\n"]
    
    if len(valid_laps) == 0:
        return report_lines
    
    df = convert_speed_to_mph(df)
    
    # 1. Delta time analysis (if 2+ laps)
    if len(valid_laps) >= 2:
        # Find fastest lap
        lap_times = {}
        for lap in valid_laps:
            lap_data = df[df['Lap'] == lap]
            lap_time = lap_data['SessionTime'].max() - lap_data['SessionTime'].min()
            lap_times[lap] = lap_time
        fastest_lap = min(lap_times, key=lap_times.get)
        
        # Add delta time plot to figures dict (will be added in next iteration)
        delta_fig = plotly_plots.plot_delta_time(df, valid_laps, fastest_lap, plots_dir, base_name)
        if delta_fig:
            report_lines.append(f"\n## Delta Time Analysis\n")
            report_lines.append(f"Reference lap: {int(fastest_lap)}\n")
    
    # 2. Corner detection and analysis
    corner_report = _corner_analysis(df, valid_laps)
    report_lines.extend(corner_report)
    
    # 3. Consistency metrics
    if len(valid_laps) >= 2:
        consistency_report = _consistency_analysis(df, valid_laps)
        report_lines.extend(consistency_report)
    
    # 4. Steering analysis
    steering_report = _steering_analysis(df, valid_laps)
    report_lines.extend(steering_report)
    
    # 5. Trail braking analysis
    trail_report = _trail_braking_analysis(df, valid_laps)
    report_lines.extend(trail_report)
    
    # 6. Track map visualization
    if 'Lat' in df.columns and 'Lon' in df.columns:
        track_fig = plotly_plots.plot_track_map(df, valid_laps, plots_dir, base_name)
        if track_fig:
            report_lines.append("\n## Track Map Visualization\n")
            report_lines.append("GPS-based racing line colored by speed.\n")
    
    return report_lines


def _corner_analysis(df: pd.DataFrame, valid_laps: list) -> list[str]:
    """Detect corners and analyze performance through each."""
    import numpy as np
    
    report_lines = ["\n## Corner-by-Corner Breakdown\n"]
    
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
    
    # print(f"Corners detected: {len(corners)}")
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
        consistency_rating = f"±{consistency:.1f} mph"
        
        report_lines.append(
            f"| {corner_num} | {avg_entry:.1f} mph | {avg_apex:.1f} mph | {avg_exit:.1f} mph | "
            f"{avg_brake_pt:.1f}% | {consistency_rating} |"
        )
    
    report_lines.append("")
    return report_lines


def _consistency_analysis(df: pd.DataFrame, valid_laps: list) -> list[str]:
    """Calculate consistency metrics across laps."""
    import numpy as np
    
    report_lines = ["\n## Consistency Metrics\n"]
    
    lap_times = []
    avg_speeds = []
    max_speeds = []
    
    for lap in valid_laps:
        lap_data = df[df['Lap'] == lap]
        lap_time = lap_data['SessionTime'].max() - lap_data['SessionTime'].min()
        lap_times.append(lap_time)
        avg_speeds.append(lap_data['Speed'].mean())
        max_speeds.append(lap_data['Speed'].max())
    
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
    report_lines.append(f"| Avg Speed | ±{speed_std:.2f} mph | {speed_rating} |")
    report_lines.append("")
    
    # print(f"Consistency: {consistency_score:.1f}/100")
    # print(f"  Lap time std: ±{lap_time_std:.3f}s ({time_rating})")
    # print(f"  Speed std: ±{speed_std:.2f} mph ({speed_rating})")
    
    return report_lines


def _steering_analysis(df: pd.DataFrame, valid_laps: list) -> list[str]:
    """Analyze steering smoothness and corrections."""
    report_lines = ["\n## Steering Analysis\n"]
    
    if 'SteeringWheelAngle' not in df.columns:
        report_lines.append("Steering data not available.\n")
        return report_lines
    
    config = load_config()
    steering_config = config['steering_analysis']
    
    # print(f"\nSteering Analysis:")
    
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
        
        # print(f"Lap {int(lap)}: {smoothness_pct:.1f}% smooth, {int(corrections)} corrections ({rating})")
    
    report_lines.append(f"\nTarget: >{steering_config['excellent_smoothness']}% smoothness, <{steering_config['excellent_corrections']} corrections/lap.\n")
    
    return report_lines


def _trail_braking_analysis(df: pd.DataFrame, valid_laps: list) -> list[str]:
    """Detect and analyze trail braking technique."""
    report_lines = ["\n## Trail Braking Analysis\n"]
    
    config = load_config()
    trail_config = config['trail_braking']
    
    # print(f"\nTrail Braking:")
    
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
        
        # print(f"Lap {int(lap)}: {trail_pct:.1f}% trail braking")
    
    report_lines.append("\nTypical range: 15-25% of lap. Progressive release rate maintains weight transfer.\n")
    
    return report_lines
