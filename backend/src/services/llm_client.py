"""
LLM Client abstraction layer for AI trainer.
Provides a unified interface for OpenRouter.
"""

import warnings
import time
import asyncio
import hashlib
import json
from typing import AsyncGenerator, Any
from langchain_core.messages import AIMessage, ToolMessage, HumanMessage
from langchain_core.runnables import RunnableConfig

try:
    from langchain.agents import create_agent
except ImportError:

    def create_agent(*args, **kwargs) -> Any:  # pylint: disable=unused-argument
        """Fallback for create_agent."""
        return Any

    class CompiledStateGraph:  # pylint: disable=too-few-public-methods
        """Fallback for CompiledStateGraph."""

        def astream(self, *args, **kwargs) -> Any:  # pylint: disable=unused-argument
            """Fallback astream."""

            async def _gen():
                yield None
                return

            return _gen()


# Suppress Pydantic V1/LangSmith warning as we cannot easily upgrade right now
warnings.filterwarnings("ignore", message=".*Core Pydantic V1 functionality.*")

from src.core.logs import logger  # noqa: E402  pylint: disable=wrong-import-position
from src.core.langsmith import (  # noqa: E402  pylint: disable=wrong-import-position
    setup_environment as setup_langsmith_environment,
    build_runnable_config,
    merge_runtime_metadata,
    create_tool_run_span,
)


