# Synthetic Demo Showcase Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the current local demo dataset with a fully synthetic English showcase account for Ethan Parker, backed by coherent chat, logs, memory, and local publish tooling.

**Architecture:** Keep the existing read-only demo protections, admin pruning flow, and publish collections. Add a deterministic synthetic-scenario authoring layer plus a new generator command that produces a publishable snapshot artifact, then extend publish to replace both Mongo demo data and Qdrant demo memories in the local environment.

**Tech Stack:** Python 3.12+, FastAPI backend scripts, MongoDB, Qdrant, Firebase Admin, Pytest, Ruff, Pylint

---

## File Structure

### New Files

- `backend/scripts/demo_scenarios/ethan_parker_v1.json`
  Purpose: Editable authored source for persona, episode copy, memory seeds, and structured-data generation parameters.
- `backend/scripts/synthetic_demo_lib.py`
  Purpose: Deterministic generator that turns the authored scenario into a publishable synthetic snapshot.
- `backend/tests/unit/scripts/test_synthetic_demo_lib.py`
  Purpose: Unit coverage for scenario loading, synthetic snapshot generation, and synthetic message construction.

### Modified Files

- `backend/scripts/build_demo_snapshot.py`
  Purpose: Add `generate-synthetic` command and extend `publish` to replace demo memories in Qdrant as part of local publish.
- `backend/tests/unit/scripts/test_demo_snapshot_lib.py`
  Purpose: Keep regression coverage for shared publish helpers and add parser/publish behavior checks if they still belong with the existing script tests.

### Existing Files To Read Before Editing

- `backend/scripts/demo_snapshot_lib.py`
  Reason: Reuse `build_message_store_docs` and preserve existing `demo_episodes` / `demo_messages` contract used by admin pruning.
- `backend/src/api/models/user_profile.py`
  Reason: Keep synthetic profile fields compatible with the app and preserve `is_demo=True`.
- `backend/src/api/models/trainer_profile.py`
  Reason: Build a valid trainer profile for the synthetic persona.
- `backend/src/api/models/workout_log.py`
  Reason: Generate workout records that match dashboard and workout list expectations.
- `backend/src/api/models/nutrition_log.py`
  Reason: Generate nutrition records that support macros and target discussion.
- `backend/src/api/models/weight_log.py`
  Reason: Generate believable trend-ready weight and composition data.
- `backend/src/services/memory_service.py`
  Reason: Reuse the memory add path for synthetic Qdrant publication instead of inventing a parallel storage format.

## Task 1: Author the Ethan Parker Scenario Source

**Files:**
- Create: `backend/scripts/demo_scenarios/ethan_parker_v1.json`
- Test: `backend/tests/unit/scripts/test_synthetic_demo_lib.py`

- [ ] **Step 1: Write the failing scenario-loading test**

```python
from pathlib import Path

from scripts.synthetic_demo_lib import load_synthetic_scenario


def test_load_synthetic_scenario_returns_ethan_v1_metadata():
    scenario = load_synthetic_scenario(
        Path("backend/scripts/demo_scenarios/ethan_parker_v1.json")
    )

    assert scenario["scenario_id"] == "ethan-parker-v1"
    assert scenario["locale"] == "en"
    assert scenario["persona"]["display_name"] == "Ethan Parker"
    assert scenario["trainer_profile"]["trainer_type"] == "atlas"
    assert len(scenario["episodes"]) == 12
    assert scenario["memory_seeds"][0]["memory"].startswith(
        "Prefers four training days"
    )
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
cd /home/colutti/projects/personal/backend && .venv/bin/pytest tests/unit/scripts/test_synthetic_demo_lib.py::test_load_synthetic_scenario_returns_ethan_v1_metadata -v
```

Expected: FAIL with `ModuleNotFoundError` for `scripts.synthetic_demo_lib` or missing file assertion.

- [ ] **Step 3: Create the authored scenario file**

