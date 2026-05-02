"""Tests for file-backed agent config registry."""

import pytest

from src.services.agents.config_registry import AgentConfigRegistry


def test_registry_loads_node_configs():
    registry = AgentConfigRegistry("src/services/agents/config")
    configs = registry.list_node_configs()
    assert len(configs) >= 8
    names = {cfg.node_name for cfg in configs}
    assert "plan_specialist" in names
    assert "prompt_security" in names
    assert "general_conversation" in names


def test_registry_returns_single_node():
    registry = AgentConfigRegistry("src/services/agents/config")
    cfg = registry.get_node_config("nutrition_specialist")
    assert cfg.node_name == "nutrition_specialist"
    assert cfg.prompt_text
    assert cfg.config_hash


def test_registry_exposes_context_contract_fields():
    registry = AgentConfigRegistry("src/services/agents/config")
    cfg = registry.get_node_config("general_conversation")
    assert cfg.context_blocks
    assert "trainer_persona" in cfg.context_blocks
    assert "plan_specialist" in cfg.peer_inputs
    assert cfg.persona_mode == "none"
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
    turn_context = registry.get_node_config("turn_context")
    general = registry.get_node_config("general_conversation")
    security = registry.get_node_config("prompt_security")
    training = registry.get_node_config("training_specialist")
    plan = registry.get_node_config("plan_specialist")
    nutrition = registry.get_node_config("nutrition_specialist")

    assert general.persona_mode == "none"
    assert "trainer_persona" in general.context_blocks
    assert "trainer_identity" not in turn_context.context_blocks
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
    assert plan.model_name == "google/gemini-3.1-flash-lite-preview"
    assert general.model_name == "google/gemini-3.1-flash-lite-preview"
    assert "OPENROUTER_ROUTING_MODEL" not in general.prompt_text
    assert "persona" not in turn_context.prompt_text.lower()
    assert "persona" not in training.prompt_text.lower()
    assert "persona" not in nutrition.prompt_text.lower()
    assert "persona" not in plan.prompt_text.lower()


def test_prompt_texts_encode_node_responsibilities():
    registry = AgentConfigRegistry("src/services/agents/config")
    training = registry.get_node_config("training_specialist")
    nutrition = registry.get_node_config("nutrition_specialist")
    plan = registry.get_node_config("plan_specialist")
    intent_router = registry.get_node_config("intent_router")
    general = registry.get_node_config("general_conversation")

    assert "save_workout" in training.prompt_text
    assert "save_daily_nutrition" in nutrition.prompt_text
    assert "upsert_plan" in plan.prompt_text
    assert "multi_domain" in intent_router.prompt_text
    assert "Treinei costas hoje e comi 2400 kcal" in intent_router.prompt_text
    assert "Leitura dos dados" in general.prompt_text
    assert "persona ativa" in general.prompt_text or "persona" in general.prompt_text
    assert "idioma predominante" in general.prompt_text
    assert "voz de treinador" in general.prompt_text
    assert "soar nativa" in general.prompt_text
    assert "Data Reading:" in general.prompt_text
    assert "Interpretation:" in general.prompt_text
    assert "Next Actions:" in general.prompt_text
    assert "Lectura de los datos:" in general.prompt_text
    assert "Proximas acciones:" in general.prompt_text
    assert "monstro" in general.prompt_text
    assert "e nois" in general.prompt_text
    assert general.temperature == 0.2
