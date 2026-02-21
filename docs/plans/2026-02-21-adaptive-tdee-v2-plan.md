# Adaptive TDEE v2 — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Refactor the adaptive TDEE calculation to use a MacroFactor-inspired algorithm that removes the off-track penalty, adds dynamic energy density (Forbes/Hall), implements real gradual adjustment, and adds gender-specific safety floors.

**Architecture:** Modify `AdaptiveTDEEService` class in-place. All changes are in the backend service layer — no frontend or API changes. The pipeline becomes: Raw Data → Outlier Detection → Weight Smoothing → Rate of Change → Energy Content (dynamic) → TDEE → Sanity Checks → Target (NO penalty) → Gradual Adjustment → Safety Floor.

**Tech Stack:** Python 3.12, NumPy, Pytest, FastAPI (backend only)

---

### Task 1: Update Constants

**Files:**
- Modify: `backend/src/services/adaptive_tdee.py:29-45`
- Test: `backend/tests/unit/services/test_adaptive_tdee_logic.py`

**Step 1: Write the failing test**

Add to `backend/tests/unit/services/test_adaptive_tdee_logic.py`:

```python
def test_v2_constants_exist(self, service):
    """Verify new v2 constants are defined on the service."""
    assert service.KCAL_PER_KG_FAT_MASS == 9400
    assert service.KCAL_PER_KG_LEAN_MASS == 1800
    assert service.KCAL_PER_KG_DEFAULT == 7700
    assert service.DEFAULT_LOOKBACK_WEEKS == 4
    assert service.MIN_CALORIES_FEMALE == 1200
    assert service.MIN_CALORIES_MALE == 1500
    assert service.MAX_DEFICIT_PCT == 0.30
    assert service.MAX_WEEKLY_ADJUSTMENT == 100
    assert service.OUTLIER_MODIFIED_Z_THRESHOLD == 3.5
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/unit/services/test_adaptive_tdee_logic.py::TestAdaptiveTDEELogic::test_v2_constants_exist -v`
Expected: FAIL with `AttributeError: 'AdaptiveTDEEService' object has no attribute 'KCAL_PER_KG_FAT_MASS'`

**Step 3: Write minimal implementation**

Replace the constants block at lines 29-45 of `backend/src/services/adaptive_tdee.py` with:

```python
    # Constants — Energy Content (Forbes/Hall model)
    KCAL_PER_KG_FAT_MASS = 9400
    KCAL_PER_KG_LEAN_MASS = 1800
    KCAL_PER_KG_DEFAULT = 7700  # Fallback when no body fat data

    # Legacy alias (used in calculate_tdee line 204)
    KCAL_PER_KG_FAT = 7700

    MIN_DATA_DAYS = 7

    # Regression config
    MIN_DATA_DAYS_FOR_REGRESSION = 10

    # Sanity Limits
    MIN_TDEE = 1200
    MAX_TDEE = 5000
    MAX_DAILY_WEIGHT_CHANGE = 1.0
    EMA_SPAN = 10

    # Coaching check-in
    MAX_WEEKLY_ADJUSTMENT = 100  # was 75, now actually used
    CHECK_IN_INTERVAL_DAYS = 7
    RATE_THRESHOLD = 0.75

    # Lookback
    DEFAULT_LOOKBACK_WEEKS = 4  # was 3

    # Safety floors (gender-specific, NIH/Harvard)
    MIN_CALORIES_FEMALE = 1200
    MIN_CALORIES_MALE = 1500
    MAX_DEFICIT_PCT = 0.30  # Never exceed 30% deficit

    # Outlier detection
    OUTLIER_MODIFIED_Z_THRESHOLD = 3.5
```

**Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/unit/services/test_adaptive_tdee_logic.py::TestAdaptiveTDEELogic::test_v2_constants_exist -v`
Expected: PASS

**Step 5: Lint check**

Run: `cd backend && ruff check src/services/adaptive_tdee.py`
Expected: No errors

**Step 6: Commit**

```bash
git add backend/src/services/adaptive_tdee.py backend/tests/unit/services/test_adaptive_tdee_logic.py
git commit -m "feat(tdee-v2): add new constants for Forbes/Hall model, safety floors, outlier detection"
```

---

### Task 2: Add `_estimate_energy_per_kg()` Method (Forbes/Hall)

**Files:**
- Modify: `backend/src/services/adaptive_tdee.py` (add new method after `_filter_outliers`, ~line 117)
- Test: `backend/tests/unit/services/test_adaptive_tdee_logic.py`

**Step 1: Write the failing tests**

Add to `backend/tests/unit/services/test_adaptive_tdee_logic.py`:

```python
class TestEnergyPerKg:
    @pytest.fixture
    def mock_db(self):
        return MagicMock(spec=MongoDatabase)

    @pytest.fixture
    def service(self, mock_db):
        return AdaptiveTDEEService(mock_db)

    def test_no_body_fat_returns_default(self, service):
        """When body_fat_pct is None, fallback to 7700."""
        result = service._estimate_energy_per_kg(body_fat_pct=None, slope=-0.05)
        assert result == 7700

    def test_average_body_fat_25pct(self, service):
        """At 25% body fat, fat_fraction = 0.75 → energy ≈ 0.75*9400 + 0.25*1800 = 7500."""
        result = service._estimate_energy_per_kg(body_fat_pct=25.0, slope=-0.05)
        assert 7400 <= result <= 7600

    def test_high_body_fat_35pct(self, service):
        """At 35% body fat, fat_fraction = 0.80 → energy ≈ 0.80*9400 + 0.20*1800 = 7880."""
        result = service._estimate_energy_per_kg(body_fat_pct=35.0, slope=-0.05)
        assert 7700 <= result <= 8100

    def test_low_body_fat_15pct(self, service):
        """At 15% body fat, fat_fraction = 0.70 → energy ≈ 0.70*9400 + 0.30*1800 = 7120."""
        result = service._estimate_energy_per_kg(body_fat_pct=15.0, slope=-0.05)
        assert 6900 <= result <= 7300

    def test_very_low_body_fat_clamps_at_50pct(self, service):
        """Fat fraction never goes below 0.50."""
        result = service._estimate_energy_per_kg(body_fat_pct=5.0, slope=-0.05)
        # 0.50 * 9400 + 0.50 * 1800 = 5600
        assert result >= 5600

    def test_very_high_body_fat_clamps_at_90pct(self, service):
        """Fat fraction never goes above 0.90."""
        result = service._estimate_energy_per_kg(body_fat_pct=60.0, slope=-0.05)
        # 0.90 * 9400 + 0.10 * 1800 = 8640
        assert result <= 8640

    def test_rapid_loss_reduces_fat_fraction(self, service):
        """Losing > 0.5 kg/week penalizes fat fraction (more lean loss)."""
        normal = service._estimate_energy_per_kg(body_fat_pct=25.0, slope=-0.05)
        rapid = service._estimate_energy_per_kg(body_fat_pct=25.0, slope=-0.15)
        # Rapid loss should have lower energy per kg (more lean tissue lost)
        assert rapid < normal
