"""Tests for conversation contract module."""

from src.services.graph.conversation_contract import (
    ActionStatus,
    InteractionMode,
    PendingActionKind,
    PrimaryOwner,
    build_snapshot,
    default_conversation_state,
    merge_pending_action_update,
    parse_latest_snapshot,
)


class TestSnapshotPersistence:
    def test_build_and_parse_roundtrip(self):
        state = {
            "active_domain": "plan",
            "interaction_mode": InteractionMode.PLAN_DISCOVERY.value,
            "primary_owner": PrimaryOwner.PLAN_SPECIALIST.value,
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
                "interaction_mode": InteractionMode.DOMAIN_ANALYSIS.value,
                "primary_owner": PrimaryOwner.TRAINING_SPECIALIST.value,
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
                "interaction_mode": InteractionMode.PLAN_DISCOVERY.value,
                "primary_owner": PrimaryOwner.PLAN_SPECIALIST.value,
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
                "interaction_mode": InteractionMode.PLAN_DISCOVERY.value,
                "primary_owner": PrimaryOwner.PLAN_SPECIALIST.value,
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


class TestDefaultState:
    def test_default_is_valid(self):
        state = default_conversation_state()
        assert state["active_domain"] == "general"
        assert state["interaction_mode"] == InteractionMode.GENERAL.value
        assert state["pending_action"]["kind"] == PendingActionKind.NONE.value


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
            "interaction_mode": InteractionMode.PLAN_DISCOVERY.value,
            "pending_action": {
                "kind": PendingActionKind.PLAN_DISCOVERY.value,
                "status": ActionStatus.NEEDS_USER_INPUT.value,
                "missing_slots": ["goal"],
            },
        }
        update = {"missing_slots": ["goal", "availability"]}
        result = merge_pending_action_update(base, update)
        assert result["active_domain"] == "plan"
        assert result["interaction_mode"] == InteractionMode.PLAN_DISCOVERY.value
        assert result["pending_action"]["missing_slots"] == ["goal", "availability"]


class TestEnumValues:
    def test_interaction_modes_cover_expected_conversation_types(self):
        values = {m.value for m in InteractionMode}
        assert "general" in values
        assert "plan_discovery" in values
        assert "execution_request" in values
        assert "slot_answer" in values

    def test_action_statuses_cover_expected_outcomes(self):
        values = {s.value for s in ActionStatus}
        assert "executed" in values
        assert "needs_user_input" in values
        assert "escalate_to_plan" in values
        assert "no_action_needed" in values

    def test_primary_owners_cover_all_conversational_nodes(self):
        values = {o.value for o in PrimaryOwner}
        assert "training_specialist" in values
        assert "nutrition_specialist" in values
        assert "plan_specialist" in values
        assert "coach_reply" in values
