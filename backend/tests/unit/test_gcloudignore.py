from pathlib import Path


def test_gcloudignore_keeps_markdown_ignored():
    gcloudignore = Path(__file__).resolve().parents[2] / ".gcloudignore"
    gcloudignore = gcloudignore.read_text(encoding="utf-8")

    assert "*.md" in gcloudignore
