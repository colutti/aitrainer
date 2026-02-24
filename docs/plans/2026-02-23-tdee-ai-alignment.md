# TDEE AI Alignment Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Enable the AI to access and align with actual TDEE calculations, and allow adjusting the activity_factor parameter based on lifestyle changes.

**Architecture:** Two new LangChain tools (`get_metabolism_data` and `update_tdee_params`) expose TDEE data to the AI trainer with full algorithm documentation. The `activity_factor` is stored per-user in the MongoDB profile and read by `AdaptiveTDEEService` instead of using hardcoded 1.45. This ensures the AI understands how TDEE is calculated and can make consistent recommendations.

**Tech Stack:** FastAPI, LangChain tools, MongoDB/Pydantic models, pytest, Python 3.12

---

## Task 1: Update UserProfile Model

**Files:**
- Modify: `backend/src/api/models/user_profile.py:105-112`
- Test: `backend/tests/test_models/test_user_profile.py` (existing, may need extension)

**Step 1: Read the current UserProfile**

Run: `cat backend/src/api/models/user_profile.py | grep -A 10 "Coaching Check-in"`

Expected: See the existing TDEE fields (`tdee_last_target`, `tdee_last_check_in`)

**Step 2: Add the new field**

Insert after line 112 (after `tdee_last_check_in`):

```python
    # TDEE Activity Factor (AI-adjustable)
    tdee_activity_factor: float | None = Field(
        default=None,
        ge=1.2,
        le=1.9,
        description="Activity factor for TDEE prior (AI-adjustable). "
                    "None = use system default (1.45). "
                    "Range: 1.2 (sedentary) to 1.9 (extremely active)."
    )
```

**Step 3: Verify syntax**

Run: `cd backend && python -m py_compile src/api/models/user_profile.py`

Expected: No output (success)

**Step 4: Commit**

```bash
cd backend
git add src/api/models/user_profile.py
git commit -m "feat: add tdee_activity_factor field to UserProfile"
```

---

## Task 2: Update AdaptiveTDEEService to Read activity_factor

**Files:**
- Modify: `backend/src/services/adaptive_tdee.py:434` and `backend/src/services/adaptive_tdee.py:839`
- Test: `backend/tests/test_services/test_adaptive_tdee.py` (existing, add new test cases)

**Step 1: Create failing test for activity_factor from profile**

Create file: `backend/tests/test_services/test_tdee_activity_factor.py`

