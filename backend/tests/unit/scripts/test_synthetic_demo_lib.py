"""Tests for synthetic demo scenario loading and generation."""

from argparse import Namespace
from pathlib import Path

import pytest
from bson import json_util
from pydantic import ValidationError

from scripts.build_demo_snapshot import (
    build_parser,
    generate_synthetic_snapshot_artifact,
    publish_snapshot,
)
from scripts.synthetic_demo_lib import (
    generate_synthetic_snapshot,
    load_synthetic_scenario,
)


def test_load_synthetic_scenario_returns_ethan_v1_metadata():
    scenario = load_synthetic_scenario(
        Path("backend/scripts/demo_scenarios/ethan_parker_v1.json")
    )

    assert scenario["scenario_id"] == "ethan-parker-v1"
    assert scenario["locale"] == "en"
    assert scenario["persona"]["display_name"] == "Ethan Parker"
    assert scenario["trainer_profile"]["trainer_type"] == "gymbro"
    assert scenario["data_windows"]["workout_weeks"] == 8
    assert len(scenario["episodes"]) == 12
    assert scenario["episodes"][0]["messages"][0]["timestamp"] == "2026-01-05T08:30:00Z"
    assert "montar um treino" in scenario["episodes"][0]["messages"][0]["translations"]["pt-BR"].lower()
    assert scenario["memory_seeds"][0]["memory"].startswith(
        "Prefers four training days"
    )


def test_ethan_scenario_uses_operations_first_system_actions_with_gymbro_voice():
    scenario = load_synthetic_scenario(
        Path("backend/scripts/demo_scenarios/ethan_parker_v1.json")
    )

    plan_episode = scenario["episodes"][0]
    hevy_episode = scenario["episodes"][1]
    calorie_episode = scenario["episodes"][2]
    macros_episode = scenario["episodes"][3]
    weight_episode = scenario["episodes"][5]
    memory_episode = scenario["episodes"][6]

    assert plan_episode["title"] == "Training plan request and fit check"
    assert (
        plan_episode["messages"][0]["content"]
        == "Could you build me a training plan here?"
    )
    assert (
        "Before I save anything, tell me how many days you can train"
        in plan_episode["messages"][1]["content"]
    )
    assert "I saved it as Upper A, Lower A, Upper B, and Lower B" in plan_episode["messages"][5]["content"]

    assert hevy_episode["title"] == "Hevy routine creation from the saved split"
    assert "Done. I created the four routines in Hevy" in hevy_episode["messages"][1]["content"]
    assert "I can coach from the work you actually did" in hevy_episode["messages"][7]["content"]

    assert calorie_episode["title"] == "Calorie target explanation from account data"
    assert "2,320 calories and 180 protein" in calorie_episode["messages"][0]["content"]
    assert "meant to hold up once Hevy workouts, weigh-ins, and nutrition logs start piling up" in calorie_episode["messages"][5]["content"]

    assert macros_episode["title"] == "Save today's macros and explain adherence"
    assert "Done, bro. I saved today's nutrition log in the system" in macros_episode["messages"][1]["content"]
    assert "2,249 kcal, 172.2 g protein, 221.3 g carbs, and 76.1 g fat" in macros_episode["messages"][1]["content"]

    assert weight_episode["title"] == "Save today's weigh-in and explain trend"
    assert "Done. I saved today's weigh-in at 82.1 kg." in weight_episode["messages"][1]["content"]
    assert "83.18 kg to 82.26 kg" in weight_episode["messages"][5]["content"]

    assert memory_episode["title"] == "Save memory for travel and lighter Wednesdays"
    assert "Done. I saved both to memory." in memory_episode["messages"][1]["content"]
    assert "Once it's saved, it should work for you." in memory_episode["messages"][7]["content"]


