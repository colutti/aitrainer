"""Helpers for exporting, auto-curating, and publishing demo-user snapshots."""

from __future__ import annotations

import json
import re
from collections import Counter
from copy import deepcopy
from datetime import UTC, datetime, timedelta
from hashlib import sha1
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, message_to_dict

SENSITIVE_PROFILE_FIELDS = {
    "_id",
    "password_hash",
    "photo_base64",
    "hevy_api_key",
    "stripe_customer_id",
    "stripe_subscription_id",
    "telegram_chat_id",
}

DOMAIN_QUOTAS = {
    "workout": 5,
    "nutrition": 4,
    "weight": 3,
    "memory": 3,
    "course_correction": 2,
}

TRAINER_DOMAIN_HINTS = {
    "gymbro": "workout",
    "atlas": "nutrition",
    "luna": "memory",
    "sargento": "course_correction",
}

EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)


def _parse_iso_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed


def _to_iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _record_datetime(record: dict[str, Any], field_name: str = "date") -> datetime | None:
    return _parse_iso_datetime(record.get(field_name))


def _sanitize_text(text: str, source_email: str, demo_email: str) -> str:
    sanitized = text.replace(source_email, demo_email)
    sanitized = EMAIL_RE.sub("[redacted-email]", sanitized)
    return sanitized.strip()


def build_demo_profile(source: dict[str, Any], demo_email: str) -> dict[str, Any]:
    """Create a protected demo profile from a source user document."""
    profile = deepcopy(source)
    for field in SENSITIVE_PROFILE_FIELDS:
        profile.pop(field, None)

    profile["email"] = demo_email
    profile["is_demo"] = True
    profile["role"] = "user"
    profile["display_name"] = profile.get("display_name") or "Demo Athlete"
    profile["photo_base64"] = None
    profile["hevy_api_key"] = None
    profile["stripe_customer_id"] = None
    profile["stripe_subscription_id"] = None
    profile["stripe_subscription_status"] = None
    profile["onboarding_completed"] = True
    return profile


def remap_user_records(
    records: list[dict[str, Any]], demo_email: str, id_field: str
) -> list[dict[str, Any]]:
    """Clone records and rewrite the user/session identifier."""
    remapped: list[dict[str, Any]] = []
    for record in records:
        cloned = deepcopy(record)
        cloned.pop("_id", None)
        cloned[id_field] = demo_email
        remapped.append(cloned)
    return remapped


def _normalize_message_doc(doc: dict[str, Any]) -> dict[str, Any] | None:
    try:
        payload = json.loads(doc["History"])
    except (KeyError, TypeError, json.JSONDecodeError):
        return None

    data = payload.get("data", {})
    additional = data.get("additional_kwargs", {})
    timestamp = _parse_iso_datetime(additional.get("timestamp"))
    if timestamp is None:
        return None

    return {
        "source_id": str(doc.get("_id", "")),
        "message_type": payload.get("type", "human"),
        "timestamp": _to_iso(timestamp),
        "timestamp_dt": timestamp,
        "trainer_type": additional.get("trainer_type"),
        "content": data.get("content", ""),
    }


def segment_message_docs(
    message_docs: list[dict[str, Any]],
    gap_minutes: int = 60,
) -> list[dict[str, Any]]:
    """Group chronological chat messages into conversation episodes."""
    normalized = [item for item in (_normalize_message_doc(doc) for doc in message_docs) if item]
    normalized.sort(key=lambda item: item["timestamp_dt"])
    if not normalized:
        return []

    episodes: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    previous_dt: datetime | None = None

    for item in normalized:
        if (
            previous_dt is None
            or (item["timestamp_dt"] - previous_dt).total_seconds() <= gap_minutes * 60
        ):
            current.append(item)
        else:
            episodes.append(current)
            current = [item]
        previous_dt = item["timestamp_dt"]

    if current:
        episodes.append(current)

    return [_build_episode(messages) for messages in episodes]


def _build_episode(messages: list[dict[str, Any]]) -> dict[str, Any]:
    first = messages[0]
    last = messages[-1]
    trainers = [item.get("trainer_type") or "<none>" for item in messages]
    episode_id = sha1(
        f"{first['timestamp']}:{last['timestamp']}:{len(messages)}".encode("utf-8")
    ).hexdigest()[:12]
    human_count = sum(1 for item in messages if item["message_type"] == "human")
    ai_count = sum(1 for item in messages if item["message_type"] == "ai")
    return {
        "episode_id": episode_id,
        "started_at": first["timestamp"],
        "ended_at": last["timestamp"],
        "message_count": len(messages),
        "human_count": human_count,
        "ai_count": ai_count,
        "trainers": [name for name, _ in Counter(trainers).most_common()],
        "messages": messages,
    }


