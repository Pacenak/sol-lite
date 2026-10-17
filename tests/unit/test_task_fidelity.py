import io
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from sol_lite.agents.runtime import AgentRuntime
from sol_lite.agents.status import StatusTracker
from sol_lite.agents.tool_allowlist import resolve_session_tools
from sol_lite.core.exceptions import SecurityError
from sol_lite.faults.log import FaultLog
from sol_lite.terminal_ui import TerminalUI
from sol_lite.tools import build_tool_registry
from sol_lite.tools.filesystem import list_workspace_directories

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("user_text", [
    "refactor the parser", "repair the parser", "upgrade dependencies",
    "update configuration", "create a test", "patch the handler",
])
def test_engineering_requests_allow_edits_without_enabling_integrations(user_text):
    from sol_lite.agents.task_fit import permitted_tools

    selected = permitted_tools(user_text, None)
    assert {"read_workspace_file", "edit_workspace_file", "execute_terminal_command"} <= selected
    assert not {"repository_push", "remote_execute", "google_email_send"} & selected


@pytest.mark.parametrize("user_text", [
    "look up the official docs", "research the latest package documentation",
    "check the API reference online",
])
def test_research_requests_allow_search_and_respect_agent_allowlist(user_text):
    from sol_lite.agents.task_fit import permitted_tools

    assert "searxng_search" in permitted_tools(user_text, None)
    assert "searxng_search" not in permitted_tools(user_text, frozenset({"read_workspace_file"}))


def test_dictionary_provider_response_executes_native_calls(tmp_path):
    tools = RecordingTools({"count": 1})
    models = ScriptedModels([
        {"message": {"content": None, "tool_calls": [
            {"function": {"name": "inventory_workspace", "arguments": {}}},
        ]}},
        {"message": {"content": "Inventory completed.", "tool_calls": None}},
    ])
    result = AgentRuntime(models, tools, object(), FaultLog(tmp_path / "faults.json")).run(
        profile="engineer", messages=[{"role": "user", "content": "inventory"}],
        allowed_tools=("inventory_workspace",),
    )
    assert tools.calls == ["inventory_workspace"]
    assert result.content == "Inventory completed."
    assert result.stopped_reason is None


def test_successful_edit_counts_as_completion_evidence(tmp_path):
    tools = RecordingTools({"ok": True})
    result = AgentRuntime(
        ScriptedModels([_message(tool_name="edit_workspace_file"), _message("Fixed.")]),
        tools, object(), FaultLog(tmp_path / "faults.json"),
    ).run(
        profile="engineer", messages=[{"role": "user", "content": "fix the parser"}],
        allowed_tools=("edit_workspace_file",),
    )
    assert result.content == "Fixed."
    assert result.stopped_reason is None


def test_failed_validation_cannot_support_completion_claim(tmp_path):
    tools = RecordingTools({"exit_code": 1, "stderr": "test failed"})
    result = AgentRuntime(
        ScriptedModels([_message(tool_name="execute_terminal_command"),
                        _message("Tests pass."), _message("Tests pass.")]),
        tools, object(), FaultLog(tmp_path / "faults.json"),
    ).run(
        profile="engineer", messages=[{"role": "user", "content": "run the tests"}],
        allowed_tools=("execute_terminal_command",),
    )
    assert result.stopped_reason == "validation_required"
    assert result.tool_failures == 1


def _message(content="", tool_name=None):
    calls = []
    if tool_name:
        calls.append(SimpleNamespace(function=SimpleNamespace(name=tool_name, arguments={})))
    return SimpleNamespace(message=SimpleNamespace(content=content, tool_calls=calls))


class ScriptedModels:
    def __init__(self, steps):
        self.steps = list(steps)
        self.schemas = []

    class Profile:
        model = "fake"
        temperature = 0.1
        timeout_seconds = 10

    def profile(self, name):
        return self.Profile()

    def chat(self, profile, messages, tools):
        self.schemas.append(tools)
        step = self.steps.pop(0)
        return step


class RecordingTools:
    def __init__(self, result):
        self.calls = []
        self.result = result

    def ollama_schemas(self, names=None):
        selected = ["sol_command_status", "list_workspace_directories"]
        if names is not None:
            allowed = set(names)
            selected = [name for name in selected if name in allowed]
        return [{"type": "function", "function": {"name": name, "description": name, "parameters": {}}} for name in selected]

    def execute(self, name, arguments, context):
        self.calls.append(name)
        return self.result


def test_engineer_schemas_exclude_command_and_pa_includes_it():
    registry = build_tool_registry()
    available = registry.names()
    engineer = resolve_session_tools(ROOT, "sol_engineer", available)
    pa = resolve_session_tools(ROOT, "sol_pa", available)
    engineer_names = {item["function"]["name"] for item in registry.ollama_schemas(engineer)}
    pa_names = {item["function"]["name"] for item in registry.ollama_schemas(pa)}
    assert "sol_command_status" not in engineer_names
    assert "list_workspace_directories" in engineer_names
    assert "sol_command_status" in pa_names
    assert "sol_jarvis_propose" in pa_names


