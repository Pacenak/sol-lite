from pathlib import Path

from sol_lite.agents.base import AgentDefinition
from sol_lite.agents.shell import AgentShell
from sol_lite.core.session import Session, Workspace


class Agents:
    def get(self, agent_id):
        return AgentDefinition(agent_id, "Test Agent", "test", "test", model_profile="engineer")

    def names(self):
        return ["sol_engineer"]


class Models:
    class Profile:
        model = "fake"

    def profile(self, name):
        return self.Profile()


class Tools:
    def names(self):
        return []


class SkillManager:
    def prompt_context(self, *args):
        return ""


class WorkspaceManager:
    def __init__(self, root):
        self.workspace = Workspace("w1", "test", str(root))

    def register(self, root):
        return self.workspace

    def recent(self):
        return []


class SessionManager:
    def create(self, agent_id, workspace):
        return Session("s1", agent_id, workspace.workspace_id, workspace.root)

    def update(self, session_id, **changes):
        return None


class Context:
    platform = type("Platform", (), {"available_shells": lambda self: []})()

    def for_workspace(self, *args, **kwargs):
        return self


class FaultLog:
    path = Path("faults.json")


class TaskManager:
    pass


def test_shell_accepts_task_manager_and_event_bus(tmp_path):
    shell = AgentShell(
        root=tmp_path,
        agents=Agents(),
        models=Models(),
        tools=Tools(),
        tool_context=Context(),
        fault_log=FaultLog(),
        workspace_manager=WorkspaceManager(tmp_path),
        session_manager=SessionManager(),
        skill_manager=SkillManager(),
        task_manager=TaskManager(),
        event_bus=object(),
        initial_agent="sol_engineer",
        initial_workspace=str(tmp_path),
    )
    assert isinstance(shell.task_manager, TaskManager)
    assert shell.event_bus is not None


def test_shell_skill_listing_uses_active_agent_context(tmp_path, capsys):
    class SkillRecord:
        skill_id = "systematic-debugging"
        trust = "BUILTIN"
        status = "BUILTIN"
        name = "Systematic Debugging"
        description = "Diagnose bugs through evidence and regression testing."

    class ListingSkillManager(SkillManager):
        def for_agent(self, agent_id, workspace_root):
            assert agent_id == "sol_engineer"
            assert Path(workspace_root) == tmp_path
            return [SkillRecord()]

    shell = AgentShell(
        root=tmp_path,
        agents=Agents(),
        models=Models(),
        tools=Tools(),
        tool_context=Context(),
        fault_log=FaultLog(),
        workspace_manager=WorkspaceManager(tmp_path),
        session_manager=SessionManager(),
        skill_manager=ListingSkillManager(),
        task_manager=TaskManager(),
        event_bus=object(),
        initial_agent="sol_engineer",
        initial_workspace=str(tmp_path),
    )
    shell._skills("")
    output = capsys.readouterr().out
    assert "systematic-debugging" in output
    assert "Diagnose bugs" in output