```

**Step 2: Run tests to verify they fail**

Run: `cd backend && pytest tests/unit/services/test_adaptive_tdee_logic.py::TestEnergyPerKg -v`
Expected: FAIL with `AttributeError: 'AdaptiveTDEEService' object has no attribute '_estimate_energy_per_kg'`

**Step 3: Write minimal implementation**

Add this method to `AdaptiveTDEEService` after `_filter_outliers` (after line 116):

```python
    def _estimate_energy_per_kg(self, body_fat_pct: float | None, slope: float) -> float:
        """
        Estimates energy content per kg of weight change using Forbes/Hall model.

        Higher body fat → more fat lost per kg → higher kcal/kg.
        Rapid loss → more lean tissue lost → lower kcal/kg.

        Args:
            body_fat_pct: User's body fat percentage (None = use default 7700).
            slope: Daily weight change in kg/day (negative = losing).

        Returns:
            Estimated kcal per kg of weight change (range: ~5600-8640).
        """
        if body_fat_pct is None:
            return self.KCAL_PER_KG_DEFAULT

        # Base fat fraction from body fat % (Forbes model)
        # At 25% bf: fat_fraction = 0.75 (baseline)
        # Each 1% bf above/below 25% shifts fraction by 0.005
        fat_fraction = 0.75 + (body_fat_pct - 25) * 0.005

        # Rapid loss penalty: losing > 0.5 kg/week means more lean tissue lost
        rate_weekly = abs(slope * 7)
        if rate_weekly > 0.5:
            fat_fraction -= 0.05 * (rate_weekly - 0.5)

        # Clamp to physiological bounds
        fat_fraction = max(0.50, min(0.90, fat_fraction))

        return fat_fraction * self.KCAL_PER_KG_FAT_MASS + (1 - fat_fraction) * self.KCAL_PER_KG_LEAN_MASS