def test_ethan_scenario_final_episode_synthesizes_saved_system_state():
    scenario = load_synthetic_scenario(
        Path("backend/scripts/demo_scenarios/ethan_parker_v1.json")
    )

    travel_episode = scenario["episodes"][7]
    macros_episode = scenario["episodes"][9]
    hevy_episode = scenario["episodes"][10]
    next_week_episode = scenario["episodes"][11]

    all_lines = [
        message["content"]
        for episode in scenario["episodes"]
        for message in episode["messages"]
    ]

    assert travel_episode["title"] == "Travel-week nutrition adjustment using saved memory"
    assert (
        travel_episode["messages"][0]["content"]
        == "You saved that I travel twice a month. I have two client dinners this week. Can you adjust the plan around that?"
    )
    assert "I used the travel note from memory" in travel_episode["messages"][1]["content"]

    assert macros_episode["title"] == "Save today's macros and explain the plan"
    assert "I saved today's nutrition log in the system" in macros_episode["messages"][1]["content"]
    assert "2,249 kcal, 172.2 g protein, 221.3 g carbs, and 76.1 g fat" in macros_episode["messages"][1]["content"]
    assert "the weekly average, not a single short landing" in macros_episode["messages"][3]["content"]

    assert hevy_episode["title"] == "Create the next training week in Hevy"
    assert "I created the four routines in Hevy" in hevy_episode["messages"][1]["content"]
    assert "Upper A is bench plus horizontal pulling" in hevy_episode["messages"][3]["content"]
    assert "I can coach from the work you actually did" in hevy_episode["messages"][7]["content"]

    assert next_week_episode["title"] == "Explain the calorie target from the account data"
    assert (
        next_week_episode["messages"][0]["content"]
        == "Could you explain how you got to 2,320 calories and 180 protein?"
    )
    assert "I set that from the data already in your account" in next_week_episode["messages"][1]["content"]
    assert "Here the target is meant to hold up once Hevy workouts, weigh-ins, and nutrition logs start piling up" in next_week_episode["messages"][5]["content"]
    assert "Hit calories consistently, keep protein near 180" in next_week_episode["messages"][7]["content"]

    assert not any("next block" in line.lower() for line in all_lines)
    assert not any("dashboard is basically" in line.lower() for line in all_lines)


def test_load_synthetic_scenario_missing_file_raises_file_not_found_error():
    with pytest.raises(FileNotFoundError):
        load_synthetic_scenario(
            Path("backend/scripts/demo_scenarios/does_not_exist.json")
        )


def test_load_synthetic_scenario_directory_path_raises_file_not_found_error(
    tmp_path: Path,
):
    with pytest.raises(FileNotFoundError):
        load_synthetic_scenario(tmp_path)


def test_load_synthetic_scenario_malformed_structure_raises_validation_error(
    tmp_path: Path,
):
    scenario_file = tmp_path / "malformed.json"
    scenario_file.write_text('{"scenario_id": "broken"}', encoding="utf-8")

    with pytest.raises(ValidationError):
        load_synthetic_scenario(scenario_file)


def test_load_synthetic_scenario_invalid_message_timestamp_raises_validation_error(
    tmp_path: Path,
):
    scenario_file = tmp_path / "invalid-timestamp.json"
    scenario_file.write_text(
        """
        {
          "scenario_id": "broken-scenario",
          "content_version": "v1",
          "locale": "en",
          "source_user_email": "synthetic:broken:v1",
          "persona": {
            "display_name": "Broken Demo",
            "age": 35,
            "gender": "Male",
            "height": 182,
            "weight": 84.6,
            "goal_type": "lose",
            "weekly_rate": 0.25,
            "target_weight": 81.5,
            "subscription_plan": "Premium",
            "occupation": "Designer",
            "notes": "Demo"
          },
          "trainer_profile": {
            "trainer_type": "atlas",
            "preferred_language": "en-US",
            "personality_level": "balanced"
          },
          "integration_state": {
            "hevy_enabled": true,
            "hevy_connected": true,
            "telegram_enabled": false
          },
          "memory_seeds": [
            {"memory": "Seed memory", "category": "context"}
          ],
          "data_windows": {
            "weight_days": 56,
            "nutrition_days": 35,
            "workout_weeks": 8
          },
          "episodes": [
            {
              "episode_id": "ep1",
              "primary_domain": "memory",
              "started_at": "2026-01-05T08:30:00Z",
              "title": "Broken timestamps",
              "messages": [
                {
                  "role": "human",
                  "trainer_type": "atlas",
                  "content": "Hello",
                  "timestamp": "not-a-timestamp"
                }
              ]
            }
          ]
        }
        """,
        encoding="utf-8",
    )

    with pytest.raises(ValidationError):
        load_synthetic_scenario(scenario_file)


