#!/usr/bin/env python3
"""Export, auto-curate, and publish a protected demo-user snapshot."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

from bson import json_util
from dotenv import dotenv_values
from pymongo import MongoClient
from pymongo.errors import PyMongoError

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scripts.demo_snapshot_lib import (  # noqa: E402
    build_demo_profile,
    build_message_store_docs,
    materialize_demo_curated_chat,
    remap_user_records,
)
from scripts.synthetic_demo_lib import (  # noqa: E402
    generate_synthetic_snapshot,
    load_synthetic_scenario,
    replace_demo_memories,
)
from scripts.utils import confirm_execution  # noqa: E402
from src.core.config import settings  # noqa: E402


COLLECTIONS = {
    "trainer_profiles": ("user_email", "date"),
    "workout_logs": ("user_email", "date"),
    "nutrition_logs": ("user_email", "date"),
    "weight_logs": ("user_email", "date"),
    "prompt_logs": ("user_email", "timestamp"),
}

PUBLISH_COLLECTIONS = (
    ("users", "email", "profile"),
    ("trainer_profiles", "user_email", "trainer_profiles"),
    ("workout_logs", "user_email", "workout_logs"),
    ("nutrition_logs", "user_email", "nutrition_logs"),
    ("weight_logs", "user_email", "weight_logs"),
    ("prompt_logs", "user_email", "prompt_logs"),
    ("message_store", "SessionId", "message_store_docs"),
    ("demo_snapshots", "demo_email", "snapshot"),
    ("demo_episodes", "demo_email", "demo_episodes"),
    ("demo_messages", "demo_email", "demo_messages"),
    ("demo_prune_log", "demo_email", None),
)

REQUIRED_CURATED_KEYS = {
    "snapshot": dict,
    "profile": dict,
    "trainer_profiles": list,
    "workout_logs": list,
    "nutrition_logs": list,
    "weight_logs": list,
    "prompt_logs": list,
    "demo_episodes": list,
    "demo_messages": list,
    "message_store_docs": list,
}


def _connect_from_env(env_file: Path) -> tuple[MongoClient, str]:
    env = dotenv_values(env_file)
    mongo_uri = str(env.get("MONGO_URI") or env.get("MONGO_PROD_URI") or "").strip()
    db_name = str(env.get("DB_NAME") or env.get("MONGO_DB_NAME") or settings.DB_NAME).strip()
    if not mongo_uri:
        raise ValueError(f"MONGO_URI not found in {env_file}")
    try:
        client = MongoClient(mongo_uri)
        client.admin.command("ping")
    except PyMongoError as exc:
        raise RuntimeError(
            f"Failed to connect to Mongo using {env_file}. "
            "Check DNS/network access and the configured Mongo URI."
        ) from exc
    return client, db_name


def _cutoff_for_months(months: int) -> datetime:
    return datetime.now(UTC) - timedelta(days=months * 31)


def _json_default(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return json_util.default(value)


def export_snapshot(args: argparse.Namespace) -> None:
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    client, db_name = _connect_from_env(Path(args.prod_env_file))
    db = client[db_name]
    cutoff = _cutoff_for_months(args.months)

    user = db.users.find_one({"email": args.source_email})
    if not user:
        raise ValueError(f"Source user not found: {args.source_email}")

    (out_dir / "user.json").write_text(json_util.dumps(user, indent=2), encoding="utf-8")

    for collection_name, (id_field, date_field) in COLLECTIONS.items():
        query: dict[str, Any] = {id_field: args.source_email}
        if date_field:
            query[date_field] = {"$gte": cutoff}
        docs = list(db[collection_name].find(query))
        (out_dir / f"{collection_name}.json").write_text(
            json_util.dumps(docs, indent=2), encoding="utf-8"
        )

    message_docs = list(db.message_store.find({"SessionId": args.source_email}))
    (out_dir / "message_store.json").write_text(
        json_util.dumps(message_docs, indent=2), encoding="utf-8"
    )

    manifest = {
        "source_email": args.source_email,
        "months": args.months,
        "exported_at": datetime.now(UTC).isoformat(),
        "message_count": len(message_docs),
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print(f"Exported raw snapshot to {out_dir}")


def prepare_snapshot(args: argparse.Namespace) -> None:
    source_dir = Path(args.source_dir)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    user = json_util.loads((source_dir / "user.json").read_text(encoding="utf-8"))
    message_docs = json_util.loads((source_dir / "message_store.json").read_text(encoding="utf-8"))
    workout_logs = json_util.loads((source_dir / "workout_logs.json").read_text(encoding="utf-8"))
    nutrition_logs = json_util.loads((source_dir / "nutrition_logs.json").read_text(encoding="utf-8"))
    weight_logs = json_util.loads((source_dir / "weight_logs.json").read_text(encoding="utf-8"))

    demo_profile = build_demo_profile(user, args.demo_email)
    demo_episodes, demo_messages = materialize_demo_curated_chat(
        message_docs,
        workout_logs=workout_logs,
        nutrition_logs=nutrition_logs,
        weight_logs=weight_logs,
        source_email=user["email"],
        demo_email=args.demo_email,
        episode_limit=args.episode_limit,
        gap_minutes=args.gap_minutes,
    )

    snapshot_id = f"demo-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"
    snapshot_meta = {
        "snapshot_id": snapshot_id,
        "source_user_email": user["email"],
        "demo_email": args.demo_email,
        "window_start": (
            min((message["timestamp"] for message in demo_messages), default=None)
        ),
        "window_end": (
            max((message["timestamp"] for message in demo_messages), default=None)
        ),
        "selection_strategy": "coverage_v1",
        "episode_count": len(demo_episodes),
        "message_count": len(demo_messages),
        "created_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
    }

    for episode in demo_episodes:
        episode["snapshot_id"] = snapshot_id
        episode["demo_email"] = args.demo_email
    for message in demo_messages:
        message["snapshot_id"] = snapshot_id
        message["demo_email"] = args.demo_email

    curated = {
        "snapshot": snapshot_meta,
        "profile": demo_profile,
        "trainer_profiles": remap_user_records(
            json_util.loads((source_dir / "trainer_profiles.json").read_text(encoding="utf-8")),
            args.demo_email,
            "user_email",
        ),
        "workout_logs": remap_user_records(workout_logs, args.demo_email, "user_email"),
        "nutrition_logs": remap_user_records(nutrition_logs, args.demo_email, "user_email"),
        "weight_logs": remap_user_records(weight_logs, args.demo_email, "user_email"),
        "prompt_logs": remap_user_records(
            json_util.loads((source_dir / "prompt_logs.json").read_text(encoding="utf-8")),
            args.demo_email,
            "user_email",
        ),
        "demo_episodes": demo_episodes,
        "demo_messages": demo_messages,
        "message_store_docs": build_message_store_docs(demo_messages, args.demo_email),
    }
    (out_dir / "curated_snapshot.json").write_text(
        json_util.dumps(curated, indent=2), encoding="utf-8"
    )
    (out_dir / "chat_review.json").write_text(
        json.dumps(
            {
                "snapshot": snapshot_meta,
                "episodes": demo_episodes,
                "message_count": len(demo_messages),
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print(f"Prepared editable curated snapshot in {out_dir}")


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
        json.dumps(synthetic, indent=2, ensure_ascii=False, default=_json_default),
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
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print(f"Generated synthetic curated snapshot in {out_dir}")


def publish_snapshot(args: argparse.Namespace) -> None:
    curated_path = Path(args.curated_file)
    curated = json_util.loads(curated_path.read_text(encoding="utf-8"))
    snapshot, demo_email = _validate_curated_snapshot(curated)

    confirm_execution(
        "Publish Demo Snapshot",
        {
            "demo_email": demo_email,
            "snapshot_id": snapshot["snapshot_id"],
            "curated_file": str(curated_path),
        },
    )

    client = MongoClient(settings.MONGO_URI)
    db = client[settings.DB_NAME]

    backups = _capture_existing_demo_state(db, demo_email)

    try:
        _delete_existing_demo_state(db, demo_email)
        _write_curated_demo_state(db, curated)
        replace_demo_memories(curated.get("memories", []), demo_email)
    except Exception:
        _restore_demo_state(db, demo_email, backups)
        raise

    print(
        json.dumps(
            {
                "demo_email": demo_email,
                "snapshot_id": snapshot["snapshot_id"],
                "workouts": len(curated["workout_logs"]),
                "nutrition_logs": len(curated["nutrition_logs"]),
                "weight_logs": len(curated["weight_logs"]),
                "episodes": len(curated["demo_episodes"]),
                "messages": len(curated["demo_messages"]),
            },
            indent=2,
        )
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Curate and publish a demo snapshot.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    export_parser = subparsers.add_parser("export")
    export_parser.add_argument("--source-email", required=True)
    export_parser.add_argument("--prod-env-file", default=".env.prod")
    export_parser.add_argument("--months", type=int, default=3)
    export_parser.add_argument("--output-dir", default="artifacts/demo/raw")
    export_parser.set_defaults(func=export_snapshot)

    prepare_parser = subparsers.add_parser("prepare")
    prepare_parser.add_argument("--source-dir", default="artifacts/demo/raw")
    prepare_parser.add_argument("--output-dir", default="artifacts/demo/curated")
    prepare_parser.add_argument("--demo-email", default="demo@fityq.it")
    prepare_parser.add_argument("--episode-limit", type=int, default=20)
    prepare_parser.add_argument("--gap-minutes", type=int, default=60)
    prepare_parser.set_defaults(func=prepare_snapshot)

    publish_parser = subparsers.add_parser("publish")
    publish_parser.add_argument(
        "--curated-file", default="artifacts/demo/curated/curated_snapshot.json"
    )
    publish_parser.set_defaults(func=publish_snapshot)

    synthetic_parser = subparsers.add_parser("generate-synthetic")
    synthetic_parser.add_argument(
        "--scenario-file",
        default="backend/scripts/demo_scenarios/ethan_parker_v1.json",
    )
    synthetic_parser.add_argument(
        "--output-dir",
        default="artifacts/demo/synthetic/ethan-parker-v1-en",
    )
    synthetic_parser.add_argument("--demo-email", default="demo@fityq.it")
    synthetic_parser.add_argument("--locale", default="en")
    synthetic_parser.set_defaults(func=generate_synthetic_snapshot_artifact)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


def _validate_curated_snapshot(curated: dict[str, Any]) -> tuple[dict[str, Any], str]:
    missing_keys = [key for key in REQUIRED_CURATED_KEYS if key not in curated]
    if missing_keys:
        raise ValueError(
            f"Missing required curated snapshot keys: {', '.join(sorted(missing_keys))}"
        )

    for key, expected_type in REQUIRED_CURATED_KEYS.items():
        if not isinstance(curated[key], expected_type):
            raise ValueError(f"Curated snapshot key '{key}' must be a {expected_type.__name__}")

    snapshot = curated["snapshot"]
    profile = curated["profile"]
    if not snapshot.get("snapshot_id"):
        raise ValueError("Curated snapshot is missing snapshot.snapshot_id")
    demo_email = profile.get("email")
    if not demo_email:
        raise ValueError("Curated snapshot is missing profile.email")
    snapshot_demo_email = snapshot.get("demo_email")
    if not snapshot_demo_email:
        raise ValueError("Curated snapshot is missing snapshot.demo_email")
    if snapshot_demo_email != demo_email:
        raise ValueError("Curated snapshot ownership mismatch: snapshot.demo_email")

    _validate_owner_list(
        curated["trainer_profiles"],
        "user_email",
        demo_email,
        "trainer_profiles",
    )
    _validate_owner_list(
        curated["workout_logs"],
        "user_email",
        demo_email,
        "workout_logs",
    )
    _validate_owner_list(
        curated["nutrition_logs"],
        "user_email",
        demo_email,
        "nutrition_logs",
    )
    _validate_owner_list(
        curated["weight_logs"],
        "user_email",
        demo_email,
        "weight_logs",
    )
    _validate_owner_list(
        curated["prompt_logs"],
        "user_email",
        demo_email,
        "prompt_logs",
    )
    _validate_owner_list(
        curated["demo_episodes"],
        "demo_email",
        demo_email,
        "demo_episodes",
    )
    _validate_owner_list(
        curated["demo_messages"],
        "demo_email",
        demo_email,
        "demo_messages",
    )
    _validate_owner_list(
        curated["message_store_docs"],
        "SessionId",
        demo_email,
        "message_store_docs",
    )
    return snapshot, demo_email


def _capture_existing_demo_state(db: Any, demo_email: str) -> dict[str, list[dict[str, Any]]]:
    backups: dict[str, list[dict[str, Any]]] = {}
    for collection_name, filter_field, _curated_key in PUBLISH_COLLECTIONS:
        collection = getattr(db, collection_name)
        backups[collection_name] = _find_many(collection, {filter_field: demo_email})
    return backups


def _delete_existing_demo_state(db: Any, demo_email: str) -> None:
    for collection_name, filter_field, _curated_key in PUBLISH_COLLECTIONS:
        getattr(db, collection_name).delete_many({filter_field: demo_email})


def _write_curated_demo_state(db: Any, curated: dict[str, Any]) -> None:
    db.users.insert_one(curated["profile"])
    if curated["trainer_profiles"]:
        db.trainer_profiles.insert_many(curated["trainer_profiles"])
    if curated["workout_logs"]:
        db.workout_logs.insert_many(curated["workout_logs"])
    if curated["nutrition_logs"]:
        db.nutrition_logs.insert_many(curated["nutrition_logs"])
    if curated["weight_logs"]:
        db.weight_logs.insert_many(curated["weight_logs"])
    if curated["prompt_logs"]:
        db.prompt_logs.insert_many(curated["prompt_logs"])
    if curated["message_store_docs"]:
        db.message_store.insert_many(curated["message_store_docs"])

    db.demo_snapshots.insert_one(curated["snapshot"])
    if curated["demo_episodes"]:
        db.demo_episodes.insert_many(curated["demo_episodes"])
    if curated["demo_messages"]:
        db.demo_messages.insert_many(curated["demo_messages"])


def _restore_demo_state(
    db: Any, demo_email: str, backups: dict[str, list[dict[str, Any]]]
) -> None:
    _delete_existing_demo_state(db, demo_email)
    for collection_name, _filter_field, _curated_key in PUBLISH_COLLECTIONS:
        docs = backups.get(collection_name, [])
        if not docs:
            continue
        collection = getattr(db, collection_name)
        if len(docs) == 1:
            collection.insert_one(docs[0])
        else:
            collection.insert_many(docs)


def _find_many(collection: Any, query: dict[str, Any]) -> list[dict[str, Any]]:
    finder = getattr(collection, "find", None)
    if finder is None:
        return []
    return list(finder(query))


def _validate_owner_list(
    records: list[dict[str, Any]],
    owner_field: str,
    expected_owner: str,
    label: str,
) -> None:
    for index, record in enumerate(records):
        actual_owner = record.get(owner_field)
        if actual_owner != expected_owner:
            raise ValueError(
                f"Curated snapshot ownership mismatch in {label}[{index}].{owner_field}"
            )


if __name__ == "__main__":
    main()