```

**Step 4: Run tests to verify they pass**

Run: `cd backend && pytest tests/unit/services/test_adaptive_tdee_logic.py::TestEnergyPerKg -v`
Expected: All 7 PASS

**Step 5: Lint check**

Run: `cd backend && ruff check src/services/adaptive_tdee.py`
Expected: No errors

**Step 6: Commit**

```bash
git add backend/src/services/adaptive_tdee.py backend/tests/unit/services/test_adaptive_tdee_logic.py
git commit -m "feat(tdee-v2): add _estimate_energy_per_kg with Forbes/Hall dynamic energy density"
```

---

### Task 3: Wire Dynamic Energy into `calculate_tdee()`

**Files:**
- Modify: `backend/src/services/adaptive_tdee.py:129,204-205` (change default lookback + use dynamic energy)
- Test: `backend/tests/unit/services/test_adaptive_tdee_logic.py`

**Step 1: Write the failing test**

Add to `backend/tests/unit/services/test_adaptive_tdee_logic.py`:

```python
class TestCalculateTDEEIntegration:
    """Tests that calculate_tdee uses dynamic energy density and 4-week lookback."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock(spec=MongoDatabase)

    @pytest.fixture
    def service(self, mock_db):
        return AdaptiveTDEEService(mock_db)

    def test_default_lookback_is_4_weeks(self, service):
        """calculate_tdee should default to 4-week lookback."""
        import inspect
        sig = inspect.signature(service.calculate_tdee)
        default = sig.parameters["lookback_weeks"].default
        assert default == 4

    def test_tdee_uses_dynamic_energy_when_body_fat_available(self, service, mock_db):
        """When weight logs have body_fat_pct, TDEE should use dynamic energy density."""
        start = date(2025, 1, 1)
        weight_logs = []
        for i in range(15):
            weight_logs.append(WeightLog(
                user_email="test@test.com",
                date=start + timedelta(days=i),
                weight_kg=80.0 - (i * 0.05),
                body_fat_pct=25.0 if i >= 10 else None,  # Last 5 have body fat
            ))

        nutrition_logs = []
        for i in range(15):
            nutrition_logs.append(MockNutritionLog(
                start + timedelta(days=i), 2000
            ))

        mock_db.get_weight_logs_by_date_range.return_value = weight_logs
        mock_db.get_nutrition_logs_by_date_range.return_value = nutrition_logs
        mock_db.get_user_profile.return_value = None

        result = service.calculate_tdee("test@test.com", lookback_weeks=3)

        # TDEE should be calculated (not fallback)
        assert result["confidence"] != "none"
        assert result["tdee"] > 0
```

**Step 2: Run tests to verify they fail**

Run: `cd backend && pytest tests/unit/services/test_adaptive_tdee_logic.py::TestCalculateTDEEIntegration -v`
Expected: `test_default_lookback_is_4_weeks` FAIL (current default is 3)

**Step 3: Write minimal implementation**

In `backend/src/services/adaptive_tdee.py`, make two changes:

**Change A — Line 129:** Change default lookback from 3 to `DEFAULT_LOOKBACK_WEEKS`:
```python
    def calculate_tdee(self, user_email: str, lookback_weeks: int = 4) -> dict:
```

**Change B — Lines 204-205:** Replace fixed energy with dynamic energy:
```python
        # 4. Calculate TDEE (dynamic energy density)
        latest_body_fat = next(
            (log.body_fat_pct for log in reversed(weight_logs) if log.body_fat_pct is not None),
            None,
        )
        energy_per_kg = self._estimate_energy_per_kg(latest_body_fat, slope)
        daily_surplus_deficit = slope * energy_per_kg
        tdee = avg_calories_logged - daily_surplus_deficit
```

**Step 4: Run tests to verify they pass**

Run: `cd backend && pytest tests/unit/services/test_adaptive_tdee_logic.py::TestCalculateTDEEIntegration -v`
Expected: All PASS

**Step 5: Run ALL existing tests to check nothing broke**

Run: `cd backend && pytest tests/unit/services/test_adaptive_tdee_logic.py -v`
Expected: All PASS

**Step 6: Lint check**

Run: `cd backend && ruff check src/services/adaptive_tdee.py`
Expected: No errors

**Step 7: Commit**

```bash
git add backend/src/services/adaptive_tdee.py backend/tests/unit/services/test_adaptive_tdee_logic.py
git commit -m "feat(tdee-v2): wire dynamic energy density into calculate_tdee, change lookback to 4 weeks"
```

---

### Task 4: Remove Off-Track Penalty from `_calculate_coaching_target()`

**Files:**
- Modify: `backend/src/services/adaptive_tdee.py:616-679`
- Test: `backend/tests/unit/services/test_adaptive_tdee_logic.py`

**Step 1: Write the failing tests**

Add to `backend/tests/unit/services/test_adaptive_tdee_logic.py`:

```python
class TestCoachingTargetNoPenalty:
    """Tests that coaching target does NOT apply off-track penalty."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock(spec=MongoDatabase)

    @pytest.fixture
    def service(self, mock_db):
        return AdaptiveTDEEService(mock_db)

    def _make_profile(self, goal_type="lose", weekly_rate=0.5, gender="Masculino",
                      tdee_last_target=None, tdee_last_check_in=None):
        """Helper to create a mock profile."""
        profile = MagicMock()
        profile.goal_type = goal_type
        profile.weekly_rate = weekly_rate
        profile.gender = gender
        profile.tdee_last_target = tdee_last_target
        profile.tdee_last_check_in = tdee_last_check_in
        return profile

    def test_lose_target_no_penalty_when_off_track(self, service):
        """
        Even when actual rate (0.2 kg/week) < goal rate (0.5 kg/week),
        there should be NO extra penalty. Target = TDEE - deficit_needed only.
        """
        profile = self._make_profile(goal_type="lose", weekly_rate=0.5)
        tdee = 2200.0
        avg_calories = 1800.0
        weekly_change = -0.2  # Only losing 0.2 kg/week (off-track)

        target = service._calculate_coaching_target(tdee, avg_calories, weekly_change, profile)

        # Target should be TDEE - (0.5 * 1100) = 2200 - 550 = 1650
        # NOT 2200 - 550 - (0.3 * 1100) = 2200 - 550 - 330 = 1320
        assert target >= 1600, f"Target {target} is too low — penalty was applied!"
        assert target <= 1700

    def test_gain_target_no_penalty_when_off_track(self, service):
        """
        Even when not gaining fast enough, no extra surplus penalty.
        """
        profile = self._make_profile(goal_type="gain", weekly_rate=0.5)
        tdee = 2200.0
        avg_calories = 2500.0
        weekly_change = 0.2  # Only gaining 0.2 kg/week (off-track)

        target = service._calculate_coaching_target(tdee, avg_calories, weekly_change, profile)

        # Target should be TDEE + (0.5 * 1100) = 2200 + 550 = 2750
        # NOT 2200 + 550 + (0.3 * 1100) = 2200 + 550 + 330 = 3080
        assert target <= 2800, f"Target {target} is too high — penalty was applied!"
        assert target >= 2700

    def test_maintain_returns_tdee(self, service):
        """Maintain goal returns TDEE directly."""
        profile = self._make_profile(goal_type="maintain")
        target = service._calculate_coaching_target(2200.0, 2200.0, 0.0, profile)
        assert target == 2200

    def test_no_profile_returns_tdee(self, service):
        """No profile returns TDEE directly."""
        target = service._calculate_coaching_target(2200.0, 2200.0, 0.0, None)
        assert target == 2200
