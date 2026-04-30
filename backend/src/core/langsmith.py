"""LangSmith tracing helpers with fail-open behavior."""

from __future__ import annotations

import os
from contextlib import nullcontext, contextmanager
from typing import Any

from langchain_core.runnables import RunnableConfig

from src.core.config import settings
from src.core.logs import logger

_PROVIDER_ALLOWLIST = {"openrouter", "gemini", "openai", "ollama"}
_LANGSMITH_TRACER: Any = None


def is_tracing_enabled() -> bool:
    """Returns true only when tracing is explicitly and validly enabled."""
    if not (settings.LANGSMITH_TRACING or settings.LANGSMITH_TRACING_ENABLED):
        return False
    if not settings.LANGSMITH_API_KEY.strip():
        logger.warning("LangSmith tracing enabled but LANGSMITH_API_KEY is empty.")
        return False
    if not settings.LANGSMITH_PROJECT.strip():
        logger.warning("LangSmith tracing enabled but LANGSMITH_PROJECT is empty.")
        return False
    return True


def setup_environment() -> None:
    """Sets process-level LangSmith env vars without failing request execution."""
    if not is_tracing_enabled():
        return
    try:
        os.environ["LANGSMITH_TRACING"] = "true"
        os.environ["LANGSMITH_API_KEY"] = settings.LANGSMITH_API_KEY
        os.environ["LANGSMITH_ENDPOINT"] = settings.LANGSMITH_ENDPOINT
        os.environ["LANGSMITH_PROJECT"] = settings.LANGSMITH_PROJECT
        if settings.LANGSMITH_WORKSPACE_ID.strip():
            os.environ["LANGSMITH_WORKSPACE_ID"] = settings.LANGSMITH_WORKSPACE_ID
        # Compatibility aliases used by several LangChain integrations.
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = settings.LANGSMITH_API_KEY
        os.environ["LANGCHAIN_ENDPOINT"] = settings.LANGSMITH_ENDPOINT
        os.environ["LANGCHAIN_PROJECT"] = settings.LANGSMITH_PROJECT
    except (ValueError, TypeError, OSError, KeyError) as exc:
        logger.warning("Failed to configure LangSmith environment: %s", exc)


def build_runnable_config(
    *,
    run_name: str,
    mode: str,
    user_email: str | None,
    input_data: dict[str, Any],
    provider_hint: str | None = None,
    recursion_limit: int | None = None,
) -> RunnableConfig:
    # pylint: disable=too-many-arguments
    """Creates standardized RunnableConfig including LangSmith metadata/tags."""
    config: RunnableConfig = {}
    if recursion_limit is not None:
        config["recursion_limit"] = int(recursion_limit)

    if not is_tracing_enabled():
        return config

    provider = _normalized_provider(provider_hint)
    session_id = str(input_data.get("session_id") or user_email or "")
    prompt_name = str(input_data.get("prompt_name") or "chat")
    user_message = str(input_data.get("user_message", ""))
    tools = input_data.get("tools") if isinstance(input_data.get("tools"), list) else []
    tags = [
        f"env:{settings.LANGSMITH_ENVIRONMENT}",
        "surface:backend",
        "flow:chat",
        f"mode:{mode}",
        f"provider:{provider}",
    ]
    metadata = {
        "user_email": user_email,
        "session_id": session_id,
        "prompt_name": prompt_name,
        "prompt_chars": len(user_message),
        "messages_count": int(input_data.get("messages_count", 0) or 0),
        "tools_available": [str(t) for t in tools],
        "status": "running",
        "request_id": input_data.get("request_id"),
        "conversation_id": input_data.get("conversation_id"),
        "turn_id": input_data.get("turn_id"),
        "node_name": input_data.get("node_name"),
        "node_config_hash": input_data.get("node_config_hash"),
    }
    config["run_name"] = run_name
    config["tags"] = tags
    config["metadata"] = metadata
    callbacks = _build_callbacks(tags=tags)
    if callbacks:
        config["callbacks"] = callbacks
    return config


