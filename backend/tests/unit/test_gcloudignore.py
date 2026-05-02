from pathlib import Path


def test_gcloudignore_keeps_graph_prompt_markdown():
    gcloudignore = Path(__file__).resolve().parents[2] / ".gcloudignore"
    gcloudignore = gcloudignore.read_text(encoding="utf-8")

    assert "*.md" in gcloudignore
    assert "!src/services/agents/config/prompts/*.md" in gcloudignore
