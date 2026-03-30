"""Synthetic demo scenario loader and deterministic snapshot generator."""

from __future__ import annotations

import json
from collections.abc import Iterable
from datetime import UTC, date, datetime, time, timedelta
from hashlib import sha1
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from scripts.demo_snapshot_lib import build_message_store_docs


class SyntheticDemoMessage(BaseModel):
    """Single authored chat message in a synthetic scenario."""

    model_config = ConfigDict(extra="forbid")

    role: str = Field(..., pattern="^(human|ai)$")
    trainer_type: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    timestamp: str = Field(..., min_length=1)
    translations: dict[str, str] | None = None


class SyntheticDemoEpisode(BaseModel):
    """Single authored episode in a synthetic scenario."""

    model_config = ConfigDict(extra="forbid")

    episode_id: str = Field(..., min_length=1)
    primary_domain: str = Field(..., min_length=1)
    started_at: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    messages: list[SyntheticDemoMessage] = Field(..., min_length=1)

    @model_validator(mode="after")
    def validate_timestamps(self) -> "SyntheticDemoEpisode":
        """Ensure authored message timestamps are valid and ordered."""
        started_at = _parse_iso_datetime(self.started_at)
        previous_timestamp: datetime | None = None
        for message in self.messages:
            current_timestamp = _parse_iso_datetime(message.timestamp)
            if current_timestamp < started_at:
                raise ValueError("message timestamp cannot be earlier than episode start")
            if previous_timestamp is not None and current_timestamp < previous_timestamp:
                raise ValueError("message timestamps must be ordered within an episode")
            previous_timestamp = current_timestamp
        return self


class SyntheticDemoPersona(BaseModel):
    """Persona metadata for a synthetic scenario."""

    model_config = ConfigDict(extra="forbid")

    display_name: str = Field(..., min_length=1)
    age: int = Field(..., ge=18, le=100)
    gender: str = Field(..., min_length=1)
    height: int = Field(..., ge=100, le=250)
    weight: float = Field(..., gt=0)
    goal_type: str = Field(..., pattern="^(lose|gain|maintain)$")
    weekly_rate: float = Field(..., ge=0)
    target_weight: float = Field(..., gt=0)
    subscription_plan: str = Field(..., min_length=1)
    occupation: str = Field(..., min_length=1)
    notes: str = Field(..., min_length=1)


class SyntheticDemoTrainerProfile(BaseModel):
    """Trainer profile metadata for a synthetic scenario."""

    model_config = ConfigDict(extra="forbid")

    trainer_type: str = Field(..., min_length=1)
    preferred_language: str = Field(..., min_length=1)
    personality_level: str = Field(..., min_length=1)


class SyntheticDemoIntegrationState(BaseModel):
    """Integration toggles for a synthetic scenario."""

    model_config = ConfigDict(extra="forbid")

    hevy_enabled: bool
    hevy_connected: bool
    telegram_enabled: bool


class SyntheticDemoMemorySeed(BaseModel):
    """Memory seed used to prime the scenario."""

    model_config = ConfigDict(extra="forbid")

    memory: str = Field(..., min_length=1)
    category: str = Field(..., min_length=1)
    translations: dict[str, str] | None = None


class SyntheticDemoDataWindows(BaseModel):
    """Time windows for authored demo data."""

    model_config = ConfigDict(extra="forbid")

    weight_days: int = Field(..., ge=1)
    nutrition_days: int = Field(..., ge=1)
    workout_weeks: int = Field(..., ge=1)


class SyntheticDemoScenario(BaseModel):
    """Validated synthetic demo scenario."""

    model_config = ConfigDict(extra="forbid")

    scenario_id: str = Field(..., min_length=1)
    content_version: str = Field(..., min_length=1)
    locale: str = Field(..., min_length=1)
    source_user_email: str = Field(..., min_length=1)
    persona: SyntheticDemoPersona
    trainer_profile: SyntheticDemoTrainerProfile
    integration_state: SyntheticDemoIntegrationState
    memory_seeds: list[SyntheticDemoMemorySeed] = Field(..., min_length=1)
    data_windows: SyntheticDemoDataWindows
    episodes: list[SyntheticDemoEpisode] = Field(..., min_length=1)

    @model_validator(mode="after")
    def validate_episode_order(self) -> "SyntheticDemoScenario":
        """Ensure episodes are authored in non-decreasing chronological order."""
        previous_start: datetime | None = None
        for episode in self.episodes:
            current_start = _parse_iso_datetime(episode.started_at)
            if previous_start is not None and current_start < previous_start:
                raise ValueError("episode start timestamps must be non-decreasing")
            previous_start = current_start
        return self


