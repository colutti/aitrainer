"""Structural guardrail tests for node tool exposure policy."""

import json
import re
from pathlib import Path

from src.services.agents.node_tool_policy import (
    ExposureClass,
    ExposureMode,
    TOOL_EXPOSURE_POLICY,
    all_known_node_names,
    all_known_tool_names,
    get_node_all_tools,
    get_node_llm_tools,
    get_node_orchestrator_tools,
)
from src.services.tool_registry import TOOL_REGISTRY


_CONFIG_DIR = Path("src/services/agents/config")
_PROMPT_DIR = _CONFIG_DIR / "prompts"
_NODE_JSON_GLOB = "nodes/*.json"


_CONVERSATIONAL_NODES = frozenset({
    "training_specialist",
    "nutrition_specialist",
    "plan_specialist",
    "coach_reply",
})


_NODE_NAMES_KNOWN = frozenset(all_known_node_names())


def _load_node_json(node_name: str) -> dict | None:
    node_path = _CONFIG_DIR / f"nodes/{node_name}.json"
    if not node_path.exists():
        return None
    return json.loads(node_path.read_text())


def _load_prompt_text(node_name: str) -> str | None:
    prompt_path = _CONFIG_DIR / f"prompts/{node_name}.md"
    if not prompt_path.exists():
        return None
    return prompt_path.read_text()


_MARKDOWN_TOOL_RE = re.compile(r"`([a-z_]+)`")


def _extract_prompt_tool_refs(prompt_text: str) -> set[str]:
    if not prompt_text:
        return set()
    refs = set()
    for match in _MARKDOWN_TOOL_RE.finditer(prompt_text):
        name = match.group(1)
        if name in all_known_tool_names():
            refs.add(name)
    return refs


class TestNodeToolPolicy:
    """Verify canonical policy internal consistency."""

    def test_all_conversational_node_names_in_policy(self):
        for name in _CONVERSATIONAL_NODES:
            assert name in _NODE_NAMES_KNOWN, (
                f"Conversational node '{name}' is not in the canonical policy"
            )

    def test_no_deprecated_tools_in_conversational_nodes(self):
        for node_name in _CONVERSATIONAL_NODES:
            tools = get_node_all_tools(node_name)
            for tool in tools:
                tp = TOOL_EXPOSURE_POLICY.get(tool)
                assert tp is not None, f"Tool '{tool}' (node '{node_name}') missing from TOOL_EXPOSURE_POLICY"
                assert tp.exposure_class == ExposureClass.CONVERSATIONAL, (
                    f"Tool '{tool}' in node '{node_name}' has class {tp.exposure_class}, "
                    f"but only CONVERSATIONAL is allowed for conversational nodes"
                )

    def test_no_raw_operational_tools_in_conversational_nodes(self):
        for node_name in _CONVERSATIONAL_NODES:
            tools = get_node_all_tools(node_name)
            for tool in tools:
                tp = TOOL_EXPOSURE_POLICY.get(tool)
                assert tp is not None
                assert tp.exposure_class != ExposureClass.OPERATIONAL_RAW, (
                    f"OPERATIONAL_RAW tool '{tool}' leaked into conversational node '{node_name}'"
                )

    def test_no_admin_maintenance_tools_in_conversational_nodes(self):
        for node_name in _CONVERSATIONAL_NODES:
            tools = get_node_all_tools(node_name)
            for tool in tools:
                tp = TOOL_EXPOSURE_POLICY.get(tool)
                assert tp is not None
                assert tp.exposure_class != ExposureClass.ADMIN_OR_MAINTENANCE, (
                    f"ADMIN_OR_MAINTENANCE tool '{tool}' leaked into conversational node '{node_name}'"
                )

    def test_deprecated_tools_have_replaced_by(self):
        for name, tp in TOOL_EXPOSURE_POLICY.items():
            if tp.exposure_class == ExposureClass.DEPRECATED:
                assert tp.replaced_by is not None, (
                    f"Deprecated tool '{name}' must have 'replaced_by' set"
                )

    def test_deprecated_tools_not_in_conversational_nodes(self):
        for node_name in _CONVERSATIONAL_NODES:
            tools = get_node_all_tools(node_name)
            for tool in tools:
                assert not (TOOL_EXPOSURE_POLICY.get(tool) and
                           TOOL_EXPOSURE_POLICY[tool].exposure_class == ExposureClass.DEPRECATED), (
                    f"Deprecated tool '{tool}' should not be exposed to conversational node '{node_name}'"
                )

    def test_reset_tdee_tracking_marked_deprecated(self):
        tp = TOOL_EXPOSURE_POLICY.get("reset_tdee_tracking")
        assert tp is not None, "reset_tdee_tracking missing from TOOL_EXPOSURE_POLICY"
        assert tp.exposure_class == ExposureClass.DEPRECATED, (
            "reset_tdee_tracking must be marked DEPRECATED"
        )
        assert tp.replaced_by == "update_tdee_params", (
            "reset_tdee_tracking must have replaced_by=update_tdee_params"
        )

    def test_update_tdee_params_replaces_reset_tdee_tracking(self):
        tp = TOOL_EXPOSURE_POLICY.get("update_tdee_params")
        assert tp is not None
        assert tp.replaces == "reset_tdee_tracking"

    def test_context_free_nodes_have_no_tools(self):
        context_free = {"session_context", "prompt_security"}
        for node_name in context_free:
            assert get_node_llm_tools(node_name) == set(), (
                f"Node '{node_name}' should have no LLM tools"
            )
            assert get_node_orchestrator_tools(node_name) == set(), (
                f"Node '{node_name}' should have no orchestrator tools"
            )


