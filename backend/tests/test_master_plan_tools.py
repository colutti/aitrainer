from unittest.mock import MagicMock

from src.services.plan_tools import create_upsert_plan_tool


def valid_payload() -> dict:
    return {
        'title': 'Plano Mestre',
        'change_reason': 'initial_plan',
        'goal': {
            'primary': 'lose_fat',
            'objective_summary': 'Chegar a 15% de gordura',
            'success_criteria': ['aderencia'],
        },
        'timeline': {'target_date': '2026-09-01T00:00:00', 'review_cadence': 'quinzenal'},
        'strategy': {
            'rationale': 'deficit moderado',
            'adaptation_policy': 'ajustes por evidencia',
            'constraints': [],
            'preferences': [],
            'current_risks': [],
        },
        'nutrition_strategy': {
            'daily_targets': {'calories': 2200, 'protein_g': 180},
            'adherence_notes': [],
        },
        'training_program': {
            'split_name': 'upper_lower',
            'frequency_per_week': 4,
            'session_duration_min': 55,
            'routines': [
                {
                    'id': 'upper_a',
                    'name': 'Upper A',
                    'exercises': [
                        {'name': 'Supino', 'sets': 4, 'reps': '6-8', 'load_guidance': 'RPE 8'}
                    ],
                }
            ],
            'weekly_schedule': [
                {'day': 'monday', 'routine_id': 'upper_a', 'focus': 'upper', 'type': 'training'}
            ],
        },
        'current_summary': {'active_focus': 'consistencia', 'rationale': 'base de 2 semanas'},
        'checkpoints': [],
    }


def test_upsert_plan_rejects_missing_required_fields():
    db = MagicMock()
    db.get_latest_plan.return_value = None

    tool = create_upsert_plan_tool(db, 'user@test.com')

    payload = valid_payload()
    payload['training_program'] = {}

    result = tool.invoke(payload)

    assert 'ERRO_UPSERT_PLAN_INCOMPLETO' in result
    db.save_plan.assert_not_called()


def test_upsert_plan_saves_master_plan_with_single_call():
    db = MagicMock()
    db.get_latest_plan.return_value = None
    db.save_plan.return_value = 'plan_123'

    tool = create_upsert_plan_tool(db, 'user@test.com')

    result = tool.invoke(valid_payload())

    assert 'SUCESSO_UPSERT_PLAN' in result
    db.save_plan.assert_called_once()
