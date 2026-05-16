"""Tests for file-backed agent config registry."""

import json

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
    assert "coach_handoff" in cfg.context_blocks
    assert cfg.peer_inputs == []
    assert cfg.persona_mode == "final_only"
    assert cfg.output_contract == "text"


def test_nutrition_specialist_has_updated_model_and_config():
    """nutrition_specialist must use the new model and extended config fields."""
    registry = AgentConfigRegistry("src/services/agents/config")
    cfg = registry.get_node_config("nutrition_specialist")
    assert cfg.model_name == "google/gemini-3-flash-preview"
    assert cfg.temperature == 0.2
    assert cfg.max_tokens >= 6144
    assert cfg.reasoning == {"effort": "low", "exclude": True}
    assert cfg.parallel_tool_calls is False
    assert cfg.provider_sort == "throughput"
    assert isinstance(cfg.response_format, dict)
    assert cfg.response_format["type"] == "json_schema"


def test_training_specialist_has_updated_model_and_config():
    """training_specialist must use the new model and extended config fields."""
    registry = AgentConfigRegistry("src/services/agents/config")
    cfg = registry.get_node_config("training_specialist")
    assert cfg.model_name == "google/gemini-3-flash-preview"
    assert cfg.temperature == 0.2
    assert cfg.max_tokens >= 6144
    assert cfg.reasoning == {"effort": "low", "exclude": True}
    assert cfg.parallel_tool_calls is False
    assert cfg.provider_sort == "throughput"


def test_node_config_handles_dict_response_format(tmp_path):
    """response_format as dict must be preserved, not stringified."""
    base = tmp_path / "config"
    (base / "nodes").mkdir(parents=True)
    (base / "prompts").mkdir(parents=True)
    (base / "prompts" / "x.md").write_text("prompt", encoding="utf-8")
    schema = {
        "type": "json_schema",
        "json_schema": {
            "name": "test_output",
            "strict": True,
            "schema": {"type": "object", "properties": {"status": {"type": "string"}}, "required": ["status"]}
        }
    }
    (base / "nodes" / "x.json").write_text(
        json.dumps({
            "node_name": "x",
            "enabled": True,
            "model_provider": "openrouter",
            "model_name": "openai/gpt-4.1-nano",
            "temperature": 0,
            "max_tokens": 256,
            "tool_policy": "restricted",
            "tool_names": [],
            "prompt_file": str(base / "prompts" / "x.md"),
            "response_format": schema,
            "version": "v1",
            "context_blocks": ["request"],
            "peer_inputs": [],
            "persona_mode": "none",
            "output_contract": "text"
        }),
        encoding="utf-8",
    )
    registry = AgentConfigRegistry(base)
    cfg = registry.get_node_config("x")
    assert isinstance(cfg.response_format, dict)
    assert cfg.response_format["type"] == "json_schema"


def test_node_config_handles_reasoning_and_parallel_tools(tmp_path):
    """reasoning and parallel_tool_calls must be preserved as-is."""
    base = tmp_path / "config"
    (base / "nodes").mkdir(parents=True)
    (base / "prompts").mkdir(parents=True)
    (base / "prompts" / "x.md").write_text("prompt", encoding="utf-8")
    (base / "nodes" / "x.json").write_text(
        json.dumps({
            "node_name": "x",
            "enabled": True,
            "model_provider": "openrouter",
            "model_name": "x",
            "temperature": 0,
            "max_tokens": 256,
            "tool_policy": "restricted",
            "tool_names": [],
            "prompt_file": str(base / "prompts" / "x.md"),
            "response_format": "json",
            "reasoning": {"effort": "low", "exclude": True},
            "parallel_tool_calls": False,
            "version": "v1",
            "context_blocks": ["request"],
            "peer_inputs": [],
            "persona_mode": "none",
            "output_contract": "text"
        }),
        encoding="utf-8",
    )
    registry = AgentConfigRegistry(base)
    cfg = registry.get_node_config("x")
    assert cfg.reasoning == {"effort": "low", "exclude": True}
    assert cfg.parallel_tool_calls is False


