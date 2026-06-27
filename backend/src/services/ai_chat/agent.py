"""Pydantic AI agent construction."""

from __future__ import annotations

from pydantic_ai import Agent

from src.services.ai_chat.deps import ChatAgentDeps
from src.services.ai_chat.model_factory import build_openrouter_model
from src.services.ai_chat.models import CoachTurnOutput
from src.services.ai_chat.prompts import CHAT_AGENT_INSTRUCTIONS


def build_chat_agent() -> Agent[ChatAgentDeps, CoachTurnOutput]:
    """Create the production chat agent."""
    return Agent(
        build_openrouter_model(),
        deps_type=ChatAgentDeps,
        output_type=CoachTurnOutput,
        instructions=CHAT_AGENT_INSTRUCTIONS,
        retries=2,
    )
