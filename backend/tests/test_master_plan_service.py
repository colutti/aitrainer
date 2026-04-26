from datetime import datetime

from src.api.models.plan import PlanUpsertInput
from src.services.plan_service import (
    build_plan_prompt_snapshot,
    build_plan_singleton,
    format_plan_snapshot,
    missing_master_plan_fields,
)


def make_payload() -> PlanUpsertInput:
    return PlanUpsertInput(
        title='Plano Mestre Teste',
        change_reason='initial_plan',
        goal={
            'primary': 'lose_fat',
            'objective_summary': 'Chegar a 15% de gordura corporal',
            'success_criteria': ['aderencia 80%'],
        },
        timeline={
            'target_date': datetime(2026, 9, 1),
            'review_cadence': 'quinzenal',
        },
        strategy={
            'rationale': 'deficit moderado e progressao de forca',
            'adaptation_policy': 'ajustes por evidencia',
            'constraints': ['dor no ombro'],
            'preferences': ['treino matinal'],
            'current_risks': ['sono irregular'],
        },
        nutrition_strategy={
            'daily_targets': {
                'calories': 2200,
                'protein_g': 180,
                'carbs_g': 200,
                'fat_g': 70,
            },
            'adherence_notes': ['hidratar 3L'],
        },
        training_program={
            'split_name': 'push_pull_legs',
            'frequency_per_week': 5,
            'session_duration_min': 60,
            'routines': [
                {
                    'id': 'push_a',
                    'name': 'Push A',
                    'exercises': [
                        {
                            'name': 'Supino Reto',
                            'sets': 4,
                            'reps': '6-8',
                            'load_guidance': 'RPE 8',
                        }
                    ],
                }
            ],
            'weekly_schedule': [
                {
                    'day': 'monday',
                    'routine_id': 'push_a',
                    'focus': 'push',
                    'type': 'training',
                }
            ],
        },
        current_summary={
            'active_focus': 'consistencia',
            'rationale': 'executar bloco base por 2 semanas',
            'key_risks': ['baixa adesao'],
            'next_review': '2026-09-15',
        },
        checkpoints=[],
    )


def test_missing_master_plan_fields_detects_contract_gaps():
    payload = make_payload()
    payload.training_program = {}

    missing = missing_master_plan_fields(payload)

    assert 'training_program.split_name' in missing
    assert 'training_program.routines' in missing


def test_build_plan_singleton_builds_master_plan_structure():
    payload = make_payload()

    plan = build_plan_singleton('user@test.com', None, payload)

    assert plan.goal.primary == 'lose_fat'
    assert plan.timeline.review_cadence == 'quinzenal'
    assert plan.nutrition_strategy.daily_targets.protein_g == 180
    assert plan.training_program.routines[0].name == 'Push A'


def test_plan_snapshot_contains_full_master_context():
    payload = make_payload()
    plan = build_plan_singleton('user@test.com', None, payload)

    snapshot = build_plan_prompt_snapshot(plan)
    text = format_plan_snapshot(snapshot)

    assert snapshot is not None
    assert snapshot.goal_primary == 'lose_fat'
    assert snapshot.training_split == 'push_pull_legs'
    assert 'Plano mestre ativo' in text
    assert 'Metas nutricionais diarias' in text


def test_build_plan_singleton_accepts_string_timeline_start_date():
    payload = make_payload()
    payload.timeline = {
        'start_date': '2026-04-26T00:00:00',
        'review_cadence': 'quinzenal',
    }

    plan = build_plan_singleton('user@test.com', None, payload)

    assert plan.timeline.start_date == datetime(2026, 4, 26, 0, 0, 0)
    assert plan.timeline.target_date == datetime(2026, 7, 19, 0, 0, 0)
