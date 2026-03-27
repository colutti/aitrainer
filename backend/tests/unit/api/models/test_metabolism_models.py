from src.api.models.metabolism import (
    MacroTargets,
    MetabolismResponse,
    WeightTrendPoint,
)


def test_metabolism_response_serializes_nested_fields():
    model = MetabolismResponse(
        tdee=2400,
        confidence="high",
        avg_calories=2200,
        weight_change_per_week=-0.3,
        logs_count=21,
        startDate="2026-03-01",
        endDate="2026-03-21",
        start_weight=82.4,
        end_weight=81.5,
        macro_targets=MacroTargets(protein=180, carbs=220, fat=70),
        weight_trend=[
            WeightTrendPoint(date="2026-03-20", weight=81.5, trend=81.7),
        ],
    )

    dumped = model.model_dump()
    assert dumped["macro_targets"]["protein"] == 180
    assert dumped["weight_trend"][0]["trend"] == 81.7
