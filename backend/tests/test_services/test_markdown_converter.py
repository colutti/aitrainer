"""Unit tests for markdown converter."""
import pytest
from src.services.markdown_converter import convert_to_telegram_markdown, safe_telegram_send


class TestMarkdownConverter:
    def test_convert_bold(self):
        """Test **bold** conversion."""
        result = convert_to_telegram_markdown("**bold text**")
        assert "*bold text*" in result
    
    def test_convert_italic(self):
        """Test *italic* conversion."""
        result = convert_to_telegram_markdown("*italic text*")
        assert "_italic text_" in result
    
    def test_escape_special_chars(self):
        """Test special character escaping."""
        result = convert_to_telegram_markdown("Hello. How are you!")
        assert "\\." in result
        assert "\\!" in result
    
    def test_remove_headers(self):
        """Test header removal."""
        result = convert_to_telegram_markdown("# Header\nContent")
        assert "# Header" not in result
        assert "Header" in result
    
    def test_safe_telegram_send_success(self):
        """Test safe send returns formatted text."""
        text, parse_mode = safe_telegram_send("**bold**")
        assert parse_mode == "MarkdownV2"
        assert "*bold*" in text
    
    def test_safe_telegram_send_fallback(self):
        """Test safe send always returns a result."""
        # Normal case - should not raise
        text, parse_mode = safe_telegram_send("normal text")
        assert parse_mode == "MarkdownV2"
        assert text is not None
