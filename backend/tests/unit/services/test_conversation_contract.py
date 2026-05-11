"""Tests for conversation contract module."""

from src.services.graph.conversation_contract import (
    ActionStatus,
    PendingActionKind,
    build_conversation_summary,
    build_snapshot,
    default_conversation_state,
    merge_pending_action_update,
    parse_latest_summary,
    parse_latest_snapshot,
    resolve_pending_action,
)


class TestSnapshotPersistence:
    def test_build_and_parse_roundtrip(self):
        state = {
            "active_domain": "plan",
            "pending_action": {
                "kind": PendingActionKind.PLAN_DISCOVERY.value,
                "status": ActionStatus.NEEDS_USER_INPUT.value,
                "missing_slots": ["timeline", "availability"],
            },
            "last_action_status": ActionStatus.NEEDS_USER_INPUT.value,
        }
        snapshot = build_snapshot(state)
        assert snapshot.startswith("[GRAPH_STATE_V1]")
        parsed = parse_latest_snapshot([snapshot])
        assert parsed == state

    def test_parse_returns_none_for_no_match(self):
        assert parse_latest_snapshot(["hello world"]) is None

    def test_parse_returns_none_for_malformed_json(self):
        assert parse_latest_snapshot(["[GRAPH_STATE_V1] {not valid}"]) is None

    def test_parse_returns_none_for_non_dict_json(self):
        assert parse_latest_snapshot(["[GRAPH_STATE_V1] 42"]) is None
        assert parse_latest_snapshot(["[GRAPH_STATE_V1] \"string\""]) is None

    def test_parse_picks_latest_when_multiple_snapshots_exist(self):
        older = build_snapshot(
            {
                "active_domain": "training",
                "pending_action": {
                    "kind": PendingActionKind.NONE.value,
                    "status": ActionStatus.NO_ACTION_NEEDED.value,
                    "missing_slots": [],
                },
                "last_action_status": ActionStatus.NO_ACTION_NEEDED.value,
            }
        )
        newer = build_snapshot(
            {
                "active_domain": "plan",
                "pending_action": {
                    "kind": PendingActionKind.PLAN_DISCOVERY.value,
                    "status": ActionStatus.NEEDS_USER_INPUT.value,
                    "missing_slots": ["goal"],
                },
                "last_action_status": ActionStatus.NEEDS_USER_INPUT.value,
            }
        )
        result = parse_latest_snapshot([older, newer])
        assert result["active_domain"] == "plan"
        assert result["pending_action"]["missing_slots"] == ["goal"]

    def test_parse_ignores_non_system_between_snapshots(self):
        snapshot = build_snapshot(
            {
                "active_domain": "plan",
                "pending_action": {
                    "kind": PendingActionKind.PLAN_DISCOVERY.value,
                    "status": ActionStatus.NEEDS_USER_INPUT.value,
                    "missing_slots": [],
                },
                "last_action_status": ActionStatus.NEEDS_USER_INPUT.value,
            }
        )
        result = parse_latest_snapshot(["random system message", snapshot, "tool feedback"])
        assert result is not None
        assert result["active_domain"] == "plan"

    def test_parse_handles_empty_list(self):
        assert parse_latest_snapshot([]) is None

    def test_parse_backward_compat_with_old_owner_fields(self):
        """Old snapshots with primary_owner/interaction_mode still parse correctly."""
        state = {
            "active_domain": "training",
            "primary_owner": "training_specialist",
            "interaction_mode": "domain_analysis",
            "pending_action": {
                "kind": PendingActionKind.DOMAIN_EXECUTION.value,
                "status": ActionStatus.EXECUTED.value,
                "missing_slots": [],
            },
            "last_action_status": ActionStatus.EXECUTED.value,
        }
        snapshot = build_snapshot(state)
        parsed = parse_latest_snapshot([snapshot])
        assert parsed is not None
        assert parsed["active_domain"] == "training"
        assert parsed["pending_action"]["kind"] == PendingActionKind.DOMAIN_EXECUTION.value


