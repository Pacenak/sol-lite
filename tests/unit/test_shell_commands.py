from pathlib import Path

from sol_lite.agents.base import AgentDefinition
from sol_lite.agents.shell import AgentShell
from sol_lite.config.user_settings import UserSettingsStore
from sol_lite.core.session import Session, Workspace


class Agents:
    def __init__(self):
        self._agents = {
            "sol_pa": AgentDefinition(
                "sol_pa", "SOL PA", "primary", "pa", model_profile="fast",
            ),
            "sol_engineer": AgentDefinition(
                "sol_engineer", "SOL Engineer", "specialist", "engineer",
                model_profile="engineer",
            ),
        }

    def get(self, agent_id):
        return self._agents[agent_id]

    def names(self):
        return sorted(self._agents)


class Models:
    class Profile:
        model = "fake"

    def profile(self, name):
        return self.Profile()

    def diagnose(self):
        return {"ok": True}


class Tools:
    def names(self):
        return ["runtime_get_context"]


class SkillManager:
    def prompt_context(self, *args):
        return ""

    def for_agent(self, agent_id, workspace_root):
        return []


class WorkspaceManager:
    def __init__(self, root):
        self.workspace = Workspace("w1", "test", str(root))

    def register(self, root):
        return self.workspace

    def recent(self):
        return []

    def list(self):
        return [self.workspace]


class SessionManager:
    def create(self, agent_id, workspace):
        return Session("s1", agent_id, workspace.workspace_id, workspace.root)

    def update(self, session_id, **changes):
        return None

    def list(self):
        return []


class Context:
    platform = type("Platform", (), {"name": "test", "available_shells": lambda self: []})()
    search_config = None

    def for_workspace(self, *args, **kwargs):
        return self


class FaultLog:
    path = Path("faults.json")


class TaskManager:
    def list(self):
        return []

    def cancel(self, task_id):
        return False


class ScriptedConsole:
    def __init__(self, answers):
        self.answers = list(answers)
        self.printed = []

    def input(self, prompt=""):
        if not self.answers:
            raise EOFError
        return self.answers.pop(0)

    def print(self, *args, **kwargs):
        self.printed.append(args)

    def push_theme(self, *args, **kwargs):
        return None


def _repository():
    return {
        "runtime": {"mode": "assisted", "max_concurrent_agents": 4},
        "agents": {
            "agents": {
                "sol_pa": {
                    "name": "SOL PA",
                    "enabled": True,
                    "role": "primary",
                    "description": "pa",
                    "model_profile": "fast",
                },
                "sol_engineer": {
                    "name": "SOL Engineer",
                    "enabled": True,
                    "role": "specialist",
                    "description": "engineer",
                    "model_profile": "engineer",
                },
            }
        },
        "models": {
            "provider": {
                "endpoint": "http://127.0.0.1:11434",
                "trusted": True,
            },
            "profiles": {
                "fast": {"model": "qwen", "temperature": 0.2, "timeout_seconds": 30, "locality": "host"},
                "engineer": {"model": "qwen-coder", "temperature": 0.2, "timeout_seconds": 30, "locality": "host"},
            },
        },
        "searxng": {
            "searxng": {
                "enabled": False,
                "url": "http://10.10.40.10:30053/",
                "timeout_seconds": 30,
                "max_results": 8,
                "categories": "general",
                "language": "en",
                "safesearch": 1,
                "engines": "",
            }
        },
    }


def _shell(tmp_path, *, search_config=None):
    context = Context()
    context.search_config = search_config if search_config is not None else {}
    shell = AgentShell(
        root=tmp_path,
        agents=Agents(),
        models=Models(),
        tools=Tools(),
        tool_context=context,
        fault_log=FaultLog(),
        workspace_manager=WorkspaceManager(tmp_path),
        session_manager=SessionManager(),
        skill_manager=SkillManager(),
        task_manager=TaskManager(),
        event_bus=object(),
        initial_agent="sol_engineer",
        initial_workspace=str(tmp_path),
        settings_store=UserSettingsStore(tmp_path / "settings.yaml"),
        settings_repository=_repository(),
    )
    shell.base_context.search_config = context.search_config
    shell.context.search_config = context.search_config
    return shell


def test_settings_command_saves_general_and_search(tmp_path):
    shell = _shell(tmp_path, search_config={"enabled": False, "url": "http://env.example"})
    shell.ui.console = ScriptedConsole(["1", "sol_pa", "6", "1", "y", "b"])

    assert shell.handle_command("/Settings") == "handled"
    assert shell.settings_store.get("general", "default_agent") == "sol_pa"
    assert shell.settings_store.get("searxng")["searxng"]["enabled"] is True
    assert shell.context.search_config["enabled"] is True
    assert shell.context.search_config["url"] == "http://env.example"