Create `backend/scripts/demo_scenarios/ethan_parker_v1.json` with the full shape below, then fill all 12 episodes and the remaining structured-data seeds in the same format.

```json
{
  "scenario_id": "ethan-parker-v1",
  "content_version": "v1",
  "locale": "en",
  "source_user_email": "synthetic:ethan-parker:v1",
  "persona": {
    "display_name": "Ethan Parker",
    "age": 35,
    "gender": "Male",
    "height": 182,
    "weight": 84.6,
    "goal_type": "lose",
    "weekly_rate": 0.25,
    "target_weight": 81.5,
    "subscription_plan": "Premium",
    "occupation": "Product design lead",
    "notes": "Busy professional. Wants a clean system that connects training, nutrition, and decision-making."
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
    {
      "memory": "Prefers four training days per week and protects Wednesday as a lighter recovery day.",
      "category": "context"
    },
    {
      "memory": "Travels for work at least twice a month and needs flexible restaurant strategies.",
      "category": "context"
    }
  ],
  "data_windows": {
    "weight_days": 70,
    "nutrition_days": 42,
    "workout_weeks": 8
  },
  "episodes": [
    {
      "episode_id": "ep01_onboarding_style",
      "primary_domain": "memory",
      "started_at": "2026-01-06T08:30:00Z",
      "title": "Onboarding and coaching style",
      "messages": [
        {
          "role": "human",
          "trainer_type": "atlas",
          "content": "I train consistently, but I waste too much energy deciding what to do each week."
        },
        {
          "role": "ai",
          "trainer_type": "atlas",
          "content": "Good. Then we are not starting from zero. We are building a cleaner system: four sessions, clear calorie targets, and fewer reactive decisions."
        }
      ]
    }
  ]
}
```

- [ ] **Step 4: Add the minimal loader**

Create `backend/scripts/synthetic_demo_lib.py` with the first minimal function needed by the test.

```python
"""Synthetic demo scenario loader and generator."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_synthetic_scenario(path: Path) -> dict[str, Any]:
    """Load an authored synthetic demo scenario from disk."""
    return json.loads(path.read_text(encoding="utf-8"))
```

- [ ] **Step 5: Run the test to verify it passes**

Run:

```bash
cd /home/colutti/projects/personal/backend && .venv/bin/pytest tests/unit/scripts/test_synthetic_demo_lib.py::test_load_synthetic_scenario_returns_ethan_v1_metadata -v
```

Expected: PASS

- [ ] **Step 6: Commit**

```bash
cd /home/colutti/projects/personal
git add backend/scripts/demo_scenarios/ethan_parker_v1.json backend/scripts/synthetic_demo_lib.py backend/tests/unit/scripts/test_synthetic_demo_lib.py
git commit -m "feat: add authored synthetic demo scenario"
```

## Task 2: Generate a Publishable Synthetic Snapshot

**Files:**
- Modify: `backend/scripts/synthetic_demo_lib.py`
- Test: `backend/tests/unit/scripts/test_synthetic_demo_lib.py`

- [ ] **Step 1: Write the failing snapshot-generation test**

Append this test to `backend/tests/unit/scripts/test_synthetic_demo_lib.py`.

```python
from scripts.synthetic_demo_lib import generate_synthetic_snapshot


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

    assert snapshot["snapshot"]["snapshot_id"] == "demo-synth-001"
    assert snapshot["snapshot"]["source_user_email"] == "synthetic:ethan-parker:v1"
    assert snapshot["profile"]["display_name"] == "Ethan Parker"
    assert snapshot["profile"]["is_demo"] is True
    assert snapshot["trainer_profiles"][0]["trainer_type"] == "atlas"
    assert len(snapshot["demo_episodes"]) == 12
    assert len(snapshot["demo_messages"]) >= 90
    assert len(snapshot["message_store_docs"]) == len(snapshot["demo_messages"])
    assert snapshot["workout_logs"][0]["source"] == "hevy"
    assert snapshot["nutrition_logs"][0]["source"] == "myfitnesspal"
    assert snapshot["weight_logs"][0]["source"] == "scale_import"
    assert snapshot["memories"][0]["user_id"] == "demo@fityq.it"
    assert snapshot["prompt_logs"][0]["user_email"] == "demo@fityq.it"
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
cd /home/colutti/projects/personal/backend && .venv/bin/pytest tests/unit/scripts/test_synthetic_demo_lib.py::test_generate_synthetic_snapshot_builds_publishable_demo_dataset -v
```

