# Graph Agent Config

This directory is the source of truth for graph node runtime behavior.
Prompt markdown files are full node instructions; Python runtime only injects allowed context, peer outputs, and output contract.

## Structure

- `nodes/*.json`: node manifests
- `prompts/*.md`: full system prompts per node
- Runtime loader: `src/services/agents/config_registry.py`

## Manifest Schema

Required/expected fields per node manifest:

- `node_name`
- `enabled`
- `model_provider`
- `model_name`
- `temperature`
- `max_tokens`
- `tool_policy`
- `tool_names`
- `prompt_file`
- `response_format`
- `version`
- `context_blocks`: required `list[str]`
- `peer_inputs`: optional `list[str]`, default `[]`
- `persona_mode`: `none` or `final_only`
- `output_contract`: required `str`

## Runtime Contract

For every node run, runtime assembles:

- `AVAILABLE_CONTEXT`: only blocks listed in `context_blocks`
- `PEER_INPUTS`: only node outputs listed in `peer_inputs`
- `OUTPUT_CONTRACT`: exact manifest output contract

`config_hash` reflects effective prompt text + manifest payload and is attached to traces/input metadata.

## Fast Edit Workflow

1. Edit prompt in `prompts/<node>.md`.
2. Edit policy/model in `nodes/<node>.json`.
3. Validate contract:
   - `cd backend && .venv/bin/pytest tests/unit/services/test_agent_config_registry.py -v`
4. Validate graph behavior:
   - `cd backend && .venv/bin/pytest tests/unit/services/test_conversation_graph.py -v`
5. Run backend gates:
   - `cd backend && .venv/bin/ruff check src tests`
   - `cd backend && .venv/bin/pylint src`

## Runtime Inspection

- `GET /admin/agent-configs`
- `GET /admin/agent-configs/{node_name}`

Endpoints expose prompt text, model policy, context policy (`context_blocks`, `peer_inputs`, `persona_mode`, `output_contract`), and `config_hash`.