```

**Step 2: Run tests to verify they fail**

Run: `cd backend && pytest tests/unit/services/test_adaptive_tdee_logic.py::TestCoachingTargetNoPenalty -v`
Expected: `test_lose_target_no_penalty_when_off_track` FAIL (current code returns ~1320, assert >= 1600 fails)

**Step 3: Write minimal implementation**

Replace `_calculate_coaching_target` (lines 616-679) in `backend/src/services/adaptive_tdee.py`:

```python
    def _calculate_coaching_target(
        self,
        tdee: float,
        avg_calories: float,
        weekly_change: float,
        profile: "UserProfile | None",
    ) -> int:
        """
        Calculates daily_target using MacroFactor-inspired approach.

        v2 changes:
        - NO off-track penalty (adherence-neutral)
        - The adaptive TDEE naturally adjusts if user isn't progressing
        - Gradual adjustment applied separately via _apply_gradual_adjustment()

        Logic:
        1. If no profile or goal=maintain: return TDEE
        2. Calculate ideal_target = TDEE ± deficit/surplus for goal_rate
        3. Apply gradual adjustment (max ±100 kcal/week vs previous target)
        4. Apply safety floor (gender min + max 30% deficit)
        """
        if not profile or profile.goal_type == "maintain":
            return int(round(tdee))

        goal_rate = abs(profile.weekly_rate or 0.0)

        # Calculate ideal target based on goal — NO penalty for being off-track
        if profile.goal_type == "lose":
            deficit_needed = goal_rate * 1100
            ideal_target = int(round(tdee - deficit_needed))
        else:  # gain
            surplus_needed = goal_rate * 1100
            ideal_target = int(round(tdee + surplus_needed))

        # Apply gradual adjustment
        ideal_target = self._apply_gradual_adjustment(ideal_target, profile)

        # Apply safety floor
        ideal_target = self._apply_safety_floor(ideal_target, tdee, profile)

        return ideal_target
```

Note: This references `_apply_gradual_adjustment` and `_apply_safety_floor` which don't exist yet. For now, add stubs so existing tests pass:

```python
    def _apply_gradual_adjustment(self, ideal_target: int, profile: "UserProfile | None") -> int:
        """Stub — implemented in Task 5."""
        return ideal_target

    def _apply_safety_floor(self, target: int, tdee: float, profile: "UserProfile | None") -> int:
        """Stub — implemented in Task 6."""
        return max(1000, target)
