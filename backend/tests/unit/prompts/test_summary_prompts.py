"""Tests for summary prompt validation.

These tests validate the structure and content of the SUMMARY_UPDATE_PROMPT
to ensure it follows best practices from ChatGPT and Mem0.
"""

# Import here to avoid triggering conftest.py config loading
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))


def test_summary_update_prompt_has_required_placeholders():
    """Should have required placeholders for current_summary and new_lines."""
    # Import directly to avoid fixtures
    from src.prompts.summary_prompts import SUMMARY_UPDATE_PROMPT

    assert "{current_summary}" in SUMMARY_UPDATE_PROMPT
    assert "{new_lines}" in SUMMARY_UPDATE_PROMPT


def test_summary_update_prompt_has_few_shot_examples():
    """Should have few-shot examples for better extraction."""
    from src.prompts.summary_prompts import SUMMARY_UPDATE_PROMPT

    # Should have input/output examples
    assert "### Input" in SUMMARY_UPDATE_PROMPT
    assert "### Output" in SUMMARY_UPDATE_PROMPT


def test_summary_update_prompt_mentions_date_format():
    """Should specify date format [DD/MM]."""
    from src.prompts.summary_prompts import SUMMARY_UPDATE_PROMPT

    assert "[DD/MM]" in SUMMARY_UPDATE_PROMPT


def test_summary_update_prompt_mentions_substitution():
    """Should mention automatic substitution of contradicting facts."""
    from src.prompts.summary_prompts import SUMMARY_UPDATE_PROMPT

    assert "SUBSTITUIÇÃO" in SUMMARY_UPDATE_PROMPT.upper() or "SUBSTITUI" in SUMMARY_UPDATE_PROMPT.upper()


def test_summary_update_prompt_mentions_categories():
    """Should mention all required categories."""
    from src.prompts.summary_prompts import SUMMARY_UPDATE_PROMPT

    categories = ["health", "goals", "preferences", "progress", "restrictions"]
    for cat in categories:
        assert cat in SUMMARY_UPDATE_PROMPT


def test_summary_update_prompt_json_format_valid():
    """Should show valid JSON examples."""
    from src.prompts.summary_prompts import SUMMARY_UPDATE_PROMPT

    # Should mention JSON output explicitly
    assert "JSON" in SUMMARY_UPDATE_PROMPT


def test_summary_update_prompt_ignores_system_logs():
    """Should explain what to ignore (system logs, etc)."""
    from src.prompts.summary_prompts import SUMMARY_UPDATE_PROMPT

    # Should mention what NOT to extract
    assert "IGNORAR" in SUMMARY_UPDATE_PROMPT or "ignora" in SUMMARY_UPDATE_PROMPT.lower()
