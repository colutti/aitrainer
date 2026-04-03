"""
LLM Client abstraction layer for AI trainer.
Provides a unified interface for different LLM providers (Gemini, Ollama, OpenAI).
"""

import warnings
import time
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


class LLMClient:
    """
    Base LLM client with all common logic.
    Children only implement __init__ to create the specific LLM object.
    """

    _initialized = False
    _llm: Any = None
    model_name: str = ""
    supports_multimodal: bool = True

    @classmethod
    def from_config(cls) -> "LLMClient":
        """
        Factory method that returns the correct LLM client based on settings.AI_PROVIDER.
        Priority: ollama > openai > gemini (default)
        """
        from src.core.config import settings  # pylint: disable=import-outside-toplevel

        if settings.AI_PROVIDER == "ollama":
            if not cls._initialized:
                logger.info(
                    "Creating OllamaClient with model: %s at %s",
                    settings.OLLAMA_LLM_MODEL,
                    settings.OLLAMA_BASE_URL,
                )
                cls._initialized = True
            return OllamaClient(
                base_url=settings.OLLAMA_BASE_URL,
                model=settings.OLLAMA_LLM_MODEL,
                temperature=settings.LLM_TEMPERATURE,
            )

        if settings.AI_PROVIDER == "openai":
            if not cls._initialized:
                logger.info(
                    "Creating OpenAIClient with model: %s", settings.OPENAI_LLM_MODEL
                )
                cls._initialized = True
            return OpenAIClient(
                api_key=settings.OPENAI_API_KEY,
                model=settings.OPENAI_LLM_MODEL,
                temperature=settings.LLM_TEMPERATURE,
            )

        # Default: Gemini
        if not cls._initialized:
            logger.info(
                "Creating GeminiClient with model: %s", settings.GEMINI_LLM_MODEL
            )
            cls._initialized = True
        return GeminiClient(
            api_key=settings.GEMINI_API_KEY,
            model=settings.GEMINI_LLM_MODEL,
            temperature=settings.LLM_TEMPERATURE,
        )

    async def stream_with_tools(
        self,
        prompt_template,
        input_data: dict,
        tools: list,
        user_email: str | None = None,
        log_callback=None,
    ) -> AsyncGenerator[str | dict, None]:
        # pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-locals,too-many-branches

        """
        Invokes the LLM with tool support using LangGraph's ReAct agent.

        Yields:
            str: Content chunks during streaming
            dict: Tool results with type="tool_result"
            dict: Final summary with type="tools_summary"
        """
        logger.info(
            "Invoking LLM with tools (LangGraph) for input: %s",
            input_data.get("user_message"),
        )
        if input_data.get("user_images") and not self.supports_multimodal:
            raise ValueError("IMAGE_INPUT_NOT_SUPPORTED_BY_PROVIDER")

        tools_called: list[str] = []
        start_time = time.time()
        usage_metadata: dict = {"input_tokens": 0, "output_tokens": 0}
        prompt_str = ""
        usage_metadata_captured = False  # Track if we already captured

        messages: list[Any] = []
        try:
            format_input = {
                key: value for key, value in input_data.items() if key != "user_image"
            }
            messages = list(prompt_template.format_messages(**format_input))
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
            prompt_str = prompt_template.format(**input_data)
            agent: Any = create_agent(self._llm, tools)
            config: RunnableConfig = {"recursion_limit": 50}
            async for item in agent.astream(
                {"messages": messages}, stream_mode="messages", config=config
            ):
                event = item[0] if isinstance(item, tuple) and len(item) == 2 else item

                if not usage_metadata_captured and isinstance(event, AIMessage):
                    usage_metadata_captured, usage_metadata = self._capture_metadata(
                        event
                    )

                if isinstance(event, ToolMessage):
                    tools_called.append(str(event.name or "unknown"))
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
            yield f"Error processing request: {str(e)}"
        finally:
            # Log prompt with tokens at the END of streaming
            duration_ms = int((time.time() - start_time) * 1000)
            if log_callback and user_email:
                try:
                    tokens_in = usage_metadata.get("input_tokens", 0)
                    tokens_out = usage_metadata.get("output_tokens", 0)
                    log_callback(
                        user_email,
                        {
                            "prompt": prompt_str,
                            "prompt_name": "chat",
                            "type": "with_tools",
                            "messages": [
                                {"role": msg.type, "content": msg.content}
                                for msg in messages
                            ],
                            "tools": [t.name for t in tools],
                            "tools_called": tools_called,
                            "tokens_input": tokens_in,
                            "tokens_output": tokens_out,
                            "duration_ms": duration_ms,
                            "model": self.model_name,
                            "status": "success",
                        },
                    )
                except (ValueError, TypeError, AttributeError, Exception) as log_err:  # pylint: disable=broad-exception-caught
                    logger.warning(
                        "Failed to log prompt in stream_with_tools: %s", log_err
                    )

            # Yield tools summary at the end to allow caller to make decisions
            yield {"type": "tools_summary", "tools_called": tools_called}

    async def stream_simple(
        self,
        prompt_template,
        input_data: dict,
        user_email: str | None = None,
        log_callback=None,
    ) -> AsyncGenerator[str, None]:
        # pylint: disable=too-many-branches,too-many-locals
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
        usage_metadata_captured = False  # Flag to ensure we capture only once

        try:
            prompt_str = prompt_template.format(**input_data)

            # Try to stream from LLM directly first (to capture usage_metadata)
            try:
                chain_before_parser = prompt_template | self._llm
                async for chunk in chain_before_parser.astream(input_data):
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
                async for chunk in chain.astream(input_data):
                    yield chunk
        except (ValueError, TypeError, AttributeError, Exception) as e:  # pylint: disable=broad-exception-caught
            logger.error("Error in stream_simple: %s", e)
            yield f"Error processing request: {str(e)}"
        finally:
            # Log prompt at the END of streaming
            duration_ms = int((time.time() - start_time) * 1000)
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


# Manual agent loop methods removed (refactoring to LangGraph)


class GeminiClient(LLMClient):
    """LLM Client for Google Gemini."""

    def __init__(self, api_key: str, model: str, temperature: float):
        """
        Initialize Gemini client.

        Args:
            api_key: Google API key for Gemini.
            model: Model name (e.g., 'gemini-1.5-flash').
            temperature: Sampling temperature.
        """
        from langchain_google_genai import ChatGoogleGenerativeAI  # pylint: disable=import-outside-toplevel

        self.model_name = model
        self._llm = ChatGoogleGenerativeAI(
            model=model,
            google_api_key=api_key or "",
            temperature=temperature,
        )


class OllamaClient(LLMClient):
    """LLM Client for Ollama (local models)."""

    def __init__(self, base_url: str, model: str, temperature: float):
        """Initialize Ollama client."""
        from langchain_ollama import ChatOllama  # pylint: disable=import-outside-toplevel

        self.model_name = model
        self.supports_multimodal = False
        self._llm = ChatOllama(
            model=model,
            base_url=base_url,
            temperature=temperature,
        )


class OpenAIClient(LLMClient):
    """LLM Client for OpenAI models."""

    def __init__(self, api_key: str, model: str, temperature: float):
        """Initialize OpenAI client."""
        from langchain_openai import ChatOpenAI  # pylint: disable=import-outside-toplevel
        from pydantic import SecretStr  # pylint: disable=import-outside-toplevel

        self.model_name = model
        self._llm = ChatOpenAI(
            model=model,
            api_key=SecretStr(api_key) if api_key else SecretStr(""),
            temperature=temperature,
        )
