from pathlib import Path
from types import SimpleNamespace

from sol_lite.agents.runtime import AgentRuntime
from sol_lite.agents.task_fit import permitted_tools
from sol_lite.faults.log import FaultLog
from sol_lite.skills.manager import SkillManager
from sol_lite.tools.filesystem import (
    _OVERVIEW_CAP,
    inventory_workspace,
    list_project_structure,
    list_workspace_directories,
)

ROOT = Path(__file__).resolve().parents[2]

WORKSPACE_QUESTION = (
    "hi, please analyse the full content of this current workspace.. "
    "tell me what the full files are for and what this workspace is"
)
GIT_ERROR = (
    "The error indicates that the path E:\\sol-lite-WS\\1 is not a Git repository, "
    "as it does not contain a .git directory."
)


def _message(content="", tool_name=None, arguments=None):
    calls = []
    if tool_name:
        calls.append(SimpleNamespace(
            function=SimpleNamespace(name=tool_name, arguments=arguments or {}),
        ))
    return SimpleNamespace(message=SimpleNamespace(content=content, tool_calls=calls))


class ScriptedModels:
    def __init__(self, steps):
        self.steps = list(steps)
        self.schemas = []
        self.seen = []

    class Profile:
        model = "fake"
        temperature = 0.1
        timeout_seconds = 10

    def profile(self, name):
        return self.Profile()

    def chat(self, profile, messages, tools):
        self.schemas.append(tools)
        self.seen.append(messages)
        return self.steps.pop(0)


class RecordingTools:
    def __init__(self, result):
        self.calls = []
        self.result = result
        self.available = [
            "inventory_workspace",
            "read_workspace_file",
            "list_workspace_directories",
            "repository_status",
            "repository_log",
        ]

    def ollama_schemas(self, names=None):
        selected = self.available
        if names is not None:
            allowed = set(names)
            selected = [name for name in selected if name in allowed]
        return [
            {"type": "function", "function": {"name": name, "description": name, "parameters": {}}}
            for name in selected
        ]

    def execute(self, name, arguments, context):
        self.calls.append(name)
        return self.result


def test_inventory_returns_every_file_for_a_small_tree(tool_context):
    overview = inventory_workspace(tool_context, {})
    assert overview["truncated"] is False
    assert overview["files"] == ["src/example.py"]
    assert overview["count"] == 1
    assert overview["top_level"] == ["src"]


def test_inventory_caps_a_large_tree(tool_context):
    root = tool_context.workspace_root
    (root / "README.md").write_text("A sample program.\n", encoding="utf-8")
    (root / "package.json").write_text("{}\n", encoding="utf-8")
    deep = root / "a" / "b" / "c" / "d"
    deep.mkdir(parents=True)
    (deep / "README.md").write_text("too deep\n", encoding="utf-8")
    for index in range(_OVERVIEW_CAP):
        (root / "src" / f"file-{index}.py").write_text("x = 1\n", encoding="utf-8")

    capped = inventory_workspace(tool_context, {})
    assert capped["count"] > _OVERVIEW_CAP
    assert capped["truncated"] is True
    assert "files" not in capped
    assert "src" in capped["top_level"]
    assert "README.md" in capped["top_level"]
    assert "README.md" in capped["manifests"]
    assert "package.json" in capped["manifests"]
    assert "a/b/c/d/README.md" not in capped["manifests"]
    assert ".py" in capped["extensions"]
    assert "list_project_structure" in capped["note"]


def test_directory_and_tree_listings_stay_bounded(tool_context):
    root = tool_context.workspace_root
    for index in range(_OVERVIEW_CAP + 1):
        (root / f"dir-{index:03d}").mkdir()
        (root / f"file-{index:03d}.txt").write_text("x\n", encoding="utf-8")
    directories = list_workspace_directories(tool_context, {})
    assert directories["truncated"] is True
    assert len(directories["directories"]) == _OVERVIEW_CAP
    assert all("/" not in path for path in directories["directories"])

    tree = list_project_structure(tool_context, {})
    assert tree["truncated"] is True
    assert len(tree["tree"]) == _OVERVIEW_CAP


def test_workspace_question_does_not_permit_git_tools():
    permitted = permitted_tools(WORKSPACE_QUESTION, None)
    assert "inventory_workspace" in permitted
    assert "read_workspace_file" in permitted
    assert "repository_status" not in permitted
    assert "repository_log" not in permitted

    git = permitted_tools("show the git log", None)
    assert "repository_log" in git
    assert "repository_status" in git
    assert "inventory_workspace" not in git