class TestDefaultState:
    def test_default_is_valid(self):
        state = default_conversation_state()
        assert state["active_domain"] == "general"
        assert state["pending_action"]["kind"] == PendingActionKind.NONE.value
        assert state["pending_action"]["status"] == ActionStatus.NO_ACTION_NEEDED.value
        assert state["last_action_status"] == ActionStatus.NO_ACTION_NEEDED.value


class TestPendingActionMerge:
    def test_merge_updates_existing_fields(self):
        base = {
            "active_domain": "plan",
            "pending_action": {
                "kind": PendingActionKind.PLAN_DISCOVERY.value,
                "status": ActionStatus.NEEDS_USER_INPUT.value,
                "missing_slots": ["goal", "timeline"],
            },
        }
        update = {"kind": PendingActionKind.DOMAIN_EXECUTION.value}
        result = merge_pending_action_update(base, update)
        assert result["pending_action"]["kind"] == PendingActionKind.DOMAIN_EXECUTION.value
        assert result["pending_action"]["status"] == ActionStatus.NEEDS_USER_INPUT.value
        assert result["pending_action"]["missing_slots"] == ["goal", "timeline"]

    def test_merge_handles_none_update(self):
        base = {
            "active_domain": "plan",
            "pending_action": {
                "kind": PendingActionKind.PLAN_DISCOVERY.value,
                "status": ActionStatus.NEEDS_USER_INPUT.value,
                "missing_slots": [],
            },
        }
        result = merge_pending_action_update(base, None)
        assert result == base

    def test_merge_handles_empty_update(self):
        base = {
            "active_domain": "plan",
            "pending_action": {
                "kind": PendingActionKind.PLAN_DISCOVERY.value,
                "status": ActionStatus.NEEDS_USER_INPUT.value,
                "missing_slots": [],
            },
        }
        result = merge_pending_action_update(base, {})
        assert result == base

    def test_merge_preserves_non_pending_fields(self):
        base = {
            "active_domain": "plan",
            "pending_action": {
                "kind": PendingActionKind.PLAN_DISCOVERY.value,
                "status": ActionStatus.NEEDS_USER_INPUT.value,
                "missing_slots": ["goal"],
            },
        }
        update = {"missing_slots": ["goal", "availability"]}
        result = merge_pending_action_update(base, update)
        assert result["active_domain"] == "plan"
        assert result["pending_action"]["missing_slots"] == ["goal", "availability"]

    def test_merge_resets_pending_action_when_kind_is_none(self):
        base = {
            "active_domain": "plan",
            "pending_action": {
                "kind": PendingActionKind.PLAN_DISCOVERY.value,
                "status": ActionStatus.NEEDS_USER_INPUT.value,
                "missing_slots": ["goal", "timeline"],
            },
        }
        update = {
            "kind": "none",
            "status": "no_action_needed",
            "missing_slots": [],
        }
        result = merge_pending_action_update(base, update)
        assert result["pending_action"]["kind"] == "none"
        assert result["pending_action"]["status"] == "no_action_needed"
        assert result["pending_action"]["missing_slots"] == []


class TestEnumValues:
    def test_action_statuses_cover_expected_outcomes(self):
        values = {s.value for s in ActionStatus}
        assert "executed" in values
        assert "needs_user_input" in values
        assert "no_action_needed" in values

    def test_pending_action_kinds_cover_expected_categories(self):
        values = {k.value for k in PendingActionKind}
        assert "plan_discovery" in values
        assert "plan_review" in values
        assert "domain_execution" in values
        assert "domain_analysis" in values
        assert "none" in values


