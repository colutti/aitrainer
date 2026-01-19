"""Telegram bot service for handling updates."""
from typing import Optional

from telegram import Update, Bot
from telegram.constants import ParseMode
from telegram.error import TelegramError

from src.core.logs import logger
from src.repositories.telegram_repository import TelegramRepository
from src.services.trainer import AITrainerBrain
from src.services.markdown_converter import safe_telegram_send


class TelegramBotService:
    """Service to handle Telegram bot operations."""

    def __init__(
        self,
        token: str,
        repository: TelegramRepository,
        brain: AITrainerBrain
    ):
        self.bot = Bot(token=token)
        self.repository = repository
        self.brain = brain

    async def handle_update(self, update_data: dict) -> None:
        """Process incoming Telegram update."""
        update = Update.de_json(update_data, self.bot)
        
        if not update.message:
            return
        
        text = update.message.text or ""
        chat_id = update.effective_chat.id
        username = update.effective_user.username
        
        if text.startswith("/start"):
            await self._handle_start(chat_id)
        elif text.startswith("/vincular"):
            await self._handle_vincular(chat_id, text, username)
        elif text.startswith("/desvincular"):
            await self._handle_desvincular(chat_id)
        else:
            await self._handle_message(chat_id, text)

    async def _handle_start(self, chat_id: int) -> None:
        """Send welcome message."""
        text = (
            "🏋️ *Bem\\-vindo ao AI Trainer\\!*\n\n"
            "Para vincular sua conta:\n"
            "1\\. Acesse a web app → Integrações → Telegram\n"
            "2\\. Gere um código de vinculação\n"
            "3\\. Envie aqui: `/vincular SEU_CODIGO`\n\n"
            "Após vincular, envie mensagens normalmente para conversar com a IA\\."
        )
        await self.bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode=ParseMode.MARKDOWN_V2
        )

    async def _handle_vincular(
        self, chat_id: int, text: str, username: Optional[str]
    ) -> None:
        """Handle /vincular command."""
        parts = text.split()
        if len(parts) < 2:
            await self.bot.send_message(
                chat_id=chat_id,
                text="⚠️ Use: /vincular SEU_CODIGO"
            )
            return
        
        code = parts[1].strip().upper()
        user_email = self.repository.validate_and_consume_code(
            code, chat_id, username
        )
        
        if user_email:
            await self.bot.send_message(
                chat_id=chat_id,
                text=f"✅ Conta vinculada com sucesso!\n\nAgora você pode conversar com a IA diretamente aqui."
            )
        else:
            await self.bot.send_message(
                chat_id=chat_id,
                text="❌ Código inválido ou expirado. Gere um novo código na web app."
            )

    async def _handle_desvincular(self, chat_id: int) -> None:
        """Handle /desvincular command."""
        link = self.repository.get_link_by_chat_id(chat_id)
        if link:
            self.repository.delete_link(link.user_email)
            await self.bot.send_message(
                chat_id=chat_id,
                text="✅ Conta desvinculada. Use /vincular para conectar novamente."
            )
        else:
            await self.bot.send_message(
                chat_id=chat_id,
                text="⚠️ Nenhuma conta vinculada."
            )

    async def _handle_message(self, chat_id: int, text: str) -> None:
        """Handle regular message - forward to AI."""
        link = self.repository.get_link_by_chat_id(chat_id)
        
        if not link:
            await self.bot.send_message(
                chat_id=chat_id,
                text="⚠️ Conta não vinculada. Use /start para instruções."
            )
            return
        
        # Send "processing" message
        processing_msg = await self.bot.send_message(
            chat_id=chat_id,
            text="⏳ Processando..."
        )
        
        try:
            # Call AI (synchronous version)
            response = self.brain.send_message_sync(
                user_email=link.user_email,
                user_input=text,
                is_telegram=True
            )
            
            # Convert markdown and send
            formatted_text, parse_mode = safe_telegram_send(response)
            
            try:
                await self.bot.send_message(
                    chat_id=chat_id,
                    text=formatted_text,
                    parse_mode=parse_mode
                )
            except TelegramError:
                # Fallback to plain text if formatting fails
                await self.bot.send_message(
                    chat_id=chat_id,
                    text=response
                )
            
            # Delete processing message
            await processing_msg.delete()
            
        except Exception as e:
            logger.error("Error processing Telegram message: %s", e)
            await self.bot.send_message(
                chat_id=chat_id,
                text="❌ Erro ao processar mensagem. Tente novamente."
            )