def _logs_near_episode(
    episode: dict[str, Any],
    records: list[dict[str, Any]],
    field_name: str = "date",
    tolerance_days: int = 2,
) -> int:
    start = _parse_iso_datetime(episode["started_at"])
    end = _parse_iso_datetime(episode["ended_at"])
    if start is None or end is None:
        return 0
    window_start = start - timedelta(days=tolerance_days)
    window_end = end + timedelta(days=tolerance_days)
    count = 0
    for record in records:
        record_dt = _record_datetime(record, field_name)
        if record_dt and window_start <= record_dt <= window_end:
            count += 1
    return count


def classify_episode(
    episode: dict[str, Any],
    workout_logs: list[dict[str, Any]],
    nutrition_logs: list[dict[str, Any]],
    weight_logs: list[dict[str, Any]],
) -> dict[str, Any]:
    """Attach domain and ranking metadata to an episode."""
    trainers = episode.get("trainers", [])
    trainer_hint = TRAINER_DOMAIN_HINTS.get(trainers[0]) if trainers else None
    workout_hits = _logs_near_episode(episode, workout_logs)
    nutrition_hits = _logs_near_episode(episode, nutrition_logs)
    weight_hits = _logs_near_episode(episode, weight_logs)
    course_correction_hits = sum(
        1
        for message in episode["messages"]
        if any(
            keyword in message["content"].lower()
            for keyword in ("errei", "saí da dieta", "furei", "voltar", "retomar", "ajusta")
        )
    )
    domain_scores = {
        "workout": workout_hits * 3,
        "nutrition": nutrition_hits * 3,
        "weight": weight_hits * 3,
        "course_correction": course_correction_hits * 2,
        "memory": 1 if episode["message_count"] >= 6 else 0,
    }
    if trainer_hint:
        domain_scores[trainer_hint] = domain_scores.get(trainer_hint, 0) + 2

    primary_domain = max(domain_scores, key=domain_scores.get)
    if domain_scores[primary_domain] <= 0:
        primary_domain = "mixed"

    scored = deepcopy(episode)
    scored["primary_domain"] = primary_domain
    scored["nearby_logs"] = {
        "workout": workout_hits,
        "nutrition": nutrition_hits,
        "weight": weight_hits,
    }
    scored["course_correction_hits"] = course_correction_hits
    scored["score"] = score_episode(scored)
    return scored


def score_episode(episode: dict[str, Any]) -> float:
    """Calculate a deterministic usefulness score for demo selection."""
    score = 0.0
    human_count = episode.get("human_count", 0)
    ai_count = episode.get("ai_count", 0)
    message_count = episode.get("message_count", 0)

    if human_count > 0 and ai_count > 0:
        score += 6
        score += min(human_count, ai_count) * 0.4

    if 4 <= message_count <= 12:
        score += 5
    elif message_count <= 20:
        score += 2
    else:
        score -= min(message_count - 20, 20) * 0.25

    nearby = episode.get("nearby_logs", {})
    score += nearby.get("workout", 0) * 1.5
    score += nearby.get("nutrition", 0) * 1.2
    score += nearby.get("weight", 0) * 1.2
    score += episode.get("course_correction_hits", 0) * 1.5

    domain = episode.get("primary_domain")
    if domain in {"workout", "nutrition", "weight", "memory", "course_correction"}:
        score += 2

    return round(score, 2)


def select_top_episodes(
    episodes: list[dict[str, Any]],
    limit: int = 20,
    quotas: dict[str, int] | None = None,
) -> list[dict[str, Any]]:
    """Select episodes with quota-based domain coverage."""
    quotas = quotas or DOMAIN_QUOTAS
    remaining = sorted(episodes, key=lambda item: item["score"], reverse=True)
    selected: list[dict[str, Any]] = []
    used_ids: set[str] = set()

    for domain, quota in quotas.items():
        domain_candidates = [item for item in remaining if item["primary_domain"] == domain]
        for candidate in domain_candidates[:quota]:
            if candidate["episode_id"] in used_ids or len(selected) >= limit:
                continue
            selected.append(candidate)
            used_ids.add(candidate["episode_id"])

    for candidate in remaining:
        if len(selected) >= limit:
            break
        if candidate["episode_id"] in used_ids:
            continue
        selected.append(candidate)
        used_ids.add(candidate["episode_id"])

    return sorted(selected, key=lambda item: item["started_at"])


