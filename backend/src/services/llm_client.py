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
    ) -> Generator[str, None, None]:
        """
        Invokes the LLM with tool support using LangGraph's ReAct agent.
        """
        logger.info(
            "Invoking LLM with tools (LangGraph) for input: %s", input_data.get("user_message")
        )

        try:
            # Format initial messages
            messages = list(prompt_template.format_messages(**input_data))

            # Create the ReAct agent (CompiledGraph)
            # state_modifier allows us to prepend the system prompt if needed,
            # but since we already formatted messages including system prompt,
            # we can pass them directly as input.
            agent = create_react_agent(self._llm, tools)

            # Stream the agent execution
            # stream_mode="messages" allows us to get the tokens as they are generated
            for event, metadata in agent.stream(
                {"messages": messages},
                stream_mode="messages"
            ):
                # Filter for AIMessageChunks (actual response content)
                # We want to yield content from the agent's final response or intermediate thoughts
                if isinstance(event, AIMessage) and event.content:
                    # Depending on streaming behavior, content might be accumulated or chunks
                    # In 'messages' mode, we get chunks wrapped in message objects usually?
                    # Let's verify behavior. Actually "messages" mode yields full messages or chunks?
                    # "messages" mode in LangGraph yields (message, metadata) tuples.
                    # For streaming tokens, we usually want "updates" or use .astream_events
                    
                    # Correction: agent.stream with stream_mode="messages" yields chunks of messages
                    # as they are generated.
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
