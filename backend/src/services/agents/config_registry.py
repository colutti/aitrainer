"""File-backed agent configuration registry."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.core.logs import logger


@dataclass(frozen=True)
class NodeConfig:
    """Runtime config for one graph node."""

    node_name: str
    enabled: bool
    model_provider: str
    model_name: str
    temperature: float
    max_tokens: int
    tool_policy: str
    tool_names: list[str]
    prompt_file: str
    response_format: str
    version: str
    context_blocks: list[str]
    peer_inputs: list[str]
    persona_mode: str
    output_contract: str
    prompt_text: str
    config_hash: str


class AgentConfigRegistry:
    """Loads node prompts/models from repository files."""

    def __init__(self, base_dir: str | Path):
        self._base_dir = Path(base_dir)
        self._configs: dict[str, NodeConfig] = {}
        self._loaded = False

    def load(self) -> None:
        """Load and validate all node configs."""
        if self._loaded:
            return

        node_dir = self._base_dir / "nodes"
        for manifest in sorted(node_dir.glob("*.json")):
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            context_blocks = payload.get("context_blocks")
            if not isinstance(context_blocks, list) or not all(
                isinstance(item, str) for item in context_blocks
            ):
                raise ValueError(
                    f"Invalid context_blocks for {manifest.name}: expected list[str]"
                )
            peer_inputs = payload.get("peer_inputs", [])
            if not isinstance(peer_inputs, list) or not all(
                isinstance(item, str) for item in peer_inputs
            ):
                raise ValueError(
                    f"Invalid peer_inputs for {manifest.name}: expected list[str]"
                )
            persona_mode = str(payload.get("persona_mode", "")).strip()
            if persona_mode not in {"none", "final_only"}:
                raise ValueError(
                    f"Invalid persona_mode for {manifest.name}: {persona_mode}"
                )
            output_contract = payload.get("output_contract")
            if not isinstance(output_contract, str) or not output_contract.strip():
                raise ValueError(
                    f"Invalid output_contract for {manifest.name}: expected non-empty string"
                )
            prompt_file = Path(payload["prompt_file"])
            if prompt_file.is_absolute():
                prompt_path = prompt_file
            else:
                cwd_candidate = Path.cwd() / prompt_file
                if cwd_candidate.exists():
                    prompt_path = cwd_candidate
                else:
                    stripped = Path(*prompt_file.parts[1:]) if prompt_file.parts and prompt_file.parts[0] == "backend" else prompt_file
                    prompt_path = Path.cwd() / stripped
            prompt_text = prompt_path.read_text(encoding="utf-8")
            raw = {
                **payload,
                "prompt_text": prompt_text,
            }
            config_hash = hashlib.sha256(
                json.dumps(raw, sort_keys=True).encode("utf-8")
            ).hexdigest()[:16]
            cfg = NodeConfig(
                node_name=str(payload["node_name"]),
                enabled=bool(payload.get("enabled", True)),
                model_provider=str(payload["model_provider"]),
                model_name=str(payload["model_name"]),
                temperature=float(payload.get("temperature", 0.0)),
                max_tokens=int(payload.get("max_tokens", 1024)),
                tool_policy=str(payload.get("tool_policy", "restricted")),
                tool_names=[str(name) for name in payload.get("tool_names", [])],
                prompt_file=str(prompt_path),
                response_format=str(payload.get("response_format", "text")),
                version=str(payload.get("version", "v1")),
                context_blocks=[str(item) for item in context_blocks],
                peer_inputs=[str(item) for item in peer_inputs],
                persona_mode=persona_mode,
                output_contract=output_contract.strip(),
                prompt_text=prompt_text,
                config_hash=config_hash,
            )
            self._configs[cfg.node_name] = cfg

        self._loaded = True
        logger.info("Loaded %d node configs from %s", len(self._configs), node_dir)

    def get_node_config(self, node_name: str) -> NodeConfig:
        """Return config for one node."""
        self.load()
        if node_name not in self._configs:
            raise KeyError(f"Missing node config: {node_name}")
        return self._configs[node_name]

    def list_node_configs(self) -> list[NodeConfig]:
        """Return all configs."""
        self.load()
        return list(self._configs.values())

    def as_metadata(self) -> dict[str, Any]:
        """Compact metadata for tracing/logging."""
        self.load()
        return {
            cfg.node_name: {
                "model_name": cfg.model_name,
                "version": cfg.version,
                "config_hash": cfg.config_hash,
                "context_blocks": cfg.context_blocks,
                "peer_inputs": cfg.peer_inputs,
                "persona_mode": cfg.persona_mode,
                "output_contract": cfg.output_contract,
            }
            for cfg in self._configs.values()
        }
