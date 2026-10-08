from pathlib import Path
from types import SimpleNamespace

from sol_lite.agents.runtime import AgentRuntime
from sol_lite.agents.shell import AgentShell
from sol_lite.faults.log import FaultLog

ROOT = Path(__file__).resolve().parents[2]


def test_engineer_prompt_contains_no_legacy_tool_protocol_examples():
    prompt_path = (
        ROOT
        / "src"
        / "sol_lite"
        / "agents"
        / "engineer"
        / "prompt.md"
    )

    prompt = prompt_path.read_text(
        encoding="utf-8"
    )

    assert "<function=" not in prompt
    assert "<tool_call>" not in prompt
    assert '{"name":"' not in prompt


def test_shell_system_prompt_contains_no_legacy_tool_protocol_examples(
    tmp_path,
):
    class Agent:
        id = "sol_engineer"
        name = "SOL Engineer"
        role = "specialist"
        description = "Engineering agent."
        capabilities = (
            "software_engineering",
            "debugging",
        )
        can_delegate_to = ()

    class Agents:
        def get(self, agent_id):
            assert agent_id == "sol_engineer"
            return Agent()

    class Platform:
        name = "windows"

        @staticmethod
        def available_shells():
            return ["powershell"]

    class Context:
        session_id = "test-session"
        platform = Platform()

    class Workspace:
        workspace_id = "workspace-test"
        root = tmp_path

    class WorkspaceManager:
        pass

    class Session:
        session_id = "session-test"

    class SessionManager:
        def create(self, agent_id, workspace):
            assert agent_id == "sol_engineer"
            return Session()

    class Models:
        pass

    class Tools:
        pass

    class Skills:
        def prompt_context(
            self,
            agent_id,
            workspace,
            prompt="",
        ):
            return ""

    shell = AgentShell.__new__(
        AgentShell
    )

    shell.root = ROOT
    shell.agents = Agents()
    shell.models = Models()
    shell.tools = Tools()
    shell.base_context = Context()
    shell.context = Context()
    shell.workspace = Workspace()
    shell.workspace_manager = WorkspaceManager()
    shell.session_manager = SessionManager()
    shell.skill_manager = Skills()
    shell.active_agent = "sol_engineer"
    shell.session = Session()

    prompt = shell._system_prompt()

    assert "<function=" not in prompt
    assert "<tool_call>" not in prompt
    assert '{"name":"' not in prompt


def test_runtime_still_rejects_textual_tool_syntax(
    tmp_path,
):
    class Models:
        class Profile:
            model = "fake"
            temperature = 0.0
            timeout_seconds = 10

        def profile(self, name):
            return self.Profile()

        def chat(self, profile, messages, tools):
            return SimpleNamespace(
                message=SimpleNamespace(
                    content=(
                        "<function=runtime_get_context>"
                        "</function>"
                        "</tool_call>"
                    ),
                    tool_calls=[],
                )
            )

    class Tools:
        def ollama_schemas(self):
            return [
                {
                    "type": "function",
                    "function": {
                        "name": "runtime_get_context",
                        "description": "test",
                        "parameters": {
                            "type": "object",
                            "properties": {},
                        },
                    },
                }
            ]

        def execute(self, *args):
            raise AssertionError(
                "Textual tool syntax must never execute."
            )

    runtime = AgentRuntime(
        Models(),
        Tools(),
        object(),
        FaultLog(
            tmp_path / "faults.json"
        ),
    )

    result = runtime.run(
        profile="engineer",
        messages=[
            {
                "role": "system",
                "content": "Use native structured tools.",
            },
            {
                "role": "user",
                "content": "Inspect the workspace.",
            },
        ],
    )

    assert result.stopped_reason == (
        "tool_call_not_native"
    )
    assert result.raw_tool_like_content is True
    assert result.native_tool_calls == 0

    faults = runtime.fault_log.get_all()

    assert any(
        fault["code"] == "TOOL_LIKE_CONTENT"
        for fault in faults
    )