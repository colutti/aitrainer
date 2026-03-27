# TDEE Reset Feature Implementation Plan

> Execution workflow: use `.agent/workflows/executing-plans.md` to implement this plan in batches.

**Goal:** Allow users to reset their Adaptive TDEE baseline calculation from a specific date forward, removing the 21-day lagging effect of old data when their lifestyle changes significantly, without breaking the fallback mechanisms.

**Architecture:** We will implement Approach 2 (Soft Cut). We'll add `tdee_start_date` to the user profile. The database will still fetch all historical data to ensure weights exist for interpolation and fallback. However, during the TDEE observation EMA calculation (`_compute_tdee_from_observations`), we will slice the observations array and only compute the EMA starting from the `tdee_start_date` (or the first available observation after it). The new EMA period will start fresh anchored to the user's `activity_factor` * `BMR`. We will also add a new tool `reset_tdee_tracking` for the AI, and update the existing `update_tdee_params` prompt.

**Tech Stack:** Python 3.12, FastAPI, MongoDB, LangChain (Tools), Pytest

---

### Task 1: Add `tdee_start_date` to `UserProfile`

**Files:**
- Modify: `src/api/models/user_profile.py`
- Test: `tests/api/models/test_user_profile.py` (if it exists, otherwise create)

**Step 1: Write the failing test**

```python
# Create tests/api/models/test_user_profile.py if not exists
from src.api.models.user_profile import UserProfile

def test_user_profile_has_tdee_start_date():
    profile = UserProfile(email="test@example.com", name="Test")
    assert hasattr(profile, "tdee_start_date")
    assert profile.tdee_start_date is None

def test_user_profile_accepts_tdee_start_date():
    profile = UserProfile(email="test@example.com", name="Test", tdee_start_date="2026-03-06")
    assert profile.tdee_start_date == "2026-03-06"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/api/models/test_user_profile.py -v`
Expected: FAIL (ValidationError or AttributeError)

**Step 3: Write minimal implementation**

Modify `src/api/models/user_profile.py`:
```python
# Add to UserProfile class
    tdee_start_date: str | None = Field(
        None, description="ISO Date string to start TDEE EMA calculation from (format: YYYY-MM-DD)"
    )
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/api/models/test_user_profile.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/api/models/user_profile.py tests/api/models/test_user_profile.py
git commit -m "feat: add tdee_start_date to UserProfile model"
```

---

### Task 2: Update `AdaptiveTDEEService` to apply Soft Cut

**Files:**
- Modify: `src/services/adaptive_tdee.py`
- Test: `tests/services/test_adaptive_tdee.py`

**Step 1: Write the failing test**

```python
# In tests/services/test_adaptive_tdee.py
from datetime import date
import pytest

def test_compute_tdee_from_observations_with_start_date(adaptive_tdee_service):
    # Setup observations: 10 days of 2000 kcal, then user resets and eats 2500 kcal
    obs = [
        (date(2026, 3, i), 2000.0) for i in range(1, 11)
    ] + [
        (date(2026, 3, i), 2500.0) for i in range(11, 16)
    ]
    
    prior_tdee = 2500.0 # BMR * new activity factor
    
    # Without start date, EMA averages everything, pulling it down
    tdee_no_reset = adaptive_tdee_service._compute_tdee_from_observations(
        observations=obs, prior_tdee=prior_tdee
    )
    
    # With start date on the 11th, it should completely ignore days 1-10
    tdee_with_reset = adaptive_tdee_service._compute_tdee_from_observations(
        observations=obs, prior_tdee=prior_tdee, start_date=date(2026, 3, 11)
    )
    
    # The reset TDEE should be exactly 2500 because it only saw 2500 kcal days
    # starting from a 2500 prior. The no_reset will be dragged down by the 2000s.
    assert tdee_with_reset > tdee_no_reset
    assert pytest.approx(tdee_with_reset, 1) == 2500.0
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/services/test_adaptive_tdee.py::test_compute_tdee_from_observations_with_start_date -v`
Expected: FAIL (TypeError: got an unexpected keyword argument 'start_date')

**Step 3: Write minimal implementation**

Modify `src/services/adaptive_tdee.py` signature of `_compute_tdee_from_observations`:

```python
    def _compute_tdee_from_observations(
        self, 
        observations: list[tuple[date, float]], 
        prior_tdee: float, 
        span: int = 21,
        start_date: date | None = None
    ) -> float:
        """
        Computes TDEE from daily observations using EMA with prior.
        If start_date is provided, observations before it are ignored,
        effectively acting as a soft-reset of the adaptive algorithm.
        """
        if not observations:
            return prior_tdee
            
        # Apply soft cut
        if start_date:
            valid_obs = [obs for obs in observations if obs[0] >= start_date]
            if not valid_obs:
                # If there are no observations after the reset, return the prior
                return prior_tdee
            observations = valid_obs

        # ... existing ema logic (alpha = 2/(span+1), ema=prior_tdee, loop obs)
```
*(Make sure to pass `start_date` from the profile to this function down inside `calculate_tdee` in Step 3.5)*

**Step 3.5: Update `calculate_tdee` to pass the parameter**

Modify `src/services/adaptive_tdee.py` inside `calculate_tdee`:
```python
    # Step 2: ... (existing profile fetch)
    tdee_start_date_str = getattr(profile, "tdee_start_date", None)
    tdee_start_date = None
    if tdee_start_date_str:
        try:
            from datetime import date
            tdee_start_date = date.fromisoformat(tdee_start_date_str)
        except ValueError:
            pass
            
    # ...
    # Step 11: Compute TDEE from observations (Task 3)
    if observations:
        tdee = self._compute_tdee_from_observations(
            observations, 
            formula_tdee, 
            span=self.TDEE_OBS_EMA_SPAN,
            start_date=tdee_start_date
        )
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/services/test_adaptive_tdee.py -k test_compute_tdee_from_observations -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/services/adaptive_tdee.py tests/services/test_adaptive_tdee.py
git commit -m "feat: apply soft cut EMA reset in AdaptiveTDEEService based on tdee_start_date"
```