```

**Step 4: Run tests to verify they pass**

Run: `cd backend && pytest tests/unit/services/test_adaptive_tdee_logic.py::TestCoachingTargetNoPenalty -v`
Expected: All 4 PASS

**Step 5: Run ALL existing tests**

Run: `cd backend && pytest tests/unit/services/test_adaptive_tdee_logic.py -v`
Expected: All PASS

**Step 6: Lint check**

Run: `cd backend && ruff check src/services/adaptive_tdee.py`
Expected: No errors

**Step 7: Commit**

```bash
git add backend/src/services/adaptive_tdee.py backend/tests/unit/services/test_adaptive_tdee_logic.py
git commit -m "feat(tdee-v2): remove off-track penalty from coaching target (MacroFactor approach)"
```

---

### Task 5: Implement `_apply_gradual_adjustment()` (Real ±100 kcal/week)

**Files:**
- Modify: `backend/src/services/adaptive_tdee.py` (replace stub)
- Test: `backend/tests/unit/services/test_adaptive_tdee_logic.py`

**Step 1: Write the failing tests**

Add to `backend/tests/unit/services/test_adaptive_tdee_logic.py`:

```python
class TestGradualAdjustment:
    """Tests that gradual adjustment caps changes to ±100 kcal/week."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock(spec=MongoDatabase)

    @pytest.fixture
    def service(self, mock_db):
        return AdaptiveTDEEService(mock_db)

    def _make_profile(self, tdee_last_target=None, tdee_last_check_in=None, **kwargs):
        profile = MagicMock()
        profile.goal_type = kwargs.get("goal_type", "lose")
        profile.weekly_rate = kwargs.get("weekly_rate", 0.5)
        profile.gender = kwargs.get("gender", "Masculino")
        profile.tdee_last_target = tdee_last_target
        profile.tdee_last_check_in = tdee_last_check_in
        return profile

    def test_first_time_no_previous_target(self, service):
        """First time: return ideal_target directly (no capping)."""
        profile = self._make_profile(tdee_last_target=None)
        result = service._apply_gradual_adjustment(1650, profile)
        assert result == 1650

    def test_small_change_within_100_passes_through(self, service):
        """Change of 80 kcal (< 100) passes through unchanged."""
        profile = self._make_profile(tdee_last_target=1600, tdee_last_check_in="2025-01-01")
        result = service._apply_gradual_adjustment(1680, profile)
        assert result == 1680

    def test_large_decrease_capped_at_minus_100(self, service):
        """Change of -300 kcal capped to -100."""
        profile = self._make_profile(tdee_last_target=1800, tdee_last_check_in="2025-01-01")
        result = service._apply_gradual_adjustment(1500, profile)
        assert result == 1700  # 1800 - 100

    def test_large_increase_capped_at_plus_100(self, service):
        """Change of +250 kcal capped to +100."""
        profile = self._make_profile(tdee_last_target=1500, tdee_last_check_in="2025-01-01")
        result = service._apply_gradual_adjustment(1750, profile)
        assert result == 1600  # 1500 + 100

    def test_check_in_too_recent_returns_previous(self, service):
        """If last check-in was < 7 days ago, return previous target."""
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        profile = self._make_profile(tdee_last_target=1600, tdee_last_check_in=yesterday)
        result = service._apply_gradual_adjustment(1400, profile)
        assert result == 1600  # No change

    def test_check_in_exactly_7_days_allows_adjustment(self, service):
        """If last check-in was exactly 7 days ago, allow adjustment."""
        seven_days_ago = (date.today() - timedelta(days=7)).isoformat()
        profile = self._make_profile(tdee_last_target=1800, tdee_last_check_in=seven_days_ago)
        result = service._apply_gradual_adjustment(1500, profile)
        assert result == 1700  # 1800 - 100
```

**Step 2: Run tests to verify they fail**

Run: `cd backend && pytest tests/unit/services/test_adaptive_tdee_logic.py::TestGradualAdjustment -v`
Expected: Most FAIL (stub just returns ideal_target)

**Step 3: Write minimal implementation**

Replace the stub `_apply_gradual_adjustment` in `backend/src/services/adaptive_tdee.py`:

```python
    def _apply_gradual_adjustment(self, ideal_target: int, profile: "UserProfile | None") -> int:
        """
        Caps target changes to ±MAX_WEEKLY_ADJUSTMENT kcal per check-in interval.

        This prevents jarring calorie target swings. If the user hasn't had a
        check-in in the last CHECK_IN_INTERVAL_DAYS, the target is adjusted by
        at most ±100 kcal from the previous target.

        Args:
            ideal_target: The calculated ideal calorie target.
            profile: User profile with previous target and check-in date.

        Returns:
            Adjusted target, capped to ±100 kcal from previous if applicable.
        """
        if not profile:
            return ideal_target

        prev_target = profile.tdee_last_target
        last_check_in = profile.tdee_last_check_in

        # First time: no previous target to cap against
        if prev_target is None or not isinstance(prev_target, int):
            return ideal_target

        # Check if enough time has passed since last check-in
        today = date.today()
        if last_check_in and isinstance(last_check_in, str):
            try:
                last_date = date.fromisoformat(last_check_in)
                if (today - last_date).days < self.CHECK_IN_INTERVAL_DAYS:
                    return prev_target  # Too soon, no change
            except (ValueError, TypeError):
                pass  # Invalid date, proceed with adjustment

        # Apply ±100 kcal cap
        diff = ideal_target - prev_target
        if abs(diff) <= self.MAX_WEEKLY_ADJUSTMENT:
            return ideal_target
        step = self.MAX_WEEKLY_ADJUSTMENT if diff > 0 else -self.MAX_WEEKLY_ADJUSTMENT
        return prev_target + step
```

**Step 4: Run tests to verify they pass**

Run: `cd backend && pytest tests/unit/services/test_adaptive_tdee_logic.py::TestGradualAdjustment -v`
Expected: All 6 PASS

**Step 5: Run ALL tests**

Run: `cd backend && pytest tests/unit/services/test_adaptive_tdee_logic.py -v`
Expected: All PASS

**Step 6: Lint check**

Run: `cd backend && ruff check src/services/adaptive_tdee.py`
Expected: No errors

**Step 7: Commit**

```bash
git add backend/src/services/adaptive_tdee.py backend/tests/unit/services/test_adaptive_tdee_logic.py
git commit -m "feat(tdee-v2): implement real gradual adjustment (±100 kcal/week cap)"
```

---

### Task 6: Implement `_apply_safety_floor()` (Gender Min + Max Deficit %)

**Files:**
- Modify: `backend/src/services/adaptive_tdee.py` (replace stub)
- Test: `backend/tests/unit/services/test_adaptive_tdee_logic.py`

**Step 1: Write the failing tests**

Add to `backend/tests/unit/services/test_adaptive_tdee_logic.py`:

```python
class TestSafetyFloor:
    """Tests gender-specific calorie floors and max deficit percentage."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock(spec=MongoDatabase)

    @pytest.fixture
    def service(self, mock_db):
        return AdaptiveTDEEService(mock_db)

    def _make_profile(self, gender="Masculino", **kwargs):
        profile = MagicMock()
        profile.gender = gender
        profile.goal_type = kwargs.get("goal_type", "lose")
        profile.weekly_rate = kwargs.get("weekly_rate", 0.5)
        profile.tdee_last_target = kwargs.get("tdee_last_target", None)
        profile.tdee_last_check_in = kwargs.get("tdee_last_check_in", None)
        return profile

    def test_male_floor_1500(self, service):
        """Male target should never go below 1500."""
        profile = self._make_profile(gender="Masculino")
        result = service._apply_safety_floor(1200, 2000.0, profile)
        assert result == 1500

    def test_female_floor_1200(self, service):
        """Female target should never go below 1200."""
        profile = self._make_profile(gender="Feminino")
        result = service._apply_safety_floor(1000, 2000.0, profile)
        assert result == 1200

    def test_max_deficit_30pct(self, service):
        """Target should not exceed 30% deficit from TDEE."""
        profile = self._make_profile(gender="Masculino")
        # TDEE=2500, 30% deficit = 1750. Target 1500 is 40% deficit → clamp to 1750
        result = service._apply_safety_floor(1500, 2500.0, profile)
        assert result == 1750

    def test_gender_floor_wins_over_deficit_pct(self, service):
        """When both apply, the HIGHER floor wins."""
        profile = self._make_profile(gender="Masculino")
        # TDEE=1800, 30% deficit = 1260. Male floor = 1500. Floor wins.
        result = service._apply_safety_floor(1100, 1800.0, profile)
        assert result == 1500

    def test_target_above_all_floors_unchanged(self, service):
        """Target above all floors passes through unchanged."""
        profile = self._make_profile(gender="Masculino")
        result = service._apply_safety_floor(1900, 2500.0, profile)
        assert result == 1900

    def test_no_profile_uses_generic_floor(self, service):
        """Without profile, use MIN_TDEE (1200) as generic floor."""
        result = service._apply_safety_floor(1000, 2000.0, None)
        assert result == 1200

    def test_gain_goal_no_deficit_floor(self, service):
        """For gain goals, deficit floor should not apply (target > TDEE)."""
        profile = self._make_profile(gender="Masculino", goal_type="gain")
        result = service._apply_safety_floor(2800, 2500.0, profile)
        assert result == 2800
