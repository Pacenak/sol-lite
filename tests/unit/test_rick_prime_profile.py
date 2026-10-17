"""Contract tests for the Rick Prime data-driven agent integration."""

from pathlib import Path

import yaml

from sol_lite.agents.registry import AgentRegistry
from sol_lite.agents.tool_allowlist import resolve_session_tools
from sol_lite.tools import build_tool_registry

ROOT = Path(__file__).resolve().parents[2]
AGENT_DIR = ROOT / "src" / "sol_lite" / "agents" / "rick_prime"


def test_rick_prime_registers_as_distinct_specialist():
    data = yaml.safe_load((ROOT / "config" / "agents.yaml").read_text(encoding="utf-8"))
    registry = AgentRegistry(data)
    agent = registry.get("rick_prime")
    assert agent.name == "Rick Prime"
    assert agent.role == "specialist"
    assert agent.model_profile == "engineer"
    assert "sol_engineer" in registry.names()
    assert "sol_docs" in agent.can_delegate_to


def test_rick_prime_manifest_only_uses_real_tools():
    available = build_tool_registry().names()
    tools = resolve_session_tools(ROOT, "rick_prime", available)
    assert "inventory_workspace" in tools
    assert "execute_terminal_command" in tools
    assert "skill_discover" in tools
    assert "searxng_search" in tools
    assert "remote_execute" in tools
    assert set(tools).issubset(set(available))
    assert "google_email_send" not in tools


def test_rick_prime_files_and_science_skills_exist():
    assert (AGENT_DIR / "agent.py").is_file()
    assert (AGENT_DIR / "prompt.md").is_file()
    assert (AGENT_DIR / "tools.yaml").is_file()
    prompt = (AGENT_DIR / "prompt.md").read_text(encoding="utf-8")
    assert "conservation" in prompt.lower()
    assert "native" in prompt.lower()
    for skill in (
        "scientific-method",
        "frontier-physics",
        "computational-science",
        "experimental-engineering",
        "scientific-source-verification",
    ):
        assert (ROOT / "skills" / skill / "SKILL.md").is_file()
