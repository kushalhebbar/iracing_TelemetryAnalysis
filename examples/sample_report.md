# Telemetry Analysis Report

**Track:** Autodromo Nazionale Monza  —  Monza, Italy
**Car:** Porsche 911 GT3 R (992)
**Driver:** Kushal Hebbar
**Turns:** 11
**Session file:** monza_full_2026-02-18
**Generated:** 2026-09-28 13:11:51

---

## Lap Times

| Lap | Time | Avg Speed (mph) | Max Speed (mph) | Status |
|-----|------|-----------------|-----------------|--------|
| 1 | 0:26.083 | 118.5 | 148.5 | Partial |
| 2 | 1:48.633 | 118.5 | 162.2 | Fastest |
| 3 | 1:51.900 | 90.5 | 161.8 | Partial |


## Gear Shift Analysis

**Total upshifts:** 69
**Total downshifts:** 70

### Upshift RPM by Gear

| Upshift | Avg RPM | Min RPM | Max RPM |
|---------|---------|---------|---------|
| 1 → 2 | 8181 | 8145 | 8216 |
| 2 → 3 | 7043 | 1296 | 8551 |
| 3 → 4 | 7521 | 1295 | 9113 |
| 4 → 5 | 8066 | 7145 | 8980 |
| 5 → 6 | 8027 | 7558 | 9014 |
| 6 → 7 | 7991 | 7806 | 8128 |

Average upshift RPM: 7799 ± 1198

High variance in shift RPM. Target: <500 RPM variation per gear.


## Input Smoothness Analysis

| Lap | Throttle Smoothness | Throttle Variation | Brake Smoothness | Brake Variation |
|-----|---------------------|--------------------|--------------------|-----------------|
| 2 | Fair | 0.0515 | Smooth | 0.0065 |

Target: <0.05 throttle variation, <0.01 brake variation. Lower values indicate smoother inputs.


## Sector Analysis (10 mini-sectors)

**Theoretical best lap:** 1:48.633

| Sector | Best time (s) | From |
|--------|---------------|------|
| 1 | 8.407 | Lap 2 |
| 2 | 14.366 | Lap 2 |
| 3 | 9.842 | Lap 2 |
| 4 | 12.273 | Lap 2 |
| 5 | 12.475 | Lap 2 |
| 6 | 10.438 | Lap 2 |
| 7 | 10.221 | Lap 2 |
| 8 | 10.028 | Lap 2 |
| 9 | 9.542 | Lap 2 |
| 10 | 11.042 | Lap 2 |


## Balance (Understeer / Oversteer)

| Lap | Balance index | Understeer % | Oversteer % | Tendency |
|-----|---------------|--------------|-------------|----------|
| 2 | -0.125 | 13% | 63% | Oversteer |

Positive index leans understeer, negative leans oversteer. Heuristic from steering angle versus lateral grip in corners.


---


# Advanced Analysis


## Corner-by-Corner Breakdown

**6 corners detected**

| Corner | Entry Speed | Apex Speed | Exit Speed | Brake Point | Consistency |
|--------|-------------|------------|------------|-------------|-------------|
| 1 | 152.4 mph | 33.2 mph | 103.7 mph | 13.6% | ±0.0 mph |
| 2 | 153.2 mph | 59.1 mph | 104.5 mph | 34.4% | ±0.0 mph |
| 3 | 83.3 mph | 67.8 mph | 113.7 mph | 42.2% | ±0.0 mph |
| 4 | 96.6 mph | 86.2 mph | 117.5 mph | 48.2% | ±0.0 mph |
| 5 | 154.4 mph | 85.1 mph | 112.5 mph | 65.7% | ±0.0 mph |
| 6 | 157.0 mph | 85.9 mph | 107.9 mph | 86.6% | ±0.0 mph |


## Steering Analysis

| Lap | Smoothness | Corrections/Lap | Max Angle | Rating |
|-----|------------|-----------------|-----------|--------|
| 2 | 91.1% | 408 | 3.399 rad | High |

Target: >90% smoothness, <10 corrections/lap.


## Trail Braking Analysis

**Lap 2:**
- Trail braking: 7.2% of lap
- Brake release rate: 0.0096


Typical range: 15-25% of lap. Progressive release rate maintains weight transfer.


## Track Map Visualization

GPS-based racing line colored by speed.
