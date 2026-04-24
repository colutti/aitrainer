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
        'current_summary': {
            'active_focus': 'consistencia',
            'rationale': 'base de 2 semanas',
            'next_review': '2026-09-15',
        },
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
    assert 'PLANO_NAO_SALVO' in result
    db.save_plan.assert_not_called()


def test_upsert_plan_rejects_missing_next_review():
    db = MagicMock()
    db.get_latest_plan.return_value = None
    tool = create_upsert_plan_tool(db, 'user@test.com')

    payload = valid_payload()
    payload['current_summary'].pop('next_review')

    result = tool.invoke(payload)

    assert 'ERRO_UPSERT_PLAN_INCOMPLETO' in result
    assert 'current_summary.next_review' in result
    db.save_plan.assert_not_called()


def test_upsert_plan_saves_master_plan_with_single_call():
    db = MagicMock()
    db.get_latest_plan.return_value = None
    db.save_plan.return_value = 'plan_123'

    tool = create_upsert_plan_tool(db, 'user@test.com')

    result = tool.invoke(valid_payload())

    assert 'SUCESSO_UPSERT_PLAN' in result
    db.save_plan.assert_called_once()


def test_upsert_plan_loop_guard_marks_not_saved_state():
    db = MagicMock()
    db.get_latest_plan.return_value = None
    db.save_plan.return_value = 'plan_123'
    tool = create_upsert_plan_tool(db, 'user@test.com')

    payload = valid_payload()
    tool.invoke(payload)
    payload2 = valid_payload()
    payload2['title'] = 'Plano Mestre v2'
    tool.invoke(payload2)
    payload3 = valid_payload()
    payload3['title'] = 'Plano Mestre v3'
    tool.invoke(payload3)
    payload4 = valid_payload()
    payload4['title'] = 'Plano Mestre v4'
    result = tool.invoke(payload4)

    assert 'ERRO_UPSERT_PLAN_LOOP_GUARD' in result
    assert 'PLANO_NAO_SALVO' in result


def test_upsert_plan_rejects_schedule_with_unknown_routine_reference():
    db = MagicMock()
    db.get_latest_plan.return_value = None
    tool = create_upsert_plan_tool(db, 'user@test.com')

    payload = valid_payload()
    payload['training_program']['weekly_schedule'] = [
        {'day': 'monday', 'routine_id': 'inexistente', 'focus': 'upper', 'type': 'training'}
    ]

    result = tool.invoke(payload)

    assert 'ERRO_UPSERT_PLAN_ESTRUTURA_INVALIDA' in result
    assert 'PLANO_NAO_SALVO' in result
    db.save_plan.assert_not_called()
