# Adaptive TDEE v2 — Design Document

**Date:** 2026-02-21
**Status:** Approved
**Approach:** MacroFactor-inspired (Abordagem A)

## Problem Statement

The current TDEE calculation produces unreasonably low calorie targets (e.g., 1415 kcal for a 75kg male with TDEE ~2200) due to:

1. **Off-track penalty** doubles down on deficit when the user doesn't lose weight fast enough
2. **Fixed energy density** (7700 kcal/kg) ignores body composition
3. **Gradual adjustment not implemented** — code jumps directly to ideal_target
4. **Gender-agnostic calorie floor** — 1200 kcal for everyone

## Research Basis

Based on extensive research of scientific literature and reference apps:

- **MacroFactor** (Stronger By Science): adherence-neutral TDEE recalculation, no penalties
- **Carbon Diet Coach** (Layne Norton): weekly check-ins, 50-100 kcal gradual adjustments
- **Forbes/Hall model**: dynamic energy density based on body fat %
- **NIH/Harvard**: gender-specific calorie minimums (1200F/1500M)

Key papers:
- Hall 2007 (PMC2376744): Energy deficit per unit weight loss
- Hall 2008 (PLoS): Dynamics of human body weight change
- Forbes (PMC2376748): Fat fraction varies with adiposity
- Garthe et al. (PubMed 21558571): Safe rate of loss for athletes

## Design

### New Constants

```python
# Energy content (Forbes/Hall model)
KCAL_PER_KG_FAT_MASS = 9400
KCAL_PER_KG_LEAN_MASS = 1800
KCAL_PER_KG_DEFAULT = 7700

# Lookback
DEFAULT_LOOKBACK_WEEKS = 4  # was 3

# Safety floors (gender-specific)
MIN_CALORIES_FEMALE = 1200
MIN_CALORIES_MALE = 1500
MAX_DEFICIT_PCT = 0.30  # never exceed 30% deficit

# Coaching
MAX_WEEKLY_ADJUSTMENT = 100  # was 75, now actually implemented
CHECK_IN_INTERVAL_DAYS = 7

# Outlier detection
OUTLIER_MODIFIED_Z_THRESHOLD = 3.5
```

### Pipeline (9 steps)

```
Raw Data
  → [1] Outlier Detection (Modified Z-Score + contextual)
  → [2] Weight Smoothing (EMA for display, regression for calculation)
  → [3] Rate of Change (weighted linear regression slope)
  → [4] Energy Content (dynamic by body fat %, fallback 7700)
  → [5] TDEE Calculation (avg_calories - slope × energy_per_kg)
  → [6] Sanity Checks (clamp MIN_TDEE..MAX_TDEE)
  → [7] Target Calculation (TDEE - deficit, NO off-track penalty)
  → [8] Gradual Adjustment (max ±100 kcal/week vs previous target)
  → [9] Safety Floor (gender min + max 30% deficit)
```

### Key Changes from Current Code

#### Change 1: Remove off-track penalty (MOST IMPACTFUL)

**Before:**
```python
if actual_rate < goal_rate * RATE_THRESHOLD:
    gap = goal_rate - actual_rate
    ideal_target -= gap * 1100  # Extra deficit
```

**After:** Removed entirely. The adaptive TDEE naturally adjusts — if the user isn't losing weight, TDEE estimate decreases, and the new target is automatically lower. No double-dipping.

#### Change 2: Dynamic energy density (Forbes/Hall)

**Before:** `KCAL_PER_KG_FAT = 7700` (fixed)

**After:**
```python
def _estimate_energy_per_kg(self, body_fat_pct, slope):
    if body_fat_pct is None:
        return 7700
    fat_fraction = 0.75 + (body_fat_pct - 25) * 0.005
    rate_weekly = abs(slope * 7)
    if rate_weekly > 0.5:
        fat_fraction -= 0.05 * (rate_weekly - 0.5)
    fat_fraction = max(0.50, min(0.90, fat_fraction))
    return fat_fraction * 9400 + (1 - fat_fraction) * 1800
```

#### Change 3: Implement gradual adjustment (was declared but not used)

**Before:** Line 679 returns `max(1000, ideal_target)` — jumps directly.

**After:**
```python
diff = ideal_target - prev_target
if abs(diff) <= MAX_WEEKLY_ADJUSTMENT:
    return ideal_target
step = MAX_WEEKLY_ADJUSTMENT if diff > 0 else -MAX_WEEKLY_ADJUSTMENT
return prev_target + step
```

#### Change 4: Gender-specific calorie floors + max deficit %

**Before:** `MIN_TDEE = 1200` for everyone.

**After:**
```python
min_cal = MIN_CALORIES_FEMALE if female else MIN_CALORIES_MALE
min_by_deficit = int(round(tdee * (1 - MAX_DEFICIT_PCT)))
target = max(min_cal, min_by_deficit, target)
```

#### Change 5: Improved outlier detection

**Before:** Only contextual spike/step-change logic.

**After:** Modified Z-Score as first pass (statistical), then contextual logic (semantic).

#### Change 6: Lookback 28 days

**Before:** `lookback_weeks=3` (21 days)

**After:** `DEFAULT_LOOKBACK_WEEKS = 4` (28 days)

### Simulation with Production Data

User: rafacolucci@gmail.com (75kg, 23.3% bf, male, goal: lose 0.5kg/week)

| Metric | Current Algorithm | New Algorithm v2 |
|--------|------------------|-----------------|
| TDEE | 2210 kcal | 2202 kcal |
| Energy per kg | 7700 (fixed) | 7435 (dynamic) |
| Base deficit | 550 kcal/day | 531 kcal/day |
| Off-track penalty | +242 kcal/day | 0 (removed) |
| Total deficit | 792 kcal/day (36%) | 531 kcal/day (24%) |
| Ideal target | 1418 kcal | 1671 kcal |
| Displayed target | 1415 kcal (locked) | 1515 kcal (gradual +100) |

The new target of 1671 kcal (ramping from 1515) is:
- A 24% deficit — sustainable and within safe bounds
- Much closer to what the AI trainer recommends (~2000)
- Aligned with MacroFactor's approach

### Files to Modify

1. `backend/src/services/adaptive_tdee.py` — main changes
2. `backend/tests/unit/services/test_adaptive_tdee_logic.py` — update tests
3. New test file for energy density and gradual adjustment

### What We're NOT Changing

- EMA calculation (already good, span=10)
- Weighted linear regression (already good, decay=0.10)
- Macro calculation logic (fixed in Feb 2025)
- Confidence scoring
- Body composition analysis
- Fallback TDEE (Mifflin-St Jeor)
- Frontend (no UI changes needed)