Expected: FAIL with `ImportError` or `AttributeError` for `generate_synthetic_snapshot`.

- [ ] **Step 3: Implement deterministic snapshot generation**

Extend `backend/scripts/synthetic_demo_lib.py` with focused builders. Reuse `build_message_store_docs` from `scripts.demo_snapshot_lib` instead of duplicating the message-store serializer.

```python
from copy import deepcopy
from datetime import UTC, date, datetime, timedelta
from hashlib import sha1

from scripts.demo_snapshot_lib import build_message_store_docs


def generate_synthetic_snapshot(
    *,
    scenario: dict[str, Any],
    demo_email: str,
    locale: str,
    snapshot_id: str,
) -> dict[str, Any]:
    profile = build_synthetic_profile(
        scenario["persona"],
        scenario["integration_state"],
        demo_email,
    )
    trainer_profile = build_synthetic_trainer_profile(
        scenario["trainer_profile"],
        demo_email,
        locale,
    )
    demo_episodes, demo_messages = build_synthetic_demo_chat(
        episodes=scenario["episodes"],
        demo_email=demo_email,
        snapshot_id=snapshot_id,
    )
    workout_logs = build_synthetic_workout_logs(
        scenario["data_windows"],
        demo_email,
    )
    nutrition_logs = build_synthetic_nutrition_logs(
        scenario["data_windows"],
        demo_email,
    )
    weight_logs = build_synthetic_weight_logs(
        scenario["data_windows"],
        demo_email,
    )
    memories = build_synthetic_memories(
        scenario["memory_seeds"],
        demo_email,
    )
    prompt_logs = build_synthetic_prompt_logs(
        scenario["episodes"],
        demo_email,
    )
    return {
        "snapshot": {
            "snapshot_id": snapshot_id,
            "source_user_email": scenario["source_user_email"],
            "demo_email": demo_email,
            "scenario_id": scenario["scenario_id"],
            "content_version": scenario["content_version"],
            "locale": locale,
            "episode_count": len(demo_episodes),
            "message_count": len(demo_messages),
            "selection_strategy": "synthetic_showcase_v1",
            "created_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        },
        "profile": profile,
        "trainer_profiles": [trainer_profile],
        "workout_logs": workout_logs,
        "nutrition_logs": nutrition_logs,
        "weight_logs": weight_logs,
        "prompt_logs": prompt_logs,
        "memories": memories,
        "demo_episodes": demo_episodes,
        "demo_messages": demo_messages,
        "message_store_docs": build_message_store_docs(demo_messages, demo_email),
    }
```

Add the focused builders in the same file. Use authored chat timestamps from the scenario and generate structured logs around the same coaching block.

