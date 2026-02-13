"""
LLM Client abstraction layer for AI trainer.
Provides a unified interface for different LLM providers (Gemini, Ollama, OpenAI).
"""

from typing import AsyncGenerator, Any
import time
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langchain.agents import create_agent
from langgraph.graph.state import CompiledStateGraph

import warnings

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

        tools_called: list[str] = []
        start_time = time.time()
        usage_metadata: dict = {"input_tokens": 0, "output_tokens": 0}
        prompt_str = ""
        usage_metadata_captured = False  # Track if we already captured

        try:
            # Format initial messages
            messages = list(prompt_template.format_messages(**input_data))
            prompt_str = prompt_template.format(**input_data)

            # Create the ReAct agent
            agent: CompiledStateGraph = create_agent(self._llm, tools)

            # Stream the agent execution with increased recursion limit
            # Default is 25, but complex tool chains may need more
            config: RunnableConfig = {"recursion_limit": 50}
            async for item in agent.astream(
                {"messages": messages}, stream_mode="messages", config=config
            ):
                if isinstance(item, tuple) and len(item) == 2:
                    event, _ = item
                else:
                    event = item

                # Capture usage_metadata from AIMessage chunks
                # Only capture ONCE - the first time we see real token values
                if not usage_metadata_captured and isinstance(event, AIMessage):
                    if hasattr(event, "usage_metadata") and event.usage_metadata:
                        # Only capture if this has real token counts (not all zeros)
                        tokens = event.usage_metadata.get("input_tokens", 0) + event.usage_metadata.get("output_tokens", 0)
                        if tokens > 0:
                            usage_metadata = event.usage_metadata
                            usage_metadata_captured = True
                            logger.info(
                                "✓ Captured usage_metadata (FIRST TIME): input=%s, output=%s, total=%s",
                                event.usage_metadata.get("input_tokens", 0),
                                event.usage_metadata.get("output_tokens", 0),
                                tokens
                            )

                # V3: Intercept Tool Outputs (System Feedback)
                if isinstance(event, ToolMessage):
                    tool_name = str(event.name) if event.name else "unknown"
                    logger.debug("Intercepted ToolMessage: %s", tool_name)
                    tools_called.append(tool_name)
                    yield {
                        "type": "tool_result",
                        "content": event.content,
                        "tool_name": tool_name,
                        "tool_call_id": event.tool_call_id,
                    }
                    continue

                # Filter for AIMessageChunks (actual response content)
                if isinstance(event, AIMessage) and event.content:
                    if isinstance(event.content, str):
                        yield event.content
                    elif isinstance(event.content, list):
                        # Handle complex content (e.g. text + tool_calls)
                        for block in event.content:
                            if isinstance(block, str):
                                yield block
                            elif isinstance(block, dict) and "text" in block:
                                yield block["text"]

        except Exception as e:  # pylint: disable=broad-exception-caught
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
                            "type": "with_tools",
                            "tokens_input": tokens_in,
                            "tokens_output": tokens_out,
                            "duration_ms": duration_ms,
                            "model": self.model_name,
                            "status": "success",
                        },
                    )
                except Exception as log_err:  # pylint: disable=broad-exception-caught
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

        try:
            prompt_str = prompt_template.format(**input_data)

            chain = prompt_template | self._llm | StrOutputParser()
            async for chunk in chain.astream(input_data):
                yield chunk
        except Exception as e:  # pylint: disable=broad-exception-caught
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
                            "type": "simple",
                            "tokens_input": 0,  # stream_simple não retorna tokens por padrão
                            "tokens_output": 0,
                            "duration_ms": duration_ms,
                            "model": self.model_name,
                            "status": "success",
                        },
                    )
                except Exception as log_err:  # pylint: disable=broad-exception-caught
                    logger.warning("Failed to log prompt in stream_simple: %s", log_err)


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