```python
"""Test TDEE activity factor retrieval from profile."""
import pytest
from datetime import date, timedelta
from unittest.mock import MagicMock, patch
from src.services.adaptive_tdee import AdaptiveTDEEService
from src.api.models.user_profile import UserProfile
from src.api.models.weight_log import WeightLog
from src.api.models.nutrition_log import NutritionLog


def test_calculate_tdee_uses_profile_activity_factor():
    """Test that TDEE calculation uses activity_factor from profile if set."""
    # Mock database
    mock_db = MagicMock()
    service = AdaptiveTDEEService(mock_db)

    # Create profile with custom activity_factor
    profile = UserProfile(
        email="test@example.com",
        gender="Masculino",
        age=30,
        height=175,
        goal_type="maintain",
        tdee_activity_factor=1.2,  # Sedentary
    )

    # Create minimal weight/nutrition logs
    weight_logs = [
        WeightLog(
            user_email="test@example.com",
            date=date.today() - timedelta(days=20),
            weight_kg=80.0,
            bmr=1700,
        ),
        WeightLog(
            user_email="test@example.com",
            date=date.today() - timedelta(days=10),
            weight_kg=79.5,
            bmr=1700,
        ),
        WeightLog(
            user_email="test@example.com",
            date=date.today(),
            weight_kg=79.0,
            bmr=1700,
        ),
    ]

    nutrition_logs = [
        NutritionLog(
            user_email="test@example.com",
            date=date.today() - timedelta(days=i),
            calories=1800,
            partial_logged=False,
        )
        for i in range(20)
    ]

    # Mock database returns
    mock_db.get_weight_logs_by_date_range.return_value = weight_logs
    mock_db.get_nutrition_logs_by_date_range.return_value = nutrition_logs
    mock_db.get_user_profile.return_value = profile
    mock_db.update_user_coaching_target = MagicMock()

    # Calculate TDEE
    result = service.calculate_tdee("test@example.com", lookback_weeks=4)

    # Expected: formula_tdee = 1700 * 1.2 = 2040
    # The adaptive TDEE should be anchored to this prior
    expected_prior = 1700 * 1.2
    assert result["tdee"] > 0
    # Check that the result uses the adjusted prior (allow ±200 margin due to EMA)
    assert abs(result["tdee"] - expected_prior) < 300


def test_calculate_tdee_uses_default_activity_factor_when_none():
    """Test that TDEE calculation falls back to 1.45 when activity_factor is None."""
    mock_db = MagicMock()
    service = AdaptiveTDEEService(mock_db)

    # Profile WITHOUT custom activity_factor (None)
    profile = UserProfile(
        email="test@example.com",
        gender="Masculino",
        age=30,
        height=175,
        goal_type="maintain",
        tdee_activity_factor=None,  # Use default
    )

    weight_logs = [
        WeightLog(
            user_email="test@example.com",
            date=date.today() - timedelta(days=20),
            weight_kg=80.0,
            bmr=1700,
        ),
        WeightLog(
            user_email="test@example.com",
            date=date.today(),
            weight_kg=79.5,
            bmr=1700,
        ),
    ]

    nutrition_logs = [
        NutritionLog(
            user_email="test@example.com",
            date=date.today() - timedelta(days=i),
            calories=1800,
            partial_logged=False,
        )
        for i in range(20)
    ]

    mock_db.get_weight_logs_by_date_range.return_value = weight_logs
    mock_db.get_nutrition_logs_by_date_range.return_value = nutrition_logs
    mock_db.get_user_profile.return_value = profile
    mock_db.update_user_coaching_target = MagicMock()

    result = service.calculate_tdee("test@example.com", lookback_weeks=4)

    # Expected: formula_tdee = 1700 * 1.45 (default)
    expected_prior = 1700 * 1.45
    assert result["tdee"] > 0
    assert abs(result["tdee"] - expected_prior) < 300


def test_calculate_fallback_tdee_uses_profile_activity_factor():
    """Test that fallback TDEE also respects activity_factor."""
    mock_db = MagicMock()
    service = AdaptiveTDEEService(mock_db)

    profile = UserProfile(
        email="test@example.com",
        gender="Masculino",
        age=30,
        height=175,
        goal_type="maintain",
        tdee_activity_factor=1.725,  # Very active
    )

    # Minimal logs (will trigger fallback)
    weight_logs = [
        WeightLog(
            user_email="test@example.com",
            date=date.today(),
            weight_kg=80.0,
            bmr=1700,
        ),
    ]
    nutrition_logs = []

    mock_db.get_weight_logs_by_date_range.return_value = weight_logs
    mock_db.get_nutrition_logs_by_date_range.return_value = nutrition_logs
    mock_db.get_user_profile.return_value = profile

    result = service.calculate_tdee("test@example.com", lookback_weeks=4)

    # Expected: 1700 * 1.725 ≈ 2932.5
    expected = 1700 * 1.725
    assert result["tdee"] > 0
    assert abs(result["tdee"] - expected) < 100
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_services/test_tdee_activity_factor.py -v`

