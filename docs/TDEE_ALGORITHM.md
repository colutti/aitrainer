# TDEE Adaptive Algorithm v3

## Overview

The TDEE (Total Daily Energy Expenditure) calculation uses real user data
(weight measurements and nutrition logs) to estimate actual metabolic rate,
rather than relying on static formulas like Harris-Benedict or Mifflin-St Jeor.

## Why Adaptive?

Static formulas estimate metabolic rate within ±20-30% accuracy because they:
- Ignore metabolic adaptation (the body adapts to calorie restriction/surplus)
- Don't account for individual differences in thermogenesis
- Assume linear energy balance

The adaptive algorithm converges toward the user's true TDEE by using observed data.

## Algorithm Steps (v3)

### 1. Data Collection
- Weight logs (with optional body fat %, muscle mass)
- Nutrition logs (calories, macros)
- Lookback period: 4 weeks (configurable via `DEFAULT_LOOKBACK_WEEKS`)

### 2. Data Cleaning
- **Outlier Detection**: Modified Z-Score (threshold 3.5) + contextual spike detection
- **Interpolation**: Linear interpolation for weight gaps ≤14 days
- **Validation**: Require ≥2 weight logs, ≥3 days of data

### 3. Weight Trend Calculation
- Exponential Moving Average (EMA) over 21 days
- Smooths short-term water fluctuations

### 4. TDEE Observations (7-day windows)
For each day with ≥4 logged meals in the last 7 days:

```
avg_calories = mean(calories_last_7d)
Δtrend_7d = trend[now] - trend[7_days_ago]
TDEE_obs = avg_calories - (Δtrend_7d / 7) × energy_per_kg
```

**Energy per kg (Forbes/Hall model):**
```
fat_fraction = 0.75 + (body_fat% - 25) × 0.005
energy_per_kg = fat_fraction × 9400 + (1 - fat_fraction) × 1800
```
- Fallback (no body comp data): 7700 kcal/kg

### 5. TDEE Smoothing
- EMA over observations (span: 21 days)
- Prior/anchor: `BMR × activity_factor` (default factor: 1.45)
- Prevents wild swings from noisy daily data

### 6. Clamping and Safety
- Absolute bounds: [1200, 5000] kcal
- Gender-specific floor: 1200 (female), 1500 (male)
- Max deficit: 30% below TDEE (prevents dangerous crash diets)

### 7. Daily Target Calculation
- Applies coaching check-in logic
- Gradual adjustment: ±100 kcal/week max
- Check-in interval: 7 days

## Configuration Parameters

Located in `AdaptiveTDEEService`:

| Parameter | Default | Purpose |
|-----------|---------|---------|
| `EMA_SPAN` | 21 | Days for weight EMA |
| `TDEE_OBS_EMA_SPAN` | 21 | Days for TDEE observation smoothing |
| `MAX_INTERPOLATION_GAP` | 14 | Max days to interpolate weight |
| `MAX_WEEKLY_ADJUSTMENT` | 100 | Max kcal change per check-in |
| `CHECK_IN_INTERVAL_DAYS` | 7 | Coaching check-in frequency |
| `DEFAULT_LOOKBACK_WEEKS` | 4 | Historical data window |
| `MIN_TDEE` / `MAX_TDEE` | 1200 / 5000 | Absolute bounds |

## Activity Factor

The activity factor (`tdee_activity_factor`) is stored per-user in the `UserProfile`:

| Factor | Level | Description |
|--------|-------|-------------|
| 1.2 | Sedentary | Desk job, minimal movement |
| 1.375 | Lightly active | Regular walking, some activity |
| 1.55 | Moderately active | Regular exercise or physical job |
| 1.725 | Very active | Heavy physical job or daily intense exercise |
| 1.9 | Extremely active | Athlete, very strenuous work |

Default: 1.45 (moderately active)

AI can adjust this via `update_tdee_params()` if user reports lifestyle changes.

## Confidence Levels

- **High**: ≥14 days of data, ≥85% nutrition adherence
- **Medium**: ≥14 days of data, 60-85% adherence
- **Low**: <14 days of data OR <60% adherence

## References

- Hall, K. D., et al. (2012). "Quantification of the effect of energy imbalance
  on bodyweight". *The Lancet*, 378(9793), 826-837.
- Forbes, G. B. (1987). "Human Body Composition: Growth, Aging, Nutrition,
  and Activity". Springer-Verlag.
- MacroFactor methodology: https://macrofactorapp.com
- Stronger by Science TDEE calculation: https://www.strongerbyscience.com