```

**Step 2: Run tests to verify they fail**

Run: `cd backend && pytest tests/unit/services/test_adaptive_tdee_logic.py::TestSafetyFloor -v`
Expected: Most FAIL (stub just returns `max(1000, target)`)

**Step 3: Write minimal implementation**

Replace the stub `_apply_safety_floor` in `backend/src/services/adaptive_tdee.py`:

```python
    def _apply_safety_floor(self, target: int, tdee: float, profile: "UserProfile | None") -> int:
        """
        Applies gender-specific calorie floor and max deficit percentage.

        Three safety checks (highest floor wins):
        1. Gender minimum: 1200 (female) / 1500 (male)
        2. Max deficit: never exceed 30% below TDEE
        3. Absolute minimum: 1200 kcal (generic)

        Args:
            target: Proposed daily calorie target.
            tdee: User's estimated TDEE.
            profile: User profile with gender info.

        Returns:
            Target with safety floors applied.
        """
        if not profile:
            return max(self.MIN_TDEE, target)

        # Gender-specific minimum
        is_female = profile.gender in ("Feminino", "female")
        gender_min = self.MIN_CALORIES_FEMALE if is_female else self.MIN_CALORIES_MALE

        # Max deficit percentage (only for deficit goals)
        if profile.goal_type == "lose":
            min_by_deficit = int(round(tdee * (1 - self.MAX_DEFICIT_PCT)))
            return max(gender_min, min_by_deficit, target)

        # For gain/maintain, only gender floor applies
        return max(gender_min, target)