def test_git_error_answer_is_corrected_once_then_rejected(tmp_path):
    tools = RecordingTools({
        "root": "E:/workspace",
        "count": 2,
        "top_level": ["src", "README.md"],
        "truncated": False,
        "files": ["README.md", "src/main.py"],
        "manifests": ["README.md"],
    })
    models = ScriptedModels([
        _message(tool_name="inventory_workspace"),
        _message(GIT_ERROR),
        _message(GIT_ERROR),
    ])
    result = AgentRuntime(
        models,
        tools,
        object(),
        FaultLog(tmp_path / "faults.json"),
    ).run(
        profile="engineer",
        allowed_tools=tuple(tools.available),
        messages=[{"role": "user", "content": WORKSPACE_QUESTION}],
    )
    names = {item["function"]["name"] for item in models.schemas[0]}
    assert "repository_status" not in names
    assert "repository_log" not in names
    assert "inventory_workspace" in names
    assert tools.calls == ["inventory_workspace"]
    assert result.stopped_reason == "workspace_evidence_required"
    assert result.content == ""
    correction = models.seen[-1]
    assert any(
        isinstance(message, dict)
        and "Top-level entries: src, README.md" in str(message.get("content", ""))
        for message in correction
    )


def test_directory_listing_keeps_sibling_folders_ahead_of_deep_git(tool_context):
    root = tool_context.workspace_root
    project = root / "PLG_Ai_Interface"
    (project / ".git" / "objects" / "aa" / "bb").mkdir(parents=True)
    (project / "src").mkdir(parents=True)
    (project / "docs").mkdir()
    result = list_workspace_directories(tool_context, {})
    assert "PLG_Ai_Interface" in result["directories"]
    assert "PLG_Ai_Interface/src" in result["directories"]
    assert "PLG_Ai_Interface/docs" in result["directories"]
    assert "PLG_Ai_Interface/.git" in result["directories"]
    assert "PLG_Ai_Interface/.git/objects" not in result["directories"]
    assert result["truncated"] is False


def test_workspace_prompt_does_not_load_unrelated_skill_denials(tmp_path):
    manager = SkillManager(ROOT, tmp_path)
    for task in (
        "please analyse the contents of this current workspace",
        "please analyse the contents of this current workspace. list the folder dir and sub dir to me here",
    ):
        text = manager.prompt_context("sol_pa", task=task)
        assert "reasoning guidance only" not in text
        assert "DETAILED SKILL:" not in text
        assert "Workspace file and directory tools remain available." in text


def test_refusing_model_still_returns_the_workspace_inventory(tmp_path):
    tools = RecordingTools({
        "root": "E:/sol-lite-WS/1",
        "count": 2,
        "top_level": ["PLG_Ai_Interface"],
        "truncated": False,
        "files": ["PLG_Ai_Interface/README.md"],
        "manifests": ["PLG_Ai_Interface/README.md"],
    })
    models = ScriptedModels([
        _message("I cannot directly access your filesystem."),
        _message("I cannot directly access your filesystem."),
    ])
    result = AgentRuntime(
        models,
        tools,
        object(),
        FaultLog(tmp_path / "faults.json"),
    ).run(
        profile="fast",
        allowed_tools=tuple(tools.available),
        messages=[{"role": "user", "content": WORKSPACE_QUESTION}],
    )
    assert tools.calls == ["inventory_workspace"]
    assert result.stopped_reason is None
    assert "PLG_Ai_Interface" in result.content
    assert "I cannot directly access" not in result.content


def test_refusing_model_still_returns_the_directory_list(tmp_path):
    tools = RecordingTools({
        "root": "E:/sol-lite-WS/1",
        "directories": ["PLG_Ai_Interface", "PLG_Ai_Interface/src", "PLG_Ai_Interface/docs"],
        "count": 3,
        "truncated": False,
    })
    models = ScriptedModels([
        _message("I cannot list folders."),
        _message("I cannot list folders."),
    ])
    result = AgentRuntime(
        models,
        tools,
        object(),
        FaultLog(tmp_path / "faults.json"),
    ).run(
        profile="engineer",
        allowed_tools=tuple(tools.available),
        messages=[{
            "role": "user",
            "content": (
                "please analyse the contents of this current workspace. "
                "list the folder dir and sub dir to me here"
            ),
        }],
    )
    assert tools.calls == ["list_workspace_directories"]
    assert result.stopped_reason is None
    assert result.content == "PLG_Ai_Interface\nPLG_Ai_Interface/src\nPLG_Ai_Interface/docs"
    assert "pasted" not in result.content.casefold()