class LLMClient:
    """
    Base LLM client.
    Subclasses implement _llm_for_node to create node-specific LLMs.
    """

    _langsmith_bootstrapped = False
    supports_multimodal: bool = True
    USER_FACING_ERROR_MESSAGES = {
        "pt-BR": "Desculpe, ocorreu um erro interno. Tente novamente em instantes.",
        "en-US": "Sorry, an internal error occurred. Please try again shortly.",
        "es-ES": "Lo sentimos, ocurrió un error interno. Inténtalo de nuevo en breve.",
    }

    @classmethod
    def _ensure_langsmith(cls):
        if not cls._langsmith_bootstrapped:
            setup_langsmith_environment()
            cls._langsmith_bootstrapped = True

    @classmethod
    def get_user_facing_error_message(cls, locale: str | None) -> str:
        """Returns localized safe error message with fallback to pt-BR."""
        return cls.USER_FACING_ERROR_MESSAGES.get(
            locale or "pt-BR", cls.USER_FACING_ERROR_MESSAGES["pt-BR"]
        )

    def _llm_for_node(
        self,
        model_override: str,
        user_email: str | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        frequency_penalty: float | None = None,
        provider_sort: str | None = None,
        max_tokens: int | None = None,
        reasoning: dict[str, Any] | None = None,
        parallel_tool_calls: bool | None = None,
    ):
        # pylint: disable=too-many-arguments,too-many-positional-arguments
        """Return an LLM runnable for a specific node. Must be overridden."""
        raise NotImplementedError("Subclasses must implement _llm_for_node")

    async def stream_with_tools(
        self,
        prompt_template,
        input_data: dict,
        tools: list,
        model_override: str,
        user_email: str | None = None,
        log_callback=None,
        temperature: float | None = None,
        top_p: float | None = None,
        frequency_penalty: float | None = None,
        provider_sort: str | None = None,
        max_tokens: int | None = None,
        reasoning: dict[str, Any] | None = None,
        parallel_tool_calls: bool | None = None,
        response_format: str | dict[str, Any] | None = None,
        run_name: str = "chat.tools",
        mode: str = "tools",
    ) -> AsyncGenerator[str | dict, None]:
        # pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-locals,too-many-branches,too-many-statements,too-many-nested-blocks

        """
        Invokes the LLM with tool support using LangGraph's ReAct agent.

        Args:
            model_override: The model name to use (required, from node config).
        Yields:
            str: Content chunks during streaming
            dict: Tool results with type="tool_result"
            dict: Final summary with type="tools_summary"
        """
        self._ensure_langsmith()

        user_message = str(input_data.get("user_message", ""))
        logger.info(
            "Invoking LLM with tools (LangGraph) for input chars=%d sha=%s",
            len(user_message),
            hashlib.sha256(user_message.encode("utf-8")).hexdigest()[:12],
        )
        if input_data.get("user_images") and not self.supports_multimodal:
            raise ValueError("IMAGE_INPUT_NOT_SUPPORTED_BY_PROVIDER")

        tools_called: list[str] = []
        start_time = time.time()
        usage_metadata: dict = {"input_tokens": 0, "output_tokens": 0}
        runtime_metadata: dict[str, Any] = {}
        usage_metadata_captured = False  # Track if we already captured
        config: RunnableConfig = {}
        requested_model = model_override

        messages: list[Any] = []
        try:
            format_input = {
                key: value for key, value in input_data.items() if key != "user_image"
            }
            messages = list(prompt_template.format_messages(**format_input))
            input_data["messages_count"] = len(messages)
            input_data["tools"] = [str(t.name) for t in tools]
            if input_data.get("user_images"):
                user_images = input_data["user_images"]
                content_blocks = [
                    {"type": "text", "text": input_data.get("user_message", "")}
                ]
                for user_image in user_images:
                    image_data_uri = (
                        f"data:{user_image['mime_type']};base64,{user_image['base64']}"
                    )
                    content_blocks.append(
                        {
                            "type": "image_url",
                            "image_url": {"url": image_data_uri},
                        }
                    )
                messages.append(
                    HumanMessage(
                        content=content_blocks
                    )
                )
            request_llm = self._llm_for_node(
                model_override=model_override,
                user_email=user_email,
                temperature=temperature,
                top_p=top_p,
                frequency_penalty=frequency_penalty,
                provider_sort=provider_sort,
                max_tokens=max_tokens,
                reasoning=reasoning,
                parallel_tool_calls=parallel_tool_calls,
            )

            from src.core.config import settings  # pylint: disable=import-outside-toplevel
            config: RunnableConfig = build_runnable_config(
                run_name=run_name,
                mode=mode,
                user_email=user_email,
                input_data=input_data,
                recursion_limit=int(settings.LLM_AGENT_RECURSION_LIMIT),
            )

            # Direct structured invocation for nodes with response_format but
            # no tools. Bypasses agent loop to avoid GRAPH_RECURSION_LIMIT
            # when tools=[], e.g., prompt_security with json_schema strict.
            if not tools and response_format is not None:
                try:
                    llm_with_format = request_llm.bind(response_format=response_format)
                    result = await llm_with_format.ainvoke(messages, config=config)
                    if isinstance(result, AIMessage):
                        usage_metadata_captured, usage_metadata = self._capture_metadata(
                            result, source="DirectStructured"
                        )
                        runtime_metadata = self._extract_runtime_metadata(result)
                        if result.content:
                            for block in self._yield_content_blocks(result.content):
                                yield block
                except Exception as exc:  # pylint: disable=broad-exception-caught
                    logger.error(
                        "Error in direct structured LLM call: %s sha=%s",
                        exc,
                        hashlib.sha256(user_message.encode("utf-8")).hexdigest()[:12],
                    )
                    yield self.get_user_facing_error_message(
                        input_data.get("user_locale")
                    )
                return

            agent_kwargs: dict[str, Any] = {}
            if response_format is not None:
                agent_kwargs["response_format"] = response_format
            agent: Any = create_agent(request_llm, tools, **agent_kwargs)
            if response_format is not None:
                result = await agent.ainvoke({"messages": messages}, config=config)
                final_messages = result.get("messages", []) if isinstance(result, dict) else []
                structured_response = (
                    result.get("structured_response") if isinstance(result, dict) else None
                )
                for event in final_messages:
                    if not usage_metadata_captured and isinstance(event, AIMessage):
                        usage_metadata_captured, usage_metadata = self._capture_metadata(
                            event, source="LangGraphStructured"
                        )
                        runtime_metadata = self._extract_runtime_metadata(event)

                    if isinstance(event, ToolMessage):
                        tools_called.append(str(event.name or "unknown"))
                        create_tool_run_span(
                            tool_name=str(event.name or "unknown"),
                            content=event.content,
                            tool_call_id=event.tool_call_id,
                        )
                        yield {
                            "type": "tool_result",
                            "content": event.content,
                            "tool_name": str(event.name or "unknown"),
                            "tool_call_id": event.tool_call_id,
                        }
                if structured_response is not None:
                    yield json.dumps(structured_response, ensure_ascii=True)
                else:
                    for event in final_messages:
                        if isinstance(event, AIMessage) and event.content:
                            for block in self._yield_content_blocks(event.content):
                                yield block
                return
            async for event in self._iter_agent_events(
                agent=agent, messages=messages, config=config
            ):

                if not usage_metadata_captured and isinstance(event, AIMessage):
                    usage_metadata_captured, usage_metadata = self._capture_metadata(
                        event
                    )
                    runtime_metadata = self._extract_runtime_metadata(event)

                if isinstance(event, ToolMessage):
                    tools_called.append(str(event.name or "unknown"))
                    create_tool_run_span(
                        tool_name=str(event.name or "unknown"),
                        content=event.content,
                        tool_call_id=event.tool_call_id,
                    )
                    yield {
                        "type": "tool_result",
                        "content": event.content,
                        "tool_name": str(event.name or "unknown"),
                        "tool_call_id": event.tool_call_id,
                    }
                    continue

                if isinstance(event, AIMessage) and event.content:
                    for block in self._yield_content_blocks(event.content):
                        yield block

        except (ValueError, TypeError, AttributeError, Exception) as e:  # pylint: disable=broad-exception-caught
            logger.error("Error in stream_with_tools: %s", e)
            yield self.get_user_facing_error_message(input_data.get("user_locale"))
        finally:
            # Log prompt with tokens at the END of streaming
            duration_ms = int((time.time() - start_time) * 1000)
            try:
                merge_runtime_metadata(
                    config,
                    {
                        "tools_called": tools_called,
                        "duration_ms": duration_ms,
                        "requested_model": requested_model,
                        "resolved_model": runtime_metadata.get("resolved_model", requested_model),
                        "resolved_provider": runtime_metadata.get("resolved_provider"),
                        "usage_cost": runtime_metadata.get("usage_cost"),
                        "service_tier": runtime_metadata.get("service_tier"),
                        "status": "success",
                        "tokens_input": usage_metadata.get("input_tokens", 0),
                        "tokens_output": usage_metadata.get("output_tokens", 0),
                    },
                )
            except (ValueError, TypeError, AttributeError, Exception) as trace_err:  # pylint: disable=broad-exception-caught
                logger.warning("Failed to append LangSmith metadata: %s", trace_err)
            if log_callback and user_email:
                try:
                    tokens_in = usage_metadata.get("input_tokens", 0)
                    tokens_out = usage_metadata.get("output_tokens", 0)
                    log_callback(
                        user_email,
                        {
                            "prompt_preview": user_message[:500],
                            "prompt_hash": hashlib.sha256(
                                user_message.encode("utf-8")
                            ).hexdigest(),
                            "prompt_chars": len(user_message),
                            "prompt_name": str(input_data.get("prompt_name", "chat")),
                            "type": "with_tools",
                            "messages_count": len(messages),
                            "tools": [t.name for t in tools],
                            "tools_called": tools_called,
                            "tokens_input": tokens_in,
                            "tokens_output": tokens_out,
                            "duration_ms": duration_ms,
                            "model": requested_model,
                            "requested_model": requested_model,
                            "resolved_model": runtime_metadata.get(
                                "resolved_model", requested_model
                            ),
                            "resolved_provider": runtime_metadata.get(
                                "resolved_provider"
                            ),
                            "usage_cost": runtime_metadata.get("usage_cost"),
                            "service_tier": runtime_metadata.get("service_tier"),
                            "status": "success",
                        },
                    )
                except (ValueError, TypeError, AttributeError, Exception) as log_err:  # pylint: disable=broad-exception-caught
                    logger.warning(
                        "Failed to log prompt in stream_with_tools: %s", log_err
                    )

            # Yield tools summary at the end to allow caller to make decisions
            yield {"type": "tools_summary", "tools_called": tools_called}

    @staticmethod
    async def _iter_agent_events(agent: Any, messages: list[Any], config: RunnableConfig):
        """Iterates over agent events with inactivity timeout enforcement."""
        from src.core.config import settings  # pylint: disable=import-outside-toplevel

        inactivity_timeout = float(settings.LLM_STREAM_INACTIVITY_TIMEOUT_SECONDS)
        events_iter = aiter(
            agent.astream({"messages": messages}, stream_mode="messages", config=config)
        )

        while True:
            try:
                item = await asyncio.wait_for(
                    anext(events_iter),
                    timeout=inactivity_timeout,
                )
            except StopAsyncIteration:
                return
            except TimeoutError as timeout_err:
                raise TimeoutError(
                    f"STREAM_INACTIVITY_TIMEOUT after {inactivity_timeout}s"
                ) from timeout_err

            yield item[0] if isinstance(item, tuple) and len(item) == 2 else item

    def _capture_metadata(
        self, event: AIMessage, source: str = "LangGraph"
    ) -> tuple[bool, Any]:
        """Helper to capture usage metadata from AI messages."""
        if hasattr(event, "usage_metadata") and event.usage_metadata:
            u_meta = event.usage_metadata
            tokens = u_meta.get("input_tokens", 0) + u_meta.get("output_tokens", 0)
            if tokens > 0:
                logger.info(
                    "✓ Captured usage_metadata (%s): input=%s, output=%s",
                    source,
                    u_meta.get("input_tokens", 0),
                    u_meta.get("output_tokens", 0),
                )
                return True, u_meta
        return False, {"input_tokens": 0, "output_tokens": 0}

    def _yield_content_blocks(self, content: str | list):
        """Helper to yield content blocks from AIMessage."""
        if isinstance(content, str):
            yield content
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, str):
                    yield block
                elif isinstance(block, dict) and "text" in block:
                    yield block["text"]

    def _extract_runtime_metadata(self, event: AIMessage) -> dict[str, Any]:
        """Extracts model/provider/cost metadata from runtime response."""
        response_metadata = getattr(event, "response_metadata", {}) or {}
        usage_metadata = getattr(event, "usage_metadata", {}) or {}
        additional_kwargs = getattr(event, "additional_kwargs", {}) or {}
        if not isinstance(response_metadata, dict):
            response_metadata = {}
        if not isinstance(usage_metadata, dict):
            usage_metadata = {}
        if not isinstance(additional_kwargs, dict):
            additional_kwargs = {}

        resolved_model = (
            response_metadata.get("model_name")
            or response_metadata.get("model")
            or response_metadata.get("resolved_model")
            or usage_metadata.get("model_name")
            or usage_metadata.get("model")
            or additional_kwargs.get("model")
        )
        resolved_provider = (
            response_metadata.get("provider")
            or response_metadata.get("provider_name")
            or response_metadata.get("model_provider")
            or usage_metadata.get("provider")
            or additional_kwargs.get("provider")
        )
        usage_cost = response_metadata.get("cost") or usage_metadata.get("cost")
        service_tier = (
            response_metadata.get("service_tier")
            or usage_metadata.get("service_tier")
        )

        return {
            "resolved_model": resolved_model,
            "resolved_provider": resolved_provider,
            "usage_cost": usage_cost,
            "service_tier": service_tier,
        }


