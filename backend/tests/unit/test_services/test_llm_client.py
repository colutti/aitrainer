import unittest
from unittest.mock import MagicMock, patch
from src.services.llm_client import LLMClient, GeminiClient, OllamaClient, OpenAIClient
from langchain_core.messages import AIMessage


class TestLLMClient(unittest.IsolatedAsyncioTestCase):
    @patch("src.core.config.settings")
    def test_factory_gemini(self, mock_settings):
        """Test creating Gemini client via factory."""
        mock_settings.AI_PROVIDER = "gemini"
        mock_settings.LLM_MODEL_NAME = "gemini-1.5-flash"
        mock_settings.GEMINI_API_KEY = "test_key"
        mock_settings.LLM_TEMPERATURE = 0.7

        with patch("src.services.llm_client.GeminiClient") as MockGemini:
            client = LLMClient.from_config()
            self.assertIsInstance(client, MagicMock)  # MockGemini return
            MockGemini.assert_called_once()

    @patch("src.core.config.settings")
    def test_factory_ollama(self, mock_settings):
        """Test creating Ollama client via factory."""
        mock_settings.AI_PROVIDER = "ollama"
        mock_settings.OLLAMA_LLM_MODEL = "llama3"
        mock_settings.OLLAMA_BASE_URL = "http://localhost:11434"
        mock_settings.LLM_TEMPERATURE = 0.7

        with patch("src.services.llm_client.OllamaClient") as MockOllama:
            LLMClient.from_config()
            MockOllama.assert_called_once()

    @patch("src.core.config.settings")
    def test_factory_openai(self, mock_settings):
        """Test creating OpenAI client via factory."""
        mock_settings.AI_PROVIDER = "openai"
        mock_settings.OPENAI_MODEL_NAME = "gpt-4"
        mock_settings.OPENAI_API_KEY = "sk-test"
        mock_settings.LLM_TEMPERATURE = 0.7

        with patch("src.services.llm_client.OpenAIClient") as MockOpenAI:
            LLMClient.from_config()
            MockOpenAI.assert_called_once()

    async def test_stream_simple_success(self):
        """Test simple streaming success."""
        client = LLMClient()
        client._llm = MagicMock()

        # Mock the chain behavior
        prompt = MagicMock()
        
        async def mock_stream(*args, **kwargs):
            yield "res"
            
        prompt.__or__.return_value.__or__.return_value.astream = mock_stream

        results = []
        async for chunk in client.stream_simple(prompt, {}):
            results.append(chunk)
            
        self.assertEqual(results, ["res"])

    async def test_stream_simple_with_logging(self):
        """Test simple streaming with log_callback."""
        client = LLMClient()
        client._llm = MagicMock()

        # Mock the chain behavior
        prompt = MagicMock()
        prompt.format.return_value = "formatted prompt"
        
        async def mock_stream(*args, **kwargs):
            yield "res"
            
        prompt.__or__.return_value.__or__.return_value.astream = mock_stream

        log_callback = MagicMock()
        user_email = "test@test.com"

        results = []
        async for chunk in client.stream_simple(
            prompt, {}, user_email=user_email, log_callback=log_callback
        ):
            results.append(chunk)
            
        self.assertEqual(results, ["res"])
        log_callback.assert_called_once_with(user_email, {"prompt": "formatted prompt", "type": "simple"})

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

        self.assertIn("Error processing request", results[0])

    def test_gemini_init(self):
        """Test Gemini client initialization."""
        with patch("langchain_google_genai.ChatGoogleGenerativeAI") as mock_cls:
            GeminiClient("key", "model", 0.5)
            mock_cls.assert_called_once()

    def test_ollama_init(self):
        """Test Ollama client initialization."""
        with patch("langchain_ollama.ChatOllama") as mock_cls:
            OllamaClient("url", "model", 0.5)
            mock_cls.assert_called_once()

    def test_openai_init(self):
        """Test OpenAI client initialization."""
        with patch("langchain_openai.ChatOpenAI") as mock_cls:
            OpenAIClient("key", "model", 0.5)
            mock_cls.assert_called_once()


if __name__ == "__main__":
    unittest.main()
