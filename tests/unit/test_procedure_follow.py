from sol_lite.agents.base import AgentDefinition
from sol_lite.agents.shell import AgentShell
from sol_lite.core.session import Session, Workspace
from tests.unit.test_procedure_tools import _context


class Agents:
    def __init__(self):
        self._agents = {
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
        return []


class SkillManager:
    def prompt_context(self, *args, **kwargs):
        return ""


class WorkspaceManager:
    def __init__(self, root):
        self.workspace = Workspace("w1", "test", str(root))

    def register(self, root):
        return self.workspace


class SessionManager:
    def create(self, agent_id, workspace):
        return Session("s1", agent_id, workspace.workspace_id, workspace.root)

    def update(self, session_id, **changes):
        return None


class FaultLog:
    def __init__(self, path):
        self.path = path


class ScriptedConsole:
    def __init__(self, answers):
        self.answers = list(answers)

    def input(self, prompt=""):
        if not self.answers:
            raise EOFError
        return self.answers.pop(0)

    def print(self, *args, **kwargs):
        return None


def test_follow_command_classifies_without_running_install_commands(tmp_path, capsys):
    root = tmp_path / "workspace"
    root.mkdir()
    (root / "checklist.md").write_text(
        """| Step | Action | Validate |
|------|--------|----------|
| A1 | `sudo bash scripts/install/plg-install-docker-official.sh` | `echo ok` |
""",
        encoding="utf-8",
    )
    context = _context(root, tmp_path / "audit.jsonl", tmp_path / "faults.json")
    shell = AgentShell(
        root=tmp_path,
        agents=Agents(),
        models=Models(),
        tools=Tools(),
        tool_context=context,
        fault_log=FaultLog(tmp_path / "faults.json"),
        workspace_manager=WorkspaceManager(root),
        session_manager=SessionManager(),
        skill_manager=SkillManager(),
        initial_agent="sol_engineer",
        initial_workspace=str(root),
    )
    shell.context = context
    shell.ui.console = ScriptedConsole(["/follow checklist.md", "/quit"])

    shell.run()

    output = capsys.readouterr().out
    assert "A1  needs_approval" in output
    assert "No approval-gated command was executed." in output
    assert shell.context.procedure_session.status()["steps"][0]["evidence"] == {}