_PT_REPLACEMENTS: list[tuple[str, str]] = [
    ("Let's go.", "Bora."),
    ("Let's go", "Bora"),
    ("No need to overreact", "Sem drama"),
    ("That's exactly what we want", "É exatamente isso que queremos"),
    ("This is not some random calculator number, man.", "Isso não é número jogado ao acaso, mano."),
    ("This is not a guess.", "Isso não é chute."),
    ("The app is reading", "O app está lendo"),
    ("The system is reading", "O sistema está lendo"),
    ("the app smooths out the daily noise", "o app suaviza o ruído do dia a dia"),
    ("One random spike does not mean the plan is broken", "Um pico isolado não quer dizer que o plano quebrou"),
    ("the trend is what tells us if you're actually moving", "a tendência é o que mostra se você está realmente evoluindo"),
    ("keep fat loss moving", "manter a perda de gordura andando"),
    ("without tanking your training or your work week", "sem destruir teu treino ou tua semana de trabalho"),
    ("You're in a good spot", "Você está em uma boa posição"),
    ("keep your average intake close to target", "manter sua ingestão média perto da meta"),
    ("bouncing all over the place", "oscilando pra todo lado"),
    ("the app can already see", "o app já consegue ver"),
    ("That is not a crisis, bro.", "Isso não é crise, bro."),
    ("we're not guessing here", "aqui a gente não está chutando"),
    ("I saved", "eu salvei"),
    ("I created", "eu criei"),
    ("I set", "eu defini"),
    ("I used", "eu usei"),
    ("I pulled", "eu puxei"),
    ("I can coach from the work you actually did", "consigo te coachar com base no trabalho que você realmente fez"),
    ("keep the 4-day structure", "manter a estrutura de 4 dias"),
    ("keep logging the day cleanly", "continuar registrando o dia direitinho"),
    ("keep protein near 180", "manter a proteína perto de 180"),
    ("keep pulling volume a touch higher", "manter um pouco mais de volume de puxada"),
    ("stay calm when a single weigh-in looks weird", "ficar tranquilo quando um único peso parecer estranho"),
    ("what should I keep exactly the same next week, and what should I adjust?", "o que eu devo manter exatamente igual na próxima semana e o que eu ajusto?"),
]


def _translate_to_pt(text: str) -> str:
    translated = text
    for source, target in _PT_REPLACEMENTS:
        translated = translated.replace(source, target)
    return translated


def _candidate_paths(path: Path) -> Iterable[Path]:
    module_dir = Path(__file__).resolve().parent
    repo_root = module_dir.parent.parent

    yield path
    if path.is_absolute():
        return

    yield Path.cwd() / path
    yield module_dir / path
    yield repo_root / path


def _resolve_scenario_path(path: Path) -> Path:
    for candidate in _candidate_paths(path):
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(path)


def load_synthetic_scenario(path: Path) -> dict[str, Any]:
    """Load and validate an authored synthetic demo scenario from disk."""
    scenario_path = _resolve_scenario_path(path)
    payload = json.loads(scenario_path.read_text(encoding="utf-8"))
    return SyntheticDemoScenario.model_validate(payload).model_dump()


