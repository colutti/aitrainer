import unittest
import asyncio
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from src.services.llm_client import LLMClient, OpenRouterClient
from langchain_core.messages import AIMessage


class _TestLLMClient(LLMClient):
    """Test subclass that returns a mock LLM from _llm_for_node."""
    def __init__(self):
        super().__init__()
        self.mock_llm = MagicMock()

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
        llm = self.mock_llm
        if user_email:
            llm = llm.bind(user=user_email)
        return llm


class TestLLMClient(unittest.IsolatedAsyncioTestCase):



    @patch("src.services.llm_client.create_agent")
    async def test_stream_with_tools_binds_openrouter_user(self, mock_create_agent):
        """stream_with_tools should bind `user` before building the agent."""
        client = _TestLLMClient()

        bound_llm = MagicMock()
        client.mock_llm.bind.return_value = bound_llm

        mock_agent = MagicMock()
        mock_create_agent.return_value = mock_agent

        async def mock_astream(*args, **kwargs):
            yield (AIMessage(content="Hello"), "meta")

        mock_agent.astream = mock_astream

        prompt = MagicMock()
        prompt.format_messages.return_value = []
        prompt.format.return_value = "prompt"

        results = []
        async for chunk in client.stream_with_tools(
            prompt, {}, [], model_override="test-model", user_email="user@test.com"
        ):
            results.append(chunk)

        client.mock_llm.bind.assert_called_once_with(user="user@test.com")
        self.assertEqual(results[0], "Hello")

    @patch("src.services.llm_client.create_agent")
    async def test_stream_with_tools_passes_runnable_config(self, mock_create_agent):
        """stream_with_tools should pass tracing-friendly RunnableConfig to agent."""
        client = _TestLLMClient()

        mock_agent = MagicMock()
        captured = {}

        async def mock_astream(*args, **kwargs):
            captured["config"] = kwargs.get("config")
            yield (AIMessage(content="Hello"), "meta")

        mock_agent.astream = mock_astream
        mock_create_agent.return_value = mock_agent

        prompt = MagicMock()
        prompt.format_messages.return_value = []
        prompt.format.return_value = "prompt"

        with patch("src.services.llm_client.build_runnable_config") as build_config:
            build_config.return_value = {"run_name": "chat.tools", "metadata": {}, "recursion_limit": 20}
            results = []
            async for chunk in client.stream_with_tools(prompt, {}, [], model_override="test-model"):
                results.append(chunk)

        self.assertEqual(captured["config"]["run_name"], "chat.tools")
        self.assertEqual(results[0], "Hello")



    @patch("src.services.llm_client.create_agent")
    async def test_stream_with_tools_success(self, mock_create_agent):
        """Test streaming with tool support."""
        client = _TestLLMClient()

        mock_agent = MagicMock()
        mock_create_agent.return_value = mock_agent

        # Mock astream yield
        async def mock_astream(*args, **kwargs):
            msg = AIMessage(content="Hello")
            yield (msg, "meta")

        mock_agent.astream = mock_astream

        prompt = MagicMock()
        prompt.format_messages.return_value = []

        results = []
        async for chunk in client.stream_with_tools(prompt, {}, [], model_override="test-model"):
            results.append(chunk)

        # Should contain the message and the tools_summary at the end
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0], "Hello")
        self.assertIsInstance(results[1], dict)
        self.assertEqual(results[1].get("type"), "tools_summary")
        self.assertEqual(results[1].get("tools_called"), [])

    @patch("src.services.llm_client.create_agent")
    async def test_stream_with_tools_error(self, mock_create_agent):
        """Test error handling in tools stream."""
        client = _TestLLMClient()
        mock_create_agent.side_effect = Exception("Agent Error")

        prompt = MagicMock()

        results = []
        async for chunk in client.stream_with_tools(prompt, {}, [], model_override="test-model"):
            results.append(chunk)

        self.assertEqual(
            results[0], client.USER_FACING_ERROR_MESSAGES["pt-BR"]
        )
        self.assertNotIn("Agent Error", results[0])

    @patch("src.services.llm_client.create_agent")
    @patch("src.core.config.settings")
    async def test_stream_with_tools_inactivity_timeout(
        self, mock_settings, mock_create_agent
    ):
        """Stream must fail fast when no events are produced for too long."""
        client = _TestLLMClient()

        mock_settings.LLM_STREAM_INACTIVITY_TIMEOUT_SECONDS = 0.01

        mock_agent = MagicMock()
        mock_create_agent.return_value = mock_agent

        async def hanging_astream(*args, **kwargs):
            await asyncio.sleep(1)
            if False:
                yield None

        mock_agent.astream = hanging_astream

        prompt = MagicMock()
        prompt.format_messages.return_value = []
        prompt.format.return_value = "prompt"

        results = []
        async for chunk in client.stream_with_tools(prompt, {}, [], model_override="test-model"):
            results.append(chunk)

        self.assertGreaterEqual(len(results), 1)
        self.assertEqual(
            results[0], client.USER_FACING_ERROR_MESSAGES["pt-BR"]
        )
        self.assertTrue(any(isinstance(item, dict) for item in results))

    @patch("src.services.llm_client.create_agent")
    async def test_stream_with_tools_error_is_localized_en_us(self, mock_create_agent):
        """Error message should be localized when user_locale is en-US."""
        client = _TestLLMClient()
        mock_create_agent.side_effect = Exception("Agent Error")
        prompt = MagicMock()

        results = []
        async for chunk in client.stream_with_tools(
            prompt, {"user_locale": "en-US"}, [], model_override="test-model"
        ):
            results.append(chunk)

        self.assertEqual(results[0], client.USER_FACING_ERROR_MESSAGES["en-US"])
        self.assertNotIn("Agent Error", results[0])

    @patch("src.services.llm_client.create_agent")
    async def test_stream_with_tools_error_is_localized_es_es(self, mock_create_agent):
        """Error message should be localized when user_locale is es-ES."""
        client = _TestLLMClient()
        mock_create_agent.side_effect = Exception("Agent Error")
        prompt = MagicMock()

        results = []
        async for chunk in client.stream_with_tools(
            prompt, {"user_locale": "es-ES"}, [], model_override="test-model"
        ):
            results.append(chunk)

        self.assertEqual(results[0], client.USER_FACING_ERROR_MESSAGES["es-ES"])
        self.assertNotIn("Agent Error", results[0])

    def test_openrouter_init(self):
        """Test OpenRouter client initialization."""
        with patch("langchain_openai.ChatOpenAI") as mock_cls:
            client = OpenRouterClient(
                api_key="or-key",
                base_url="https://openrouter.ai/api/v1",
            )
            client._llm_for_node(
                model_override="google/gemini-2.5-flash-lite",
                user_email="test@test.com",
                temperature=0.5,
            )
            mock_cls.assert_called_once()
            kwargs = mock_cls.call_args.kwargs
            self.assertEqual(kwargs["model"], "google/gemini-2.5-flash-lite")
            self.assertEqual(kwargs["base_url"], "https://openrouter.ai/api/v1")
            self.assertEqual(kwargs["temperature"], 0.5)

    def test_openrouter_receives_max_tokens_reasoning_and_parallel_tool_calls(self):
        """OpenRouter client must accept max_tokens, reasoning, parallel_tool_calls."""
        with patch("langchain_openai.ChatOpenAI") as mock_cls:
            client = OpenRouterClient(
                api_key="or-key",
                base_url="https://openrouter.ai/api/v1",
            )
            client._llm_for_node(
                model_override="google/gemini-3-flash-preview",
                user_email="test@test.com",
                temperature=0.2,
                max_tokens=6144,
                reasoning={"effort": "low", "exclude": True},
                parallel_tool_calls=False,
            )
            mock_cls.assert_called_once()
            kwargs = mock_cls.call_args.kwargs
            self.assertEqual(kwargs["model"], "google/gemini-3-flash-preview")
            self.assertEqual(kwargs["temperature"], 0.2)
            self.assertEqual(kwargs.get("max_tokens"), 6144)
            self.assertEqual(kwargs.get("reasoning"), {"effort": "low", "exclude": True})
            model_kw = kwargs.get("model_kwargs", {})
            self.assertIsNotNone(model_kw)
            self.assertEqual(model_kw.get("parallel_tool_calls"), False)

    @patch("src.services.llm_client.create_agent")
    async def test_stream_with_tools_passes_response_format(self, mock_create_agent):
        """stream_with_tools should pass response_format to create_agent."""
        client = _TestLLMClient()
        mock_agent = MagicMock()
        mock_create_agent.return_value = mock_agent

        async def mock_astream(*args, **kwargs):
            yield (AIMessage(content="Hello"), "meta")

        mock_agent.astream = mock_astream
        prompt = MagicMock()
        prompt.format_messages.return_value = []

        results = []
        async for chunk in client.stream_with_tools(
            prompt, {}, [], model_override="test-model",
            response_format={"type": "json_schema", "json_schema": {"name": "test", "strict": True, "schema": {"type": "object"}}},
        ):
            results.append(chunk)

        mock_create_agent.assert_called_once()
        _, call_kwargs = mock_create_agent.call_args
        self.assertIn("response_format", call_kwargs)
        self.assertEqual(call_kwargs["response_format"]["type"], "json_schema")

    @patch("src.services.llm_client.create_agent")
    async def test_stream_with_tools_uses_structured_response_from_ainvoke(self, mock_create_agent):
        """When response_format is provided, structured_response must be returned."""
        client = _TestLLMClient()
        mock_agent = MagicMock()
        mock_agent.ainvoke = AsyncMock(
            return_value={
                "messages": [AIMessage(content="")],
                "structured_response": {"status": "ok"},
            }
        )
        mock_create_agent.return_value = mock_agent

        prompt = MagicMock()
        prompt.format_messages.return_value = []

        results = []
        async for chunk in client.stream_with_tools(
            prompt,
            {},
            [],
            model_override="test-model",
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "test",
                    "strict": True,
                    "schema": {"type": "object"},
                },
            },
        ):
            results.append(chunk)

        mock_agent.ainvoke.assert_called_once()
        self.assertEqual(results[0], '{"status": "ok"}')


if __name__ == "__main__":
    unittest.main()
