"""
LLM Client abstraction layer for AI trainer.
Provides a unified interface for different LLM providers (Gemini, Ollama, OpenAI).
"""

from typing import Generator
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import AIMessage, ToolMessage

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
        Invokes the LLM with tool support and yields response chunks.
        Implements full agent loop - executes tools and sends results back to model.
        """
        logger.info(
            "Invoking LLM with tools for input: %s", input_data.get("user_message")
        )

        try:
            llm_with_tools = self._llm.bind_tools(tools)
            messages = list(prompt_template.format_messages(**input_data))

            for iteration in range(1, 4):  # max 3 iterations
                logger.debug("Agent loop iteration %d", iteration)

                content_chunks, tool_calls = yield from self._stream_and_collect(
                    llm_with_tools, messages
                )

                if not tool_calls:
                    logger.debug("No tool calls, agent loop complete")
                    break

                self._process_tool_calls(messages, content_chunks, tool_calls, tools)
                logger.info("Continuing agent loop with tool results")

        except Exception as e:
            logger.error("Error in stream_with_tools: %s", e)
            yield f"Error processing request: {str(e)}"

    def _stream_and_collect(
        self, llm_with_tools, messages: list
    ) -> Generator[str, None, tuple[list[str], list[dict]]]:
        """
        Streams LLM response, yields content chunks, and collects tool calls.
        Handles incremental tool call arguments from OpenAI streaming.
        
        Returns:
            Tuple of (accumulated_content, tool_calls)
        """
        import json
        
        accumulated_content = []
        tool_calls_by_index = {}  # Use index for accumulation (not id, as id comes late)

        for chunk in llm_with_tools.stream(messages):
            # Yield text content
            if hasattr(chunk, "content") and chunk.content:
                for text in self._extract_text_from_content(chunk.content):
                    accumulated_content.append(text)
                    yield text

            # Collect and merge tool calls - handle streaming format
            if hasattr(chunk, "tool_call_chunks") and chunk.tool_call_chunks:
                # OpenAI streaming uses tool_call_chunks
                for tc_chunk in chunk.tool_call_chunks:
                    idx = tc_chunk.get("index", 0)
                    if idx not in tool_calls_by_index:
                        tool_calls_by_index[idx] = {
                            "id": tc_chunk.get("id", ""),
                            "name": tc_chunk.get("name", ""),
                            "args_str": tc_chunk.get("args", ""),
                            "type": "tool_call",
                        }
                    else:
                        existing = tool_calls_by_index[idx]
                        if tc_chunk.get("id"):
                            existing["id"] = tc_chunk["id"]
                        if tc_chunk.get("name"):
                            existing["name"] = tc_chunk["name"]
                        if tc_chunk.get("args"):
                            existing["args_str"] += tc_chunk["args"]
            
            elif hasattr(chunk, "tool_calls") and chunk.tool_calls:
                # Fallback for complete tool_calls
                for i, tc in enumerate(chunk.tool_calls):
                    if isinstance(tc, dict):
                        tc_id = tc.get("id")
                        tc_name = tc.get("name", "")
                        tc_args = tc.get("args", {})
                    else:
                        tc_id = getattr(tc, "id", None)
                        tc_name = getattr(tc, "name", "")
                        tc_args = getattr(tc, "args", {})
                    
                    if tc_id and i not in tool_calls_by_index:
                        tool_calls_by_index[i] = {
                            "id": tc_id,
                            "name": tc_name,
                            "args": dict(tc_args) if tc_args else {},
                            "type": "tool_call",
                        }

        # Parse accumulated JSON args
        result = []
        for tc in tool_calls_by_index.values():
            if "args_str" in tc:
                try:
                    tc["args"] = json.loads(tc["args_str"]) if tc["args_str"] else {}
                except json.JSONDecodeError:
                    logger.warning("Failed to parse tool args: %s", tc["args_str"])
                    tc["args"] = {}
                del tc["args_str"]
            result.append(tc)

        return accumulated_content, result

    def _extract_text_from_content(self, content) -> Generator[str, None, None]:
        """Extracts text strings from various content formats."""
        if isinstance(content, str):
            yield content
        elif isinstance(content, list):
            for part in content:
                if isinstance(part, str):
                    yield part
                elif hasattr(part, "text"):
                    yield part.text

    def _process_tool_calls(
        self, messages: list, content_chunks: list[str], tool_calls: list, tools: list
    ) -> None:
        """Executes tool calls and adds results to message history."""
        # Filter out invalid tool calls (OpenAI sometimes returns empty ones)
        valid_tool_calls = [
            tc for tc in tool_calls
            if tc.get("id") and tc.get("name")
        ]
        
        if not valid_tool_calls:
            logger.warning("No valid tool calls found after filtering")
            return
            
        logger.info("Tool calls detected: %s", valid_tool_calls)

        # Add AI message with tool calls
        ai_message = AIMessage(content="".join(content_chunks), tool_calls=valid_tool_calls)
        messages.append(ai_message)

        # Execute each tool and add result
        for tool_call in valid_tool_calls:
            result = self._execute_tool_call(tool_call, tools)
            messages.append(
                ToolMessage(
                    content=result or "Tool executed successfully",
                    tool_call_id=tool_call["id"],
                )
            )
            logger.debug("Added tool result: %s", result[:100] if result else "None")

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

    def _execute_tool_call(self, tool_call: dict, tools: list) -> str:
        """
        Executes a tool call from the LLM and returns the result.

        Args:
            tool_call: The tool call dict with 'name' and 'args'.
            tools: List of available tools.

        Returns:
            The result string from executing the tool.
        """
        try:
            tool_name = tool_call.get("name")
            tool_args = tool_call.get("args", {})

            logger.info("Executing tool: %s with args: %s", tool_name, tool_args)

            for tool in tools:
                if tool.name == tool_name:
                    result = tool.invoke(tool_args)
                    logger.info("Tool %s returned: %s", tool_name, result)
                    return result

            logger.warning("Tool %s not found", tool_name)
            return f"Tool {tool_name} not found"

        except Exception as e:
            logger.error("Failed to execute tool %s: %s", tool_call.get("name"), e)
            return f"Error executing tool: {str(e)}"


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
