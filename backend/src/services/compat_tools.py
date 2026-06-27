"""Small tool wrapper used by legacy factory modules.

The chat runtime no longer depends on external agent frameworks. These wrappers
keep the old factory modules importable for direct service tests and any non-agent callers
that still use ``invoke``/``ainvoke``.
"""

from __future__ import annotations

import inspect
from functools import wraps
from typing import Any, Callable


class SimpleTool:
    """Minimal callable tool object compatible with the old local tests."""

    def __init__(self, func: Callable[..., Any], name: str | None = None):
        self.func = func
        self.name = name or func.__name__
        self.description = inspect.getdoc(func) or ""

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self.func(*args, **kwargs)

    def invoke(self, input_data: dict[str, Any] | None = None) -> Any:
        """Invoke a synchronous tool with a tool dict payload."""
        payload = input_data or {}
        return self.func(**payload)

    async def ainvoke(self, input_data: dict[str, Any] | None = None) -> Any:
        """Invoke a tool asynchronously, awaiting async functions when needed."""
        payload = input_data or {}
        result = self.func(**payload)
        if inspect.isawaitable(result):
            return await result
        return result


def tool(
    func: Callable[..., Any] | None = None,
    *,
    args_schema: type[Any] | None = None,
) -> Callable[[Callable[..., Any]], SimpleTool] | SimpleTool:
    """Decorate a function as a local tool without framework coupling."""

    def decorator(inner: Callable[..., Any]) -> SimpleTool:
        @wraps(inner)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if args_schema is not None and kwargs:
                validated = args_schema(**kwargs)
                kwargs = validated.model_dump()
            return inner(*args, **kwargs)

        return SimpleTool(wrapper, name=inner.__name__)

    if func is not None:
        return decorator(func)
    return decorator
