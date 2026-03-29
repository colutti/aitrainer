"""Tests for demo snapshot curation helpers."""

from datetime import UTC, datetime

from scripts.demo_snapshot_lib import (
    build_demo_profile,
    build_message_store_docs,
    classify_episode,
    materialize_demo_curated_chat,
    reduce_episode_messages,
    segment_message_docs,
    select_top_episodes,
)


def test_build_demo_profile_strips_sensitive_fields():
    source = {
        "_id": "mongo-id",
        "email": "rafacolucci@gmail.com",
        "display_name": "Rafael",
        "photo_base64": "base64",
        "hevy_api_key": "secret",
        "hevy_webhook_secret": "secret",
        "stripe_customer_id": "cus_123",
        "stripe_subscription_id": "sub_123",
        "telegram_notify_on_workout": True,
        "goal_type": "lose",
        "weekly_rate": 0.5,
    }

    result = build_demo_profile(source, "demo@fityq.it")

    assert result["email"] == "demo@fityq.it"
    assert result["is_demo"] is True
    assert result["photo_base64"] is None
    assert result["hevy_api_key"] is None
    assert result["hevy_webhook_secret"] is None
    assert result["stripe_customer_id"] is None
    assert result["stripe_subscription_id"] is None
    assert "_id" not in result


def test_segment_message_docs_accepts_naive_timestamps_and_splits_on_gap():
    docs = [
        {
            "_id": "1",
            "History": '{"type": "human", "data": {"content": "First", "additional_kwargs": {"timestamp": "2026-03-01T10:00:00", "trainer_type": "gymbro"}}}',
        },
        {
            "_id": "2",
            "History": '{"type": "ai", "data": {"content": "Reply", "additional_kwargs": {"timestamp": "2026-03-01T10:05:00", "trainer_type": "gymbro"}}}',
        },
        {
            "_id": "3",
            "History": '{"type": "human", "data": {"content": "Later", "additional_kwargs": {"timestamp": "2026-03-01T12:30:00", "trainer_type": "atlas"}}}',
        },
    ]

    result = segment_message_docs(docs, gap_minutes=60)

    assert len(result) == 2
    assert result[0]["message_count"] == 2
    assert result[1]["message_count"] == 1


def test_classify_episode_prefers_nearby_structured_logs():
    episode = {
        "episode_id": "abc",
        "started_at": "2026-03-01T10:00:00Z",
        "ended_at": "2026-03-01T10:10:00Z",
        "message_count": 4,
        "human_count": 2,
        "ai_count": 2,
        "trainers": ["gymbro"],
        "messages": [
            {"content": "Treino feito", "source_id": "1"},
            {"content": "Boa", "source_id": "2"},
        ],
    }

    classified = classify_episode(
        episode,
        workout_logs=[{"date": datetime(2026, 3, 1, 9, 0, tzinfo=UTC)}],
        nutrition_logs=[],
        weight_logs=[],
    )

    assert classified["primary_domain"] == "workout"
    assert classified["score"] > 0


def test_select_top_episodes_respects_domain_coverage_before_wildcards():
    episodes = [
        {
            "episode_id": f"workout-{index}",
            "primary_domain": "workout",
            "score": 10 - index,
            "started_at": f"2026-03-0{index + 1}T10:00:00Z",
        }
        for index in range(6)
    ] + [
        {
            "episode_id": "nutrition-1",
            "primary_domain": "nutrition",
            "score": 9,
            "started_at": "2026-03-10T10:00:00Z",
        },
        {
            "episode_id": "weight-1",
            "primary_domain": "weight",
            "score": 8,
            "started_at": "2026-03-11T10:00:00Z",
        },
    ]

    selected = select_top_episodes(
        episodes,
        limit=3,
        quotas={"workout": 1, "nutrition": 1},
    )

    assert {item["primary_domain"] for item in selected} >= {"workout", "nutrition"}
    assert len(selected) == 3


def test_reduce_episode_messages_limits_volume_but_keeps_edges():
    messages = [
        {
            "source_id": str(index),
            "message_type": "human" if index % 2 == 0 else "ai",
            "timestamp": f"2026-03-01T10:{index:02d}:00Z",
            "trainer_type": "gymbro",
            "content": f"Message {index}",
        }
        for index in range(12)
    ]

    reduced = reduce_episode_messages(messages, target_max=6)

    assert len(reduced) == 6
    assert reduced[0]["source_id"] == "0"
    assert reduced[-1]["source_id"] == "11"


def test_materialize_demo_curated_chat_builds_published_messages():
    docs = [
        {
            "_id": "1",
            "History": '{"type": "human", "data": {"content": "Treino bom", "additional_kwargs": {"timestamp": "2026-03-01T10:00:00Z", "trainer_type": "gymbro"}}}',
        },
        {
            "_id": "2",
            "History": '{"type": "ai", "data": {"content": "Excelente", "additional_kwargs": {"timestamp": "2026-03-01T10:05:00Z", "trainer_type": "gymbro"}}}',
        },
    ]

    episodes, messages = materialize_demo_curated_chat(
        docs,
        workout_logs=[{"date": datetime(2026, 3, 1, 8, 0, tzinfo=UTC)}],
        nutrition_logs=[],
        weight_logs=[],
        source_email="rafacolucci@gmail.com",
        demo_email="demo@fityq.it",
        episode_limit=20,
        gap_minutes=60,
    )

    assert len(episodes) == 1
    assert len(messages) == 2
    assert messages[0]["status"] == "published"

    message_store_docs = build_message_store_docs(messages, "demo@fityq.it")
    assert len(message_store_docs) == 2
    assert message_store_docs[0]["SessionId"] == "demo@fityq.it"
