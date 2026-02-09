"""
LLM Client abstraction layer for AI trainer.
Provides a unified interface for different LLM providers (Gemini, Ollama, OpenAI).
"""

from typing import Generator
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langchain.agents import create_agent
from langgraph.graph.state import CompiledStateGraph

import warnings

# Suppress Pydantic V1/LangSmith warning as we cannot easily upgrade right now
warnings.filterwarnings("ignore", message=".*Core Pydantic V1 functionality.*")

from src.core.logs import logger  # noqa: E402


class LLMClient:
    """
    Base LLM client with all common logic.
    Children only implement __init__ to create the specific LLM object.
    """

    _llm: BaseChatModel

    @classmethod
    def from_config(cls) -> "LLMClient":
        """
        Factory method that returns the correct LLM client based on settings.AI_PROVIDER.
        Priority: ollama > openai > gemini (default)
        """
        from src.core.config import settings

        if settings.AI_PROVIDER == "ollama":
            logger.info(
                "Creating OllamaClient with model: %s at %s",
                settings.OLLAMA_LLM_MODEL,
                settings.OLLAMA_BASE_URL,
            )
            return OllamaClient(
                base_url=settings.OLLAMA_BASE_URL,
                model=settings.OLLAMA_LLM_MODEL,
                temperature=settings.LLM_TEMPERATURE,
            )

        if settings.AI_PROVIDER == "openai":
            logger.info(
                "Creating OpenAIClient with model: %s", settings.OPENAI_LLM_MODEL
            )
            return OpenAIClient(
                api_key=settings.OPENAI_API_KEY,
                model=settings.OPENAI_LLM_MODEL,
                temperature=settings.LLM_TEMPERATURE,
            )

        # Default: Gemini
        logger.info("Creating GeminiClient with model: %s", settings.GEMINI_LLM_MODEL)
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
    ) -> Generator[str | dict, None, None]:
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

        try:
            # Format initial messages
            messages = list(prompt_template.format_messages(**input_data))

            # V3: Log Prompt if callback provided
            if log_callback and user_email:
                try:
                    prompt_str = prompt_template.format(**input_data)
                    log_callback(user_email, {"prompt": prompt_str, "type": "with_tools"})
                except Exception as log_err:
                    logger.warning("Failed to log prompt in stream_with_tools: %s", log_err)

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

                # V3: Intercept Tool Outputs (System Feedback)
                if isinstance(event, ToolMessage):
                    logger.debug("Intercepted ToolMessage: %s", event.name)
                    tools_called.append(event.name)
                    yield {
                        "type": "tool_result",
                        "content": event.content,
                        "tool_name": event.name,
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

        except Exception as e:
            logger.error("Error in stream_with_tools: %s", e)
            yield f"Error processing request: {str(e)}"
        finally:
            # Yield tools summary at the end to allow caller to make decisions
            yield {"type": "tools_summary", "tools_called": tools_called}

    async def stream_simple(
        self,
        prompt_template,
        input_data: dict,
        user_email: str | None = None,
        log_callback=None,
    ) -> Generator[str, None, None]:
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

        try:
            # V3: Log Prompt if callback provided
            if log_callback and user_email:
                try:
                    prompt_str = prompt_template.format(**input_data)
                    log_callback(user_email, {"prompt": prompt_str, "type": "simple"})
                except Exception as log_err:
                    logger.warning("Failed to log prompt in stream_simple: %s", log_err)

            chain = prompt_template | self._llm | StrOutputParser()
            async for chunk in chain.astream(input_data):
                yield chunk
        except Exception as e:
            logger.error("Error in stream_simple: %s", e)
            yield f"Error processing request: {str(e)}"


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
        from langchain_google_genai import ChatGoogleGenerativeAI

        self._llm = ChatGoogleGenerativeAI(
            model=model,
            google_api_key=api_key or "",
            temperature=temperature,
        )


class OllamaClient(LLMClient):
    """LLM Client for Ollama (local models)."""

    def __init__(self, base_url: str, model: str, temperature: float):
        """Initialize Ollama client."""
        from langchain_ollama import ChatOllama

        self._llm = ChatOllama(
            model=model,
            base_url=base_url,
            temperature=temperature,
        )


class OpenAIClient(LLMClient):
    """LLM Client for OpenAI models."""

    def __init__(self, api_key: str, model: str, temperature: float):
        """Initialize OpenAI client."""
        from langchain_openai import ChatOpenAI
        from pydantic import SecretStr

        self._llm = ChatOpenAI(
            model=model,
            api_key=SecretStr(api_key) if api_key else SecretStr(""),
            temperature=temperature,
        )
