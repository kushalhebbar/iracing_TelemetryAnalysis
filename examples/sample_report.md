# Telemetry Analysis Report

**Track:** Autodromo Nazionale Monza  —  Monza, Italy
**Car:** Porsche 911 GT3 R (992)
**Driver:** Kushal Hebbar
**Turns:** 11
**Session file:** demo_4laps
**Generated:** 2026-10-05 09:56:15

---

## Lap Times

| Lap | Time | Avg Speed (mph) | Max Speed (mph) | Status |
|-----|------|-----------------|-----------------|--------|
| 1 | 1:49.285 | 125.9 | 158.5 |  |
| 2 | 1:48.633 | 126.8 | 166.5 | Fastest |
| 3 | 1:49.720 | 125.9 | 164.3 |  |
| 4 | 1:48.959 | 126.7 | 162.8 |  |


## Gear Shift Analysis

**Total upshifts:** 184
**Total downshifts:** 188

### Upshift RPM by Gear

| Upshift | Avg RPM | Min RPM | Max RPM |
|---------|---------|---------|---------|
| 1 → 2 | 7926 | 7620 | 8240 |
| 2 → 3 | 7857 | 7249 | 8761 |
| 3 → 4 | 7793 | 7000 | 8307 |
| 4 → 5 | 8028 | 7354 | 8956 |
| 5 → 6 | 7983 | 7606 | 8522 |
| 6 → 7 | 8051 | 7760 | 8380 |

Average upshift RPM: 7940 ± 334

Consistent shift points.


## Input Smoothness Analysis

| Lap | Throttle Smoothness | Throttle Variation | Brake Smoothness | Brake Variation |
|-----|---------------------|--------------------|--------------------|-----------------|
| 1 | Smooth | 0.0468 | Smooth | 0.0077 |
| 2 | Smooth | 0.0468 | Smooth | 0.0077 |
| 3 | Smooth | 0.0469 | Smooth | 0.0077 |
| 4 | Smooth | 0.0468 | Smooth | 0.0077 |

Target: <0.05 throttle variation, <0.01 brake variation. Lower values indicate smoother inputs.


## Sector Analysis (10 mini-sectors)

**Theoretical best lap:** 1:46.627
That is **2.006s** quicker than your best actual lap (Lap 2, 1:48.633).

| Sector | Best time (s) | From |
|--------|---------------|------|
| 1 | 8.236 | Lap 3 |
| 2 | 14.149 | Lap 2 |
| 3 | 9.573 | Lap 2 |
| 4 | 12.056 | Lap 2 |
| 5 | 12.294 | Lap 1 |
| 6 | 10.245 | Lap 1 |
| 7 | 10.034 | Lap 4 |
| 8 | 9.790 | Lap 4 |
| 9 | 9.354 | Lap 4 |
| 10 | 10.897 | Lap 3 |


## Balance (Understeer / Oversteer)

| Lap | Balance index | Understeer % | Oversteer % | Tendency |
|-----|---------------|--------------|-------------|----------|
| 1 | -0.186 | 6% | 72% | Oversteer |
| 2 | -0.185 | 6% | 72% | Oversteer |
| 3 | -0.186 | 6% | 72% | Oversteer |
| 4 | -0.186 | 6% | 72% | Oversteer |

Positive index leans understeer, negative leans oversteer. Heuristic from steering angle versus lateral grip in corners.


## Fastest Lap Analysis

Fastest lap (Lap 2) was **1.087s faster** than slowest (Lap 3).

### Key Differences

- **Average speed:** 126.8 mph vs 125.9 mph
- **Average throttle:** 85.0% vs 85.0%


---


# Advanced Analysis


## Delta Time Analysis

Reference lap: 2


## Corner-by-Corner Breakdown

**6 corners detected**

| Corner | Entry Speed | Apex Speed | Exit Speed | Brake Point | Consistency |
|--------|-------------|------------|------------|-------------|-------------|
| 1 | 160.7 mph | 33.0 mph | 105.9 mph | 13.5% | ±0.2 mph |
| 2 | 151.8 mph | 58.9 mph | 105.0 mph | 34.4% | ±0.7 mph |
| 3 | 86.1 mph | 67.4 mph | 114.5 mph | 42.2% | ±0.8 mph |
| 4 | 97.3 mph | 85.8 mph | 118.0 mph | 48.3% | ±1.3 mph |
| 5 | 153.4 mph | 84.7 mph | 112.0 mph | 65.7% | ±1.1 mph |
| 6 | 155.8 mph | 85.5 mph | 106.8 mph | 86.6% | ±1.0 mph |


## Consistency Metrics

**Consistency Score:** 83.9/100

| Metric | Std Deviation | Rating |
|--------|---------------|--------|
| Lap Time | ±0.402s | Good |
| Avg Speed | ±0.41 mph | Good |


## Steering Analysis

| Lap | Corrections | Max Angle | Rating |
|-----|-------------|-----------|--------|
| 1 | 38 | 3.40 rad | Good |
| 2 | 40 | 3.40 rad | Good |
| 3 | 40 | 3.40 rad | Good |
| 4 | 38 | 3.40 rad | Good |

Corrections = steering reversals larger than 6°. Fewer, deliberate inputs are smoother.


## Trail Braking Analysis

**Lap 1:**
- Trail braking: 5.2% of lap
- Brake release rate: 0.0131

**Lap 2:**
- Trail braking: 5.1% of lap
- Brake release rate: 0.0135

**Lap 3:**
- Trail braking: 5.1% of lap
- Brake release rate: 0.0128

**Lap 4:**
- Trail braking: 5.2% of lap
- Brake release rate: 0.0132


Typical range: 15-25% of lap. Progressive release rate maintains weight transfer.


## Track Map Visualization

GPS-based racing line colored by speed.
