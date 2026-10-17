"""Rick Prime behavioural instruction and integration contract checks."""
from pathlib import Path

import yaml

from sol_lite.agents.tool_allowlist import resolve_session_tools
from sol_lite.tools import build_tool_registry

ROOT = Path(__file__).resolve().parents[2]
PROMPT = ROOT / "src/sol_lite/agents/rick_prime/prompt.md"


def test_greeting_is_not_a_tool_request():
    prompt = PROMPT.read_text(encoding="utf-8").lower()
    assert "small talk" in prompt
    assert "no tools" in prompt
    assert "studio_list_project_structure" in prompt


def test_scientific_evidence_gate_is_explicit():
    prompt = PROMPT.read_text(encoding="utf-8").lower()
    for phrase in (
        "demonstrated technology", "engineering extrapolation",
        "research hypothesis", "speculative/fictional", "governing equations",
        "independent replication", "uncertainty", "pass/fail",
        "simulation", "patent", "no fabricated results",
    ):
        assert phrase in prompt, phrase


def test_rick_tools_are_actual_runtime_names():
    available = set(build_tool_registry().names())
    selected = set(resolve_session_tools(ROOT, "rick_prime", available))
    assert selected <= available
    assert "inventory_workspace" in selected
    assert "skill_discover" in selected
    assert "studio_list_project_structure" not in selected


def test_rick_tools_yaml_is_valid():
    data = yaml.safe_load((PROMPT.parent / "tools.yaml").read_text(encoding="utf-8"))
    assert isinstance(data["tools"], list)
    assert len(data["tools"]) == len(set(data["tools"]))