def test_documented_commands_are_handled(tmp_path, capsys):
    shell = _shell(tmp_path)
    commands = [
        "/help",
        "/agents",
        "/use sol_pa",
        "/workspace",
        "/workspaces",
        "/sessions",
        "/skills",
        "/skills list",
        "/tools",
        "/status",
        "/tasks",
        "/verbose",
        "/debug",
        "/normal",
        "/doctor",
        "/follow",
    ]

    for command in commands:
        assert shell.handle_command(command) == "handled", command

    assert shell.handle_command("/use") == "handled"
    assert "Usage: /use" in capsys.readouterr().out
    assert shell.handle_command("/background") == "handled"
    assert shell.handle_command("/not-a-command") == "handled"
    output = capsys.readouterr().out
    assert "Usage: /background" in output
    assert "Unknown command" in output
    assert shell.handle_command("inspect this workspace") == "chat"
    assert shell.handle_command("/quit") == "quit"


def test_listen_queues_transcript_as_the_user_line(tmp_path, monkeypatch, capsys):
    shell = _shell(tmp_path)
    monkeypatch.setattr(shell, "_transcribe", lambda: "plan the sprint")
    assert shell.handle_command("/listen") == "utterance"
    assert shell._queued_utterance == "plan the sprint"
    assert not shell._queued_utterance.startswith("/")
    assert "Heard: plan the sprint" in capsys.readouterr().out


def test_follow_command_classifies_without_running_install_commands(tmp_path, capsys):
    from tests.unit.test_procedure_tools import _context

    shell = _shell(tmp_path)
    (tmp_path / "checklist.md").write_text(
        """| Step | Action | Validate |
|------|--------|----------|
| A1 | `sudo bash scripts/install/plg-install-docker-official.sh` | `echo ok` |
""",
        encoding="utf-8",
    )
    shell.context = _context(
        tmp_path,
        tmp_path / "audit.jsonl",
        tmp_path / "faults.json",
    )

    assert shell.handle_command("/follow checklist.md") == "handled"
    output = capsys.readouterr().out
    assert "A1  needs_approval" in output
    assert "No approval-gated command was executed." in output
    assert shell.context.procedure_session.status()["steps"][0]["evidence"] == {}

    assert shell.handle_command("/follow ../outside.md") == "handled"
    assert "Procedure load failed" in capsys.readouterr().out


def test_documented_commands_run_without_calling_the_agent(tmp_path, capsys):
    shell = _shell(tmp_path)
    shell.ui.console = ScriptedConsole([
        "/help",
        "/agents",
        "/use sol_pa",
        "/workspace",
        "/workspaces",
        "/sessions",
        "/skills",
        "/skills list",
        "/tools",
        "/status",
        "/tasks",
        "/verbose",
        "/debug",
        "/normal",
        "/doctor",
        "/background",
        "/follow",
        "/settings",
        "b",
        "/quit",
    ])
    calls = []

    def fail_if_called(**kwargs):
        calls.append(kwargs["messages"][-1]["content"])
        raise AssertionError("command reached the agent")

    shell.runtime.run = fail_if_called
    shell.run()
    output = capsys.readouterr().out
    assert calls == []
    assert "sol_pa" in output
    assert "Usage: /background" in output
    assert "Usage: /follow" in output
    assert "Current workspace:" in output


def test_slash_command_from_settings_menu_runs_that_command(tmp_path, capsys):
    shell = _shell(tmp_path)
    shell.ui.console = ScriptedConsole(["/settings", "/agents", "/quit"])

    def fail_if_called(**kwargs):
        raise AssertionError("command reached the agent")

    shell.runtime.run = fail_if_called
    shell.run()
    assert "sol_engineer" in capsys.readouterr().out


def test_settings_typed_at_the_prompt_is_not_sent_to_the_agent(tmp_path):
    shell = _shell(tmp_path)
    shell.ui.console = ScriptedConsole(["/settings", "b"])
    calls = []

    def fail_if_called(**kwargs):
        calls.append(kwargs["messages"][-1]["content"])
        raise AssertionError(kwargs["messages"][-1]["content"])

    shell.runtime.run = fail_if_called
    shell.run()
    assert calls == []


def test_settings_typed_during_approval_opens_the_menu(tmp_path):
    from contextlib import nullcontext

    from sol_lite.agents.runtime import AgentResult

    shell = _shell(tmp_path)
    shell.ui.console = ScriptedConsole(["inspect the workspace", "b"])
    shell.ui.live_status = lambda tracker: nullcontext()
    seen = []

    def fake_run(**kwargs):
        seen.append(kwargs["messages"][-1]["content"])
        return AgentResult(
            "",
            1,
            True,
            "shell_command",
            shell_command="/settings",
        )

    shell.runtime.run = fake_run
    shell.run()
    assert seen == ["inspect the workspace"]
    assert shell.ui.console.answers == []


def test_composed_chat_keeps_paragraph_breaks(tmp_path, monkeypatch):
    shell = _shell(tmp_path)
    monkeypatch.setattr(
        "sol_lite.agents.shell.read_message",
        lambda console, prompt: "  first\n\nsecond  ",
    )
    assert shell._prompt("SOL ❯ ", compose=True) == "first\n\nsecond"


def test_settings_without_store_reports_unavailable(tmp_path, capsys):
    shell = _shell(tmp_path)
    shell.settings_store = None

    assert shell.handle_command("/settings") == "handled"
    assert "unavailable" in capsys.readouterr().out.casefold()