class WideTools:
    def __init__(self):
        self.calls = []
        self.available = [
            "inventory_workspace",
            "read_workspace_file",
            "write_workspace_file",
            "execute_terminal_command",
            "repository_status",
            "repository_log",
            "workspace_notes_read",
            "workspace_notes_write",
        ]

    def ollama_schemas(self, names=None):
        selected = self.available
        if names is not None:
            allowed = set(names)
            selected = [name for name in selected if name in allowed]
        return [
            {"type": "function", "function": {"name": name, "description": name, "parameters": {}}}
            for name in selected
        ]

    def execute(self, name, arguments, context):
        self.calls.append(name)
        if name == "workspace_notes_write":
            from sol_lite.tools.notes import workspace_notes_write
            return workspace_notes_write(context, arguments)
        if name == "execute_terminal_command":
            return {"ok": True, "exit_code": 0}
        return {"ok": True}


def _plant_project(root):
    (root / "README.md").write_text(
        "# Demo heading\n\nBuilds the operator console.\n",
        encoding="utf-8",
    )
    (root / "package.json").write_text(
        '{"name": "PLG_Ai_Interface", "description": "package description"}\n',
        encoding="utf-8",
    )


def test_project_name_answer_replaces_a_git_error(tool_context, tmp_path):
    _plant_project(tool_context.workspace_root)
    tools = WideTools()
    models = ScriptedModels([
        _message(GIT_ERROR),
        _message(GIT_ERROR),
    ])
    result = AgentRuntime(
        models,
        tools,
        tool_context,
        FaultLog(tmp_path / "faults.json"),
    ).run(
        profile="engineer",
        allowed_tools=tuple(tools.available),
        messages=[{"role": "user", "content": "what is the project name?"}],
    )
    names = {item["function"]["name"] for item in models.schemas[0]}
    assert "repository_status" not in names
    assert "repository_log" not in names
    assert "inventory_workspace" in names
    assert result.stopped_reason is None
    assert "PLG_Ai_Interface" in result.content
    assert "not a Git repository" not in result.content


def test_pasted_file_list_is_replaced_by_the_readme_purpose(tool_context, tmp_path):
    _plant_project(tool_context.workspace_root)
    pasted = (
        "It looks like you've provided a list of file paths, "
        'possibly from a project directory, and included a count ("count": 426).'
    )
    result = AgentRuntime(
        ScriptedModels([_message(pasted), _message(pasted)]),
        WideTools(),
        tool_context,
        FaultLog(tmp_path / "faults.json"),
    ).run(
        profile="engineer",
        allowed_tools=tuple(WideTools().available),
        messages=[{
            "role": "user",
            "content": "analyse the workspace. What does it contain?",
        }],
    )
    assert result.stopped_reason is None
    assert "Builds the operator console." in result.content
    assert "you've provided" not in result.content.casefold()


def test_notes_request_waits_for_a_saved_note(tool_context, tmp_path):
    purpose = "Builds the operator console."
    tool_context.memory_root = tmp_path / "memory"
    tool_context.workspace_id = "ws-1"
    refused = AgentRuntime(
        ScriptedModels([
            _message("Got it. I've reviewed the workspace structure."),
            _message("Got it. I've reviewed the workspace structure."),
        ]),
        WideTools(),
        tool_context,
        FaultLog(tmp_path / "refused.json"),
    ).run(
        profile="engineer",
        allowed_tools=tuple(WideTools().available),
        messages=[{"role": "user", "content": "write notes so you know"}],
    )
    assert refused.stopped_reason == "notes_required"
    assert refused.content == ""

    saved = AgentRuntime(
        ScriptedModels([
            _message("Got it. I've reviewed the workspace structure."),
            _message(
                tool_name="workspace_notes_write",
                arguments={"content": purpose},
            ),
            _message("Noted for next time."),
        ]),
        WideTools(),
        tool_context,
        FaultLog(tmp_path / "saved.json"),
    ).run(
        profile="engineer",
        allowed_tools=tuple(WideTools().available),
        messages=[{"role": "user", "content": "write notes so you know"}],
    )
    assert saved.stopped_reason is None
    assert purpose in (tmp_path / "memory" / "ws-1" / "notes.md").read_text(encoding="utf-8")