class TestResolvePendingAction:
    def test_picks_domain_execution_over_none(self):
        suggestions = {
            "training_specialist": {
                "kind": PendingActionKind.DOMAIN_EXECUTION.value,
                "status": ActionStatus.NEEDS_USER_INPUT.value,
                "missing_slots": [],
            },
            "nutrition_specialist": {
                "kind": PendingActionKind.NONE.value,
                "status": ActionStatus.NO_ACTION_NEEDED.value,
                "missing_slots": [],
            },
        }
        result = resolve_pending_action(suggestions)
        assert result["kind"] == PendingActionKind.DOMAIN_EXECUTION.value

    def test_picks_plan_discovery_over_domain_analysis(self):
        suggestions = {
            "nutrition_specialist": {
                "kind": PendingActionKind.DOMAIN_ANALYSIS.value,
                "status": ActionStatus.NO_ACTION_NEEDED.value,
                "missing_slots": [],
            },
            "plan_specialist": {
                "kind": PendingActionKind.PLAN_DISCOVERY.value,
                "status": ActionStatus.NEEDS_USER_INPUT.value,
                "missing_slots": ["goal"],
            },
        }
        result = resolve_pending_action(suggestions)
        assert result["kind"] == PendingActionKind.PLAN_DISCOVERY.value
        assert result["missing_slots"] == ["goal"]

    def test_defaults_to_no_action_when_all_none(self):
        suggestions = {
            "training_specialist": {
                "kind": PendingActionKind.NONE.value,
                "status": ActionStatus.NO_ACTION_NEEDED.value,
                "missing_slots": [],
            },
            "nutrition_specialist": {
                "kind": PendingActionKind.NONE.value,
                "status": ActionStatus.NO_ACTION_NEEDED.value,
                "missing_slots": [],
            },
            "plan_specialist": {
                "kind": PendingActionKind.NONE.value,
                "status": ActionStatus.NO_ACTION_NEEDED.value,
                "missing_slots": [],
            },
        }
        result = resolve_pending_action(suggestions)
        assert result["kind"] == PendingActionKind.NONE.value

    def test_defaults_to_no_action_on_empty(self):
        result = resolve_pending_action({})
        assert result["kind"] == PendingActionKind.NONE.value
        assert result["status"] == ActionStatus.NO_ACTION_NEEDED.value

    def test_picks_domain_execution_over_plan_discovery(self):
        suggestions = {
            "training_specialist": {
                "kind": PendingActionKind.DOMAIN_EXECUTION.value,
                "status": ActionStatus.NEEDS_USER_INPUT.value,
                "missing_slots": [],
            },
            "plan_specialist": {
                "kind": PendingActionKind.PLAN_DISCOVERY.value,
                "status": ActionStatus.NEEDS_USER_INPUT.value,
                "missing_slots": ["goal"],
            },
        }
        result = resolve_pending_action(suggestions)
        assert result["kind"] == PendingActionKind.DOMAIN_EXECUTION.value


class TestConversationSummary:
    def test_build_and_parse_roundtrip(self):
        summary_text = "Usuario busca hipertrofia. Treinos FB 5x/semana."
        built = build_conversation_summary(summary_text)
        assert built.startswith("[CONVERSATION_SUMMARY_V1]")
        parsed = parse_latest_summary([built])
        assert parsed == summary_text

    def test_parse_returns_none_for_no_summary(self):
        assert parse_latest_summary(["hello world"]) is None
        assert parse_latest_summary(["[GRAPH_STATE_V1] {}"]) is None

    def test_parse_picks_latest_when_multiple(self):
        old = build_conversation_summary("old summary")
        new = build_conversation_summary("new summary")
        parsed = parse_latest_summary([old, new])
        assert parsed == "new summary"

    def test_parse_ignores_non_summary_messages(self):
        summary = build_conversation_summary("current summary")
        msgs = ["[GRAPH_STATE_V1] {}", "regular message", summary]
        parsed = parse_latest_summary(msgs)
        assert parsed == "current summary"

    def test_parse_handles_empty_content(self):
        assert parse_latest_summary(["[CONVERSATION_SUMMARY_V1]"]) is None
        assert parse_latest_summary(["[CONVERSATION_SUMMARY_V1] "]) is None