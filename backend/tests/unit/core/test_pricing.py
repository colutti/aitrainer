from src.core.pricing import get_cost_usd


def test_get_cost_usd_uses_per_million_token_rates():
    assert get_cost_usd("gpt-4o-mini", 100_000, 50_000) == 0.045


def test_get_cost_usd_returns_zero_for_unknown_model():
    assert get_cost_usd("unknown-model", 100, 100) == 0.0


def test_get_cost_usd_rounds_to_four_decimals():
    assert get_cost_usd("gemini-3-pro", 12_345, 67_890) == 0.8394