class TestToolPolicyConsistency:
    """Cross-reference TOOL_EXPOSURE_POLICY with global tool name lists."""

    def test_all_policy_tools_are_valid_names(self):
        for name in TOOL_EXPOSURE_POLICY:
            assert name and isinstance(name, str) and "_" in name, (
                f"Invalid tool name in policy: '{name}'"
            )

    def test_memory_hub_tools_are_orchestrator_only(self):
        tools = get_node_orchestrator_tools("memory_hub")
        for tool in tools:
            tp = TOOL_EXPOSURE_POLICY.get(tool)
            if tp:
                assert tp.exposure_mode == ExposureMode.ORCHESTRATOR_ONLY, (
                    f"memory_hub orchestrator tool '{tool}' has mode {tp.exposure_mode}"
                )

    def test_conversational_non_orchestrator_tools_are_llm_direct(self):
        for name, tp in TOOL_EXPOSURE_POLICY.items():
            if tp.exposure_class == ExposureClass.CONVERSATIONAL:
                if tp.exposure_mode != ExposureMode.ORCHESTRATOR_ONLY:
                    assert tp.exposure_mode == ExposureMode.LLM_DIRECT, (
                        f"Conversational tool '{name}' should be LLM_DIRECT or ORCHESTRATOR_ONLY"
                    )


class TestNodeJsonAlignment:
    """Verify node JSON tool_names match canonical policy."""

    def test_training_specialist_json_matches_policy(self):
        js = _load_node_json("training_specialist")
        assert js is not None
        json_tools = set(js.get("tool_names", []))
        policy_tools = get_node_all_tools("training_specialist")
        assert json_tools == policy_tools, (
            f"training_specialist JSON tools {sorted(json_tools)} "
            f"!= policy tools {sorted(policy_tools)}"
        )

    def test_nutrition_specialist_json_matches_policy(self):
        js = _load_node_json("nutrition_specialist")
        assert js is not None
        json_tools = set(js.get("tool_names", []))
        policy_tools = get_node_all_tools("nutrition_specialist")
        assert json_tools == policy_tools, (
            f"nutrition_specialist JSON tools {sorted(json_tools)} "
            f"!= policy tools {sorted(policy_tools)}"
        )

    def test_plan_specialist_json_matches_policy(self):
        js = _load_node_json("plan_specialist")
        assert js is not None
        json_tools = set(js.get("tool_names", []))
        policy_tools = get_node_all_tools("plan_specialist")
        assert json_tools == policy_tools, (
            f"plan_specialist JSON tools {sorted(json_tools)} "
            f"!= policy tools {sorted(policy_tools)}"
        )

    def test_coach_reply_json_matches_policy(self):
        js = _load_node_json("coach_reply")
        assert js is not None
        json_tools = set(js.get("tool_names", []))
        policy_tools = get_node_all_tools("coach_reply")
        assert json_tools == policy_tools, (
            f"coach_reply JSON tools {sorted(json_tools)} "
            f"!= policy tools {sorted(policy_tools)}"
        )

    def test_memory_hub_json_matches_policy(self):
        js = _load_node_json("memory_hub")
        assert js is not None
        json_tools = set(js.get("tool_names", []))
        policy_tools = get_node_all_tools("memory_hub")
        assert json_tools == policy_tools, (
            f"memory_hub JSON tools {sorted(json_tools)} "
            f"!= policy tools {sorted(policy_tools)}"
        )


class TestToolRegistryMatchesPolicy:
    """Verify global TOOL_REGISTRY entries exist for all classified tools."""

    def test_all_known_tools_have_registry_entry(self):
        missing = []
        for name in all_known_tool_names():
            if name not in TOOL_REGISTRY:
                missing.append(name)
        assert not missing, (
            f"Tools in TOOL_EXPOSURE_POLICY missing from TOOL_REGISTRY: {missing}"
        )