```python
def build_synthetic_profile(
    persona: dict[str, Any],
    integration_state: dict[str, Any],
    demo_email: str,
) -> dict[str, Any]:
    return {
        "email": demo_email,
        "role": "user",
        "is_demo": True,
        "display_name": persona["display_name"],
        "gender": persona["gender"],
        "age": persona["age"],
        "height": persona["height"],
        "weight": persona["weight"],
        "goal_type": persona["goal_type"],
        "weekly_rate": persona["weekly_rate"],
        "target_weight": persona["target_weight"],
        "subscription_plan": persona["subscription_plan"],
        "onboarding_completed": True,
        "photo_base64": None,
        "notes": persona["notes"],
        "hevy_enabled": integration_state["hevy_enabled"],
        "hevy_last_sync": "2026-02-25T07:15:00Z",
        "hevy_api_key": None,
        "messages_sent_today": 0,
        "messages_sent_this_month": 0,
        "total_messages_sent": 0,
    }


def build_synthetic_demo_chat(
    *,
    episodes: list[dict[str, Any]],
    demo_email: str,
    snapshot_id: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    demo_episodes: list[dict[str, Any]] = []
    demo_messages: list[dict[str, Any]] = []
    for episode in episodes:
        published_ids: list[str] = []
        for index, message in enumerate(episode["messages"]):
            message_id = sha1(
                f"{episode['episode_id']}:{index}:{message['content']}".encode("utf-8")
            ).hexdigest()[:16]
            demo_messages.append(
                {
                    "snapshot_id": snapshot_id,
                    "demo_email": demo_email,
                    "episode_id": episode["episode_id"],
                    "message_id": message_id,
                    "source_message_id": message_id,
                    "role": message["role"],
                    "trainer_type": message["trainer_type"],
                    "timestamp": message["timestamp"],
                    "content": message["content"],
                    "status": "published",
                }
            )
            published_ids.append(message_id)
        demo_episodes.append(
            {
                "snapshot_id": snapshot_id,
                "demo_email": demo_email,
                "episode_id": episode["episode_id"],
                "title": episode["title"],
                "started_at": episode["started_at"],
                "ended_at": episode["messages"][-1]["timestamp"],
                "primary_domain": episode["primary_domain"],
                "trainers": sorted(
                    {message["trainer_type"] for message in episode["messages"]}
                ),
                "source_message_ids": published_ids,
                "published_message_ids": published_ids,
                "score": 100.0,
                "status": "published",
            }
        )
    return demo_episodes, demo_messages
```

Implement the remaining builders with deterministic counts:

- `build_synthetic_trainer_profile(...)`
- `build_synthetic_workout_logs(...)`
- `build_synthetic_nutrition_logs(...)`
- `build_synthetic_weight_logs(...)`
- `build_synthetic_memories(...)`
- `build_synthetic_prompt_logs(...)`

The generated records must satisfy these exact rules:

- workout logs: 28 to 34 logs, `source="hevy"`, split across 8 weeks
- nutrition logs: 35 to 45 logs, `source="myfitnesspal"`
- weight logs: 56 to 72 entries, `source="scale_import"` with mild downward trend noise
- memories: 3 to 5 items using the scenario seed text plus `created_at` / `updated_at`
- prompt logs: at least one per episode

- [ ] **Step 4: Run the test to verify it passes**

Run:

```bash
cd /home/colutti/projects/personal/backend && .venv/bin/pytest tests/unit/scripts/test_synthetic_demo_lib.py::test_generate_synthetic_snapshot_builds_publishable_demo_dataset -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd /home/colutti/projects/personal
git add backend/scripts/synthetic_demo_lib.py backend/tests/unit/scripts/test_synthetic_demo_lib.py
git commit -m "feat: generate synthetic demo snapshots"
```

## Task 3: Add the Synthetic Generator CLI and Publish Demo Memories

**Files:**
- Modify: `backend/scripts/build_demo_snapshot.py`
- Test: `backend/tests/unit/scripts/test_synthetic_demo_lib.py`

- [ ] **Step 1: Write the failing CLI and publish tests**

Append these tests to `backend/tests/unit/scripts/test_synthetic_demo_lib.py`.

