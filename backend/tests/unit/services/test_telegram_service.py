
import unittest
from unittest.mock import MagicMock, AsyncMock, patch
from src.services.telegram_service import TelegramBotService

class TestTelegramService(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.mock_repo = MagicMock()
        self.mock_brain = MagicMock()
        self.mock_token = "TEST_TOKEN"
        
        # We need to patch 'src.services.telegram_service.Bot' class
        # But since we instantiate it in __init__, we do it in each test or setup
        # Easier to patch the class method or just Mock the instance attribute after init?
        # Better: Patch the class so __init__ returns our mock
        pass

    async def asyncSetUp(self):
        # Async setup for async mocks
        pass

    @patch("src.services.telegram_service.Bot")
    @patch("src.services.telegram_service.Update")
    async def test_handle_start(self, MockUpdate, MockBot):
        # Setup Bot Mock
        mock_bot_instance = MockBot.return_value
        mock_bot_instance.send_message = AsyncMock()
        
        service = TelegramBotService(self.mock_token, self.mock_repo, self.mock_brain)
        
        # Setup Update Mock
        mock_update = MagicMock()
        mock_update.message.text = "/start"
        mock_update.effective_chat.id = 12345
        MockUpdate.de_json.return_value = mock_update
        
        await service.handle_update({})
        
        mock_bot_instance.send_message.assert_called_once()
        args, kwargs = mock_bot_instance.send_message.call_args
        self.assertEqual(kwargs['chat_id'], 12345)
        self.assertIn("AI Trainer", kwargs['text'])

    @patch("src.services.telegram_service.Bot")
    @patch("src.services.telegram_service.Update")
    async def test_handle_vincular_success(self, MockUpdate, MockBot):
        mock_bot_instance = MockBot.return_value
        mock_bot_instance.send_message = AsyncMock()
        service = TelegramBotService(self.mock_token, self.mock_repo, self.mock_brain)
        
        mock_update = MagicMock()
        mock_update.message.text = "/vincular ABC12"
        mock_update.effective_chat.id = 12345
        mock_update.effective_user.username = "user1"
        MockUpdate.de_json.return_value = mock_update
        
        # Mock Repo success
        self.mock_repo.validate_and_consume_code.return_value = "user@test.com"
        
        await service.handle_update({})
        
        self.mock_repo.validate_and_consume_code.assert_called_with("ABC12", 12345, "user1")
        mock_bot_instance.send_message.assert_called_with(
            chat_id=12345,
            text="✅ Conta vinculada com sucesso!\n\nAgora você pode conversar com a IA diretamente aqui."
        )

    @patch("src.services.telegram_service.Bot")
    @patch("src.services.telegram_service.Update")
    async def test_handle_vincular_invalid(self, MockUpdate, MockBot):
        mock_bot_instance = MockBot.return_value
        mock_bot_instance.send_message = AsyncMock()
        service = TelegramBotService(self.mock_token, self.mock_repo, self.mock_brain)
        
        mock_update = MagicMock()
        mock_update.message.text = "/vincular BADCODE"
        mock_update.effective_chat.id = 12345
        MockUpdate.de_json.return_value = mock_update
        
        # Mock Repo fail
        self.mock_repo.validate_and_consume_code.return_value = None
        
        await service.handle_update({})
        
        mock_bot_instance.send_message.assert_called()
        args, kwargs = mock_bot_instance.send_message.call_args
        self.assertIn("Código inválido", kwargs['text'])

    @patch("src.services.telegram_service.Bot")
    @patch("src.services.telegram_service.Update")
    async def test_handle_message_not_linked(self, MockUpdate, MockBot):
        mock_bot_instance = MockBot.return_value
        mock_bot_instance.send_message = AsyncMock()
        service = TelegramBotService(self.mock_token, self.mock_repo, self.mock_brain)
        
        mock_update = MagicMock()
        mock_update.message.text = "Hello AI"
        mock_update.effective_chat.id = 12345
        MockUpdate.de_json.return_value = mock_update
        
        # Mock Repo: No link found
        self.mock_repo.get_link_by_chat_id.return_value = None
        
        await service.handle_update({})
        
        mock_bot_instance.send_message.assert_called()
        args, kwargs = mock_bot_instance.send_message.call_args
        self.assertIn("Conta não vinculada", kwargs['text'])

    @patch("src.services.telegram_service.Bot")
    @patch("src.services.telegram_service.Update")
    async def test_handle_message_success(self, MockUpdate, MockBot):
        mock_bot_instance = MockBot.return_value
        mock_bot_instance.send_message = AsyncMock()
        
        # Mock "Processing" message
        mock_processing_msg = MagicMock()
        mock_processing_msg.delete = AsyncMock()
        mock_bot_instance.send_message.return_value = mock_processing_msg
        
        service = TelegramBotService(self.mock_token, self.mock_repo, self.mock_brain)
        
        mock_update = MagicMock()
        mock_update.message.text = "Hello AI"
        mock_update.effective_chat.id = 12345
        MockUpdate.de_json.return_value = mock_update
        
        # Mock Repo: Linked
        mock_link = MagicMock()
        mock_link.user_email = "user@test.com"
        self.mock_repo.get_link_by_chat_id.return_value = mock_link
        
        # Mock Brain
        self.mock_brain.send_message_sync.return_value = "AI Response"
        
        # Patch safe_telegram_send to avoid markdown complexity in test
        with patch("src.services.telegram_service.safe_telegram_send") as mock_safe_send:
            mock_safe_send.return_value = ("AI Response Formatted", "MarkdownV2")
            
            await service.handle_update({})
            
            # 1. Processing message sent
            # 2. AI called
            self.mock_brain.send_message_sync.assert_called_with(
                user_email="user@test.com", user_input="Hello AI", is_telegram=True
            )
            # 3. Response sent
            # Check calls. Should have called send_message twice.
            # First "Processando...", Second "AI Response"
            self.assertEqual(mock_bot_instance.send_message.call_count, 2)
            
            # Check deletion of first message
            mock_processing_msg.delete.assert_called_once()