def test_node_config_rejects_invalid_reasoning(tmp_path):
    """reasoning must be None if payload value is not a dict."""
    base = tmp_path / "config"
    (base / "nodes").mkdir(parents=True)
    (base / "prompts").mkdir(parents=True)
    (base / "prompts" / "x.md").write_text("prompt", encoding="utf-8")
    (base / "nodes" / "x.json").write_text(
        json.dumps({
            "node_name": "x",
            "enabled": True,
            "model_provider": "openrouter",
            "model_name": "x",
            "temperature": 0,
            "max_tokens": 256,
            "tool_policy": "restricted",
            "tool_names": [],
            "prompt_file": str(base / "prompts" / "x.md"),
            "response_format": "text",
            "reasoning": "invalid",
            "version": "v1",
            "context_blocks": ["request"],
            "peer_inputs": [],
            "persona_mode": "none",
            "output_contract": "text"
        }),
        encoding="utf-8",
    )
    registry = AgentConfigRegistry(base)
    cfg = registry.get_node_config("x")
    assert cfg.reasoning is None


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
    assert training.model_name == "google/gemini-3-flash-preview"
    assert "save_workout" in training.tool_names
    assert "save_daily_nutrition" in nutrition.tool_names
    assert nutrition.model_name == "google/gemini-3-flash-preview"
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

    assert "TrainingSpecialistNode" in training.prompt_text
    assert "no_action_needed" in training.prompt_text
    assert "NutritionSpecialistNode" in nutrition.prompt_text
    assert "no_action_needed" in nutrition.prompt_text
    assert "provide material nutrition guidance" in nutrition.prompt_text
    assert "PlanSpecialistNode" in plan.prompt_text
    assert "upsert_plan" in plan.prompt_text
    assert "no_action_needed" in plan.prompt_text
    assert "Two Operational Modes" in plan.prompt_text
    assert "Sufficiency Rule" in plan.prompt_text
    assert "Field Relationships" in plan.prompt_text
    assert "Output Quality Rejection Checklist" in plan.prompt_text
    assert "Discovery Checklist" in plan.prompt_text
    assert "Plan Creation Sequence" in plan.prompt_text


def test_specialist_prompts_enforce_authority_and_external_fact_boundary():
    registry = AgentConfigRegistry("src/services/agents/config")
    training = registry.get_node_config("training_specialist")
    nutrition = registry.get_node_config("nutrition_specialist")
    plan = registry.get_node_config("plan_specialist")
    coach = registry.get_node_config("coach_reply")
    memory_hub = registry.get_node_config("memory_hub")

    assert "You are the training authority." in training.prompt_text
    assert "Do NOT ask the user to choose technical training parameters" in training.prompt_text
    assert "facts that are genuinely external to the system" in training.prompt_text
    assert "If the user says anything equivalent to \"decide yourself\"" in training.prompt_text
    assert "Do not ask the user for sets, reps, load guidance" in training.prompt_text
    assert "You are an upstream specialist for the plan orchestrator." in training.prompt_text
    assert "Never claim that the plan was updated, saved, replaced, or persisted" in training.prompt_text
    assert "`action_status` must use only: executed, failed, needs_user_input, no_action_needed." in training.prompt_text
    assert "plan_payload" in training.prompt_text

    assert "You are the nutrition authority." in nutrition.prompt_text
    assert "Do NOT ask the user to choose technical nutrition parameters" in nutrition.prompt_text
    assert "facts that are genuinely external to the system" in nutrition.prompt_text
    assert "calories" in nutrition.prompt_text
    assert "macro target strategy" in nutrition.prompt_text

    assert "You must treat specialist-owned technical decisions as already delegated" in plan.prompt_text
    assert "Do NOT ask the user for specialist-owned technical parameters." in plan.prompt_text
    assert "Valid user-facing pending slots are facts that are truly external to the system" in plan.prompt_text
    assert "It asks the user for specialist-owned technical parameters." in plan.prompt_text

    assert "You may not expand a specialist question into extra requirements." in coach.prompt_text
    assert "Never fabricate facts, outcomes, plan changes, saved data, tool results, or extra user requirements." in coach.prompt_text

    assert "Do not persist specialist-owned technical questions as durable user facts." in memory_hub.prompt_text
    assert "missing fact is genuinely external to the system" in memory_hub.prompt_text
    assert "history_summary" not in coach.prompt_text
    assert "CoachReplyNode" in coach.prompt_text
    assert "no_action_needed" in coach.prompt_text
    assert "persona" in coach.prompt_text.lower()
    assert coach.temperature == 0.2


def test_prompt_security_has_structured_output():
    """prompt_security must use strict json_schema."""
    registry = AgentConfigRegistry("src/services/agents/config")
    cfg = registry.get_node_config("prompt_security")
    assert cfg.model_name == "google/gemini-2.5-flash-lite"
    assert cfg.temperature == 0.0
    assert cfg.max_tokens >= 1024
    assert isinstance(cfg.response_format, dict)
    assert cfg.response_format["type"] == "json_schema"
    assert cfg.provider_sort == "throughput"


def test_session_context_config():
    registry = AgentConfigRegistry("src/services/agents/config")
    cfg = registry.get_node_config("session_context")
    assert cfg.model_name == "openai/gpt-oss-120b"
    assert cfg.temperature == 0.0
    assert cfg.top_p == 1.0
    assert cfg.frequency_penalty == 0.0
    assert cfg.tool_names == []


def test_coach_reply_has_no_context_summary_in_context_blocks():
    registry = AgentConfigRegistry("src/services/agents/config")
    cfg = registry.get_node_config("coach_reply")
    assert "context_summary" not in cfg.context_blocks
    assert "coach_handoff" in cfg.context_blocks
    assert "training_analysis" not in cfg.context_blocks
    assert "nutrition_analysis" not in cfg.context_blocks
    assert "active_plan" not in cfg.context_blocks
    assert "metabolism" not in cfg.context_blocks


