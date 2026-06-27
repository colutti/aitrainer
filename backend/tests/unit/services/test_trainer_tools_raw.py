"""Tests for Pydantic AI chat tool registration."""

from src.services.ai_chat.tools.registry import (
    MAX_AI_TOOLS_PER_TURN,
    build_chat_tools,
    build_core_toolset,
    select_chat_toolsets,
)


def _toolset_names(toolsets) -> set[str]:
    names: set[str] = set()
    for toolset in toolsets:
        names.update(toolset.tools.keys())
    return names


def test_registry_exposes_domain_tools_instead_of_legacy_tool_fanout():
    names = {tool.__name__ for tool in build_chat_tools()}

    assert len(names) <= MAX_AI_TOOLS_PER_TURN
    assert {
        "plan_ops",
        "training_ops",
        "nutrition_ops",
        "body_ops",
        "schedule_ops",
        "memory_ops",
        "metabolism_ops",
        "profile_ops",
    }.issubset(names)
    assert "get_plan_status" not in names
    assert "update_plan_section" not in names
    assert "get_workouts_raw" not in names


def test_default_toolsets_exclude_hevy_and_raw_domains():
    toolsets = select_chat_toolsets(user_input="ola", runtime_context={})
    names = _toolset_names(toolsets)

    assert len(names) <= MAX_AI_TOOLS_PER_TURN
    assert "plan_ops" in names
    assert "training_ops" in names
    assert "hevy_ops" not in names
    assert "raw_data_ops" not in names


def test_hevy_toolset_is_selected_only_for_hevy_intent():
    toolsets = select_chat_toolsets(
        user_input="crie uma rotina no Hevy trocando exercicios",
        runtime_context={},
    )
    names = _toolset_names(toolsets)

    assert len(names) <= MAX_AI_TOOLS_PER_TURN
    assert "hevy_ops" in names
    assert "raw_data_ops" not in names


def test_raw_toolset_is_selected_only_for_audit_intent():
    toolsets = select_chat_toolsets(
        user_input="mostre os dados brutos de treino para auditoria",
        runtime_context={},
    )
    names = _toolset_names(toolsets)

    assert len(names) <= MAX_AI_TOOLS_PER_TURN
    assert "raw_data_ops" in names
    assert "hevy_ops" not in names


def test_required_plan_execution_keeps_plan_ops_available():
    toolsets = select_chat_toolsets(
        user_input="ok pode aplicar",
        runtime_context={"plan_execution": {"required_tool": "update_plan_section"}},
    )
    names = _toolset_names(toolsets)

    assert len(names) <= MAX_AI_TOOLS_PER_TURN
    assert "plan_ops" in names


def test_selected_tool_schemas_avoid_defs_for_google_tool_declarations():
    toolsets = select_chat_toolsets(
        user_input="debug da rotina Hevy com dados brutos",
        runtime_context={},
    )

    for toolset in toolsets:
        for tool in toolset.tools.values():
            schema = tool.function_schema.json_schema
            assert "$defs" not in schema, tool.function_schema.name
            assert len(str(schema)) < 5000, tool.function_schema.name

    plan_schema = build_core_toolset().tools["plan_ops"].function_schema.json_schema
    assert set(plan_schema["properties"]) == {
        "action",
        "payload",
        "output_format",
    }
