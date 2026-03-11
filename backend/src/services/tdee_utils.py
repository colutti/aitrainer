"""Utility functions for TDEE calculations and body composition analysis."""
from typing import List, cast, TYPE_CHECKING

if TYPE_CHECKING:
    from src.api.models.weight_log import WeightLog
    from src.api.models.user_profile import UserProfile

def calculate_macro_targets(daily_target: int, weight_kg: float) -> dict:
    """
    Calculates macro targets ensuring total calories = daily_target.
    """
    # Protein: 1.8g per kg, cap at 40% of target
    ideal_protein_g = weight_kg * 1.8
    protein_kcal_max = daily_target * 0.40
    ideal_protein_g = min(ideal_protein_g, protein_kcal_max / 4)
    protein_g = int(round(ideal_protein_g))
    protein_kcal = protein_g * 4

    # Fat: 27% of daily target
    fat_kcal = daily_target * 0.27
    fat_g = int(round(fat_kcal / 9))
    fat_kcal = fat_g * 9

    # Carbs: remainder
    remaining_kcal = daily_target - protein_kcal - fat_kcal
    carb_g = int(round(max(0, remaining_kcal / 4)))

    return {"protein": protein_g, "carbs": carb_g, "fat": fat_g}

def calculate_body_composition_changes(logs: List["WeightLog"]) -> dict | None:
    """Calculate fat and muscle mass changes using scale data."""
    valid_logs = [log for log in logs if log.body_fat_pct is not None]
    if len(valid_logs) < 2:
        return None

    first, last = valid_logs[0], valid_logs[-1]
    fat_mass_start = first.weight_kg * (cast(float, first.body_fat_pct) / 100.0)
    fat_mass_end = last.weight_kg * (cast(float, last.body_fat_pct) / 100.0)
    fat_change = fat_mass_end - fat_mass_start

    muscle_change = None
    if first.muscle_mass_kg is not None and last.muscle_mass_kg is not None:
        muscle_change = last.muscle_mass_kg - first.muscle_mass_kg
    elif first.muscle_mass_pct and last.muscle_mass_pct:
        m_start = first.weight_kg * (first.muscle_mass_pct / 100.0)
        m_end = last.weight_kg * (last.muscle_mass_pct / 100.0)
        muscle_change = m_end - m_start
    else:
        muscle_change = (last.weight_kg - first.weight_kg) - fat_change

    res = {
        "fat_change_kg": round(fat_change, 2),
        "muscle_change_kg": round(muscle_change, 2),
        "start_fat_pct": round(cast(float, first.body_fat_pct), 2),
        "end_fat_pct": round(cast(float, last.body_fat_pct), 2),
    }

    if first.muscle_mass_pct:
        res["start_muscle_pct"] = round(cast(float, first.muscle_mass_pct), 2)
    elif first.muscle_mass_kg:
        res["start_muscle_pct"] = round(first.muscle_mass_kg / first.weight_kg * 100, 2)

    if last.muscle_mass_pct:
        res["end_muscle_pct"] = round(cast(float, last.muscle_mass_pct), 2)
    elif last.muscle_mass_kg:
        res["end_muscle_pct"] = round(last.muscle_mass_kg / last.weight_kg * 100, 2)

    res["start_muscle_kg"] = (
        round(first.muscle_mass_kg, 2) if first.muscle_mass_kg else None
    )
    res["end_muscle_kg"] = (
        round(last.muscle_mass_kg, 2) if last.muscle_mass_kg else None
    )

    return res
