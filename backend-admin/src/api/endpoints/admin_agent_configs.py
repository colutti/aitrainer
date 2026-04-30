"""Read-only endpoints for graph agent config inspection."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

from src.core.deps import CURRENT_ADMIN_DEP

router = APIRouter(prefix="/admin/agent-configs", tags=["admin"])


def _config_base_dir() -> Path:
    return Path(__file__).resolve().parents[4] / "backend/src/services/agents/config"


def _load_configs() -> list[dict]:
    base = _config_base_dir()
    rows: list[dict] = []
    for manifest in sorted((base / "nodes").glob("*.json")):
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        prompt_rel = payload.get("prompt_file", "")
        prompt_path = Path(__file__).resolve().parents[4] / str(prompt_rel)
        prompt_text = prompt_path.read_text(encoding="utf-8") if prompt_path.exists() else ""
        raw = {**payload, "prompt_text": prompt_text}
        config_hash = hashlib.sha256(
            json.dumps(raw, sort_keys=True).encode("utf-8")
        ).hexdigest()[:16]
        rows.append(
            {
                **payload,
                "prompt_file": str(prompt_path),
                "prompt_text": prompt_text,
                "context_blocks": payload.get("context_blocks", []),
                "peer_inputs": payload.get("peer_inputs", []),
                "persona_mode": payload.get("persona_mode", "none"),
                "output_contract": payload.get("output_contract", "text"),
                "config_hash": config_hash,
            }
        )
    return rows


@router.get("/")
def list_agent_configs(_admin: CURRENT_ADMIN_DEP) -> dict:
    """List effective node configuration for all graph agents."""
    return {"configs": _load_configs()}


@router.get("/{node_name}")
def get_agent_config(node_name: str, _admin: CURRENT_ADMIN_DEP) -> dict:
    """Return effective configuration for a single graph agent node."""
    for cfg in _load_configs():
        if cfg.get("node_name") == node_name:
            return cfg
    raise HTTPException(status_code=404, detail="Node config not found")