```python
from argparse import Namespace
from pathlib import Path

from scripts.build_demo_snapshot import build_parser, publish_snapshot


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
    assert args.locale == "en"


def test_publish_snapshot_replaces_demo_memories(monkeypatch, tmp_path):
    calls: list[tuple[str, str]] = []

    def fake_replace_demo_memories(memories, demo_email):
        calls.append((demo_email, memories[0]["memory"]))

    monkeypatch.setattr(
        "scripts.build_demo_snapshot.replace_demo_memories",
        fake_replace_demo_memories,
    )
    monkeypatch.setattr(
        "scripts.build_demo_snapshot.confirm_execution",
        lambda *args, **kwargs: None,
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
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:

```bash
cd /home/colutti/projects/personal/backend && .venv/bin/pytest tests/unit/scripts/test_synthetic_demo_lib.py -k "generate_synthetic_command or replaces_demo_memories" -v
```

Expected: FAIL because `generate-synthetic` does not exist and `replace_demo_memories` is missing.

- [ ] **Step 3: Implement the new command and memory replacement**

Modify `backend/scripts/build_demo_snapshot.py` to import the synthetic helpers and add a new subcommand.

```python
from scripts.synthetic_demo_lib import (
    generate_synthetic_snapshot,
    load_synthetic_scenario,
    replace_demo_memories,
)


