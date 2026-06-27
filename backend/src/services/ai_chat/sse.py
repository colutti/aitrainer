"""SSE serialization helpers."""

from __future__ import annotations

import json


def format_sse_event(event: str, payload: dict | str) -> str:
    """Serialize one SSE event frame."""
    data = (
        payload
        if isinstance(payload, str)
        else json.dumps(payload, ensure_ascii=True, separators=(",", ":"))
    )
    return f"event: {event}\ndata: {data}\n\n"