def test_fix_claim_without_proof_is_rejected(tmp_path):
    tools = WideTools()
    models = ScriptedModels([
        _message("Fixed. Tests pass."),
        _message("Fixed. Tests pass."),
    ])
    result = AgentRuntime(
        models,
        tools,
        object(),
        FaultLog(tmp_path / "faults.json"),
    ).run(
        profile="engineer",
        allowed_tools=tuple(tools.available),
        messages=[{"role": "user", "content": "Fix the bug and run the tests"}],
    )
    names = {item["function"]["name"] for item in models.schemas[0]}
    assert "write_workspace_file" in names
    assert "execute_terminal_command" in names
    assert "repository_status" not in names
    assert result.stopped_reason == "validation_required"
    assert result.content == ""


def test_blocked_change_answer_is_kept(tmp_path):
    result = AgentRuntime(
        ScriptedModels([_message("I am blocked. The source file is missing.")]),
        WideTools(),
        object(),
        FaultLog(tmp_path / "faults.json"),
    ).run(
        profile="engineer",
        allowed_tools=tuple(WideTools().available),
        messages=[{"role": "user", "content": "Fix the bug"}],
    )
    assert result.stopped_reason is None
    assert "blocked" in result.content.casefold()


def test_empty_workspace_claim_is_replaced_with_the_inventory(tmp_path):
    tools = RecordingTools({
        "root": "/Users/paceenak/Documents/sol-lite-WS/Pa-WS",
        "count": 1,
        "top_level": ["house-hold", "plg-studio", ".DS_Store"],
        "truncated": False,
        "files": [".DS_Store"],
        "manifests": [],
    })
    empty = "The workspace exists but is empty.\n\n• 0 files\n• 0 directories"
    models = ScriptedModels([
        _message(tool_name="inventory_workspace"),
        _message(empty),
        _message(empty),
    ])
    result = AgentRuntime(
        models,
        tools,
        object(),
        FaultLog(tmp_path / "faults.json"),
    ).run(
        profile="fast",
        allowed_tools=tuple(tools.available),
        messages=[{"role": "user", "content": "tell me about the current workspace"}],
    )
    assert result.stopped_reason is None
    assert "house-hold" in result.content
    assert "plg-studio" in result.content
    assert "0 files" not in result.content
    assert any(
        "Top-level entries: house-hold, plg-studio, .DS_Store" in str(message.get("content", ""))
        for seen in models.seen
        for message in seen
        if isinstance(message, dict)
    )


class FailingModels:
    def __init__(self, errors, final="house-hold and plg-studio"):
        self.errors = list(errors)
        self.final = final
        self.seen = []

    class Profile:
        model = "fake"
        temperature = 0
        timeout_seconds = 10

    def profile(self, name):
        return self.Profile()

    def chat(self, profile, messages, tools):
        self.seen.append(messages)
        if self.errors:
            from sol_lite.core.exceptions import ModelError
            raise ModelError(self.errors.pop(0))
        return _message(self.final)


def test_xml_tool_error_retries_once_then_answers_in_text(tmp_path):
    error = "Ollama chat failed: XML syntax error on line 4: element <function> closed by </parameter> (status code: 500)"
    models = FailingModels([error, error])
    result = AgentRuntime(
        models,
        RecordingTools({"count": 0, "top_level": []}),
        object(),
        FaultLog(tmp_path / "faults.json"),
    ).run(
        profile="fast",
        allowed_tools=("inventory_workspace",),
        messages=[{"role": "user", "content": "take note of this base dir"}],
    )
    assert result.stopped_reason is None
    assert "tool call was invalid" in result.content
    assert any(
        "native structured tool interface" in str(message.get("content", ""))
        for message in models.seen[-1]
        if isinstance(message, dict)
    )


def test_timeout_retries_once_then_answers_in_text(tmp_path):
    models = FailingModels([
        "Ollama chat failed: timed out",
        "Ollama chat failed: timed out",
    ])
    result = AgentRuntime(
        models,
        RecordingTools({"count": 0, "top_level": []}),
        object(),
        FaultLog(tmp_path / "faults.json"),
    ).run(
        profile="fast",
        allowed_tools=("inventory_workspace",),
        messages=[{"role": "user", "content": "hello"}],
    )
    assert result.stopped_reason is None
    assert "timed out" in result.content.casefold()