def test_load_synthetic_scenario_out_of_order_message_timestamps_raise_validation_error(
    tmp_path: Path,
):
    scenario_file = tmp_path / "out-of-order.json"
    scenario_file.write_text(
        """
        {
          "scenario_id": "broken-scenario",
          "content_version": "v1",
          "locale": "en",
          "source_user_email": "synthetic:broken:v1",
          "persona": {
            "display_name": "Broken Demo",
            "age": 35,
            "gender": "Male",
            "height": 182,
            "weight": 84.6,
            "goal_type": "lose",
            "weekly_rate": 0.25,
            "target_weight": 81.5,
            "subscription_plan": "Premium",
            "occupation": "Designer",
            "notes": "Demo"
          },
          "trainer_profile": {
            "trainer_type": "atlas",
            "preferred_language": "en-US",
            "personality_level": "balanced"
          },
          "integration_state": {
            "hevy_enabled": true,
            "hevy_connected": true,
            "telegram_enabled": false
          },
          "memory_seeds": [
            {"memory": "Seed memory", "category": "context"}
          ],
          "data_windows": {
            "weight_days": 56,
            "nutrition_days": 35,
            "workout_weeks": 8
          },
          "episodes": [
            {
              "episode_id": "ep1",
              "primary_domain": "memory",
              "started_at": "2026-01-05T08:30:00Z",
              "title": "Broken ordering",
              "messages": [
                {
                  "role": "human",
                  "trainer_type": "atlas",
                  "content": "First",
                  "timestamp": "2026-01-05T08:36:00Z"
                },
                {
                  "role": "ai",
                  "trainer_type": "atlas",
                  "content": "Second",
                  "timestamp": "2026-01-05T08:30:00Z"
                }
              ]
            }
          ]
        }
        """,
        encoding="utf-8",
    )

    with pytest.raises(ValidationError):
        load_synthetic_scenario(scenario_file)


def test_generate_synthetic_snapshot_builds_publishable_demo_dataset():
    scenario = load_synthetic_scenario(
        Path("backend/scripts/demo_scenarios/ethan_parker_v1.json")
    )

    snapshot = generate_synthetic_snapshot(
        scenario=scenario,
        demo_email="demo@fityq.it",
        locale="en",
        snapshot_id="demo-synth-001",
    )
    repeated = generate_synthetic_snapshot(
        scenario=scenario,
        demo_email="demo@fityq.it",
        locale="en",
        snapshot_id="demo-synth-001",
    )

    assert snapshot["snapshot"]["snapshot_id"] == "demo-synth-001"
    assert snapshot["snapshot"]["scenario_id"] == "ethan-parker-v1"
    assert snapshot["snapshot"]["content_version"] == "v1"
    assert snapshot["snapshot"]["locale"] == "en"
    assert snapshot["snapshot"]["source_user_email"] == "synthetic:ethan-parker:v1"
    assert snapshot["snapshot"]["selection_strategy"] == "synthetic_showcase_v1"
    assert snapshot["snapshot"]["created_at"] != snapshot["demo_messages"][-1]["timestamp"]
    assert snapshot["snapshot"]["created_at"] == repeated["snapshot"]["created_at"]
    assert snapshot["profile"]["display_name"] == "Ethan Parker"
    assert snapshot["profile"]["is_demo"] is True
    assert snapshot["profile"]["hevy_last_sync"] is not None
    assert snapshot["profile"]["hevy_api_key"] is None
    assert snapshot["profile"]["hevy_webhook_token"] is None
    assert snapshot["profile"]["hevy_webhook_secret"] is None
    assert snapshot["profile"]["messages_sent_today"] == 0
    assert snapshot["profile"]["messages_sent_this_month"] == 0
    assert snapshot["profile"]["total_messages_sent"] == 0
    assert snapshot["trainer_profiles"][0]["trainer_type"] == "gymbro"
    assert len(snapshot["demo_episodes"]) == 12
    assert len(snapshot["demo_messages"]) >= 90
    assert len(snapshot["message_store_docs"]) == len(snapshot["demo_messages"])
    assert snapshot["demo_messages"][0]["timestamp"] == "2026-01-05T08:30:00Z"
    assert snapshot["demo_messages"][0]["message_id"].startswith("msg-")
    assert snapshot["demo_messages"][0]["source_message_id"].startswith("src-")
    assert snapshot["demo_messages"][0]["translations"]["pt-BR"]
    assert snapshot["workout_logs"][0]["source"] == "hevy"
    assert snapshot["workout_logs"][0]["external_id"].startswith("hevy-ethan-parker-v1-")
    assert snapshot["workout_logs"][0]["date"].isoformat() >= "2026-01-01T00:00:00+00:00"
    assert snapshot["workout_logs"][-1]["date"].isoformat() >= "2026-03-01T00:00:00+00:00"
    assert snapshot["nutrition_logs"][0]["source"] == "myfitnesspal"
    assert snapshot["weight_logs"][0]["source"] == "scale_import"
    assert snapshot["memories"][0]["user_id"] == "demo@fityq.it"
    assert snapshot["prompt_logs"][0]["user_email"] == "demo@fityq.it"


