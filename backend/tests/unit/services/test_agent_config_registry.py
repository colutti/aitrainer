"""Tests for file-backed agent config registry."""

import pytest

from src.services.agents.config_registry import AgentConfigRegistry


def test_registry_loads_node_configs():
    registry = AgentConfigRegistry("src/services/agents/config")
    configs = registry.list_node_configs()
    assert len(configs) >= 7
    names = {cfg.node_name for cfg in configs}
    assert "plan_specialist" in names
    assert "prompt_security" in names
    assert "coach_reply" in names


def test_registry_returns_single_node():
    registry = AgentConfigRegistry("src/services/agents/config")
    cfg = registry.get_node_config("nutrition_specialist")
    assert cfg.node_name == "nutrition_specialist"
    assert cfg.prompt_text
    assert cfg.config_hash


def test_registry_exposes_context_contract_fields():
    registry = AgentConfigRegistry("src/services/agents/config")
    cfg = registry.get_node_config("coach_reply")
    assert cfg.context_blocks
    assert "trainer_persona" in cfg.context_blocks
    assert "history_summary" in cfg.context_blocks
    assert "plan_specialist" in cfg.peer_inputs
    assert cfg.persona_mode == "final_only"
    assert cfg.output_contract == "text"


def test_registry_rejects_invalid_persona_mode(tmp_path):
    base = tmp_path / "config"
    (base / "nodes").mkdir(parents=True)
    (base / "prompts").mkdir(parents=True)
    (base / "prompts" / "x.md").write_text("prompt", encoding="utf-8")
    (base / "nodes" / "x.json").write_text(
        '{"node_name":"x","enabled":true,"model_provider":"openrouter",'
        '"model_name":"openai/gpt-4.1-nano","temperature":0,"max_tokens":256,'
        '"tool_policy":"restricted","tool_names":[],"prompt_file":"'
        + str(base / "prompts" / "x.md")
        + '","response_format":"text","version":"v1","context_blocks":["request"],'
        '"peer_inputs":[],"persona_mode":"invalid","output_contract":"text"}',
        encoding="utf-8",
    )
    registry = AgentConfigRegistry(base)
    with pytest.raises(ValueError, match="persona_mode"):
        registry.list_node_configs()


def test_node_contract_defaults_match_runtime_design():
    registry = AgentConfigRegistry("src/services/agents/config")
    session_context = registry.get_node_config("session_context")
    coach = registry.get_node_config("coach_reply")
    security = registry.get_node_config("prompt_security")
    training = registry.get_node_config("training_specialist")
    plan = registry.get_node_config("plan_specialist")
    nutrition = registry.get_node_config("nutrition_specialist")
    memory_hub = registry.get_node_config("memory_hub")

    assert coach.persona_mode == "final_only"
    assert training.persona_mode == "none"
    assert nutrition.persona_mode == "none"
    assert plan.persona_mode == "none"
    assert security.persona_mode == "none"
    assert memory_hub.persona_mode == "none"
    assert "trainer_persona" in coach.context_blocks
    assert "history_summary" in coach.context_blocks
    assert "history_summary_neutral" in training.context_blocks
    assert "history_summary_neutral" in nutrition.context_blocks
    assert "history_summary_neutral" in plan.context_blocks
    assert "history_summary" not in training.context_blocks
    assert "history_summary" not in nutrition.context_blocks
    assert "history_summary" not in plan.context_blocks
    assert "trainer_identity" not in session_context.context_blocks
    assert "trainer_identity" not in training.context_blocks
    assert "trainer_identity" not in nutrition.context_blocks
    assert "trainer_identity" not in plan.context_blocks
    assert security.context_blocks == ["request"]
    assert security.model_name == "google/gemini-2.5-flash-lite"
    assert "trainer_persona" not in training.context_blocks
    assert training.model_name == "google/gemini-3.1-flash-lite-preview"
    assert "save_workout" in training.tool_names
    assert "save_daily_nutrition" in nutrition.tool_names
    assert nutrition.model_name == "google/gemini-3.1-flash-lite-preview"
    assert "upsert_plan" in plan.tool_names
    assert "training_analysis" in plan.context_blocks
    assert plan.model_name == "openai/gpt-oss-120b"
    assert coach.model_name == "google/gemini-3.1-flash-lite-preview"
    assert "OPENROUTER_ROUTING_MODEL" not in coach.prompt_text
    assert "context_summary" not in session_context.prompt_text.lower()
    assert "context_summary" not in training.prompt_text.lower()
    assert "context_summary" not in nutrition.prompt_text.lower()
    assert "context_summary" not in plan.prompt_text.lower()
    assert "conversation_state" in training.context_blocks
    assert "conversation_state" in nutrition.context_blocks
    assert "conversation_state" in plan.context_blocks


def test_prompt_texts_encode_node_responsibilities():
    registry = AgentConfigRegistry("src/services/agents/config")
    training = registry.get_node_config("training_specialist")
    nutrition = registry.get_node_config("nutrition_specialist")
    plan = registry.get_node_config("plan_specialist")
    coach = registry.get_node_config("coach_reply")

    assert "TrainingSpecialistNode" in training.prompt_text
    assert "no_action_needed" in training.prompt_text
    assert "NutritionSpecialistNode" in nutrition.prompt_text
    assert "no_action_needed" in nutrition.prompt_text
    assert "PlanSpecialistNode" in plan.prompt_text
    assert "upsert_plan" in plan.prompt_text
    assert "no_action_needed" in plan.prompt_text
    assert "history_summary" not in coach.prompt_text
    assert "CoachReplyNode" in coach.prompt_text
    assert "no_action_needed" in coach.prompt_text
    assert "persona" in coach.prompt_text.lower()
    assert coach.temperature == 0.2


def test_session_context_config():
    registry = AgentConfigRegistry("src/services/agents/config")
    cfg = registry.get_node_config("session_context")
    assert cfg.model_name == "qwen/qwen3-next-80b-a3b-instruct"
    assert cfg.temperature == 0.0
    assert cfg.top_p == 1.0
    assert cfg.frequency_penalty == 0.0
    assert cfg.tool_names == []


def test_coach_reply_has_no_context_summary_in_context_blocks():
    registry = AgentConfigRegistry("src/services/agents/config")
    cfg = registry.get_node_config("coach_reply")
    assert "context_summary" not in cfg.context_blocks
    assert "training_analysis" in cfg.context_blocks
    assert "nutrition_analysis" in cfg.context_blocks
    assert "plan_workspace" in cfg.context_blocks


def test_plan_specialist_outputs_technical_summary_not_user_reply():
    registry = AgentConfigRegistry("src/services/agents/config")
    cfg = registry.get_node_config("plan_specialist")
    assert "technical_summary" in cfg.output_contract
    assert "user_reply" not in cfg.output_contract
    assert "context_summary" not in cfg.context_blocks


def test_memory_hub_receives_coach_reply_as_peer_input():
    registry = AgentConfigRegistry("src/services/agents/config")
    cfg = registry.get_node_config("memory_hub")
    assert "coach_reply" in cfg.peer_inputs
    assert "coach_response" in cfg.context_blocks