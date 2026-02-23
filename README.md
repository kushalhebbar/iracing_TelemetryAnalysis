# iRacing Telemetry Analysis

Converts iRacing telemetry `.ibt` files to CSV with automatic analysis to improve driving performance.

## Features

**Data Conversion:**
- Full CSV with all 287 telemetry channels
- Filtered CSV with essential racing data
- Per-lap CSV files (complete laps only, ≥90% track coverage)
- Automatic partial lap detection

**Core Analysis:**
- Lap time calculations (MM:SS.sss format)
- Speed traces with lap time overlays
- Throttle/brake input visualization per lap
- Braking point identification
- Gear shift analysis with RPM patterns
- Input smoothness analysis
- Lap-to-lap consistency tracking
- Summary statistics export

**Advanced Analysis:**
- Delta time analysis (time gained/lost vs fastest lap)
- Corner-by-corner breakdown (entry/apex/exit speeds)
- Consistency metrics (lap-to-lap variation, scored 0-100)
- Steering analysis (smoothness, correction counting)
- Trail braking analysis (brake release rate, technique)
- Track map visualization (GPS racing line with speed overlay)

## Setup

1. Install Poetry: https://python-poetry.org/docs/#installation
2. Install dependencies:

```bash
poetry install
```

## Project Structure

```
iRacing_Telemetry/
├── ibt_input/          # Place your .ibt files here
├── csv_output/         # All CSVs (full, filtered, per-lap, summary)
├── plots/              # All generated plots
└── src/
    └── iracing_telemetry/
```

## Usage

1. Place `.ibt` file in `ibt_input/` folder
2. Run the converter:

```bash
poetry run iracing-telemetry ibt_input/<your-file>.ibt
```

**Output:**
- `csv_output/<track>_<date>.csv` - Full telemetry (all channels)
- `csv_output/<track>_<date>_filtered.csv` - Essential channels only
- `csv_output/<track>_<date>_lap<N>.csv` - Individual lap files (complete laps only)
- `csv_output/<track>_<date>_summary.csv` - Lap statistics
- `plots/<track>_<date>_*.png` - All visualizations

## Analysis Features

### Smart Lap Detection
- **Partial lap elimination**: Only processes laps with ≥90% track coverage
- Automatically skips incomplete laps (out-lap, recording started/stopped mid-lap)
- Focuses analysis on complete, comparable laps

### Lap Statistics
- Lap times (MM:SS.sss format)
- Average & maximum speed (mph)
- Throttle/brake usage percentages
- Braking event counts
- Complete vs partial lap marking

### Gear Shift Analysis
- Total upshifts/downshifts
- Average RPM per gear transition (e.g., 3→4 at 7,521 RPM)
- Shift consistency feedback
- Variance analysis (identifies inconsistent shift points)

### Input Smoothness Analysis
- Calculates throttle/brake input variation
- Rates each lap: Smooth / Fair / Rough
- Lower variation = smoother inputs

### Visualizations

**Per-Lap Plots:**
1. **Speed Trace** - Compare speed across all laps with lap times in legend
2. **Throttle/Brake Input** - Input patterns with speed overlay per lap
**Per-Lap Plots:**
1. **Speed Trace** - Compare speed across all laps with lap times in legend
2. **Throttle/Brake Input** - Input patterns with speed overlay per lap
3. **Brake Trace** - Detailed brake pressure + speed context for each lap
4. **Braking Points** - Identifies braking zones and corner speeds per lap

**Consistency Analysis (2+ complete laps):**
5. **Brake Consistency Overlay** - All laps overlaid to show brake consistency
6. **Throttle Consistency Overlay** - All laps overlaid to show throttle application patterns

**Comparison (2+ complete laps):**
7. **Fastest vs Slowest Lap** - Side-by-side speed and throttle comparison

**Advanced Driver Improvement (2+ complete laps):**
8. **Delta Time Plot** - Color-coded time gained/lost vs fastest lap at every point
9. **Track Map** - GPS-based racing line colored by speed, shows line consistency

All plots include lap times in titles/legends for easy reference.

### Advanced Analysis Features

**Delta Time Analysis:**
- Time gained/lost vs fastest lap at every point on track
- Includes speed comparison

**Corner-by-Corner Breakdown:**
- Auto-detects corners using speed and brake data
- Entry speed, apex speed, exit speed per corner
- Brake point location (% around track)
- Consistency rating per corner (variation across laps)

**Consistency Metrics:**
- Overall consistency score (0-100)
- Lap time standard deviation (target: <0.5s)
- Speed variation analysis
- Rating system: Good / Fair / High

**Steering Analysis:**
- Steering smoothness percentage
- Correction counting (steering reversals)
- Max steering angle per lap

**Trail Braking Analysis:**
- Detects trail braking (braking while turning)
- Measures brake release rate
- Shows % of lap spent trail braking
- Typical range: 15-25% of lap

**Track Map Visualization:**
- GPS (Lat/Lon) racing line plot
- Color-coded by speed
- Multiple lap overlay for line consistency

## Filtered Channels

The filtered CSV includes:
- SessionTime, Lap, LapDistPct
- Speed, Throttle, Brake
- SteeringWheelAngle, Gear, RPM
- LatAccel, LongAccel
- Lat, Lon (GPS coordinates for track mapping)

## Example Output

```bash
poetry run iracing-telemetry ibt_input/<your-file>.ibt
```

The tool will:
1. Convert `.ibt` to CSV files in `csv_output/`
2. Generate per-lap CSV files (complete laps only)
3. Create comprehensive plots in `plots/`
4. Export summary statistics
5. Generate a detailed analysis report (`plots/report.md`)

Check the generated `report.md` for complete session analysis including lap times, gear shift patterns, and performance insights.

## Best Practices

**For Better Analysis:**
- Record 3-5+ complete laps for meaningful consistency analysis
- Avoid saving telemetry mid-lap (affects partial lap detection)
- Delta time and corner comparison require 2+ complete laps
- More laps = better consistency metrics and corner-to-corner insights

**Interpreting Results:**
- Focus on consistency first
- Delta time plot shows biggest time loss areas
- Corner breakdown identifies weakest corners
- Steering corrections >20/lap indicates instability
- Trail braking typical range: 15-25%
- Track map shows line variation

## Speed Units

All speeds are converted from iRacing's native m/s to **mph** for display in plots and analysis.
