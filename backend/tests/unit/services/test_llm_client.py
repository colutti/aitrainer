import unittest
import asyncio
from unittest.mock import MagicMock, patch
from src.services.llm_client import LLMClient, OpenRouterClient
from langchain_core.messages import AIMessage


class TestLLMClient(unittest.IsolatedAsyncioTestCase):
    @patch("src.core.config.settings")
    def test_factory_openrouter(self, mock_settings):
        """Test creating OpenRouter client via factory."""
        mock_settings.OPENROUTER_CHAT_MODEL = "deepseek/deepseek-v4-flash"
        mock_settings.OPENROUTER_PROMPT_PRESET = ""
        mock_settings.OPENROUTER_API_KEY = "or-test"
        mock_settings.OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

        with patch("src.services.llm_client.OpenRouterClient") as MockOpenRouter:
            client = LLMClient.from_config()
            self.assertIsInstance(client, MagicMock)  # MockOpenRouter return
            MockOpenRouter.assert_called_once_with(
                api_key="or-test",
                model="deepseek/deepseek-v4-flash",
                preset=None,
                base_url="https://openrouter.ai/api/v1",
            )

    async def test_stream_simple_success(self):
        """Test simple streaming success."""
        client = LLMClient()
        client._llm = MagicMock()

        # Mock the chain behavior
        prompt = MagicMock()
        prompt.format.return_value = "test prompt"

        async def mock_stream(*args, **kwargs):
            yield "res"

        # Mock prompt | llm (returns mock_llm)
        mock_llm_chain = MagicMock()
        mock_llm_chain.astream = mock_stream
        prompt.__or__.return_value = mock_llm_chain

        results = []
        async for chunk in client.stream_simple(prompt, {}):
            results.append(chunk)

        self.assertEqual(results, ["res"])

    async def test_stream_simple_with_logging(self):
        """Test simple streaming with log_callback."""
        client = LLMClient()
        client.model_name = "test-model"
        client._llm = MagicMock()

        # Mock the chain behavior
        prompt = MagicMock()
        prompt.format.return_value = "formatted prompt"

        async def mock_stream(*args, **kwargs):
            yield "res"

        # Mock prompt | llm
        mock_llm_chain = MagicMock()
        mock_llm_chain.astream = mock_stream
        prompt.__or__.return_value = mock_llm_chain

        log_callback = MagicMock()
        user_email = "test@test.com"

        results = []
        async for chunk in client.stream_simple(
            prompt, {}, user_email=user_email, log_callback=log_callback
        ):
            results.append(chunk)

        self.assertEqual(results, ["res"])
        # Verify log_callback was called with the correct structure
        log_callback.assert_called_once()
        call_args = log_callback.call_args
        logged_data = call_args[0][1]
        self.assertEqual(logged_data["prompt"], "formatted prompt")
        self.assertEqual(logged_data["type"], "simple")
        self.assertEqual(logged_data["model"], "test-model")

    async def test_stream_simple_captures_token_usage(self):
        """Test that stream_simple captures token usage from LLM metadata."""
        client = LLMClient()
        client.model_name = "test-model"

        # Create a mock AIMessage with usage_metadata
        ai_msg = AIMessage(
            content="response text",
            usage_metadata={"input_tokens": 10, "output_tokens": 5, "total_tokens": 15}
        )

        # Mock the LLM to return AIMessage with metadata
        async def mock_llm_stream(*args, **kwargs):
            yield ai_msg

        mock_llm = MagicMock()
        mock_llm.astream = mock_llm_stream
        client._llm = mock_llm

        # Mock the prompt template
        prompt = MagicMock()
        prompt.format.return_value = "formatted prompt"

        # Mock pipe operator to return the LLM (skip StrOutputParser for this test)
        prompt.__or__.return_value = mock_llm

        log_callback = MagicMock()
        user_email = "test@test.com"

        results = []
        async for chunk in client.stream_simple(
            prompt, {}, user_email=user_email, log_callback=log_callback
        ):
            results.append(chunk)

        # Verify callback was called with token data
        log_callback.assert_called_once()
        call_args = log_callback.call_args
        logged_data = call_args[0][1]  # Second argument to log_callback

        # THIS IS THE KEY TEST: tokens should be > 0
        self.assertGreater(logged_data["tokens_input"], 0,
                          "stream_simple should capture tokens_input from LLM metadata")
        self.assertGreater(logged_data["tokens_output"], 0,
                          "stream_simple should capture tokens_output from LLM metadata")

    async def test_stream_simple_captures_only_first_valid_tokens(self):
        """Test that stream_simple captures tokens only ONCE (from first chunk with valid tokens).

        Bug: Multiple chunks arrive with usage_metadata, and we must capture only the first one
        with tokens > 0, not the last one. This prevents tokens from being overwritten with
        later chunks that have 0 input tokens.
        """
        client = LLMClient()
        client.model_name = "test-model"

        # Simulate multiple chunks like real LLM streaming:
        # 1. First chunk: Full metadata (input=1386, output=2452)
        # 2. Second chunk: Only output (input=0, output=27)
        # 3. Third chunk: Only output (input=0, output=24)
        first_chunk = AIMessage(
            content="response",
            usage_metadata={
                "input_tokens": 1386,
                "output_tokens": 2452,
                "total_tokens": 3838
            }
        )
        second_chunk = AIMessage(
            content=" chunk",
            usage_metadata={
                "input_tokens": 0,
                "output_tokens": 27,
                "total_tokens": 27
            }
        )
        third_chunk = AIMessage(
            content=" more",
            usage_metadata={
                "input_tokens": 0,
                "output_tokens": 24,
                "total_tokens": 24
            }
        )

        # Mock the LLM to return multiple chunks
        async def mock_llm_stream(*args, **kwargs):
            yield first_chunk
            yield second_chunk
            yield third_chunk

        mock_llm = MagicMock()
        mock_llm.astream = mock_llm_stream
        client._llm = mock_llm

        # Mock the prompt template
        prompt = MagicMock()
        prompt.format.return_value = "formatted prompt"
        prompt.__or__.return_value = mock_llm

        log_callback = MagicMock()
        user_email = "test@test.com"

        results = []
        async for chunk in client.stream_simple(
            prompt, {}, user_email=user_email, log_callback=log_callback
        ):
            results.append(chunk)

        # Verify callback was called
        log_callback.assert_called_once()
        call_args = log_callback.call_args
        logged_data = call_args[0][1]

        # BUG TEST: Should capture FIRST chunk tokens (1386/2452), not LAST chunk (0/24)
        self.assertEqual(logged_data["tokens_input"], 1386,
                        "Should capture tokens from FIRST chunk with valid tokens, not last chunk")
        self.assertEqual(logged_data["tokens_output"], 2452,
                        "Should capture tokens from FIRST chunk with valid tokens, not last chunk")

    async def test_stream_simple_binds_openrouter_user(self):
        """stream_simple should bind `user` so OpenRouter can track per-user costs."""
        client = LLMClient()
        client._llm = MagicMock()

        bound_llm = MagicMock()
        bound_llm.astream = MagicMock()

        async def mock_bound_stream(*args, **kwargs):
            yield "ok"

        bound_llm.astream = mock_bound_stream
        client._llm.bind.return_value = bound_llm

        prompt = MagicMock()
        prompt.format.return_value = "formatted prompt"
        prompt.__or__.return_value = bound_llm

        results = []
        async for chunk in client.stream_simple(
            prompt, {}, user_email="user@test.com"
        ):
            results.append(chunk)

        client._llm.bind.assert_called_once_with(user="user@test.com")
        self.assertEqual(results, ["ok"])

    async def test_stream_simple_passes_runnable_config(self):
        """stream_simple should pass tracing-friendly RunnableConfig to astream."""
        client = LLMClient()
        client._llm = MagicMock()

        mock_chain = MagicMock()
        captured = {}

        async def mock_stream(*args, **kwargs):
            captured["config"] = kwargs.get("config")
            yield "ok"

        mock_chain.astream = mock_stream
        prompt = MagicMock()
        prompt.format.return_value = "formatted prompt"
        prompt.__or__.return_value = mock_chain

        with patch("src.services.llm_client.build_runnable_config") as build_config:
            build_config.return_value = {"run_name": "chat.simple", "metadata": {}}
            results = []
            async for chunk in client.stream_simple(prompt, {}, user_email="u@test.com"):
                results.append(chunk)

        self.assertEqual(results, ["ok"])
        self.assertEqual(captured["config"]["run_name"], "chat.simple")

    @patch("src.services.llm_client.create_agent")
    async def test_stream_with_tools_binds_openrouter_user(self, mock_create_agent):
        """stream_with_tools should bind `user` before building the agent."""
        client = LLMClient()
        client._llm = MagicMock()

        bound_llm = MagicMock()
        client._llm.bind.return_value = bound_llm

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
            prompt, {}, [], user_email="user@test.com"
        ):
            results.append(chunk)

        client._llm.bind.assert_called_once_with(user="user@test.com")
        self.assertEqual(results[0], "Hello")

    @patch("src.services.llm_client.create_agent")
    async def test_stream_with_tools_passes_runnable_config(self, mock_create_agent):
        """stream_with_tools should pass tracing-friendly RunnableConfig to agent."""
        client = LLMClient()
        client._llm = MagicMock()

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
            async for chunk in client.stream_with_tools(prompt, {}, []):
                results.append(chunk)

        self.assertEqual(captured["config"]["run_name"], "chat.tools")
        self.assertEqual(results[0], "Hello")

    async def test_stream_simple_tracing_metadata_failure_is_fail_open(self):
        """Metadata merge failures must not break stream_simple response."""
        client = LLMClient()
        client._llm = MagicMock()

        mock_chain = MagicMock()

        async def mock_stream(*args, **kwargs):
            yield "ok"

        mock_chain.astream = mock_stream
        prompt = MagicMock()
        prompt.format.return_value = "formatted prompt"
        prompt.__or__.return_value = mock_chain

        with patch("src.services.llm_client.merge_runtime_metadata", side_effect=ValueError("boom")):
            results = []
            async for chunk in client.stream_simple(prompt, {}, user_email="u@test.com"):
                results.append(chunk)

        self.assertEqual(results, ["ok"])

    async def test_stream_simple_without_user_does_not_bind(self):
        """stream_simple should preserve legacy behavior when no user email is provided."""
        client = LLMClient()
        client._llm = MagicMock()

        async def mock_stream(*args, **kwargs):
            yield "res"

        mock_llm_chain = MagicMock()
        mock_llm_chain.astream = mock_stream
        prompt = MagicMock()
        prompt.format.return_value = "test prompt"
        prompt.__or__.return_value = mock_llm_chain

        results = []
        async for chunk in client.stream_simple(prompt, {}):
            results.append(chunk)

        client._llm.bind.assert_not_called()
        self.assertEqual(results, ["res"])

    @patch("src.services.llm_client.create_agent")
    async def test_stream_with_tools_success(self, mock_create_agent):
        """Test streaming with tool support."""
        client = LLMClient()
        client._llm = MagicMock()

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
        async for chunk in client.stream_with_tools(prompt, {}, []):
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
        client = LLMClient()
        mock_create_agent.side_effect = Exception("Agent Error")

        prompt = MagicMock()

        results = []
        async for chunk in client.stream_with_tools(prompt, {}, []):
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
        client = LLMClient()
        client._llm = MagicMock()

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
        async for chunk in client.stream_with_tools(prompt, {}, []):
            results.append(chunk)

        self.assertGreaterEqual(len(results), 1)
        self.assertEqual(
            results[0], client.USER_FACING_ERROR_MESSAGES["pt-BR"]
        )
        self.assertTrue(any(isinstance(item, dict) for item in results))

    @patch("src.services.llm_client.create_agent")
    async def test_stream_with_tools_error_is_localized_en_us(self, mock_create_agent):
        """Error message should be localized when user_locale is en-US."""
        client = LLMClient()
        mock_create_agent.side_effect = Exception("Agent Error")
        prompt = MagicMock()

        results = []
        async for chunk in client.stream_with_tools(
            prompt, {"user_locale": "en-US"}, []
        ):
            results.append(chunk)

        self.assertEqual(results[0], client.USER_FACING_ERROR_MESSAGES["en-US"])
        self.assertNotIn("Agent Error", results[0])

    @patch("src.services.llm_client.create_agent")
    async def test_stream_with_tools_error_is_localized_es_es(self, mock_create_agent):
        """Error message should be localized when user_locale is es-ES."""
        client = LLMClient()
        mock_create_agent.side_effect = Exception("Agent Error")
        prompt = MagicMock()

        results = []
        async for chunk in client.stream_with_tools(
            prompt, {"user_locale": "es-ES"}, []
        ):
            results.append(chunk)

        self.assertEqual(results[0], client.USER_FACING_ERROR_MESSAGES["es-ES"])
        self.assertNotIn("Agent Error", results[0])

    def test_openrouter_init(self):
        """Test OpenRouter client initialization."""
        with patch("langchain_openai.ChatOpenAI") as mock_cls:
            OpenRouterClient(
                api_key="or-key",
                model="@preset/fityq-chat",
                preset="@preset/fityq-chat",
                base_url="https://openrouter.ai/api/v1",
            )
            mock_cls.assert_called_once()
            kwargs = mock_cls.call_args.kwargs
            self.assertEqual(kwargs["model"], "@preset/fityq-chat")
            self.assertEqual(kwargs["base_url"], "https://openrouter.ai/api/v1")
            self.assertIn("api_key", kwargs)
            self.assertEqual(kwargs["extra_body"], {"preset": "@preset/fityq-chat"})

    def test_openrouter_auto_router_has_no_preset_payload(self):
        """OpenRouter client should not forward preset via extra_body."""
        with patch("langchain_openai.ChatOpenAI") as mock_cls:
            OpenRouterClient(
                api_key="or-key",
                model="deepseek/deepseek-v4-flash",
                preset=None,
                base_url="https://openrouter.ai/api/v1",
            )
            mock_cls.assert_called_once()
            kwargs = mock_cls.call_args.kwargs
            self.assertEqual(kwargs["model"], "deepseek/deepseek-v4-flash")
            self.assertEqual(kwargs["base_url"], "https://openrouter.ai/api/v1")
            self.assertIn("api_key", kwargs)
            self.assertEqual(kwargs["extra_body"], None)

    def test_factory_rejects_preset_as_model(self):
        """Preset-style model names must be rejected by the factory."""
        with patch("src.core.config.settings") as mock_settings:
            mock_settings.OPENROUTER_CHAT_MODEL = "@preset/fityq-chat-prod"
            mock_settings.OPENROUTER_PROMPT_PRESET = ""
            mock_settings.OPENROUTER_API_KEY = "or-test"
            mock_settings.OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

            with self.assertRaises(ValueError, msg="OPENROUTER_CHAT_MODEL must be a model name, not a preset slug"):
                LLMClient.from_config()


if __name__ == "__main__":
    unittest.main()
