# Telemetry Analysis Report

**Track:** Autodromo Nazionale Monza  —  Monza, Italy
**Car:** Porsche 911 GT3 R (992)
**Driver:** Kushal Hebbar
**Turns:** 11
**Session file:** demo_4laps
**Generated:** 2026-09-28 13:42:26

---

## Lap Times

| Lap | Time | Avg Speed (mph) | Max Speed (mph) | Status |
|-----|------|-----------------|-----------------|--------|
| 1 | 1:49.285 | 125.9 | 158.5 |  |
| 2 | 1:48.633 | 126.9 | 166.5 | Fastest |
| 3 | 1:49.720 | 126.0 | 164.3 |  |
| 4 | 1:48.959 | 126.7 | 162.8 |  |


## Gear Shift Analysis

**Total upshifts:** 88
**Total downshifts:** 96

### Upshift RPM by Gear

| Upshift | Avg RPM | Min RPM | Max RPM |
|---------|---------|---------|---------|
| 2 → 3 | 7526 | 7402 | 7735 |
| 3 → 4 | 7684 | 7401 | 7924 |
| 4 → 5 | 7796 | 7429 | 8076 |
| 5 → 6 | 7870 | 7386 | 8401 |
| 6 → 7 | 7714 | 7052 | 8256 |

Average upshift RPM: 7758 ± 265

Consistent shift points.


## Input Smoothness Analysis

| Lap | Throttle Smoothness | Throttle Variation | Brake Smoothness | Brake Variation |
|-----|---------------------|--------------------|--------------------|-----------------|
| 1 | Fair | 0.0947 | Rough | 0.0397 |
| 2 | Fair | 0.0942 | Rough | 0.0394 |
| 3 | Fair | 0.0940 | Rough | 0.0396 |
| 4 | Fair | 0.0939 | Rough | 0.0395 |

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
| 1 | -0.262 | 4% | 85% | Oversteer |
| 2 | -0.261 | 4% | 85% | Oversteer |
| 3 | -0.262 | 4% | 85% | Oversteer |
| 4 | -0.261 | 4% | 84% | Oversteer |

Positive index leans understeer, negative leans oversteer. Heuristic from steering angle versus lateral grip in corners.


## Fastest Lap Analysis

Fastest lap (Lap 2) was **1.087s faster** than slowest (Lap 3).

### Key Differences

- **Average speed:** 126.9 mph vs 126.0 mph
- **Average throttle:** 84.8% vs 84.8%


---


# Advanced Analysis


## Delta Time Analysis

Reference lap: 2


## Corner-by-Corner Breakdown

**4 corners detected**

| Corner | Entry Speed | Apex Speed | Exit Speed | Brake Point | Consistency |
|--------|-------------|------------|------------|-------------|-------------|
| 1 | 160.7 mph | 33.1 mph | 105.7 mph | 13.6% | ±0.2 mph |
| 2 | 151.7 mph | 58.9 mph | 104.4 mph | 34.4% | ±0.7 mph |
| 3 | 96.7 mph | 85.9 mph | 117.6 mph | 48.2% | ±1.3 mph |
| 4 | 153.3 mph | 84.7 mph | 111.4 mph | 65.8% | ±1.1 mph |


## Consistency Metrics

**Consistency Score:** 83.9/100

| Metric | Std Deviation | Rating |
|--------|---------------|--------|
| Lap Time | ±0.402s | Good |
| Avg Speed | ±0.41 mph | Good |


## Steering Analysis

| Lap | Smoothness | Corrections/Lap | Max Angle | Rating |
|-----|------------|-----------------|-----------|--------|
| 1 | 42.0% | 254 | 3.310 rad | High |
| 2 | 42.2% | 260 | 3.304 rad | High |
| 3 | 42.1% | 258 | 3.316 rad | High |
| 4 | 41.5% | 264 | 3.307 rad | High |

Target: >90% smoothness, <10 corrections/lap.


## Trail Braking Analysis

**Lap 1:**
- Trail braking: 5.3% of lap
- Brake release rate: 0.0701

**Lap 2:**
- Trail braking: 5.0% of lap
- Brake release rate: 0.0710

**Lap 3:**
- Trail braking: 5.3% of lap
- Brake release rate: 0.0685

**Lap 4:**
- Trail braking: 5.3% of lap
- Brake release rate: 0.0650


Typical range: 15-25% of lap. Progressive release rate maintains weight transfer.


## Track Map Visualization

GPS-based racing line colored by speed.
