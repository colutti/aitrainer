"""
LLM Client abstraction layer for AI trainer.
Provides a unified interface for OpenRouter.
"""

import warnings
import time
import asyncio
import hashlib
from typing import AsyncGenerator, Any
from langchain_core.output_parsers import StrOutputParser
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
    Base LLM client with all common logic.
    Children only implement __init__ to create the specific LLM object.
    """

    _initialized = False
    _llm: Any = None
    model_name: str = ""
    supports_multimodal: bool = True
    USER_FACING_ERROR_MESSAGES = {
        "pt-BR": "Desculpe, ocorreu um erro interno. Tente novamente em instantes.",
        "en-US": "Sorry, an internal error occurred. Please try again shortly.",
        "es-ES": "Lo sentimos, ocurrió un error interno. Inténtalo de nuevo en breve.",
    }
    _langsmith_bootstrapped = False

    def _llm_for_request(
        self,
        user_email: str | None,
        model_override: str | None = None,
    ):
        """Returns an LLM runnable bound to OpenRouter user when available."""
        request_llm = self._llm
        if model_override:
            request_llm = self._llm_for_node(
                model_override=model_override,
            )
        if user_email:
            return request_llm.bind(user=user_email)
        return request_llm

    def _llm_for_node(
        self,
        model_override: str | None = None,
    ):
        """Return a node-specific LLM runnable. Base implementation reuses default."""
        del model_override
        return self._llm

    @classmethod
    def get_user_facing_error_message(cls, locale: str | None) -> str:
        """Returns localized safe error message with fallback to pt-BR."""
        return cls.USER_FACING_ERROR_MESSAGES.get(
            locale or "pt-BR", cls.USER_FACING_ERROR_MESSAGES["pt-BR"]
        )

    @classmethod
    def from_config(cls) -> "LLMClient":
        """
        Factory method that returns the OpenRouter LLM client.
        """
        from src.core.config import settings  # pylint: disable=import-outside-toplevel

        if not cls._langsmith_bootstrapped:
            setup_langsmith_environment()
            cls._langsmith_bootstrapped = True

        if not cls._initialized:
            logger.info(
                "Creating OpenRouterClient with chat model %s",
                settings.OPENROUTER_CHAT_MODEL or "deepseek/deepseek-v4-flash",
            )
            cls._initialized = True
        routing_model = settings.OPENROUTER_CHAT_MODEL
        if not routing_model:
            raise ValueError("OPENROUTER_CHAT_MODEL must be configured with a model name")
        if routing_model.startswith("@preset/"):
            raise ValueError(
                "OPENROUTER_CHAT_MODEL must be a model name, not a preset slug"
            )
        return OpenRouterClient(
            api_key=settings.OPENROUTER_API_KEY,
            model=routing_model,
            preset=settings.OPENROUTER_PROMPT_PRESET or None,
            base_url=settings.OPENROUTER_BASE_URL,
        )

    async def stream_with_tools(
        self,
        prompt_template,
        input_data: dict,
        tools: list,
        user_email: str | None = None,
        log_callback=None,
        model_override: str | None = None,
        run_name: str = "chat.tools",
        mode: str = "tools",
    ) -> AsyncGenerator[str | dict, None]:
        # pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-locals,too-many-branches,too-many-statements

        """
        Invokes the LLM with tool support using LangGraph's ReAct agent.

        Yields:
            str: Content chunks during streaming
            dict: Tool results with type="tool_result"
            dict: Final summary with type="tools_summary"
        """
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
        requested_model = model_override or self.model_name

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
            request_llm = self._llm_for_request(
                user_email=user_email,
                model_override=model_override,
            )
            agent: Any = create_agent(request_llm, tools)
            from src.core.config import settings  # pylint: disable=import-outside-toplevel
            config: RunnableConfig = build_runnable_config(
                run_name=run_name,
                mode=mode,
                user_email=user_email,
                input_data=input_data,
                recursion_limit=int(settings.LLM_AGENT_RECURSION_LIMIT),
            )
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
                        "resolved_model": runtime_metadata.get("resolved_model", self.model_name),
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
                                "resolved_model", self.model_name
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

    async def stream_simple(
        self,
        prompt_template,
        input_data: dict,
        user_email: str | None = None,
        log_callback=None,
    ) -> AsyncGenerator[str, None]:
        # pylint: disable=too-many-branches,too-many-locals,too-many-statements
        """
        Simple streaming without tools.

        Args:
            prompt_template: The LangChain prompt template to use.
            input_data: Dictionary with input variables for the template.
            user_email: Optional user email for logging.
            log_callback: Optional callback for logging the prompt.

        Yields:
            Individual chunks of the LLM response content.
        """
        logger.info(
            "Invoking LLM (simple) for user: %s, input keys: %s",
            user_email,
            list(input_data.keys()),
        )

        start_time = time.time()
        prompt_str = ""
        usage_metadata: dict = {"input_tokens": 0, "output_tokens": 0}
        runtime_metadata: dict[str, Any] = {}
        usage_metadata_captured = False  # Flag to ensure we capture only once
        config: RunnableConfig = {}

        try:
            prompt_str = prompt_template.format(**input_data)
            input_data["prompt_name"] = "resumo"
            config: RunnableConfig = build_runnable_config(
                run_name="chat.simple",
                mode="simple",
                user_email=user_email,
                input_data=input_data,
            )

            # Try to stream from LLM directly first (to capture usage_metadata)
            try:
                request_llm = self._llm_for_request(user_email)
                chain_before_parser = prompt_template | request_llm
                async for chunk in chain_before_parser.astream(input_data, config=config):
                    # Capture usage_metadata from AIMessage (only once - first chunk with tokens)
                    if isinstance(chunk, AIMessage):
                        # Capture usage_metadata if not captured yet
                        if (
                            not usage_metadata_captured
                            and hasattr(chunk, "usage_metadata")
                            and chunk.usage_metadata
                        ):
                            usage_metadata_captured, usage_metadata = (
                                self._capture_metadata(chunk, "stream_simple")
                            )
                            runtime_metadata = self._extract_runtime_metadata(chunk)
                        # Always yield the text content
                        if chunk.content:
                            if isinstance(chunk.content, str):
                                yield chunk.content
                            elif isinstance(chunk.content, list):
                                for block in chunk.content:
                                    if isinstance(block, str):
                                        yield block
                                    elif isinstance(block, dict) and "text" in block:
                                        yield block["text"]
                    elif isinstance(chunk, str):
                        yield chunk
            except (AttributeError, TypeError):
                # Fallback: use full chain with parser if direct LLM stream fails
                chain = prompt_template | self._llm | StrOutputParser()
                async for chunk in chain.astream(input_data, config=config):
                    yield chunk
        except (ValueError, TypeError, AttributeError, Exception) as e:  # pylint: disable=broad-exception-caught
            logger.error("Error in stream_simple: %s", e)
            yield self.get_user_facing_error_message(input_data.get("user_locale"))
        finally:
            # Log prompt at the END of streaming
            duration_ms = int((time.time() - start_time) * 1000)
            try:
                merge_runtime_metadata(
                    config,
                    {
                        "duration_ms": duration_ms,
                        "requested_model": self.model_name,
                        "resolved_model": runtime_metadata.get("resolved_model", self.model_name),
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
                    log_callback(
                        user_email,
                        {
                            "prompt": prompt_str,
                            "prompt_name": "resumo",
                            "type": "simple",
                            "tokens_input": usage_metadata.get("input_tokens", 0),
                            "tokens_output": usage_metadata.get("output_tokens", 0),
                            "duration_ms": duration_ms,
                            "model": self.model_name,
                            "requested_model": self.model_name,
                            "resolved_model": runtime_metadata.get(
                                "resolved_model", self.model_name
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
                    logger.warning("Failed to log prompt in stream_simple: %s", log_err)

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

    def __init__(
        self,
        api_key: str,
        model: str,
        preset: str | None,
        base_url: str,
    ):
        """Initialize OpenRouter client through OpenAI-compatible API."""
        from langchain_openai import ChatOpenAI  # pylint: disable=import-outside-toplevel
        from pydantic import SecretStr  # pylint: disable=import-outside-toplevel

        self.model_name = model
        self._api_key = api_key
        self._base_url = base_url
        self._preset = preset
        self._llm = ChatOpenAI(
            model=model,
            base_url=base_url,
            api_key=SecretStr(api_key) if api_key else SecretStr(""),
            extra_body={"preset": preset} if preset else None,
        )

    def _llm_for_node(
        self,
        model_override: str | None = None,
    ):
        """Return an OpenRouter client for a specific graph node."""
        from langchain_openai import ChatOpenAI  # pylint: disable=import-outside-toplevel
        from pydantic import SecretStr  # pylint: disable=import-outside-toplevel

        model = model_override or self.model_name
        if not model:
            raise ValueError("OpenRouter node model is not configured")
        if model.startswith("@preset/"):
            raise ValueError("OpenRouter node model must not be a preset slug")
        return ChatOpenAI(
            model=model,
            base_url=self._base_url,
            api_key=SecretStr(self._api_key) if self._api_key else SecretStr(""),
            extra_body={"preset": self._preset} if self._preset else None,
        )
