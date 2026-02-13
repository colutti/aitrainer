"""
Token pricing configuration for different LLM providers.
Prices are per 1 million tokens in USD.
Last updated: 2026-02-13

Pricing sources:
- Gemini: https://ai.google.dev/gemini-api/docs/pricing
- OpenAI: https://openai.com/api/pricing/
"""

# Prices per 1 million tokens (USD)
PROVIDER_PRICING = {
    "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
    "gemini-2.0-flash": {"input": 0.10, "output": 0.40},
    "gemini-3-flash-preview": {"input": 0.50, "output": 3.00},  # Primary model
    "gemini-3-pro": {"input": 2.00, "output": 12.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4o": {"input": 2.50, "output": 10.0},
    "gpt-5-mini": {"input": 2.50, "output": 2.00},  # As of February 2026
    "ollama": {"input": 0.0, "output": 0.0},  # Local model (free)
}


def get_cost_usd(model: str, tokens_input: int, tokens_output: int) -> float:
    """
    Calculate the cost in USD for a given model and token counts.

    Args:
        model: Model name (e.g., 'gemini-3-flash-preview')
        tokens_input: Number of input tokens
        tokens_output: Number of output tokens

    Returns:
        Cost in USD, rounded to 4 decimal places
    """
    if model not in PROVIDER_PRICING:
        return 0.0

    pricing = PROVIDER_PRICING[model]
    cost = (tokens_input * pricing["input"] + tokens_output * pricing["output"]) / 1_000_000
    return round(cost, 4)