def merge_runtime_metadata(
    config: RunnableConfig, runtime_updates: dict[str, Any]
) -> RunnableConfig:
    """Merges final metadata into config without raising."""
    try:
        current = config.get("metadata")
        merged = dict(current) if isinstance(current, dict) else {}
        merged.update(runtime_updates)
        config["metadata"] = merged
    except (ValueError, TypeError, AttributeError) as exc:
        logger.warning("Failed to merge LangSmith metadata: %s", exc)
    return config


def create_tool_run_span(tool_name: str, content: Any, tool_call_id: str | None = None) -> None:
    """Creates an explicit tool span as a child run under current run tree."""
    try:
        from langsmith.run_helpers import (  # pylint: disable=import-outside-toplevel
            get_current_run_tree,
        )

        run_tree = get_current_run_tree()
        if run_tree is None:
            return
        child = run_tree.create_child(
            name=f"tool:{tool_name}",
            run_type="tool",
            inputs={"tool_name": tool_name, "tool_call_id": tool_call_id},
            outputs={"content": content},
        )
        child.end(outputs={"content": content})
    except (ValueError, TypeError, AttributeError, ImportError, Exception) as exc:  # pylint: disable=broad-exception-caught
        logger.warning("Failed to create LangSmith tool span: %s", exc)


def _normalized_provider(provider_hint: str | None) -> str:
    if provider_hint:
        normalized = str(provider_hint).lower().strip()
        if normalized in _PROVIDER_ALLOWLIST:
            return normalized
    return "openrouter"


def _build_callbacks(tags: list[str]) -> list[Any]:
    """Builds LangSmith tracer callbacks. Returns empty on any failure."""
    global _LANGSMITH_TRACER  # pylint: disable=global-statement
    if not is_tracing_enabled():
        return []
    try:
        if _LANGSMITH_TRACER is None:
            from langsmith import Client  # pylint: disable=import-outside-toplevel
            from langchain_core.tracers import (  # pylint: disable=import-outside-toplevel
                LangChainTracer,
            )

            client = Client(
                api_key=settings.LANGSMITH_API_KEY,
                api_url=settings.LANGSMITH_ENDPOINT,
                workspace_id=(
                    settings.LANGSMITH_WORKSPACE_ID.strip() or None
                ),
            )
            _LANGSMITH_TRACER = LangChainTracer(
                project_name=settings.LANGSMITH_PROJECT,
                client=client,
                tags=tags,
            )
        return [_LANGSMITH_TRACER]
    except (ValueError, TypeError, AttributeError, ImportError, Exception) as exc:  # pylint: disable=broad-exception-caught
        logger.warning("Failed to initialize LangSmith tracer callback: %s", exc)
        return []


def create_graph_run_context(
    *,
    run_name: str,
    metadata: dict[str, Any] | None = None,
):
    """Create a root LangSmith trace context for graph execution."""
    if not is_tracing_enabled():
        return nullcontext()
    try:
        from langsmith.run_helpers import trace  # pylint: disable=import-outside-toplevel

        return trace(
            name=run_name,
            run_type="chain",
            metadata=metadata or {},
        )
    except (ValueError, TypeError, AttributeError, ImportError, Exception) as exc:  # pylint: disable=broad-exception-caught
        logger.warning("Failed to create LangSmith graph trace context: %s", exc)
        return nullcontext()


@contextmanager
def create_node_run_context(
    *,
    node_name: str,
    metadata: dict[str, Any] | None = None,
):
    """Create one explicit child run for a graph node."""
    if not is_tracing_enabled():
        yield None
        return
    try:
        from langsmith.run_helpers import (  # pylint: disable=import-outside-toplevel
            get_current_run_tree,
        )

        run_tree = get_current_run_tree()
        if run_tree is None:
            yield None
            return
        child = run_tree.create_child(
            name=f"graph.node.{node_name}",
            run_type="chain",
            inputs={"node_name": node_name},
        )
        if metadata and hasattr(child, "add_metadata"):
            child.add_metadata(metadata)
        try:
            yield child
        except Exception as exc:  # pylint: disable=broad-exception-caught
            child.end(
                outputs={"status": "error", "error_type": type(exc).__name__}
            )
            raise
        child.end(outputs={"status": "success"})
    except (ValueError, TypeError, AttributeError, ImportError, Exception) as exc:  # pylint: disable=broad-exception-caught
        logger.warning("Failed to create LangSmith node trace context: %s", exc)
        yield None
