"""Pydantic AI model factory for OpenRouter."""

from __future__ import annotations

from pydantic_ai.models.openrouter import OpenRouterModel, OpenRouterModelSettings
from pydantic_ai.providers.openrouter import OpenRouterProvider

from src.core.config import settings


def build_openrouter_model(provider_sort: str = "throughput") -> OpenRouterModel:
    """Build an OpenRouter model with production defaults."""
    model_settings = OpenRouterModelSettings(
        temperature=0.2,
        max_tokens=4096,
        parallel_tool_calls=False,
        service_tier=settings.OPENROUTER_SERVICE_TIER or None,
        openrouter_provider={"sort": provider_sort},
        openrouter_reasoning={"effort": "low", "exclude": True},
        openrouter_usage={"include": True},
    )
    # Pydantic AI's OpenRouterProvider owns the OpenRouter endpoint; base_url is
    # only used by our direct OpenAI-compatible embedding client.
    provider = OpenRouterProvider(api_key=settings.OPENROUTER_API_KEY)
    return OpenRouterModel(
        settings.OPENROUTER_CHAT_MODEL,
        provider=provider,
        settings=model_settings,
    )