# Manual agent loop methods removed (refactoring to LangGraph)


class OpenRouterClient(LLMClient):
    """LLM Client for OpenRouter models."""

    def __init__(self, api_key: str, base_url: str):
        """Initialize OpenRouter client through OpenAI-compatible API."""
        self._api_key = api_key
        self._base_url = base_url

    def _llm_for_node(
        self,
        model_override: str,
        user_email: str | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        frequency_penalty: float | None = None,
        provider_sort: str | None = None,
        max_tokens: int | None = None,
        reasoning: dict[str, Any] | None = None,
        parallel_tool_calls: bool | None = None,
    ):
        # pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-locals
        """Return an OpenRouter client for a specific graph node."""
        from langchain_openai import ChatOpenAI  # pylint: disable=import-outside-toplevel
        from pydantic import SecretStr  # pylint: disable=import-outside-toplevel
        from src.core.config import settings  # pylint: disable=import-outside-toplevel

        if not model_override:
            raise ValueError("model_override is required")
        kwargs: dict[str, Any] = {
            "model": model_override,
            "base_url": self._base_url,
            "api_key": SecretStr(self._api_key) if self._api_key else SecretStr(""),
        }
        if temperature is not None:
            kwargs["temperature"] = temperature
        if top_p is not None:
            kwargs["top_p"] = top_p
        if frequency_penalty is not None:
            kwargs["frequency_penalty"] = frequency_penalty
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        if reasoning is not None:
            kwargs["reasoning"] = reasoning
        model_kw: dict[str, Any] = {}
        if parallel_tool_calls is not None:
            model_kw["parallel_tool_calls"] = parallel_tool_calls
        if model_kw:
            kwargs["model_kwargs"] = model_kw
        extra: dict[str, Any] = {}
        if provider_sort:
            extra["provider"] = {"sort": provider_sort}
        if settings.OPENROUTER_SERVICE_TIER:
            extra["service_tier"] = settings.OPENROUTER_SERVICE_TIER
        if extra:
            kwargs["extra_body"] = extra
        llm = ChatOpenAI(**kwargs)
        if user_email:
            llm = llm.bind(user=user_email)
        return llm