def test_folder_request_rejects_command_status_then_lists_directories(tmp_path):
    tools = RecordingTools({
        "root": "E:/workspace",
        "directories": ["src", "src/pkg"],
        "count": 2,
        "truncated": False,
    })
    approvals = []
    models = ScriptedModels([
        _message(tool_name="sol_command_status"),
        _message(tool_name="list_workspace_directories"),
        _message("src\nsrc/pkg"),
    ])
    result = AgentRuntime(
        models,
        tools,
        object(),
        FaultLog(tmp_path / "faults.json"),
        approval_callback=lambda request: approvals.append(request),
    ).run(
        profile="engineer",
        allowed_tools=("sol_command_status", "list_workspace_directories"),
        messages=[{"role": "user", "content": "list the folders and directory paths"}],
    )
    assert approvals == []
    assert tools.calls == ["list_workspace_directories"]
    assert result.stopped_reason is None
    assert result.content == "src\nsrc/pkg"
    assert models.schemas[0]
    assert all(item["function"]["name"] != "sol_command_status" for item in models.schemas[0])


def test_second_off_task_tool_stops_the_turn(tmp_path):
    tools = RecordingTools({"directories": []})
    result = AgentRuntime(
        ScriptedModels([
            _message(tool_name="sol_command_status"),
            _message(tool_name="searxng_search"),
        ]),
        tools,
        object(),
        FaultLog(tmp_path / "faults.json"),
    ).run(
        profile="engineer",
        allowed_tools=("sol_command_status", "searxng_search", "list_workspace_directories"),
        messages=[{"role": "user", "content": "list the folders"}],
    )
    assert tools.calls == []
    assert result.stopped_reason == "task_tool_mismatch"


def test_invented_directory_path_is_rejected_once_then_fails(tmp_path):
    tools = RecordingTools({
        "root": "E:/workspace",
        "directories": ["src"],
        "count": 1,
        "truncated": False,
    })
    result = AgentRuntime(
        ScriptedModels([
            _message(tool_name="list_workspace_directories"),
            _message("secret/missing"),
            _message("secret/missing"),
        ]),
        tools,
        object(),
        FaultLog(tmp_path / "faults.json"),
    ).run(
        profile="engineer",
        allowed_tools=("list_workspace_directories",),
        messages=[{"role": "user", "content": "list the folders"}],
    )
    assert tools.calls == ["list_workspace_directories"]
    assert result.stopped_reason is None
    assert result.content == "src"


def test_list_workspace_directories_walks_nested_dirs_and_stays_inside(tool_context):
    root = tool_context.workspace_root
    (root / "src" / "pkg").mkdir()
    outside = root.parent / "outside-dir"
    outside.mkdir()
    link = root / "escape"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError):
        link = None
    result = list_workspace_directories(tool_context, {})
    assert result["directories"] == ["src", "src/pkg"]
    assert result["truncated"] is False
    assert "escape" not in result["directories"]
    with pytest.raises(SecurityError):
        list_workspace_directories(tool_context, {"path": ".."})


def test_approval_input_runs_while_live_status_is_stopped():
    from rich.console import Console

    ui = TerminalUI(console=Console(file=io.StringIO(), force_terminal=True, width=80))
    tracker = StatusTracker(heartbeat_interval=60)
    seen = {}

    def fake_input(prompt=""):
        live = ui._live
        seen["started"] = bool(live is not None and getattr(live, "is_started", False))
        return "n"

    ui.console.input = fake_input
    request = SimpleNamespace(
        operation="sol_command_status",
        target="paired SOL-Command",
        arguments={},
        plan_hash="abc",
        approval_id="a1",
    )
    with ui.live_status(tracker):
        assert ui._live.is_started
        answer = ui.approval(request)
    assert seen["started"] is False
    assert answer is None


def test_awaiting_approval_does_not_become_stalled():
    tracker = StatusTracker(stall_threshold=0.01, heartbeat_interval=60)
    tracker.begin("INTERACTIVE", "Starting")
    tracker.await_approval("Approval required · sol_command_status")
    time.sleep(0.05)
    assert tracker.state() == "AWAITING_APPROVAL"


def test_take_note_permits_workspace_notes():
    from sol_lite.agents.task_fit import permitted_tools

    noted = permitted_tools("take note of this base dir and folder layout", None)
    assert "workspace_notes_write" in noted
    assert "workspace_notes_write" in permitted_tools("note this folder layout", None)
    assert "workspace_notes_write" in permitted_tools("note that for later", None)


def test_approval_prompt_hides_the_api_token():
    from rich.console import Console

    buffer = io.StringIO()
    ui = TerminalUI(console=Console(file=buffer, force_terminal=True, width=100))
    ui.console.input = lambda prompt="": "n"
    request = SimpleNamespace(
        operation="jira_save_workspace",
        target="https://example.atlassian.net",
        arguments={
            "projects": ["SOL"],
            "email": "ada@example.com",
            "token": "secret-token-value",
        },
        plan_hash="abc",
        approval_id="a1",
    )
    assert ui.approval(request) is None
    text = buffer.getvalue()
    assert "secret-token-value" not in text
    assert "[redacted]" in text
    assert "ada@example.com" in text