def generate_synthetic_snapshot_artifact(args: argparse.Namespace) -> None:
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    scenario = load_synthetic_scenario(Path(args.scenario_file))
    snapshot_id = f"demo-synth-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"
    synthetic = generate_synthetic_snapshot(
        scenario=scenario,
        demo_email=args.demo_email,
        locale=args.locale,
        snapshot_id=snapshot_id,
    )
    (out_dir / "curated_snapshot.json").write_text(
        json_util.dumps(synthetic, indent=2),
        encoding="utf-8",
    )
    (out_dir / "chat_review.json").write_text(
        json.dumps(
            {
                "snapshot": synthetic["snapshot"],
                "episodes": synthetic["demo_episodes"],
                "message_count": len(synthetic["demo_messages"]),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
```

Register the parser:

```python
    synthetic_parser = subparsers.add_parser("generate-synthetic")
    synthetic_parser.add_argument(
        "--scenario-file",
        default="scripts/demo_scenarios/ethan_parker_v1.json",
    )
    synthetic_parser.add_argument(
        "--output-dir",
        default="artifacts/demo/synthetic/ethan-parker-v1-en",
    )
    synthetic_parser.add_argument("--demo-email", default="demo@fityq.it")
    synthetic_parser.add_argument("--locale", default="en")
    synthetic_parser.set_defaults(func=generate_synthetic_snapshot_artifact)
```

Extend `publish_snapshot` to replace Qdrant memories after the Mongo writes:

```python
    memories = curated.get("memories", [])
    if memories:
        replace_demo_memories(memories, demo_email)
```

Implement `replace_demo_memories` in `backend/scripts/synthetic_demo_lib.py` using the existing Qdrant stack:

```python
from qdrant_client import models as qdrant_models

from src.core.config import settings
from src.core.deps import get_qdrant_client
from src.services.memory_service import add_memory as add_memory_record


def replace_demo_memories(memories: list[dict[str, Any]], demo_email: str) -> None:
    qdrant_client = get_qdrant_client()
    user_filter = qdrant_models.Filter(
        must=[
            qdrant_models.FieldCondition(
                key="user_id",
                match=qdrant_models.MatchValue(value=demo_email),
            )
        ]
    )
    qdrant_client.delete(
        collection_name=settings.QDRANT_COLLECTION_NAME,
        points_selector=qdrant_models.FilterSelector(filter=user_filter),
    )
    for memory in memories:
        add_memory_record(
            user_id=demo_email,
            text=memory["memory"],
            qdrant_client=qdrant_client,
            collection_name=settings.QDRANT_COLLECTION_NAME,
            category=memory.get("category", "context"),
        )
```

- [ ] **Step 4: Run the tests to verify they pass**

Run:

```bash
cd /home/colutti/projects/personal/backend && .venv/bin/pytest tests/unit/scripts/test_synthetic_demo_lib.py -k "generate_synthetic_command or replaces_demo_memories" -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd /home/colutti/projects/personal
git add backend/scripts/build_demo_snapshot.py backend/scripts/synthetic_demo_lib.py backend/tests/unit/scripts/test_synthetic_demo_lib.py
git commit -m "feat: add synthetic demo CLI and memory publish"
```

## Task 4: Lock in Regression Coverage and Validation Gates

**Files:**
- Modify: `backend/tests/unit/scripts/test_demo_snapshot_lib.py`
- Modify: `backend/tests/unit/scripts/test_synthetic_demo_lib.py`

- [ ] **Step 1: Write the missing regression tests**

Add one shared regression test to confirm the synthetic snapshot still respects the admin-pruning contract by emitting stable `demo_message_id` / `demo_episode_id` fields in `message_store_docs`.

```python
def test_generate_synthetic_snapshot_keeps_admin_pruning_metadata():
    scenario = load_synthetic_scenario(
        Path("backend/scripts/demo_scenarios/ethan_parker_v1.json")
    )

    snapshot = generate_synthetic_snapshot(
        scenario=scenario,
        demo_email="demo@fityq.it",
        locale="en",
        snapshot_id="demo-synth-002",
    )

    first_doc = snapshot["message_store_docs"][0]
    assert first_doc["SessionId"] == "demo@fityq.it"
    assert first_doc["demo_message_id"]
    assert first_doc["demo_episode_id"]
```

- [ ] **Step 2: Run the tests to verify current behavior**

Run:

```bash
cd /home/colutti/projects/personal/backend && .venv/bin/pytest tests/unit/scripts/test_demo_snapshot_lib.py tests/unit/scripts/test_synthetic_demo_lib.py -v
```

Expected: FAIL only if the synthetic path is not preserving the metadata or scenario counts correctly.

- [ ] **Step 3: Fix the generator or shared helper until the suite passes**

If metadata is missing, adapt `build_synthetic_demo_chat` so every synthetic message includes:

```python
{
    "message_id": message_id,
    "episode_id": episode["episode_id"],
    "source_message_id": message_id,
    "status": "published",
}
```

If `message_store_docs` drops those ids, keep using `build_message_store_docs` from `scripts.demo_snapshot_lib` rather than creating a second serializer.

- [ ] **Step 4: Run the backend validation gate**

Run:

```bash
cd /home/colutti/projects/personal/backend && .venv/bin/ruff check src tests scripts/build_demo_snapshot.py scripts/demo_snapshot_lib.py scripts/synthetic_demo_lib.py
cd /home/colutti/projects/personal/backend && .venv/bin/pylint src
cd /home/colutti/projects/personal/backend && .venv/bin/pytest tests/unit/scripts/test_demo_snapshot_lib.py tests/unit/scripts/test_synthetic_demo_lib.py -v
```

Expected:

- Ruff: PASS
- Pylint: PASS for `src`
- Pytest: PASS for both script suites

- [ ] **Step 5: Commit**

```bash
cd /home/colutti/projects/personal
git add backend/tests/unit/scripts/test_demo_snapshot_lib.py backend/tests/unit/scripts/test_synthetic_demo_lib.py backend/scripts/synthetic_demo_lib.py
git commit -m "test: cover synthetic demo publish artifacts"
```

## Task 5: Generate, Publish, and Smoke-Test the Local Synthetic Demo

**Files:**
- Modify if needed: `backend/scripts/demo_scenarios/ethan_parker_v1.json`
- Modify if needed: `backend/scripts/synthetic_demo_lib.py`

- [ ] **Step 1: Generate the synthetic artifact**

Run:

```bash
cd /home/colutti/projects/personal/backend && .venv/bin/python scripts/build_demo_snapshot.py generate-synthetic --scenario-file scripts/demo_scenarios/ethan_parker_v1.json --output-dir artifacts/demo/synthetic/ethan-parker-v1-en --demo-email demo@fityq.it --locale en
```

Expected: PASS and create:

- `backend/artifacts/demo/synthetic/ethan-parker-v1-en/curated_snapshot.json`
- `backend/artifacts/demo/synthetic/ethan-parker-v1-en/chat_review.json`

- [ ] **Step 2: Publish the synthetic demo locally**

Run:

```bash
cd /home/colutti/projects/personal/backend && printf 'OK\n' | .venv/bin/python scripts/build_demo_snapshot.py publish --curated-file artifacts/demo/synthetic/ethan-parker-v1-en/curated_snapshot.json
```

Expected: PASS and print counts for workouts, nutrition logs, weight logs, episodes, and messages.

- [ ] **Step 3: Ensure the Firebase dev user exists**

Run:

```bash
cd /home/colutti/projects/personal/backend && .venv/bin/python - <<'PY'
import json
from pathlib import Path
import firebase_admin
from firebase_admin import auth, credentials

service_account = json.loads(Path("firebase-admin-dev.json").read_text())
if not firebase_admin._apps:
    firebase_admin.initialize_app(credentials.Certificate(service_account))

email = "demo@fityq.it"
password = "FityqDemo!2026"

try:
    user = auth.get_user_by_email(email)
    auth.update_user(
        user.uid,
        password=password,
        display_name="Ethan Parker",
        email_verified=True,
        disabled=False,
    )
    print("UPDATED", user.uid)
except auth.UserNotFoundError:
    user = auth.create_user(
        email=email,
        password=password,
        display_name="Ethan Parker",
        email_verified=True,
    )
    print("CREATED", user.uid)
PY
```

Expected: `UPDATED <uid>` or `CREATED <uid>`

- [ ] **Step 4: Run the smoke test against the live local stack**

Run:

```bash
cd /home/colutti/projects/personal && python - <<'PY'
from pathlib import Path
import requests

api_key = None
for line in Path("frontend/.env").read_text().splitlines():
    if line.startswith("VITE_FIREBASE_API_KEY="):
        api_key = line.split("=", 1)[1].strip().strip('"')
        break

firebase_resp = requests.post(
    f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}",
    json={
        "email": "demo@fityq.it",
        "password": "FityqDemo!2026",
        "returnSecureToken": True,
    },
    timeout=20,
)
firebase_resp.raise_for_status()
id_token = firebase_resp.json()["idToken"]

login_resp = requests.post(
    "http://localhost:8000/user/login",
    json={"token": id_token},
    timeout=20,
)
login_resp.raise_for_status()
platform_token = login_resp.json()["token"]
headers = {"Authorization": f"Bearer {platform_token}"}

me_resp = requests.get("http://localhost:8000/user/me", headers=headers, timeout=20)
me_resp.raise_for_status()
history_resp = requests.get(
    "http://localhost:8000/message/history?limit=5&offset=0",
    headers=headers,
    timeout=20,
)
history_resp.raise_for_status()
write_resp = requests.post(
    "http://localhost:8000/message",
    headers=headers,
    json={"user_message": "This should be blocked"},
    timeout=20,
)

me_data = me_resp.json()
print(
    {
        "email": me_data["email"],
        "display_name": me_data.get("display_name"),
        "is_demo": me_data["is_demo"],
        "history_count": len(history_resp.json()),
        "write_status": write_resp.status_code,
        "write_body": write_resp.text,
    }
)
PY
```

Expected:

- `display_name` is `Ethan Parker`
- `is_demo` is `True`
- `history_count` is greater than `0`
- `write_status` is `403`
- `write_body` contains `demo_read_only`

- [ ] **Step 5: Commit the final scenario refinements**

```bash
cd /home/colutti/projects/personal
git add backend/scripts/demo_scenarios/ethan_parker_v1.json backend/scripts/synthetic_demo_lib.py backend/scripts/build_demo_snapshot.py backend/tests/unit/scripts/test_synthetic_demo_lib.py
git commit -m "feat: publish synthetic local demo showcase"
```