def test_generate_synthetic_snapshot_respects_integration_state_for_workout_source():
    scenario = load_synthetic_scenario(
        Path("backend/scripts/demo_scenarios/ethan_parker_v1.json")
    )
    scenario["integration_state"]["hevy_enabled"] = False
    scenario["integration_state"]["hevy_connected"] = False

    snapshot = generate_synthetic_snapshot(
        scenario=scenario,
        demo_email="demo@fityq.it",
        locale="en",
        snapshot_id="demo-synth-disconnected",
    )

    assert snapshot["profile"]["hevy_last_sync"] is None
    assert snapshot["workout_logs"][0]["source"] == "manual"
    assert snapshot["workout_logs"][0]["external_id"] is None


def test_generate_synthetic_snapshot_uses_passed_locale_consistently():
    scenario = load_synthetic_scenario(
        Path("backend/scripts/demo_scenarios/ethan_parker_v1.json")
    )

    snapshot = generate_synthetic_snapshot(
        scenario=scenario,
        demo_email="demo@fityq.it",
        locale="en-GB",
        snapshot_id="demo-synth-locale-override",
    )

    assert snapshot["snapshot"]["locale"] == "en-GB"
    assert snapshot["profile"]["preferred_locale"] == "en-GB"
    assert snapshot["prompt_logs"][0]["prompt"]["locale"] == "en-GB"


def test_generate_synthetic_snapshot_clears_hevy_sync_when_hevy_disabled():
    scenario = load_synthetic_scenario(
        Path("backend/scripts/demo_scenarios/ethan_parker_v1.json")
    )
    scenario["integration_state"]["hevy_enabled"] = False
    scenario["integration_state"]["hevy_connected"] = True

    snapshot = generate_synthetic_snapshot(
        scenario=scenario,
        demo_email="demo@fityq.it",
        locale="en",
        snapshot_id="demo-synth-hevy-disabled",
    )

    assert snapshot["workout_logs"][0]["source"] == "manual"
    assert snapshot["workout_logs"][0]["external_id"] is None
    assert snapshot["profile"]["hevy_last_sync"] is None


def test_build_parser_supports_generate_synthetic_command():
    parser = build_parser()

    args = parser.parse_args(
        [
            "generate-synthetic",
            "--scenario-file",
            "backend/scripts/demo_scenarios/ethan_parker_v1.json",
            "--output-dir",
            "artifacts/demo/synthetic/ethan-parker-v1-en",
            "--demo-email",
            "demo@fityq.it",
            "--locale",
            "en",
        ]
    )

    assert args.command == "generate-synthetic"
    assert args.scenario_file == "backend/scripts/demo_scenarios/ethan_parker_v1.json"
    assert args.output_dir == "artifacts/demo/synthetic/ethan-parker-v1-en"
    assert args.demo_email == "demo@fityq.it"
    assert args.locale == "en"


