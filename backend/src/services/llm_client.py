"""
LLM Client abstraction layer for AI trainer.
Provides a unified interface for different LLM providers (Gemini, Ollama, OpenAI).
"""

from typing import Generator
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import AIMessage
from langgraph.prebuilt import create_react_agent

import warnings
# Suppress Pydantic V1/LangSmith warning as we cannot easily upgrade right now
warnings.filterwarnings("ignore", message=".*Core Pydantic V1 functionality.*")

from src.core.logs import logger


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
            logger.info("Creating OpenAIClient with model: %s", settings.OPENAI_MODEL_NAME)
            return OpenAIClient(
                api_key=settings.OPENAI_API_KEY,
                model=settings.OPENAI_MODEL_NAME,
                temperature=settings.LLM_TEMPERATURE,
            )

        # Default: Gemini
        logger.info("Creating GeminiClient with model: %s", settings.LLM_MODEL_NAME)
        return GeminiClient(
            api_key=settings.GEMINI_API_KEY,
            model=settings.LLM_MODEL_NAME,
            temperature=settings.LLM_TEMPERATURE,
        )

    def stream_with_tools(
        self, prompt_template, input_data: dict, tools: list
    ) -> Generator[str | tuple[str, bool], None, None]:
        """
        Invokes the LLM with tool support using LangGraph's ReAct agent.
        
        Yields:
            str: Content chunks during streaming
            tuple[str, bool]: Final signal ("", tool_was_called) at the end
        """
        logger.info(
            "Invoking LLM with tools (LangGraph) for input: %s", input_data.get("user_message")
        )

        try:
            # Format initial messages
            messages = list(prompt_template.format_messages(**input_data))

            # Create the ReAct agent
            agent = create_react_agent(self._llm, tools)
            
            # Map tool names to their write status (default False)
            write_tools = {
                t.name: t.extras.get("is_write_operation", False)
                for t in tools
                if hasattr(t, "extras") and t.extras
            }
            
            write_tool_was_called = False

            # Stream the agent execution with increased recursion limit
            # Default is 25, but complex tool chains may need more
            config = {"recursion_limit": 50}
            for event, metadata in agent.stream(
                {"messages": messages},
                stream_mode="messages",
                config=config
            ):
                # Detect tool calls in the stream
                if hasattr(event, 'tool_calls') and event.tool_calls:
                    for tc in event.tool_calls:
                        tool_name = tc.get("name", "")
                        if write_tools.get(tool_name, False):
                            write_tool_was_called = True
                            logger.debug("Write tool call detected: %s", tool_name)
                        else:
                            logger.debug("Read tool call detected (memory ok): %s", tool_name)

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

            # Signal end of stream with write tool usage flag
            yield ("", write_tool_was_called)

        except Exception as e:
            logger.error("Error in stream_with_tools: %s", e)
            yield f"Error processing request: {str(e)}"
            yield ("", False)  # Signal end even on error

    def stream_simple(
        self, prompt_template, input_data: dict
    ) -> Generator[str, None, None]:
        """
        Simple streaming without tools.

        Args:
            prompt_template: The LangChain prompt template to use.
            input_data: Dictionary with input variables for the template.

        Yields:
            Individual chunks of the LLM response content.
        """
        logger.info(
            "Invoking LLM (simple) for input: %s", input_data.get("user_message")
        )

        try:
            chain = prompt_template | self._llm | StrOutputParser()
            for chunk in chain.stream(input_data):
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

        self._llm = ChatOpenAI(
            model=model,
            api_key=api_key,
            temperature=temperature,
        )
