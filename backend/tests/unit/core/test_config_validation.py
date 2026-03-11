"""
Tests for Settings validation in config.py.
Specifically tests the model_validator that enforces
COMPACTION_THRESHOLD > MAX_SHORT_TERM_MEMORY_MESSAGES.
"""

import pytest
from pydantic import ValidationError


def test_settings_rejects_compaction_threshold_equal_to_window():
    """COMPACTION_THRESHOLD == MAX_SHORT_TERM_MEMORY_MESSAGES should raise ValidationError."""
    from src.core.config import Settings

    with pytest.raises(ValidationError, match="COMPACTION_THRESHOLD"):
        Settings(
            MAX_SHORT_TERM_MEMORY_MESSAGES=40,
            COMPACTION_THRESHOLD=40,  # Equal — invalid
        )


def test_settings_rejects_compaction_threshold_less_than_window():
    """COMPACTION_THRESHOLD < MAX_SHORT_TERM_MEMORY_MESSAGES should raise ValidationError.

    This is the exact production bug: window=40, threshold defaults to 25.
    """
    from src.core.config import Settings

    with pytest.raises(ValidationError, match="COMPACTION_THRESHOLD"):
        Settings(
            MAX_SHORT_TERM_MEMORY_MESSAGES=40,
            COMPACTION_THRESHOLD=25,  # Less than window — the production bug
        )


def test_settings_accepts_valid_compaction_threshold():
    """COMPACTION_THRESHOLD > MAX_SHORT_TERM_MEMORY_MESSAGES should succeed."""
    from src.core.config import Settings

    # Should NOT raise
    s = Settings(
        MAX_SHORT_TERM_MEMORY_MESSAGES=40,
        COMPACTION_THRESHOLD=60,
    )
    assert s.COMPACTION_THRESHOLD == 60
    assert s.MAX_SHORT_TERM_MEMORY_MESSAGES == 40


def test_settings_accepts_compaction_threshold_at_minimum_valid_gap():
    """COMPACTION_THRESHOLD = MAX_SHORT_TERM_MEMORY_MESSAGES + 1 is the minimum valid value."""
    from src.core.config import Settings

    s = Settings(
        MAX_SHORT_TERM_MEMORY_MESSAGES=20,
        COMPACTION_THRESHOLD=21,
    )
    assert s.COMPACTION_THRESHOLD == 21
