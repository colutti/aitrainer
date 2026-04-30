"""Tests for file-backed agent config registry."""

import pytest

from src.services.agents.config_registry import AgentConfigRegistry


def test_registry_loads_node_configs():
    registry = AgentConfigRegistry("src/services/agents/config")
    configs = registry.list_node_configs()
    assert len(configs) >= 9
    names = {cfg.node_name for cfg in configs}
    assert "plan_manager" in names
    assert "prompt_security" in names
    assert "persona_response" in names


def test_registry_returns_single_node():
    registry = AgentConfigRegistry("src/services/agents/config")
    cfg = registry.get_node_config("nutrition_specialist")
    assert cfg.node_name == "nutrition_specialist"
    assert cfg.prompt_text
    assert cfg.config_hash


def test_registry_exposes_context_contract_fields():
    registry = AgentConfigRegistry("src/services/agents/config")
    cfg = registry.get_node_config("persona_response")
    assert cfg.context_blocks
    assert cfg.peer_inputs == ["general_conversation"]
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
    persona = registry.get_node_config("persona_response")
    security = registry.get_node_config("prompt_security")
    training = registry.get_node_config("training_specialist")

    assert persona.persona_mode == "final_only"
    assert "trainer_persona" in persona.context_blocks
    assert security.context_blocks == ["request"]
    assert "trainer_persona" not in training.context_blocks