class TestPromptToolAlignment:
    """Verify prompt tool references match node exposure."""

    def test_nutrition_specialist_prompt_references_exposed_tools(self):
        prompt = _load_prompt_text("nutrition_specialist")
        assert prompt is not None
        refs = _extract_prompt_tool_refs(prompt)
        policy_tools = get_node_all_tools("nutrition_specialist")
        for ref in refs:
            assert ref in policy_tools, (
                f"nutrition_specialist prompt references '{ref}' but it is not "
                f"in the node's tool policy"
            )

    def test_training_specialist_prompt_references_exposed_tools(self):
        prompt = _load_prompt_text("training_specialist")
        assert prompt is not None
        refs = _extract_prompt_tool_refs(prompt)
        policy_tools = get_node_all_tools("training_specialist")
        for ref in refs:
            assert ref in policy_tools, (
                f"training_specialist prompt references '{ref}' but it is not "
                f"in the node's tool policy"
            )

    def test_plan_specialist_prompt_references_exposed_tools(self):
        prompt = _load_prompt_text("plan_specialist")
        assert prompt is not None
        refs = _extract_prompt_tool_refs(prompt)
        policy_tools = get_node_all_tools("plan_specialist")
        for ref in refs:
            assert ref in policy_tools, (
                f"plan_specialist prompt references '{ref}' but it is not "
                f"in the node's tool policy"
            )

    def test_coach_reply_prompt_references_exposed_tools(self):
        prompt = _load_prompt_text("coach_reply")
        assert prompt is not None
        refs = _extract_prompt_tool_refs(prompt)
        policy_tools = get_node_all_tools("coach_reply")
        for ref in refs:
            assert ref in policy_tools, (
                f"coach_reply prompt references '{ref}' but it is not "
                f"in the node's tool policy"
            )

    def test_no_prompt_references_deprecated(self):
        for node_name in _CONVERSATIONAL_NODES:
            prompt = _load_prompt_text(node_name)
            if not prompt:
                continue
            for ref in _extract_prompt_tool_refs(prompt):
                tp = TOOL_EXPOSURE_POLICY.get(ref)
                if tp and tp.exposure_class == ExposureClass.DEPRECATED:
                    replacement = tp.replaced_by or "N/A"
                    raise AssertionError(
                        f"Prompt for '{node_name}' references deprecated tool "
                        f"'{ref}'. Use '{replacement}' instead."
                    )


class TestRawToolsNotExposedToNodes:
    """Ensure operational raw tools are never exposed to conversational nodes."""

    _RAW_TOOLS = frozenset({
        "get_workouts_raw",
        "get_nutrition_raw",
        "get_body_composition_raw",
        "get_goal_history_raw",
        "get_events_raw",
        "get_memories_raw",
        "list_raw_memories",
    })

    _ADMIN_TOOLS = frozenset({
        "delete_memories_batch",
    })

    def test_raw_tools_not_in_any_conversational_node(self):
        for node_name in _CONVERSATIONAL_NODES:
            tools = get_node_all_tools(node_name)
            leaked = tools & self._RAW_TOOLS
            assert not leaked, (
                f"RAW tool(s) {leaked} leaked into conversational node '{node_name}'"
            )

    def test_admin_tools_not_in_any_conversational_node(self):
        for node_name in _CONVERSATIONAL_NODES:
            tools = get_node_all_tools(node_name)
            leaked = tools & self._ADMIN_TOOLS
            assert not leaked, (
                f"ADMIN tool(s) {leaked} leaked into conversational node '{node_name}'"
            )

    def test_reset_tdee_tracking_not_in_any_conversational_node(self):
        for node_name in _CONVERSATIONAL_NODES:
            tools = get_node_all_tools(node_name)
            assert "reset_tdee_tracking" not in tools, (
                f"reset_tdee_tracking leaked into conversational node '{node_name}'"
            )


class TestRegistryCompleteness:
    """Verify every global tool returned by get_tools() is classified."""

    def test_all_global_tools_have_policy_entry(self):
        from src.services.tool_registry import TOOL_REGISTRY as reg

        for name in reg:
            assert name in TOOL_EXPOSURE_POLICY, (
                f"TOOL_REGISTRY tool '{name}' is missing from TOOL_EXPOSURE_POLICY. "
                f"Every globally registered tool must have an exposure classification."
            )

    def test_all_global_tools_are_non_deprecated_or_known(self):
        for name in TOOL_EXPOSURE_POLICY:
            tp = TOOL_EXPOSURE_POLICY[name]
            assert isinstance(tp.exposure_class, ExposureClass)
            assert isinstance(tp.exposure_mode, ExposureMode)
