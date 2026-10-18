from sol_lite.agents.project_brief import build_project_brief, format_project_brief
from sol_lite.agents.shell import conversation_messages
from sol_lite.agents.task_fit import (
    DIRECTORY_LISTING_TOOL_NAMES,
    permitted_tools,
)
from sol_lite.core.session import SessionManager, Workspace
from sol_lite.memory.notes import read_notes, write_notes


def test_brief_prefers_package_name_and_readme_purpose(tool_context):
    root = tool_context.workspace_root
    (root / "README.md").write_text(
        "# Demo heading\n\nBuilds the operator console.\n",
        encoding="utf-8",
    )
    (root / "package.json").write_text(
        '{"name": "PLG_Ai_Interface", "description": "package description"}\n',
        encoding="utf-8",
    )
    brief = build_project_brief(tool_context)
    assert brief["name"] == "PLG_Ai_Interface"
    assert brief["purpose"] == "Builds the operator console."
    text = format_project_brief(brief)
    assert "Project name: PLG_Ai_Interface" in text
    assert "Builds the operator console." in text


def test_identity_change_and_notes_tools_stay_in_their_lanes():
    identity = permitted_tools("what is the project name?", None)
    assert "inventory_workspace" in identity
    assert "repository_status" not in identity
    assert "write_workspace_file" not in identity
    assert "workspace_notes_write" not in identity

    notes = permitted_tools(
        "analyse the program and write notes so you know",
        None,
    )
    assert "workspace_notes_write" in notes
    assert "read_workspace_file" in notes
    assert "repository_status" not in notes

    change = permitted_tools("Fix the bug and run the tests", None)
    assert "write_workspace_file" in change
    assert "execute_terminal_command" in change
    assert "repository_status" not in change

    assert permitted_tools("list the folders", None) == DIRECTORY_LISTING_TOOL_NAMES
    plain = permitted_tools(
        "hello",
        frozenset({
            "inventory_workspace",
            "workspace_notes_write",
            "execute_terminal_command",
        }),
    )
    assert plain == frozenset({"inventory_workspace"})


def test_second_turn_keeps_the_answer_and_drops_tool_json():
    manager = SessionManager(object())
    workspace = Workspace("ws-1", "demo", "E:/demo")
    session = manager.create("sol_engineer", workspace)
    manager.remember_turn(
        session.session_id,
        "analyse the workspace",
        "Project name: Demo",
    )
    messages = conversation_messages(
        "system",
        session.transcript,
        "what is the project name?",
    )
    assert messages[1] == {"role": "user", "content": "analyse the workspace"}
    assert messages[2] == {"role": "assistant", "content": "Project name: Demo"}
    assert messages[-1]["content"] == "what is the project name?"
    assert all(message["role"] != "tool" for message in messages)
    assert "tool_name" not in "\n".join(message["content"] for message in messages)


def test_saved_notes_are_visible_to_the_next_prompt(tmp_path):
    purpose = "Builds the operator console."
    write_notes(tmp_path / "memory", "ws-1", purpose)
    assert purpose in read_notes(tmp_path / "memory", "ws-1")

    from sol_lite.agents.shell import AgentShell

    class Agent:
        id = "sol_engineer"
        name = "SOL Engineer"
        role = "specialist"
        description = "Engineering agent."
        capabilities = ("software_engineering",)
        can_delegate_to = ()

    class Agents:
        def get(self, agent_id):
            return Agent()

    class Platform:
        name = "windows"

        @staticmethod
        def available_shells():
            return []

    class Context:
        platform = Platform()
        memory_root = tmp_path / "memory"

    class WorkspaceView:
        workspace_id = "ws-1"
        root = tmp_path
        name = "demo"

    class Session:
        session_id = "session-test"
        transcript = ()

    shell = AgentShell.__new__(AgentShell)
    shell.root = tmp_path
    shell.agents = Agents()
    shell.tools = object()
    shell.context = Context()
    shell.workspace = WorkspaceView()
    shell.session = Session()
    shell.active_agent = "sol_engineer"
    prompt = shell._system_prompt()
    assert "Workspace notes:" not in prompt
    assert "Process working directory:" not in prompt
    assert "SOL-Lite program directory (not a workspace):" in prompt
    assert "only place to inspect or modify" in prompt
    assert purpose not in prompt  # Workspace data must not become trusted system policy.
    messages = shell._messages_for("what is the project name?")
    assert messages[0]["role"] == "system"
    assert purpose not in messages[0]["content"]
