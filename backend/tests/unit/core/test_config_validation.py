"""Tests for core Settings defaults used by chat memory windowing."""


def test_settings_default_short_term_window_is_50():
    """Default short-term prompt window should be 50 messages."""
    from src.core.config import Settings

    settings = Settings()
    assert settings.MAX_SHORT_TERM_MEMORY_MESSAGES == 50


def test_settings_accepts_custom_short_term_window():
    """Custom short-term prompt window should be accepted."""
    from src.core.config import Settings

    settings = Settings(MAX_SHORT_TERM_MEMORY_MESSAGES=30)
    assert settings.MAX_SHORT_TERM_MEMORY_MESSAGES == 30