def test_plan_specialist_has_hardened_config():
    """plan_specialist must use strict json_schema and extended config fields."""
    registry = AgentConfigRegistry("src/services/agents/config")
    cfg = registry.get_node_config("plan_specialist")
    assert cfg.model_name == "openai/gpt-oss-120b"
    assert cfg.temperature == 0.1
    assert cfg.max_tokens >= 4096
    assert cfg.reasoning == {"effort": "low", "exclude": True}
    assert cfg.parallel_tool_calls is False
    assert cfg.provider_sort == "throughput"
    assert isinstance(cfg.response_format, dict)
    assert cfg.response_format["type"] == "json_schema"


def test_plan_specialist_outputs_public_internal_operation_result():
    registry = AgentConfigRegistry("src/services/agents/config")
    cfg = registry.get_node_config("plan_specialist")
    assert "public_message" in cfg.output_contract
    assert "internal_analysis" in cfg.output_contract
    assert "operation_result" in cfg.output_contract
    assert "technical_summary" not in cfg.output_contract
    assert "user_reply" not in cfg.output_contract
    assert "context_summary" not in cfg.context_blocks


def test_memory_hub_has_structured_output_and_config():
    """memory_hub must use strict json_schema."""
    registry = AgentConfigRegistry("src/services/agents/config")
    cfg = registry.get_node_config("memory_hub")
    assert cfg.model_name == "google/gemini-3.1-flash-lite-preview"
    assert cfg.temperature == 0.0
    assert cfg.max_tokens >= 2048
    assert isinstance(cfg.response_format, dict)
    assert cfg.response_format["type"] == "json_schema"
    assert cfg.provider_sort == "throughput"


def test_memory_hub_does_not_receive_coach_response_as_fact_context():
    registry = AgentConfigRegistry("src/services/agents/config")
    cfg = registry.get_node_config("memory_hub")
    assert "coach_reply" not in cfg.peer_inputs
    assert "coach_response" not in cfg.context_blocks
    assert "specialist_results" in cfg.context_blocks


def test_node_schemas_require_public_internal_operation_result():
    registry = AgentConfigRegistry("src/services/agents/config")
    for node_name in ("training_specialist", "nutrition_specialist", "plan_specialist"):
        cfg = registry.get_node_config(node_name)
        schema = cfg.response_format["json_schema"]["schema"]
        required = set(schema["required"])
        assert "public_message" in required
        assert "internal_analysis" in required
        assert "operation_result" in required
        assert "technical_summary" not in required
        operation_schema = schema["properties"]["operation_result"]
        assert operation_schema["additionalProperties"] is False
        assert set(operation_schema["required"]) == {
            "attempted",
            "succeeded",
            "tool_name",
            "error_code",
            "evidence",
        }


def test_training_specialist_schema_exposes_plan_payload_for_planner_handoff():
    registry = AgentConfigRegistry("src/services/agents/config")
    cfg = registry.get_node_config("training_specialist")
    schema = cfg.response_format["json_schema"]["schema"]
    required = set(schema["required"])

    assert "plan_payload" in required
    payload_schema = schema["properties"]["plan_payload"]
    assert payload_schema["type"] == "object"
    assert payload_schema["additionalProperties"] is True


def test_plan_specialist_model_stays_gpt_oss_120b():
    registry = AgentConfigRegistry("src/services/agents/config")
    cfg = registry.get_node_config("plan_specialist")
    assert cfg.model_name == "openai/gpt-oss-120b"


def test_coach_receives_coach_handoff_not_plan_workspace_raw_data():
    registry = AgentConfigRegistry("src/services/agents/config")
    cfg = registry.get_node_config("coach_reply")
    assert "coach_handoff" in cfg.context_blocks
    assert "training_analysis" not in cfg.context_blocks
    assert "nutrition_analysis" not in cfg.context_blocks
    assert "active_plan" not in cfg.context_blocks
    assert "metabolism" not in cfg.context_blocks


def test_prompt_texts_do_not_use_coach_say_markers():
    registry = AgentConfigRegistry("src/services/agents/config")
    for cfg in registry.list_node_configs():
        text = cfg.prompt_text
        assert "COACH_SAY" not in text
        assert "STATUS:" not in text
        assert "SUCCESS:" not in text


def test_coach_prompt_mentions_coach_handoff_and_public_message():
    registry = AgentConfigRegistry("src/services/agents/config")
    cfg = registry.get_node_config("coach_reply")
    assert "coach_handoff" in cfg.prompt_text
    assert "public_message" in cfg.prompt_text


def test_memory_prompt_forbids_coach_response_as_fact_source():
    registry = AgentConfigRegistry("src/services/agents/config")
    cfg = registry.get_node_config("memory_hub")
    assert "SPECIALIST_RESULTS_JSON" in cfg.prompt_text
    assert "Do not use coach prose as evidence" in cfg.prompt_text
    assert "coach_response" in cfg.prompt_text


def test_plan_prompt_requires_operation_result_for_upsert():
    registry = AgentConfigRegistry("src/services/agents/config")
    cfg = registry.get_node_config("plan_specialist")
    assert "operation_result" in cfg.prompt_text
    assert "upsert_plan" in cfg.prompt_text
    assert "ERRO_UPSERT_PLAN_" in cfg.prompt_text