def _parse_iso_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def _to_iso_z(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _stable_fraction(seed: str) -> float:
    digest = sha1(seed.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) / 0xFFFFFFFF


def _stable_signed(seed: str, scale: float) -> float:
    return (_stable_fraction(seed) * 2.0 - 1.0) * scale


def _resolve_recent_anchor_day(scenario: dict[str, Any]) -> date:
    """Anchor generated telemetry close to the present for meaningful dashboard metrics."""
    last_episode_day = _parse_iso_datetime(scenario["episodes"][-1]["started_at"]).date()
    return max(last_episode_day, datetime.now(UTC).date() - timedelta(days=1))


def _ordered_unique(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return ordered


def _build_profile(
    *, scenario: dict[str, Any], demo_email: str, locale: str
) -> dict[str, Any]:
    persona = scenario["persona"]
    integration_state = scenario["integration_state"]
    hevy_active = integration_state["hevy_enabled"] and integration_state["hevy_connected"]
    hevy_last_sync = None
    if hevy_active:
        hevy_last_sync = _to_iso_z(
            max(_parse_iso_datetime(message["timestamp"]) for episode in scenario["episodes"] for message in episode["messages"])
        )
    return {
        "email": demo_email,
        "display_name": persona["display_name"],
        "age": persona["age"],
        "gender": persona["gender"],
        "height": persona["height"],
        "weight": persona["weight"],
        "goal_type": persona["goal_type"],
        "target_weight": persona["target_weight"],
        "weekly_rate": persona["weekly_rate"],
        "notes": persona["notes"],
        "role": "user",
        "is_demo": True,
        "subscription_plan": persona["subscription_plan"],
        "occupation": persona["occupation"],
        "onboarding_completed": True,
        "hevy_enabled": integration_state["hevy_enabled"],
        "hevy_last_sync": hevy_last_sync,
        "hevy_api_key": None,
        "hevy_webhook_token": None,
        "hevy_webhook_secret": None,
        "timezone": "UTC",
        "photo_base64": None,
        "preferred_locale": locale,
        "messages_sent_today": 0,
        "messages_sent_this_month": 0,
        "total_messages_sent": 0,
    }


def _build_trainer_profiles(*, scenario: dict[str, Any], demo_email: str) -> list[dict[str, Any]]:
    trainer_profile = dict(scenario["trainer_profile"])
    trainer_profile["user_email"] = demo_email
    return [trainer_profile]


def _build_demo_chat(
    *, scenario: dict[str, Any], demo_email: str, snapshot_id: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    demo_episodes: list[dict[str, Any]] = []
    demo_messages: list[dict[str, Any]] = []

    for episode_index, episode in enumerate(scenario["episodes"], start=1):
        source_message_ids: list[str] = []
        published_message_ids: list[str] = []
        timestamps: list[str] = []

        for message in episode["messages"]:
            timestamp = message["timestamp"]
            message_key = (
                f"{scenario['scenario_id']}:{scenario['content_version']}:"
                f"{episode['episode_id']}:{timestamp}:{message['role']}:"
                f"{message['trainer_type']}:{message['content']}"
            )
            stable_digest = sha1(message_key.encode("utf-8")).hexdigest()[:16]
            source_message_id = f"src-{stable_digest}"
            message_id = f"msg-{stable_digest}"
            source_message_ids.append(source_message_id)
            published_message_ids.append(message_id)
            timestamps.append(timestamp)

            demo_messages.append(
                {
                    "snapshot_id": snapshot_id,
                    "demo_email": demo_email,
                    "episode_id": episode["episode_id"],
                    "message_id": message_id,
                    "role": message["role"],
                    "trainer_type": message["trainer_type"],
                    "timestamp": timestamp,
                    "content": message["content"].strip(),
                    "translations": message.get("translations")
                    or {"pt-BR": _translate_to_pt(message["content"].strip())},
                    "source_message_id": source_message_id,
                    "status": "published",
                }
            )

        demo_episodes.append(
            {
                "snapshot_id": snapshot_id,
                "demo_email": demo_email,
                "episode_id": episode["episode_id"],
                "title": episode["title"],
                "started_at": timestamps[0],
                "ended_at": timestamps[-1],
                "primary_domain": episode["primary_domain"],
                "trainers": _ordered_unique(
                    message["trainer_type"] for message in episode["messages"]
                ),
                "source_message_ids": source_message_ids,
                "published_message_ids": published_message_ids,
                "score": round(10.0 + episode_index * 0.25, 2),
                "status": "published",
                "message_count": len(published_message_ids),
            }
        )

    return demo_episodes, demo_messages


def _workout_exercises(workout_index: int) -> list[dict[str, Any]]:
    templates = [
        [
            ("Bench Press", [8, 8, 7], [72.5, 72.5, 75.0]),
            ("Chest Supported Row", [10, 10, 10], [52.5, 52.5, 55.0]),
            ("Incline Dumbbell Press", [10, 9, 9], [28.0, 28.0, 28.0]),
        ],
        [
            ("Back Squat", [6, 6, 6], [105.0, 107.5, 107.5]),
            ("Romanian Deadlift", [8, 8, 8], [92.5, 92.5, 95.0]),
            ("Leg Curl", [12, 12, 12], [42.5, 42.5, 45.0]),
        ],
        [
            ("Overhead Press", [8, 8, 7], [47.5, 47.5, 50.0]),
            ("Lat Pulldown", [10, 10, 10], [57.5, 60.0, 60.0]),
            ("Cable Row", [12, 12, 12], [47.5, 47.5, 50.0]),
        ],
        [
            ("Trap Bar Deadlift", [5, 5, 5], [125.0, 127.5, 127.5]),
            ("Bulgarian Split Squat", [10, 10, 10], [22.0, 22.0, 24.0]),
            ("Walking Lunge", [12, 12, 12], [18.0, 18.0, 20.0]),
        ],
    ]
    exercise_template = templates[workout_index % len(templates)]
    exercises: list[dict[str, Any]] = []
    for exercise_index, (name, reps, weights) in enumerate(exercise_template):
        load_bump = round(_stable_fraction(f"workout:{workout_index}:{exercise_index}") * 2.0, 1)
        exercises.append(
            {
                "name": name,
                "sets": len(reps),
                "reps_per_set": reps,
                "weights_per_set": [round(weight + load_bump, 1) for weight in weights],
                "distance_meters_per_set": [],
                "duration_seconds_per_set": [],
            }
        )
    return exercises


def _build_workout_logs(*, scenario: dict[str, Any], demo_email: str) -> list[dict[str, Any]]:
    weeks = max(scenario["data_windows"]["workout_weeks"], 8)
    count = min(max(weeks * 3 + 2, 28), 34)
    first_episode_day = _parse_iso_datetime(scenario["episodes"][0]["started_at"]).date()
    last_episode_day = _parse_iso_datetime(scenario["episodes"][-1]["started_at"]).date()
    start_day = first_episode_day - timedelta(days=4)
    target_end_day = max(last_episode_day - timedelta(days=2), start_day)
    span_days = max((target_end_day - start_day).days, 1)
    workout_types = ["Upper A", "Lower A", "Upper B", "Lower B"]
    hevy_connected = (
        scenario["integration_state"]["hevy_enabled"]
        and scenario["integration_state"]["hevy_connected"]
    )
    source = "hevy" if hevy_connected else "manual"

    workout_logs: list[dict[str, Any]] = []
    for index in range(count):
        offset_days = round((span_days * index) / max(count - 1, 1))
        workout_date = datetime.combine(
            start_day + timedelta(days=offset_days),
            time(hour=6 + (index % 3), minute=(index * 7) % 60),
            tzinfo=UTC,
        )
        workout_logs.append(
            {
                "user_email": demo_email,
                "date": workout_date,
                "workout_type": workout_types[index % len(workout_types)],
                "exercises": _workout_exercises(index),
                "duration_minutes": 52 + (index % 4) * 6,
                "source": source,
                "external_id": (
                    f"hevy-{scenario['scenario_id']}-{index + 1:03d}" if hevy_connected else None
                ),
            }
        )

    return workout_logs


def _build_nutrition_logs(*, scenario: dict[str, Any], demo_email: str) -> list[dict[str, Any]]:
    count = min(max(scenario["data_windows"]["nutrition_days"], 35), 45)
    last_episode_day = _resolve_recent_anchor_day(scenario)
    start_day = last_episode_day - timedelta(days=count - 1)
    target_weight = scenario["persona"]["target_weight"]

    nutrition_logs: list[dict[str, Any]] = []
    for index in range(count):
        log_day = start_day + timedelta(days=index)
        calories = 2280 + int(_stable_signed(f"nutrition:calories:{index}", 140))
        protein = round(target_weight * 2.1 + _stable_signed(f"nutrition:protein:{index}", 8), 1)
        carbs = round(220 + _stable_signed(f"nutrition:carbs:{index}", 28), 1)
        fats = round(68 + _stable_signed(f"nutrition:fats:{index}", 9), 1)
        nutrition_logs.append(
            {
                "user_email": demo_email,
                "date": datetime.combine(log_day, time(hour=20, minute=15), tzinfo=UTC),
                "calories": calories,
                "protein_grams": protein,
                "carbs_grams": carbs,
                "fat_grams": fats,
                "fiber_grams": round(28 + _stable_signed(f"nutrition:fiber:{index}", 4), 1),
                "sugar_grams": round(48 + _stable_signed(f"nutrition:sugar:{index}", 9), 1),
                "sodium_mg": round(2300 + _stable_signed(f"nutrition:sodium:{index}", 260), 1),
                "cholesterol_mg": round(
                    280 + _stable_signed(f"nutrition:cholesterol:{index}", 35), 1
                ),
                "source": "myfitnesspal",
                "notes": "Synthetic imported nutrition summary for demo showcase.",
                "partial_logged": False,
            }
        )

    return nutrition_logs


def _build_weight_logs(*, scenario: dict[str, Any], demo_email: str) -> list[dict[str, Any]]:
    count = min(max(scenario["data_windows"]["weight_days"], 56), 72)
    last_episode_day = _resolve_recent_anchor_day(scenario)
    start_day = last_episode_day - timedelta(days=count - 1)
    start_weight = float(scenario["persona"]["weight"])
    target_weight = float(scenario["persona"]["target_weight"])
    intended_drop = min(start_weight - target_weight, 2.4)
    slope = intended_drop / max(count - 1, 1)

    weight_logs: list[dict[str, Any]] = []
    trend_weight = start_weight
    for index in range(count):
        day = start_day + timedelta(days=index)
        noisy_weight = round(
            start_weight - slope * index + _stable_signed(f"weight:{index}", 0.28),
            2,
        )
        trend_weight = round((trend_weight * 0.82) + (noisy_weight * 0.18), 2)
        weight_logs.append(
            {
                "user_email": demo_email,
                "date": day,
                "weight_kg": noisy_weight,
                "trend_weight": trend_weight,
                "body_fat_pct": round(21.5 - (index * 0.03), 2),
                "muscle_mass_pct": round(39.8 + _stable_signed(f"muscle_pct:{index}", 0.25), 2),
                "muscle_mass_kg": round(33.6 + _stable_signed(f"muscle_kg:{index}", 0.35), 2),
                "bone_mass_kg": 3.4,
                "body_water_pct": round(56.5 + _stable_signed(f"water:{index}", 0.5), 2),
                "visceral_fat": round(10.8 - (index * 0.015), 2),
                "bmr": 1825,
                "bmi": round(noisy_weight / ((scenario["persona"]["height"] / 100) ** 2), 2),
                "waist_cm": round(92.0 - (index * 0.05), 2),
                "source": "scale_import",
                "notes": "Synthetic scale import for demo showcase.",
            }
        )

    return weight_logs


def _build_memories(*, scenario: dict[str, Any], demo_email: str) -> list[dict[str, Any]]:
    created_base = _parse_iso_datetime(scenario["episodes"][0]["started_at"]) - timedelta(days=5)
    memories: list[dict[str, Any]] = []
    for index, seed in enumerate(scenario["memory_seeds"][:5]):
        created_at = created_base + timedelta(days=index * 6)
        updated_at = created_at + timedelta(days=2)
        memory_id = sha1(
            f"{scenario['scenario_id']}:{seed['category']}:{seed['memory']}".encode("utf-8")
        ).hexdigest()[:16]
        memories.append(
            {
                "id": memory_id,
                "memory": seed["memory"],
                "translations": seed.get("translations"),
                "category": seed["category"],
                "user_id": demo_email,
                "created_at": _to_iso_z(created_at),
                "updated_at": _to_iso_z(updated_at),
            }
        )
    return memories


def _build_prompt_logs(
    *,
    scenario: dict[str, Any],
    demo_email: str,
    demo_messages: list[dict[str, Any]],
    locale: str,
) -> list[dict[str, Any]]:
    messages_by_episode: dict[str, list[dict[str, Any]]] = {}
    for message in demo_messages:
        messages_by_episode.setdefault(message["episode_id"], []).append(message)

    prompt_logs: list[dict[str, Any]] = []
    for index, episode in enumerate(scenario["episodes"], start=1):
        episode_messages = messages_by_episode[episode["episode_id"]]
        timestamp = _parse_iso_datetime(episode_messages[-1]["timestamp"]) + timedelta(minutes=1)
        prompt_logs.append(
            {
                "user_email": demo_email,
                "timestamp": timestamp,
                "prompt": {
                    "episode_id": episode["episode_id"],
                    "title": episode["title"],
                    "locale": locale,
                    "messages": episode_messages,
                },
                "tokens_input": 950 + index * 37,
                "tokens_output": 180 + index * 14,
                "duration_ms": 1200 + index * 55,
                "model": "synthetic-authored-v1",
                "status": "success",
            }
        )
    return prompt_logs


def generate_synthetic_snapshot(
    *,
    scenario: dict[str, Any],
    demo_email: str,
    locale: str,
    snapshot_id: str,
) -> dict[str, Any]:
    """Generate a publishable deterministic synthetic demo snapshot."""
    demo_episodes, demo_messages = _build_demo_chat(
        scenario=scenario,
        demo_email=demo_email,
        snapshot_id=snapshot_id,
    )

    window_start = demo_messages[0]["timestamp"] if demo_messages else None
    window_end = demo_messages[-1]["timestamp"] if demo_messages else None
    created_anchor = _parse_iso_datetime(window_end or scenario["episodes"][-1]["started_at"])
    created_offset_seconds = int(sha1(snapshot_id.encode("utf-8")).hexdigest()[:4], 16) % 600 + 60
    snapshot = {
        "snapshot_id": snapshot_id,
        "scenario_id": scenario["scenario_id"],
        "content_version": scenario["content_version"],
        "source_user_email": scenario["source_user_email"],
        "demo_email": demo_email,
        "locale": locale,
        "window_start": window_start,
        "window_end": window_end,
        "selection_strategy": "synthetic_showcase_v1",
        "episode_count": len(demo_episodes),
        "message_count": len(demo_messages),
        "created_at": _to_iso_z(created_anchor + timedelta(seconds=created_offset_seconds)),
    }

    return {
        "snapshot": snapshot,
        "profile": _build_profile(scenario=scenario, demo_email=demo_email, locale=locale),
        "trainer_profiles": _build_trainer_profiles(scenario=scenario, demo_email=demo_email),
        "workout_logs": _build_workout_logs(scenario=scenario, demo_email=demo_email),
        "nutrition_logs": _build_nutrition_logs(scenario=scenario, demo_email=demo_email),
        "weight_logs": _build_weight_logs(scenario=scenario, demo_email=demo_email),
        "memories": _build_memories(scenario=scenario, demo_email=demo_email),
        "prompt_logs": _build_prompt_logs(
            scenario=scenario,
            demo_email=demo_email,
            demo_messages=demo_messages,
            locale=locale,
        ),
        "demo_episodes": demo_episodes,
        "demo_messages": demo_messages,
        "message_store_docs": build_message_store_docs(demo_messages, demo_email),
    }


def replace_demo_memories(memories: list[dict[str, Any]], demo_email: str) -> None:
    """Replace all stored memories for the demo user in Qdrant."""
    from qdrant_client import models as qdrant_models

    from src.core.config import settings
    from src.core.deps import get_qdrant_client
    from src.services.memory_service import add_memory

    qdrant_client = get_qdrant_client()
    user_filter = qdrant_models.Filter(
        must=[
            qdrant_models.FieldCondition(
                key="user_id",
                match=qdrant_models.MatchValue(value=demo_email),
            )
        ]
    )
    existing_points = _scroll_memory_points(
        qdrant_client=qdrant_client,
        collection_name=settings.QDRANT_COLLECTION_NAME,
        user_filter=user_filter,
    )
    qdrant_client.delete(
        collection_name=settings.QDRANT_COLLECTION_NAME,
        points_selector=qdrant_models.FilterSelector(filter=user_filter),
    )

    try:
        for memory in memories:
            add_memory(
                user_id=demo_email,
                memory_data={
                    "text": memory["memory"],
                    "translations": memory.get("translations"),
                },
                qdrant_client=qdrant_client,
                collection_name=settings.QDRANT_COLLECTION_NAME,
                category=memory.get("category", "context"),
            )
    except Exception:
        qdrant_client.delete(
            collection_name=settings.QDRANT_COLLECTION_NAME,
            points_selector=qdrant_models.FilterSelector(filter=user_filter),
        )
        if existing_points:
            restored_points = [
                qdrant_models.PointStruct(
                    id=point.id,
                    vector=getattr(point, "vector", None),
                    payload=point.payload,
                )
                for point in existing_points
            ]
            qdrant_client.upsert(
                collection_name=settings.QDRANT_COLLECTION_NAME,
                points=restored_points,
            )
        raise


def _scroll_memory_points(
    *,
    qdrant_client: Any,
    collection_name: str,
    user_filter: Any,
) -> list[Any]:
    points: list[Any] = []
    offset = None
    while True:
        batch, offset = qdrant_client.scroll(
            collection_name=collection_name,
            scroll_filter=user_filter,
            with_payload=True,
            with_vectors=True,
            offset=offset,
            limit=256,
        )
        points.extend(batch)
        if offset is None:
            return points