Expected: FAIL (AdaptiveTDEEService doesn't read activity_factor yet)

**Step 3: Modify calculate_tdee() to read activity_factor**

In `backend/src/services/adaptive_tdee.py`, line ~434 (in `calculate_tdee` method), find:

```python
base_bmr = scale_bmr or calc_bmr or (latest_weight * 22) or 1500
formula_tdee = base_bmr * 1.45
```

Replace with:

```python
base_bmr = scale_bmr or calc_bmr or (latest_weight * 22) or 1500
activity_factor = (profile.tdee_activity_factor or 1.45) if profile else 1.45
formula_tdee = base_bmr * activity_factor
```

**Step 4: Modify _calculate_fallback_tdee() to read activity_factor**

In the same file, line ~839 (in `_calculate_fallback_tdee` method), find:

```python
base_bmr = scale_bmr or calc_bmr or (latest_weight * 22) or 1500
tdee_est = base_bmr * 1.45
```

Replace with:

```python
base_bmr = scale_bmr or calc_bmr or (latest_weight * 22) or 1500
activity_factor = (profile.tdee_activity_factor or 1.45) if profile else 1.45
tdee_est = base_bmr * activity_factor
```

**Step 5: Run tests to verify they pass**

Run: `cd backend && pytest tests/test_services/test_tdee_activity_factor.py -v`

Expected: PASS (all 3 tests)

**Step 6: Run existing TDEE tests to verify no regression**

Run: `cd backend && pytest tests/test_services/test_adaptive_tdee.py -v`

Expected: PASS (all existing tests still pass)

**Step 7: Commit**

```bash
cd backend
git add src/services/adaptive_tdee.py tests/test_services/test_tdee_activity_factor.py
git commit -m "feat: read tdee_activity_factor from profile instead of hardcoded 1.45"
```

---

## Task 3: Create metabolism_tools.py

**Files:**
- Create: `backend/src/services/metabolism_tools.py`
- Test: `backend/tests/test_services/test_metabolism_tools.py`

**Step 1: Write the failing test**

Create: `backend/tests/test_services/test_metabolism_tools.py`

```python
"""Tests for metabolism tools (TDEE reading and parameter adjustment)."""
import pytest
from unittest.mock import MagicMock, patch
from datetime import date, timedelta
from src.services.metabolism_tools import (
    create_get_metabolism_tool,
    create_update_tdee_params_tool,
)
from src.api.models.user_profile import UserProfile
from src.api.models.weight_log import WeightLog
from src.api.models.nutrition_log import NutritionLog


def test_get_metabolism_tool_returns_tdee_data():
    """Test that get_metabolism_tool returns TDEE data with algorithm explanation."""
    mock_db = MagicMock()

    # Mock TDEE service
    with patch("src.services.metabolism_tools.AdaptiveTDEEService") as mock_tdee_service_class:
        mock_tdee_service = MagicMock()
        mock_tdee_service_class.return_value = mock_tdee_service

        # Mock TDEE calculation result
        mock_tdee_service.calculate_tdee.return_value = {
            "tdee": 1850,
            "daily_target": 1500,
            "confidence": "medium",
            "confidence_reason": "Partial adherence",
        }

        mock_profile = UserProfile(
            email="test@example.com",
            gender="Masculino",
            age=30,
            height=175,
            goal_type="maintain",
            tdee_activity_factor=1.45,
        )
        mock_db.get_user_profile.return_value = mock_profile

        # Create and call tool
        tool = create_get_metabolism_tool(mock_db, "test@example.com")
        result = tool()

        # Verify result contains TDEE data
        assert "TDEE atual" in result or "tdee" in result.lower()
        assert "1850" in result
        assert "1500" in result
        assert "COMO ESTE TDEE É CALCULADO" in result or "algoritmo" in result.lower()
        assert "MacroFactor" in result or "algoritmo" in result.lower()


def test_update_tdee_params_accepts_valid_activity_factor():
    """Test that update_tdee_params accepts values between 1.2 and 1.9."""
    mock_db = MagicMock()
    mock_profile = UserProfile(
        email="test@example.com",
        gender="Masculino",
        age=30,
        height=175,
        goal_type="maintain",
        tdee_activity_factor=1.45,
    )
    mock_db.get_user_profile.return_value = mock_profile

    tool = create_update_tdee_params_tool(mock_db, "test@example.com")

    # Test valid values
    for factor in [1.2, 1.375, 1.55, 1.725, 1.9]:
        result = tool(activity_factor=factor)
        assert "sucesso" in result.lower() or "updated" in result.lower()
        assert str(factor) in result or "atividade" in result.lower()


def test_update_tdee_params_rejects_invalid_activity_factor():
    """Test that update_tdee_params rejects values outside 1.2-1.9."""
    mock_db = MagicMock()
    mock_profile = UserProfile(
        email="test@example.com",
        gender="Masculino",
        age=30,
        height=175,
        goal_type="maintain",
        tdee_activity_factor=1.45,
    )
    mock_db.get_user_profile.return_value = mock_profile

    tool = create_update_tdee_params_tool(mock_db, "test@example.com")

    # Test invalid values
    for factor in [1.0, 1.19, 1.91, 2.0]:
        result = tool(activity_factor=factor)
        assert "erro" in result.lower() or "error" in result.lower() or "inválido" in result.lower()


def test_update_tdee_params_persists_to_database():
    """Test that update_tdee_params saves the new factor to the profile."""
    mock_db = MagicMock()
    mock_profile = UserProfile(
        email="test@example.com",
        gender="Masculino",
        age=30,
        height=175,
        goal_type="maintain",
        tdee_activity_factor=1.45,
    )
    mock_db.get_user_profile.return_value = mock_profile

    tool = create_update_tdee_params_tool(mock_db, "test@example.com")
    result = tool(activity_factor=1.2)

    # Verify database was called to save
    mock_db.save_user_profile.assert_called_once()
    saved_profile = mock_db.save_user_profile.call_args[0][0]
    assert saved_profile.tdee_activity_factor == 1.2
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_services/test_metabolism_tools.py -v`

Expected: FAIL (module doesn't exist)

**Step 3: Create metabolism_tools.py**

Create: `backend/src/services/metabolism_tools.py`

```python
"""
LangChain tools for TDEE and metabolism data access.
Provides AI trainer access to adaptive TDEE calculations with full algorithm documentation.
"""

from langchain_core.tools import tool
from src.core.logs import logger
from src.services.database import MongoDatabase
from src.services.adaptive_tdee import AdaptiveTDEEService


def create_get_metabolism_tool(database: MongoDatabase, user_email: str):
    """
    Factory function to create a get_metabolism_data tool with injected dependencies.
    """

    @tool
    def get_metabolism_data() -> str:
        """
        Consulta o TDEE adaptativo real do aluno e a meta calórica diária.

        USE ESTA TOOL SEMPRE que for falar sobre:
        - Calorias para comer (meta, déficit, superávit)
        - Metabolismo, TDEE, gasto energético
        - Progresso de peso em relação ao objetivo
        - Recomendações de nutrição personalizadas

        NUNCA use fórmulas padrão (Harris-Benedict, Mifflin-St Jeor, etc.)
        para estimar calorias. Os dados desta tool são sempre mais precisos
        porque usam dados reais do aluno.
        """
        try:
            tdee_service = AdaptiveTDEEService(database)
            tdee_data = tdee_service.calculate_tdee(user_email)
            profile = database.get_user_profile(user_email)

            # Format the response with algorithm explanation
            response = f"""=== METABOLISMO ADAPTATIVO DO ALUNO ===

TDEE atual: {tdee_data.get('tdee', 'N/A')} kcal
  → Calculado a partir de {tdee_data.get('weight_logs_count', '?')} pesagens de dados reais
  → Confiança: {tdee_data.get('confidence', 'desconhecida').upper()}
    ({tdee_data.get('confidence_reason', 'dados insuficientes')})

Meta diária: {tdee_data.get('daily_target', 'N/A')} kcal
  → Balanço energético: {tdee_data.get('energy_balance', 0):.0f} kcal
  → Status: {tdee_data.get('status', 'desconhecido').upper()}
  → Objetivo: {tdee_data.get('goal_type', 'manter')} peso
    ({tdee_data.get('goal_weekly_rate', 0)} kg/semana)

Fator de atividade atual: {profile.tdee_activity_factor or 1.45}
  → Usado como âncora inicial do cálculo
  → Pode ser ajustado via update_tdee_params() se o nível de atividade mudou

=== COMO ESTE TDEE É CALCULADO ===

Algoritmo: Adaptativo v3 (baseado no método MacroFactor / Stronger by Science)

Fórmula central (janela de 7 dias):
  TDEE_obs = média_calorias_7d − (Δpeso_tendência_7d ÷ 7) × energia_por_kg

Suavização final:
  EMA de 21 dias sobre as observações diárias
  Ancorada no prior: BMR × fator_atividade

Energia por kg de peso (modelo Forbes/Hall, 1987):
  fat_fraction = 0.75 + (gordura_corporal% − 25) × 0.005
  energia_por_kg = fat_fraction × 9400 + (1 − fat_fraction) × 1800
  Fallback sem dados de composição: 7700 kcal/kg

Peso suavizado: EMA 21 dias + interpolação linear (gaps ≤ 14 dias)

Por que é mais preciso que Harris-Benedict / Mifflin-St Jeor:
  Fórmulas estáticas erram ±20-30% pois ignoram adaptação metabólica.
  Este algoritmo usa dados reais do aluno e converge para o valor verdadeiro.

Referências:
  - Hall et al. (2012) "Quantification of the effect of energy imbalance on bodyweight"
  - Forbes (1987) "Human Body Composition"
  - MacroFactor methodology (https://macrofactorapp.com)

=== INSTRUÇÃO PARA O TREINADOR ===
Baseie TODAS as recomendações calóricas nos valores acima.
Se o aluno questionar os números, explique que são calculados
a partir do comportamento real do peso e calorias consumidas —
não de estimativas genéricas.
"""
            return response

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Failed to get metabolism data for %s: %s", user_email, e)
            return (
                "Erro ao buscar dados de metabolismo. "
                "Certifique-se de que há histórico de peso e nutrição registrado."
            )

    return get_metabolism_data


def create_update_tdee_params_tool(database: MongoDatabase, user_email: str):
    """
    Factory function to create an update_tdee_params tool with injected dependencies.
    """

    @tool
    def update_tdee_params(activity_factor: float) -> str:
        """
        Ajusta o fator de atividade usado no cálculo do TDEE adaptativo do aluno.

        Use quando o aluno reportar mudança SIGNIFICATIVA e PERMANENTE no nível
        de atividade do dia a dia (não treinos — esses já estão no TDEE adaptativo).

        Valores de referência:
        - 1.2   → Sedentário (trabalho de mesa, pouco movimento)
        - 1.375 → Levemente ativo (caminhadas, trabalho em pé)
        - 1.55  → Moderadamente ativo (trabalho físico leve)
        - 1.725 → Muito ativo (trabalho físico pesado, muito movimento)
        - 1.9   → Extremamente ativo (atleta, trabalho extenuante)

        IMPORTANTE: Não ajuste por causa de treinos (já capturados pelo adaptativo).
        Ajuste apenas quando o ESTILO DE VIDA base mudar.

        Exemplos válidos:
          - "Comecei a trabalhar em escritório" → 1.2
          - "Mudei de escritório para trabalho de pé" → 1.55

        Exemplos inválidos:
          - "Comecei a treinar 3x/semana" → NÃO ajustar (adaptativo já captura)
        """
        try:
            # Validate range
            if not isinstance(activity_factor, (int, float)):
                return (
                    "Erro: activity_factor deve ser um número entre 1.2 e 1.9. "
                    f"Recebido: {activity_factor}"
                )

            if activity_factor < 1.2 or activity_factor > 1.9:
                return (
                    f"Erro: activity_factor deve estar entre 1.2 e 1.9. "
                    f"Recebido: {activity_factor}. "
                    "Valores de referência: 1.2 (sedentário) até 1.9 (extremamente ativo)."
                )

            profile = database.get_user_profile(user_email)
            if not profile:
                return "Perfil do aluno não encontrado."

            old_factor = profile.tdee_activity_factor or 1.45
            profile.tdee_activity_factor = activity_factor
            database.save_user_profile(profile)

            activity_labels = {
                1.2: "sedentário",
                1.375: "levemente ativo",
                1.55: "moderadamente ativo",
                1.725: "muito ativo",
                1.9: "extremamente ativo",
            }
            label = activity_labels.get(activity_factor, f"{activity_factor}")

            logger.info(
                "User %s updated activity_factor from %s to %s",
                user_email,
                old_factor,
                activity_factor,
            )

            return (
                f"Fator de atividade atualizado com sucesso! "
                f"Novo fator: {activity_factor} ({label}). "
                f"O TDEE será recalculado no próximo check-in com este novo valor."
            )

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Failed to update TDEE params for %s: %s", user_email, e)
            return f"Erro ao atualizar parâmetros de metabolismo: {str(e)}"

    return update_tdee_params
```

**Step 4: Run tests to verify they pass**

Run: `cd backend && pytest tests/test_services/test_metabolism_tools.py -v`

Expected: PASS (all tests)

**Step 5: Commit**

```bash
cd backend
git add src/services/metabolism_tools.py tests/test_services/test_metabolism_tools.py
git commit -m "feat: create metabolism tools for TDEE access and activity_factor adjustment"
```

---

## Task 4: Update Tool Registry

**Files:**
- Modify: `backend/src/services/tool_registry.py:95-97`
- Test: (test indirectly via trainer integration)

**Step 1: Add tool metadata**

In `backend/src/services/tool_registry.py`, add two new entries to `TOOL_REGISTRY` dict after the memory tools:

```python
    # Metabolism (adaptive TDEE and parameters)
    "get_metabolism_data": ToolMetadata(
        "get_metabolism_data", ToolMemoryType.EPHEMERAL, "Get adaptive TDEE data"
    ),
    "update_tdee_params": ToolMetadata(
        "update_tdee_params", ToolMemoryType.MEMORABLE, "Update TDEE parameters (activity_factor)"
    ),
```

**Step 2: Verify syntax**

Run: `cd backend && python -m py_compile src/services/tool_registry.py`

Expected: No output

**Step 3: Commit**

```bash
cd backend
git add src/services/tool_registry.py
git commit -m "feat: register metabolism tools in tool registry"
```

---

## Task 5: Integrate Tools into Trainer Service

**Files:**
- Modify: `backend/src/services/trainer.py:1-40` (imports) and `~460` (tool instantiation)
- Test: (integration test via existing trainer tests)

**Step 1: Add imports**

At the top of `backend/src/services/trainer.py`, after the nutrition tool imports (line ~20), add:

```python
from src.services.metabolism_tools import (
    create_get_metabolism_tool,
    create_update_tdee_params_tool,
)
```

**Step 2: Instantiate tools in chat method**

Find the `chat` method in `trainer.py` (around line 400). After the memory tools are created, add:

```python
        # Metabolism tools (TDEE and activity_factor)
        get_metabolism_tool = create_get_metabolism_tool(self._database, user_email)
        update_tdee_params_tool = create_update_tdee_params_tool(
            self._database, user_email
        )
```

**Step 3: Add tools to the tools list**

Find where `tools` list is created in the `chat` method (around line 480). Add the two new tools to the list:

```python
        tools = [
            save_workout_tool,
            get_workouts_tool,
            save_nutrition_tool,
            get_nutrition_tool,
            save_composition_tool,
            get_composition_tool,
            list_hevy_routines_tool,
            create_hevy_routine_tool,
            update_hevy_routine_tool,
            search_hevy_exercises_tool,
            replace_hevy_exercise_tool,
            get_hevy_routine_detail_tool,
            set_routine_rest_and_ranges_tool,
            get_user_goal_tool,
            update_user_goal_tool,
            get_metabolism_tool,  # NEW
            update_tdee_params_tool,  # NEW
            save_memory_tool,
            search_memory_tool,
            list_raw_memories_tool,
            update_memory_tool,
            delete_memory_tool,
            delete_memories_batch_tool,
        ]
```

**Step 4: Verify syntax**

Run: `cd backend && python -m py_compile src/services/trainer.py`

Expected: No output

**Step 5: Run existing trainer tests**

Run: `cd backend && pytest tests/test_services/test_trainer.py -v -k chat`

Expected: All existing chat tests still pass

**Step 6: Commit**

```bash
cd backend
git add src/services/trainer.py
git commit -m "feat: integrate metabolism tools into trainer service"
```

---

## Task 6: Backend Linting and Full Test Suite

**Files:**
- All modified files (validation only)

**Step 1: Run backend linter**

Run: `cd backend && ruff check . --fix`

Expected: No errors (fixes auto-applied if any)

**Step 2: Run full backend test suite**

Run: `cd backend && pytest tests/ -v --tb=short`

Expected: All tests PASS

**Step 3: Run TDEE-specific tests**

Run: `cd backend && pytest tests/test_services/test_adaptive_tdee.py tests/test_services/test_tdee_activity_factor.py tests/test_services/test_metabolism_tools.py -v`

Expected: All PASS

**Step 4: Commit linting fixes (if any)**

```bash
cd backend
git add -A
git commit -m "fix: apply ruff linting fixes"
```

---

## Task 7: Documentation

**Files:**
- Create: `docs/TDEE_ALGORITHM.md` (reference doc for future developers)
- Modify: None (tool docstrings are self-documenting)

**Step 1: Create algorithm documentation**

Create: `docs/TDEE_ALGORITHM.md`

```markdown
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
```

**Step 2: Commit**

```bash
git add docs/TDEE_ALGORITHM.md
git commit -m "docs: add comprehensive TDEE algorithm documentation"
```

---

## Summary

| Task | Files | Tests | Time |
|------|-------|-------|------|
| 1. Update UserProfile | 1 modified | 0 new | 3 min |
| 2. Update AdaptiveTDEEService | 1 modified | 3 new | 5 min |
| 3. Create metabolism_tools.py | 1 created | 4 new | 8 min |
| 4. Update tool_registry | 1 modified | 0 new | 2 min |
| 5. Integrate into trainer service | 1 modified | 0 new | 3 min |
| 6. Linting + full tests | All | existing | 5 min |
| 7. Documentation | 1 created | 0 new | 5 min |

**Total effort:** ~30-40 minutes of development + testing

**Commits per task:** 1 per task = 7 total commits (clean history)

**QA Checkpoints:**
- After Task 2: TDEE algorithm uses profile activity_factor ✓
- After Task 3: Tools return proper data and explanations ✓
- After Task 5: Trainer service exposes tools to AI ✓
- After Task 6: No regressions, all tests pass ✓
