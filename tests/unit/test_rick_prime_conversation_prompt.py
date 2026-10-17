"""Regression guard for Rick Prime conversational routing guidance."""
from pathlib import Path

PROMPT = Path(__file__).resolve().parents[2] / "src/sol_lite/agents/rick_prime/prompt.md"


def test_rick_prime_prompt_includes_conversation_first_rules():
    text = PROMPT.read_text(encoding="utf-8")
    assert "Conversation-first behaviour" in text
    assert "For greetings, small talk" in text
    assert "Never guess a tool name" in text
    assert "studio_list_project_structure" in text