def reduce_episode_messages(
    messages: list[dict[str, Any]],
    target_max: int = 8,
) -> list[dict[str, Any]]:
    """Keep the most representative turns from an episode."""
    if len(messages) <= target_max:
        return deepcopy(messages)

    selected_indices = {0, len(messages) - 1}
    ai_indices = [index for index, item in enumerate(messages) if item["message_type"] == "ai"]
    human_indices = [
        index for index, item in enumerate(messages) if item["message_type"] == "human"
    ]

    for collection in (human_indices[:2], ai_indices[:2], human_indices[-2:], ai_indices[-2:]):
        selected_indices.update(collection)
        if len(selected_indices) >= target_max:
            break

    if len(selected_indices) < target_max:
        step = max(len(messages) // max(target_max - len(selected_indices), 1), 1)
        for index in range(step, len(messages) - 1, step):
            selected_indices.add(index)
            if len(selected_indices) >= target_max:
                break

    ordered_indices = sorted(selected_indices)
    if len(ordered_indices) > target_max:
        middle_slots = max(target_max - 2, 0)
        middle = ordered_indices[1:-1][:middle_slots]
        ordered_indices = [ordered_indices[0], *middle, ordered_indices[-1]]

    reduced = [deepcopy(messages[index]) for index in ordered_indices[:target_max]]
    return reduced


def materialize_demo_curated_chat(
    message_docs: list[dict[str, Any]],
    *,
    workout_logs: list[dict[str, Any]],
    nutrition_logs: list[dict[str, Any]],
    weight_logs: list[dict[str, Any]],
    source_email: str,
    demo_email: str,
    episode_limit: int = 20,
    gap_minutes: int = 60,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Build selected episodes and published message metadata."""
    episodes = segment_message_docs(message_docs, gap_minutes=gap_minutes)
    classified = [
        classify_episode(episode, workout_logs, nutrition_logs, weight_logs)
        for episode in episodes
    ]
    selected = select_top_episodes(classified, limit=episode_limit)

    demo_episodes: list[dict[str, Any]] = []
    demo_messages: list[dict[str, Any]] = []
    for episode in selected:
        reduced = reduce_episode_messages(episode["messages"])
        published_ids: list[str] = []
        for order, message in enumerate(reduced):
            message_id = f"{episode['episode_id']}-{order}"
            published_ids.append(message_id)
            demo_messages.append(
                {
                    "episode_id": episode["episode_id"],
                    "message_id": message_id,
                    "role": message["message_type"],
                    "trainer_type": message.get("trainer_type"),
                    "timestamp": message["timestamp"],
                    "content": _sanitize_text(message["content"], source_email, demo_email),
                    "source_message_id": message["source_id"],
                    "status": "published",
                }
            )

        demo_episodes.append(
            {
                "episode_id": episode["episode_id"],
                "title": build_episode_title(episode),
                "started_at": episode["started_at"],
                "ended_at": episode["ended_at"],
                "primary_domain": episode["primary_domain"],
                "trainers": episode["trainers"],
                "source_message_ids": [item["source_id"] for item in episode["messages"]],
                "published_message_ids": published_ids,
                "score": episode["score"],
                "status": "published",
                "message_count": len(published_ids),
            }
        )

    return demo_episodes, demo_messages


def build_episode_title(episode: dict[str, Any]) -> str:
    """Generate a short title for admin inspection."""
    domain = episode.get("primary_domain", "mixed").replace("_", " ").title()
    trainer = next((name for name in episode.get("trainers", []) if name != "<none>"), "coach")
    return f"{domain} with {trainer}"


def build_message_store_docs(
    demo_messages: list[dict[str, Any]], demo_email: str
) -> list[dict[str, Any]]:
    """Convert curated demo messages into message_store documents."""
    docs: list[dict[str, Any]] = []

    for item in demo_messages:
        if item.get("status") != "published":
            continue

        additional_kwargs: dict[str, Any] = {}
        if item.get("timestamp"):
            additional_kwargs["timestamp"] = item["timestamp"]
        if item.get("trainer_type"):
            additional_kwargs["trainer_type"] = item["trainer_type"]
        if item.get("translations"):
            additional_kwargs["translations"] = item["translations"]

        message_type = item.get("role", "human")
        content = item.get("content") or ""
        if message_type == "ai":
            message = AIMessage(content=content, additional_kwargs=additional_kwargs)
        elif message_type == "system":
            message = SystemMessage(content=content, additional_kwargs=additional_kwargs)
        else:
            message = HumanMessage(content=content, additional_kwargs=additional_kwargs)

        docs.append(
            {
                "SessionId": demo_email,
                "demo_message_id": item.get("message_id"),
                "demo_episode_id": item.get("episode_id"),
                "History": json.dumps(message_to_dict(message)),
            }
        )

    return docs