---

### Task 3: Create `reset_tdee_tracking` Tool

**Files:**
- Modify: `src/services/metabolism_tools.py`
- Test: `tests/services/test_metabolism_tools.py`

**Step 1: Write the failing test**

```python
# In tests/services/test_metabolism_tools.py
from src.services.metabolism_tools import create_reset_tdee_tracking_tool
from src.api.models.user_profile import UserProfile
from datetime import date

def test_reset_tdee_tracking_tool(mock_db):
    # Setup mock user profile
    profile = UserProfile(email="test@user.com", name="Test")
    mock_db.get_user_profile.return_value = profile
    
    tool = create_reset_tdee_tracking_tool(mock_db, "test@user.com")
    result = tool.invoke({"start_date_iso": "2026-03-06"})
    
    assert "sucesso" in result.lower()
    assert profile.tdee_start_date == "2026-03-06"
    mock_db.save_user_profile.assert_called_once_with(profile)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/services/test_metabolism_tools.py -k test_reset_tdee_tracking_tool -v`
Expected: FAIL (ImportError)

**Step 3: Write minimal implementation**

Modify `src/services/metabolism_tools.py`:

```python
# Add new tool factory
def create_reset_tdee_tracking_tool(database: MongoDatabase, user_email: str):
    """Factory function for the TDEE reset tool."""

    @tool
    def reset_tdee_tracking(start_date_iso: str) -> str:
        """
        Zera o histórico do algoritmo adaptativo de TDEE, descartando os dados anteriores
        à data informada no cálculo da Média Móvel. 
        
        USE ESTA TOOL quando o aluno reportar que mudou radicalmente sua rotina de 
        treinos/atividade física recentemente, e a meta calórica atual sugerida
        parece muito baixa ou incorreta por causa de um "atraso/lag" do algoritmo 
        (que ainda está puxando a média para baixo com dados de quando o aluno gastava menos).
        
        Args:
            start_date_iso (str): A data a partir da qual o algoritmo deve começar 
                                  a considerar os dados para a média. Formato YYYY-MM-DD.
                                  Se a mudança foi hoje, passe a data de hoje.
        """
        try:
            profile = database.get_user_profile(user_email)
            if not profile:
                return "Perfil do aluno não encontrado."
                
            profile.tdee_start_date = start_date_iso
            database.save_user_profile(profile)
            
            logger.info("User %s reset TDEE tracking from date %s", user_email, start_date_iso)
            
            return (
                f"Histórico adaptativo resetado com sucesso! O algoritmo agora usará "
                f"somente dados de dieta e peso a partir de {start_date_iso}. "
                f"A nova meta será recalculada imediatamente."
            )
        except Exception as e:
            logger.error("Failed to reset TDEE tracking for %s: %s", user_email, e)
            return f"Erro ao resetar histórico: {str(e)}"

    return reset_tdee_tracking
```
*(Remember to export it if `__all__` is defined)*

**Step 3.5: Register the tool in the agent**

Check `src/trainers/trainer_agent.py` or wherever tools are gathered (likely `src/services/trainer_service.py` etc.). Find where `create_get_metabolism_tool` and `create_update_tdee_params_tool` are called and add `create_reset_tdee_tracking_tool(self.db, user_email)`. Also import the tool function there.

**Step 4: Run test to verify it passes**

Run: `pytest tests/services/test_metabolism_tools.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/services/metabolism_tools.py tests/services/test_metabolism_tools.py 
# And the file where the tool was registered
git commit -m "feat: add reset_tdee_tracking AI tool"
```

---

### Task 4: Update `update_tdee_params` prompt

**Files:**
- Modify: `src/services/metabolism_tools.py`

**Step 1: Modify the docstring prompt in `update_tdee_params`**

In `src/services/metabolism_tools.py` under `@tool def update_tdee_params`.
Change the strict restriction against using it for workouts to authorize it in tandem with the reset.

```python
        """
        Ajusta o fator de atividade usado no cálculo do TDEE adaptativo do aluno.

        Valores de referência:
        ... (keep previous values)
        
        IMPORTANTE: 
        O algoritmo adaptativo normalmente aprende sozinho sobre novos treinos. 
        PORÉM, se o aluno aumentou muito o volume de treino RECENTEMENTE e
        a meta calórica atual está visivelmente "atrasada" (muito baixa), você DEVE:
        1. Usar esta tool para aumentar o fator de atividade (ex: ir para 1.55 ou 1.725)
        2. E EM SEGUIDA, usar a tool `reset_tdee_tracking(today)` para forçar
           o algoritmo a descartar a inércia do passado.
        """
```

**Step 2: Commit**

```bash
git add src/services/metabolism_tools.py
git commit -m "chore: update update_tdee_params instructions to allow workout-based resets"
```

---

### Task 5: Security & Lint Checks

**Step 1: Run complete backend checks**

Run: `cd backend && ruff check .`
Run: `cd backend && pytest`
Run: `make security-check`

**Step 2: Fix any issues**

If `ruff` complains about long lines in docstrings or unused imports, fix them to meet the ZERO warning requirement.

**Step 3: Final Commit**

```bash
git add .
git commit -m "chore: pass all lint and sec checks for TDEE reset feature"
```
