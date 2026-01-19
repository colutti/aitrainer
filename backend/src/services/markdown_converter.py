"""Convert standard Markdown to Telegram MarkdownV2."""
import re


def convert_to_telegram_markdown(text: str) -> str:
    """
    Convert standard Markdown to Telegram MarkdownV2.
    
    Conversions:
    - **bold** → *bold*
    - *italic* or _italic_ → _italic_
    - Escape special characters
    - Remove unsupported elements (headers, lists)
    """
    # Remove headers (# Header)
    text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)
    
    # Step 1: Convert **bold** to placeholder
    text = re.sub(r'\*\*(.+?)\*\*', r'XBOLDSTARTX\1XBOLDENDX', text)
    
    # Step 2: Convert remaining *italic* to _italic_
    text = re.sub(r'\*(.+?)\*', r'_\1_', text)
    
    # Step 3: Convert bold placeholders to *
    text = text.replace('XBOLDSTARTX', '*')
    text = text.replace('XBOLDENDX', '*')
    
    # Escape special characters for MarkdownV2
    # Characters that need escaping: _ * [ ] ( ) ~ ` > # + - = | { } . !
    # But NOT inside code blocks or already-converted formatting
    
    # Protect our formatting markers
    text = text.replace('*', 'XASTERISKX')
    text = text.replace('_', 'XUNDERSCOREX')
    
    # Escape remaining special chars
    text = re.sub(r'([.!>\-#+=|{}()\[\]~`])', r'\\\1', text)
    
    # Restore formatting
    text = text.replace('XASTERISKX', '*')
    text = text.replace('XUNDERSCOREX', '_')
    
    return text


def safe_telegram_send(text: str) -> tuple[str, str]:
    """
    Returns (formatted_text, parse_mode).
    If conversion fails, returns plain text.
    """
    try:
        converted = convert_to_telegram_markdown(text)
        return converted, "MarkdownV2"
    except Exception:
        # Fallback to plain text
        return text, None