```

**Step 4: Run tests to verify they pass**

Run: `cd backend && pytest tests/unit/services/test_adaptive_tdee_logic.py::TestSafetyFloor -v`
Expected: All 7 PASS

**Step 5: Run ALL tests**

Run: `cd backend && pytest tests/unit/services/test_adaptive_tdee_logic.py -v`
Expected: All PASS

**Step 6: Lint check**

Run: `cd backend && ruff check src/services/adaptive_tdee.py`
Expected: No errors

**Step 7: Commit**

```bash
git add backend/src/services/adaptive_tdee.py backend/tests/unit/services/test_adaptive_tdee_logic.py
git commit -m "feat(tdee-v2): add gender-specific safety floors and max 30% deficit cap"
```

---

### Task 7: Improve Outlier Detection with Modified Z-Score

**Files:**
- Modify: `backend/src/services/adaptive_tdee.py:51-116` (`_filter_outliers`)
- Test: `backend/tests/unit/services/test_adaptive_tdee_logic.py`

**Step 1: Write the failing tests**

Add to `backend/tests/unit/services/test_adaptive_tdee_logic.py`:

```python
class TestModifiedZScoreOutlier:
    """Tests Modified Z-Score outlier detection as first pass."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock(spec=MongoDatabase)

    @pytest.fixture
    def service(self, mock_db):
        return AdaptiveTDEEService(mock_db)

    def _create_logs(self, weight_values, start_date=None):
        if start_date is None:
            start_date = date(2025, 1, 1)
        logs = []
        for i, w in enumerate(weight_values):
            logs.append(WeightLog(
                user_email="test@test.com",
                date=start_date + timedelta(days=i),
                weight_kg=w,
            ))
        return logs

    def test_statistical_outlier_detected(self, service):
        """A single extreme value among consistent data should be detected."""
        # 14 days at ~76 kg, one day at 82 kg (extreme outlier)
        weights = [76.0, 76.1, 75.9, 76.2, 76.0, 75.8, 76.1,
                   82.0,  # Statistical outlier
                   76.0, 76.1, 75.9, 76.2, 76.0, 75.8]
        logs = self._create_logs(weights)
        filtered, count = service._filter_outliers(logs)
        assert count >= 1
        # The 82.0 should be removed
        assert all(log.weight_kg < 80.0 for log in filtered)

    def test_no_outliers_in_consistent_data(self, service):
        """Consistent data with normal variation should have no outliers."""
        weights = [76.0, 76.2, 75.8, 76.1, 75.9, 76.3, 76.0,
                   75.7, 76.1, 76.2, 75.8, 76.0, 76.1, 75.9]
        logs = self._create_logs(weights)
        filtered, count = service._filter_outliers(logs)
        assert count == 0
        assert len(filtered) == 14
```

**Step 2: Run tests to verify they fail**

Run: `cd backend && pytest tests/unit/services/test_adaptive_tdee_logic.py::TestModifiedZScoreOutlier -v`
Expected: `test_statistical_outlier_detected` FAIL (current contextual logic may miss it if delta is <1.0 per day)

**Step 3: Write minimal implementation**

Replace `_filter_outliers` (lines 51-116) in `backend/src/services/adaptive_tdee.py`:

```python
    def _filter_outliers(self, logs: List[WeightLog]) -> tuple[List[WeightLog], int]:
        """
        Filters out weight anomalies using a two-pass approach:
        1. Modified Z-Score (statistical) — catches extreme one-off values
        2. Contextual (semantic) — handles step changes and transient spikes

        Returns:
            tuple: (filtered_logs, count_of_removed_logs)
        """
        if len(logs) < 3:
            return logs, 0

        sorted_logs = sorted(logs, key=lambda x: x.date)

        # === Pass 1: Modified Z-Score ===
        weights = np.array([log.weight_kg for log in sorted_logs])
        median = np.median(weights)
        mad = np.median(np.abs(weights - median))

        statistical_clean = []
        stat_removed = 0

        if mad > 0:
            modified_z_scores = 0.6745 * (weights - median) / mad
            for i, log in enumerate(sorted_logs):
                if abs(modified_z_scores[i]) > self.OUTLIER_MODIFIED_Z_THRESHOLD:
                    logger.info(
                        "Modified Z-Score outlier: %.1f kg on %s (z=%.2f)",
                        log.weight_kg, log.date, modified_z_scores[i],
                    )
                    stat_removed += 1
                else:
                    statistical_clean.append(log)
        else:
            # MAD=0 means all values are the same (or very close), no outliers
            statistical_clean = list(sorted_logs)

        if len(statistical_clean) < 3:
            return statistical_clean, stat_removed

        # === Pass 2: Contextual (spike/step-change) ===
        clean_logs = [statistical_clean[0]]
        last_valid_log = statistical_clean[0]
        contextual_removed = 0

        i = 1
        while i < len(statistical_clean):
            curr = statistical_clean[i]
            delta = abs(curr.weight_kg - last_valid_log.weight_kg)
            days_diff = (curr.date - last_valid_log.date).days

            if delta > self.MAX_DAILY_WEIGHT_CHANGE and days_diff <= 3:
                if i + 1 < len(statistical_clean):
                    next_log = statistical_clean[i + 1]
                    dist_to_baseline = abs(next_log.weight_kg - last_valid_log.weight_kg)

                    # Case A: Spike
                    if dist_to_baseline < delta:
                        logger.info(
                            "Ignoring transient weight spike: %s kg on %s",
                            curr.weight_kg, curr.date,
                        )
                        contextual_removed += 1
                        i += 1
                        continue

                    # Case B: Step Change
                    logger.info(
                        "Detected Step Change: %s -> %s. Resetting baseline.",
                        last_valid_log.weight_kg, curr.weight_kg,
                    )
                    contextual_removed += len(clean_logs)
                    clean_logs = [curr]
                    last_valid_log = curr
                    i += 1
                    continue

                logger.info(
                    "Last weight log shows large jump: %s -> %s",
                    last_valid_log.weight_kg, curr.weight_kg,
                )

            clean_logs.append(curr)
            last_valid_log = curr
            i += 1

        return clean_logs, stat_removed + contextual_removed
```

**Step 4: Run tests to verify they pass**

Run: `cd backend && pytest tests/unit/services/test_adaptive_tdee_logic.py::TestModifiedZScoreOutlier -v`
Expected: All 2 PASS

**Step 5: Run ALL existing outlier tests**

Run: `cd backend && pytest tests/unit/services/test_adaptive_tdee_logic.py::TestAdaptiveTDEELogic -v`
Expected: All PASS (water_drop, transient_spike, true_weight_loss, step_change_up)

**Step 6: Run ALL tests**

Run: `cd backend && pytest tests/unit/services/test_adaptive_tdee_logic.py -v`
Expected: All PASS

**Step 7: Lint check**

Run: `cd backend && ruff check src/services/adaptive_tdee.py`
Expected: No errors

**Step 8: Commit**

```bash
git add backend/src/services/adaptive_tdee.py backend/tests/unit/services/test_adaptive_tdee_logic.py
git commit -m "feat(tdee-v2): add Modified Z-Score as first pass in outlier detection"
```

---

### Task 8: End-to-End Integration Test with Production-Like Data

**Files:**
- Test: `backend/tests/unit/services/test_adaptive_tdee_logic.py`

**Step 1: Write the integration test**

Add to `backend/tests/unit/services/test_adaptive_tdee_logic.py`:

```python
class TestAdaptiveTDEEV2Integration:
    """
    End-to-end test simulating production data to verify v2 algorithm
    produces reasonable targets (not the old 1415 kcal bug).
    """

    @pytest.fixture
    def mock_db(self):
        return MagicMock(spec=MongoDatabase)

    @pytest.fixture
    def service(self, mock_db):
        return AdaptiveTDEEService(mock_db)

    def test_production_scenario_male_moderate_loss(self, service, mock_db):
        """
        Simulates the real production bug scenario:
        75kg male, 23% bf, goal lose 0.5kg/week, avg intake ~1900 kcal.
        OLD result: 1415 kcal (36% deficit — too aggressive!)
        NEW result: should be ~1650-1700 kcal (24% deficit — sustainable)
        """
        start = date(2025, 1, 1)

        # 28 days of weight logs: gradual decline 77 → 75.5
        weight_logs = []
        for i in range(28):
            w = 77.0 - (i * 0.054)  # ~0.054 kg/day = ~0.38 kg/week
            weight_logs.append(WeightLog(
                user_email="test@test.com",
                date=start + timedelta(days=i),
                weight_kg=round(w, 1),
                body_fat_pct=23.3 if i >= 20 else None,
            ))

        # 28 days of nutrition: avg ~1900 kcal
        nutrition_logs = []
        import random
        random.seed(42)
        for i in range(28):
            cal = 1900 + random.randint(-200, 200)
            nutrition_logs.append(MockNutritionLog(start + timedelta(days=i), cal))

        # Profile: male, lose 0.5 kg/week, no previous target (first calculation)
        profile = MagicMock()
        profile.goal_type = "lose"
        profile.weekly_rate = 0.5
        profile.gender = "Masculino"
        profile.target_weight = 72.0
        profile.tdee_last_target = None
        profile.tdee_last_check_in = None
        profile.height = 175
        profile.age = 45
        profile.weight = 75.0

        mock_db.get_weight_logs_by_date_range.return_value = weight_logs
        mock_db.get_nutrition_logs_by_date_range.return_value = nutrition_logs
        mock_db.get_user_profile.return_value = profile
        mock_db.update_user_coaching_target.return_value = None

        result = service.calculate_tdee("test@test.com", lookback_weeks=4)

        # The TDEE should be reasonable (around 2100-2300)
        assert 2000 <= result["tdee"] <= 2400, f"TDEE {result['tdee']} out of expected range"

        # The daily target should NOT be as low as 1415 (the old bug)
        assert result["daily_target"] >= 1500, (
            f"daily_target {result['daily_target']} is below male minimum — v2 bug!"
        )

        # The deficit should be at most 30%
        deficit_pct = (result["tdee"] - result["daily_target"]) / result["tdee"]
        assert deficit_pct <= 0.31, (
            f"Deficit {deficit_pct:.0%} exceeds 30% max — safety floor not working!"
        )

    def test_female_low_tdee_respects_1200_floor(self, service, mock_db):
        """Female user with low TDEE should not go below 1200."""
        start = date(2025, 1, 1)
        weight_logs = []
        for i in range(28):
            w = 55.0 - (i * 0.02)
            weight_logs.append(WeightLog(
                user_email="test@test.com",
                date=start + timedelta(days=i),
                weight_kg=round(w, 1),
            ))

        nutrition_logs = []
        for i in range(28):
            nutrition_logs.append(MockNutritionLog(start + timedelta(days=i), 1400))

        profile = MagicMock()
        profile.goal_type = "lose"
        profile.weekly_rate = 0.5
        profile.gender = "Feminino"
        profile.target_weight = 50.0
        profile.tdee_last_target = None
        profile.tdee_last_check_in = None
        profile.height = 160
        profile.age = 30
        profile.weight = 55.0

        mock_db.get_weight_logs_by_date_range.return_value = weight_logs
        mock_db.get_nutrition_logs_by_date_range.return_value = nutrition_logs
        mock_db.get_user_profile.return_value = profile
        mock_db.update_user_coaching_target.return_value = None

        result = service.calculate_tdee("test@test.com", lookback_weeks=4)

        assert result["daily_target"] >= 1200, (
            f"Female daily_target {result['daily_target']} below 1200 floor!"
        )
```

**Step 2: Run tests**

Run: `cd backend && pytest tests/unit/services/test_adaptive_tdee_logic.py::TestAdaptiveTDEEV2Integration -v`
Expected: All PASS

**Step 3: Run FULL test suite**

Run: `cd backend && pytest tests/unit/services/test_adaptive_tdee_logic.py -v`
Expected: All PASS

**Step 4: Lint check**

Run: `cd backend && ruff check src/services/adaptive_tdee.py`
Expected: No errors

**Step 5: Commit**

```bash
git add backend/tests/unit/services/test_adaptive_tdee_logic.py
git commit -m "test(tdee-v2): add integration tests with production-like data scenarios"
```

---

### Task 9: Clean Up Legacy Code and Remove Dead Constants

**Files:**
- Modify: `backend/src/services/adaptive_tdee.py`
- Test: Run all tests

**Step 1: Remove `KCAL_PER_KG_FAT` legacy alias**

In `backend/src/services/adaptive_tdee.py`, the `KCAL_PER_KG_FAT` constant is no longer used in `calculate_tdee` (replaced by dynamic `energy_per_kg` in Task 3). Remove the alias and update any remaining references in `_calculate_fallback_tdee` to use `KCAL_PER_KG_DEFAULT`:

Check if `KCAL_PER_KG_FAT` is still referenced anywhere:

Run: `cd backend && grep -n "KCAL_PER_KG_FAT" src/services/adaptive_tdee.py`

If only in the constant declaration, remove it. If referenced in `_calculate_fallback_tdee`, update to `KCAL_PER_KG_DEFAULT`.

**Step 2: Remove `RATE_THRESHOLD` constant**

The `RATE_THRESHOLD` constant is no longer used (off-track penalty removed). Remove it.

**Step 3: Run ALL tests**

Run: `cd backend && pytest tests/unit/services/test_adaptive_tdee_logic.py -v`
Expected: All PASS

**Step 4: Lint check**

Run: `cd backend && ruff check src/services/adaptive_tdee.py`
Expected: No errors

**Step 5: Run backend-wide tests for safety**

Run: `cd backend && pytest --timeout=30`
Expected: All PASS (or only unrelated failures)

**Step 6: Commit**

```bash
git add backend/src/services/adaptive_tdee.py
git commit -m "refactor(tdee-v2): remove legacy KCAL_PER_KG_FAT and RATE_THRESHOLD constants"
```

---

### Task 10: Final Verification and Squash

**Step 1: Run full backend test suite**

Run: `cd backend && pytest -v --timeout=30`
Expected: All PASS

**Step 2: Run ruff lint**

Run: `cd backend && ruff check .`
Expected: No errors

**Step 3: Verify the algorithm produces expected output**

Create a quick manual verification script:

```bash
cd backend && python -c "
from src.services.adaptive_tdee import AdaptiveTDEEService
s = AdaptiveTDEEService(None)

# Test dynamic energy at 23% bf
e = s._estimate_energy_per_kg(23.0, -0.05)
print(f'Energy at 23% bf: {e:.0f} kcal/kg')

# Test safety floor male
from unittest.mock import MagicMock
p = MagicMock()
p.gender = 'Masculino'
p.goal_type = 'lose'
floor = s._apply_safety_floor(1300, 2200.0, p)
print(f'Safety floor (male, 1300 target, 2200 TDEE): {floor}')

# Test safety floor female
p.gender = 'Feminino'
floor = s._apply_safety_floor(1100, 1800.0, p)
print(f'Safety floor (female, 1100 target, 1800 TDEE): {floor}')

print('All checks passed!')
"
```

Expected output:
```
Energy at 23% bf: ~7490 kcal/kg
Safety floor (male, 1300 target, 2200 TDEE): 1540
Safety floor (female, 1100 target, 1800 TDEE): 1260
All checks passed!
```

**Step 4: Review all commits**

Run: `git log --oneline -10`

Verify 9 commits from this feature are present and clean.

**Step 5: Done!**

The Adaptive TDEE v2 is complete. All changes are in:
- `backend/src/services/adaptive_tdee.py` (modified)
- `backend/tests/unit/services/test_adaptive_tdee_logic.py` (modified)

No frontend changes, no API changes, no new files (besides the plan/design docs).