def test_generate_synthetic_parser_default_scenario_file_resolves_from_repo_root(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    parser = build_parser()
    args = parser.parse_args(["generate-synthetic"])
    args.output_dir = str(tmp_path / "synthetic-artifact")

    repo_root = Path(__file__).resolve().parents[4]
    monkeypatch.chdir(repo_root)

    generate_synthetic_snapshot_artifact(args)

    assert (Path(args.output_dir) / "curated_snapshot.json").is_file()
    assert (Path(args.output_dir) / "chat_review.json").is_file()


def test_publish_snapshot_replaces_demo_memories(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    calls: list[tuple[str, str]] = []

    def fake_replace_demo_memories(memories, demo_email):
        calls.append((demo_email, memories[0]["memory"]))

    class FakeCollection:
        def delete_many(self, *_args, **_kwargs):
            return None

        def insert_one(self, *_args, **_kwargs):
            return None

        def insert_many(self, *_args, **_kwargs):
            return None

    class FakeDatabase:
        def __init__(self):
            collection = FakeCollection()
            self.users = collection
            self.trainer_profiles = collection
            self.workout_logs = collection
            self.nutrition_logs = collection
            self.weight_logs = collection
            self.prompt_logs = collection
            self.message_store = collection
            self.demo_snapshots = collection
            self.demo_episodes = collection
            self.demo_messages = collection
            self.demo_prune_log = collection

    class FakeMongoClient:
        def __getitem__(self, _name: str):
            return FakeDatabase()

    monkeypatch.setattr(
        "scripts.build_demo_snapshot.replace_demo_memories",
        fake_replace_demo_memories,
    )
    monkeypatch.setattr(
        "scripts.build_demo_snapshot.confirm_execution",
        lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(
        "scripts.build_demo_snapshot.MongoClient",
        lambda *_args, **_kwargs: FakeMongoClient(),
    )

    curated = {
        "snapshot": {"snapshot_id": "demo-synth-001", "demo_email": "demo@fityq.it"},
        "profile": {"email": "demo@fityq.it"},
        "trainer_profiles": [],
        "workout_logs": [],
        "nutrition_logs": [],
        "weight_logs": [],
        "prompt_logs": [],
        "demo_episodes": [],
        "demo_messages": [],
        "message_store_docs": [],
        "memories": [
            {
                "user_id": "demo@fityq.it",
                "memory": "Prefers concise weekly plans.",
                "category": "context",
            }
        ],
    }
    curated_path = tmp_path / "curated_snapshot.json"
    curated_path.write_text(json_util.dumps(curated), encoding="utf-8")

    publish_snapshot(Namespace(curated_file=str(curated_path)))

    assert calls == [("demo@fityq.it", "Prefers concise weekly plans.")]


def test_publish_snapshot_with_empty_memories_still_clears_demo_memories(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    calls: list[tuple[str, list[dict]]] = []

    def fake_replace_demo_memories(memories, demo_email):
        calls.append((demo_email, list(memories)))

    class FakeCollection:
        def delete_many(self, *_args, **_kwargs):
            return None

        def insert_one(self, *_args, **_kwargs):
            return None

        def insert_many(self, *_args, **_kwargs):
            return None

        def find(self, *_args, **_kwargs):
            return []

    class FakeDatabase:
        def __init__(self):
            collection = FakeCollection()
            self.users = collection
            self.trainer_profiles = collection
            self.workout_logs = collection
            self.nutrition_logs = collection
            self.weight_logs = collection
            self.prompt_logs = collection
            self.message_store = collection
            self.demo_snapshots = collection
            self.demo_episodes = collection
            self.demo_messages = collection
            self.demo_prune_log = collection

    class FakeMongoClient:
        def __getitem__(self, _name: str):
            return FakeDatabase()

    monkeypatch.setattr(
        "scripts.build_demo_snapshot.replace_demo_memories",
        fake_replace_demo_memories,
    )
    monkeypatch.setattr(
        "scripts.build_demo_snapshot.confirm_execution",
        lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(
        "scripts.build_demo_snapshot.MongoClient",
        lambda *_args, **_kwargs: FakeMongoClient(),
    )

    curated = {
        "snapshot": {"snapshot_id": "demo-synth-001", "demo_email": "demo@fityq.it"},
        "profile": {"email": "demo@fityq.it"},
        "trainer_profiles": [],
        "workout_logs": [],
        "nutrition_logs": [],
        "weight_logs": [],
        "prompt_logs": [],
        "demo_episodes": [],
        "demo_messages": [],
        "message_store_docs": [],
        "memories": [],
    }
    curated_path = tmp_path / "curated_snapshot.json"
    curated_path.write_text(json_util.dumps(curated), encoding="utf-8")

    publish_snapshot(Namespace(curated_file=str(curated_path)))

    assert calls == [("demo@fityq.it", [])]


def test_publish_snapshot_rejects_invalid_curated_payload_before_destructive_actions(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    delete_calls: list[str] = []

    class FakeCollection:
        def delete_many(self, *_args, **_kwargs):
            delete_calls.append("delete")
            return None

    class FakeDatabase:
        def __init__(self):
            collection = FakeCollection()
            self.users = collection
            self.trainer_profiles = collection
            self.workout_logs = collection
            self.nutrition_logs = collection
            self.weight_logs = collection
            self.prompt_logs = collection
            self.message_store = collection
            self.demo_snapshots = collection
            self.demo_episodes = collection
            self.demo_messages = collection
            self.demo_prune_log = collection

    class FakeMongoClient:
        def __getitem__(self, _name: str):
            return FakeDatabase()

    monkeypatch.setattr(
        "scripts.build_demo_snapshot.confirm_execution",
        lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(
        "scripts.build_demo_snapshot.MongoClient",
        lambda *_args, **_kwargs: FakeMongoClient(),
    )

    curated_path = tmp_path / "invalid_curated_snapshot.json"
    curated_path.write_text(
        json_util.dumps(
            {
                "snapshot": {"snapshot_id": "demo-synth-001"},
                "trainer_profiles": [],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Missing required curated snapshot keys"):
        publish_snapshot(Namespace(curated_file=str(curated_path)))

    assert delete_calls == []


def test_publish_snapshot_rejects_missing_snapshot_demo_email_before_destructive_actions(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    delete_calls: list[str] = []

    class FakeCollection:
        def delete_many(self, *_args, **_kwargs):
            delete_calls.append("delete")
            return None

    class FakeDatabase:
        def __init__(self):
            collection = FakeCollection()
            self.users = collection
            self.trainer_profiles = collection
            self.workout_logs = collection
            self.nutrition_logs = collection
            self.weight_logs = collection
            self.prompt_logs = collection
            self.message_store = collection
            self.demo_snapshots = collection
            self.demo_episodes = collection
            self.demo_messages = collection
            self.demo_prune_log = collection

    class FakeMongoClient:
        def __getitem__(self, _name: str):
            return FakeDatabase()

    monkeypatch.setattr(
        "scripts.build_demo_snapshot.confirm_execution",
        lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(
        "scripts.build_demo_snapshot.MongoClient",
        lambda *_args, **_kwargs: FakeMongoClient(),
    )

    curated = {
        "snapshot": {"snapshot_id": "demo-synth-001"},
        "profile": {"email": "demo@fityq.it"},
        "trainer_profiles": [],
        "workout_logs": [],
        "nutrition_logs": [],
        "weight_logs": [],
        "prompt_logs": [],
        "demo_episodes": [],
        "demo_messages": [],
        "message_store_docs": [],
    }
    curated_path = tmp_path / "missing_snapshot_demo_email.json"
    curated_path.write_text(json_util.dumps(curated), encoding="utf-8")

    with pytest.raises(ValueError, match="snapshot.demo_email"):
        publish_snapshot(Namespace(curated_file=str(curated_path)))

    assert delete_calls == []


def test_publish_snapshot_restores_previous_mongo_state_on_write_failure(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    class FakeCollection:
        def __init__(
            self,
            name: str,
            initial_docs: list[dict],
            fail_insert_many: bool = False,
        ):
            self.name = name
            self.docs = [dict(doc) for doc in initial_docs]
            self.fail_insert_many = fail_insert_many

        def find(self, query: dict):
            key, value = next(iter(query.items()))
            return [dict(doc) for doc in self.docs if doc.get(key) == value]

        def delete_many(self, query: dict):
            key, value = next(iter(query.items()))
            self.docs = [doc for doc in self.docs if doc.get(key) != value]
            return None

        def insert_one(self, doc: dict):
            self.docs.append(dict(doc))
            return None

        def insert_many(self, docs: list[dict]):
            if self.fail_insert_many:
                raise RuntimeError(f"{self.name} insert failed")
            self.docs.extend(dict(doc) for doc in docs)
            return None

    class FakeDatabase:
        def __init__(self):
            self.users = FakeCollection(
                "users",
                [{"email": "demo@fityq.it", "display_name": "Original Demo"}],
            )
            self.trainer_profiles = FakeCollection(
                "trainer_profiles",
                [{"user_email": "demo@fityq.it", "trainer_type": "atlas"}],
            )
            self.workout_logs = FakeCollection(
                "workout_logs",
                [{"user_email": "demo@fityq.it", "source": "manual"}],
            )
            self.nutrition_logs = FakeCollection("nutrition_logs", [])
            self.weight_logs = FakeCollection("weight_logs", [])
            self.prompt_logs = FakeCollection("prompt_logs", [])
            self.message_store = FakeCollection("message_store", [])
            self.demo_snapshots = FakeCollection(
                "demo_snapshots",
                [{"demo_email": "demo@fityq.it", "snapshot_id": "old"}],
            )
            self.demo_episodes = FakeCollection("demo_episodes", [])
            self.demo_messages = FakeCollection("demo_messages", [], fail_insert_many=True)
            self.demo_prune_log = FakeCollection("demo_prune_log", [])

    fake_db = FakeDatabase()

    class FakeMongoClient:
        def __getitem__(self, _name: str):
            return fake_db

    replace_calls: list[str] = []

    monkeypatch.setattr(
        "scripts.build_demo_snapshot.confirm_execution",
        lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(
        "scripts.build_demo_snapshot.MongoClient",
        lambda *_args, **_kwargs: FakeMongoClient(),
    )
    monkeypatch.setattr(
        "scripts.build_demo_snapshot.replace_demo_memories",
        lambda *_args, **_kwargs: replace_calls.append("called"),
    )

    curated = {
        "snapshot": {"snapshot_id": "demo-synth-001", "demo_email": "demo@fityq.it"},
        "profile": {"email": "demo@fityq.it", "display_name": "New Demo"},
        "trainer_profiles": [{"user_email": "demo@fityq.it", "trainer_type": "atlas"}],
        "workout_logs": [{"user_email": "demo@fityq.it", "source": "hevy"}],
        "nutrition_logs": [],
        "weight_logs": [],
        "prompt_logs": [],
        "demo_episodes": [],
        "demo_messages": [{"demo_email": "demo@fityq.it", "message_id": "msg-1"}],
        "message_store_docs": [],
        "memories": [{"user_id": "demo@fityq.it", "memory": "Keep recovery Wednesday."}],
    }
    curated_path = tmp_path / "curated_snapshot.json"
    curated_path.write_text(json_util.dumps(curated), encoding="utf-8")

    with pytest.raises(RuntimeError, match="demo_messages insert failed"):
        publish_snapshot(Namespace(curated_file=str(curated_path)))

    assert fake_db.users.docs == [{"email": "demo@fityq.it", "display_name": "Original Demo"}]
    assert fake_db.workout_logs.docs == [{"user_email": "demo@fityq.it", "source": "manual"}]
    assert fake_db.demo_snapshots.docs == [{"demo_email": "demo@fityq.it", "snapshot_id": "old"}]
    assert replace_calls == []


def test_publish_snapshot_restores_previous_mongo_state_on_memory_replacement_failure(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    class FakeCollection:
        def __init__(self, initial_docs: list[dict]):
            self.docs = [dict(doc) for doc in initial_docs]

        def find(self, query: dict):
            key, value = next(iter(query.items()))
            return [dict(doc) for doc in self.docs if doc.get(key) == value]

        def delete_many(self, query: dict):
            key, value = next(iter(query.items()))
            self.docs = [doc for doc in self.docs if doc.get(key) != value]
            return None

        def insert_one(self, doc: dict):
            self.docs.append(dict(doc))
            return None

        def insert_many(self, docs: list[dict]):
            self.docs.extend(dict(doc) for doc in docs)
            return None

    class FakeDatabase:
        def __init__(self):
            self.users = FakeCollection(
                [{"email": "demo@fityq.it", "display_name": "Original Demo"}]
            )
            self.trainer_profiles = FakeCollection(
                [{"user_email": "demo@fityq.it", "trainer_type": "atlas"}]
            )
            self.workout_logs = FakeCollection(
                [{"user_email": "demo@fityq.it", "source": "manual"}]
            )
            self.nutrition_logs = FakeCollection([])
            self.weight_logs = FakeCollection([])
            self.prompt_logs = FakeCollection([])
            self.message_store = FakeCollection([])
            self.demo_snapshots = FakeCollection(
                [{"demo_email": "demo@fityq.it", "snapshot_id": "old"}]
            )
            self.demo_episodes = FakeCollection(
                [{"demo_email": "demo@fityq.it", "episode_id": "old-ep"}]
            )
            self.demo_messages = FakeCollection(
                [{"demo_email": "demo@fityq.it", "message_id": "old-msg"}]
            )
            self.demo_prune_log = FakeCollection([])

    fake_db = FakeDatabase()

    class FakeMongoClient:
        def __getitem__(self, _name: str):
            return fake_db

    monkeypatch.setattr(
        "scripts.build_demo_snapshot.confirm_execution",
        lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(
        "scripts.build_demo_snapshot.MongoClient",
        lambda *_args, **_kwargs: FakeMongoClient(),
    )
    monkeypatch.setattr(
        "scripts.build_demo_snapshot.replace_demo_memories",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("qdrant failed")),
    )

    curated = {
        "snapshot": {"snapshot_id": "demo-synth-001", "demo_email": "demo@fityq.it"},
        "profile": {"email": "demo@fityq.it", "display_name": "New Demo"},
        "trainer_profiles": [{"user_email": "demo@fityq.it", "trainer_type": "atlas"}],
        "workout_logs": [{"user_email": "demo@fityq.it", "source": "hevy"}],
        "nutrition_logs": [],
        "weight_logs": [],
        "prompt_logs": [],
        "demo_episodes": [{"demo_email": "demo@fityq.it", "episode_id": "new-ep"}],
        "demo_messages": [{"demo_email": "demo@fityq.it", "message_id": "new-msg"}],
        "message_store_docs": [],
        "memories": [{"user_id": "demo@fityq.it", "memory": "Keep recovery Wednesday."}],
    }
    curated_path = tmp_path / "curated_snapshot.json"
    curated_path.write_text(json_util.dumps(curated), encoding="utf-8")

    with pytest.raises(RuntimeError, match="qdrant failed"):
        publish_snapshot(Namespace(curated_file=str(curated_path)))

    assert fake_db.users.docs == [{"email": "demo@fityq.it", "display_name": "Original Demo"}]
    assert fake_db.workout_logs.docs == [{"user_email": "demo@fityq.it", "source": "manual"}]
    assert fake_db.demo_snapshots.docs == [{"demo_email": "demo@fityq.it", "snapshot_id": "old"}]
    assert fake_db.demo_episodes.docs == [{"demo_email": "demo@fityq.it", "episode_id": "old-ep"}]
    assert fake_db.demo_messages.docs == [{"demo_email": "demo@fityq.it", "message_id": "old-msg"}]


def test_publish_snapshot_rejects_mismatched_child_ownership_before_destructive_actions(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    delete_calls: list[str] = []

    class FakeCollection:
        def delete_many(self, *_args, **_kwargs):
            delete_calls.append("delete")
            return None

        def find(self, *_args, **_kwargs):
            return []

    class FakeDatabase:
        def __init__(self):
            collection = FakeCollection()
            self.users = collection
            self.trainer_profiles = collection
            self.workout_logs = collection
            self.nutrition_logs = collection
            self.weight_logs = collection
            self.prompt_logs = collection
            self.message_store = collection
            self.demo_snapshots = collection
            self.demo_episodes = collection
            self.demo_messages = collection
            self.demo_prune_log = collection

    class FakeMongoClient:
        def __getitem__(self, _name: str):
            return FakeDatabase()

    monkeypatch.setattr(
        "scripts.build_demo_snapshot.confirm_execution",
        lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(
        "scripts.build_demo_snapshot.MongoClient",
        lambda *_args, **_kwargs: FakeMongoClient(),
    )

    curated = {
        "snapshot": {"snapshot_id": "demo-synth-001", "demo_email": "demo@fityq.it"},
        "profile": {"email": "demo@fityq.it"},
        "trainer_profiles": [{"user_email": "other@fityq.it", "trainer_type": "atlas"}],
        "workout_logs": [],
        "nutrition_logs": [],
        "weight_logs": [],
        "prompt_logs": [],
        "demo_episodes": [],
        "demo_messages": [],
        "message_store_docs": [],
    }
    curated_path = tmp_path / "mismatched_curated_snapshot.json"
    curated_path.write_text(json_util.dumps(curated), encoding="utf-8")

    with pytest.raises(ValueError, match="ownership mismatch"):
        publish_snapshot(Namespace(curated_file=str(curated_path)))

    assert delete_calls == []
