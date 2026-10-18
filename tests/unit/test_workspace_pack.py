from pathlib import Path

import pytest

from sol_lite.agents.runtime import _PROOF_TOOLS
from sol_lite.agents.task_fit import permitted_tools
from sol_lite.agents.tool_allowlist import resolve_session_tools
from sol_lite.core.exceptions import ApprovalRequired, PermissionDenied, SecurityError
from sol_lite.tools import build_tool_registry
from sol_lite.tools.filesystem import edit_workspace_file, write_workspace_file
from sol_lite.tools.notes import workspace_notes_read, workspace_notes_write
from sol_lite.tools.workspace_pack import (
    workspace_pack_append,
    workspace_pack_init,
    workspace_pack_intake,
    workspace_pack_status,
)
from sol_lite.workspace_pack.context import orientation
from sol_lite.workspace_pack.pack import AGENTS, FILES, QUESTIONS, Pack, parse_plan


def complete(root, skip=None):
    for key in QUESTIONS:
        pack = Pack(root)
        args = {"question_id": key, "answer": f"Answer for {key}"}
        if key == skip:
            args = {"question_id": key, "skip": True}
        pack.answer(args)
        pack.commit()
    pack = Pack(root)
    pack.initialize()
    pack.commit()


def approve(function, ctx, args):
    with pytest.raises(ApprovalRequired) as caught:
        function(ctx, args)
    return function(ctx, {**args, "approval_id": caught.value.request.approval_id})


def test_fixed_questions_resume_and_skip(tmp_path):
    assert Pack(tmp_path).answer({})["next"]["id"] == "purpose"
    with pytest.raises(ValueError, match="order"):
        Pack(tmp_path).answer({"question_id": "agents", "answer": "engineer"})
    pack = Pack(tmp_path)
    pack.answer({"question_id": "purpose", "answer": "A tool"})
    pack.commit()
    assert Pack(tmp_path).answer({})["next"]["id"] == "project_types"


def test_create_skip_defaults_and_idempotence(tmp_path):
    complete(tmp_path, skip="conventions")
    folder = tmp_path / "_workspace"
    assert {path.name for path in folder.iterdir()} == set(FILES)
    entries, errors = parse_plan((folder / "PLAN.md").read_text(encoding="utf-8"))
    assert not errors
    assert entries[0]["id"] == "T-0001"
    assert entries[0]["tags"] == "needs-info"
    before = {path.name: path.read_bytes() for path in folder.iterdir()}
    pack = Pack(tmp_path)
    pack.initialize()
    assert pack.commit()["written"] == []
    assert before == {path.name: path.read_bytes() for path in folder.iterdir()}


def test_templates_match_golden_files(tmp_path, monkeypatch):
    from sol_lite.workspace_pack import pack as module

    monkeypatch.setattr(module, "stamp", lambda: "2026-10-19T14:32:00+13:00")
    complete(tmp_path, skip="conventions")
    golden = Path(__file__).resolve().parents[1] / "fixtures/workspace-pack/golden"
    for name in FILES:
        assert (tmp_path / "_workspace" / name).read_bytes() == (golden / name).read_bytes()


def test_readme_rerender_preserves_notes_and_lore(tmp_path):
    complete(tmp_path)
    path = tmp_path / "_workspace/README.md"
    path.write_text(path.read_text(encoding="utf-8") + "My durable lore.\n", encoding="utf-8")
    pack = Pack(tmp_path)
    pack.answer({"question_id": "purpose", "answer": "New purpose"})
    pack.commit()
    assert "New purpose" in path.read_text(encoding="utf-8")
    assert path.read_text(encoding="utf-8").endswith("My durable lore.\n")
    assert "Updated intake answers" in (tmp_path / "_workspace/CHANGELOG.md").read_text()


def test_followups_limited_and_recorded(tmp_path):
    complete(tmp_path)
    pack = Pack(tmp_path)
    pack.answer({"question_id": "followup_1", "question": "Which format?", "answer": "Markdown"})
    pack.commit()
    assert "Which format?" in Pack(tmp_path).intake()["followup_1"]
    with pytest.raises(ValueError):
        Pack(tmp_path).answer({"question_id": "followup_3", "answer": "bad"})


def test_plan_append_validation_and_preservation(tmp_path):
    complete(tmp_path)
    path = tmp_path / "_workspace/PLAN.md"
    with path.open("a", encoding="utf-8") as out:
        out.write("\n## Tasks\n### T-0042 malformed\nstatus: invented\n")
    original = path.read_bytes()
    pack = Pack(tmp_path, "sol_docs")
    identity = pack.append(
        "plan_task",
        {
            "title": "Document",
            "status": "todo",
            "owner": "sol_docs",
            "due": "2026-10-25",
            "notes": "First line\nSecond line",
        },
    )
    assert identity == "T-0043"
    pack.commit()
    assert path.read_bytes().startswith(original)
    entries, errors = parse_plan(path.read_text(encoding="utf-8"))
    assert entries[-1]["schedule"] == "none"
    assert entries[-1]["notes"] == "First line\nSecond line"
    assert errors[0]["line"] > 0
    for invalid in ({"status": "wrong"}, {"owner": "intruder"}, {"due": "yesterday"}):
        with pytest.raises(ValueError):
            Pack(tmp_path).append(
                "plan_task", {"title": "Invalid", "status": "todo", "owner": "sol_pa", **invalid}
            )


@pytest.mark.parametrize(
    "source",
    [
        "## Tasks\n### T-0001\nstatus: todo\nowner: sol_pa\n",
        "## Tasks\n### T-0001 Title\nstatus: todo\nowner: sol_pa\nextra: bad\n",
        "## Routines\n### T-0001 Title\nstatus: todo\nowner: sol_pa\n",
        "## Tasks\n### T-0001 Title\nstatus: todo\nstatus: done\nowner: sol_pa\n",
        "## Tasks\n### T-0001 Title\nstatus: todo\nowner: sol_pa\ndue: 2026-02-30\n",
    ],
)
def test_malformed_plan_entries_reported(source):
    entries, errors = parse_plan(source)
    assert not entries and errors and errors[0]["line"] > 0


def test_task_and_routine_append_alternates_without_rewriting(tmp_path):
    complete(tmp_path)
    for kind, status in (("plan_task", "todo"), ("plan_routine", "active"), ("plan_task", "doing")):
        path = tmp_path / "_workspace/PLAN.md"
        before = path.read_bytes()
        pack = Pack(tmp_path)
        pack.append(
            kind,
            {
                "title": "Title",
                "status": status,
                "owner": "sol_pa",
                "schedule": "every weekday 09:00",
            },
        )
        pack.commit()
        assert path.read_bytes().startswith(before)
    entries, errors = parse_plan(path.read_text(encoding="utf-8"))
    assert not errors
    assert [row["id"] for row in entries] == ["T-0001", "R-0001", "T-0002"]


def test_index_new_removed_and_purposes(tmp_path):
    complete(tmp_path)
    (tmp_path / "hello.txt").write_text("hello")
    pack = Pack(tmp_path)
    pack.refresh()
    pack.commit()
    path = tmp_path / "_workspace/INDEX.md"
    path.write_text(path.read_text().replace("(needs purpose)", "A greeting"))
    Pack(tmp_path).status()  # Read-only status must not advance removal cycles.
    (tmp_path / "hello.txt").unlink()
    pack = Pack(tmp_path)
    pack.refresh()
    pack.commit()
    assert "(removed)" in path.read_text()
    assert "A greeting" in path.read_text()
    pack = Pack(tmp_path)
    pack.refresh()
    pack.commit()
    assert "hello.txt" not in path.read_text()
    (tmp_path / "new.txt").write_text("new")
    pack = Pack(tmp_path)
    pack.refresh()
    pack.commit()
    path.write_text(path.read_text().replace("(needs purpose)", "Keep this purpose"))
    pack = Pack(tmp_path)
    pack.refresh()
    pack.commit()
    assert "Keep this purpose" in path.read_text()


def test_project_intake_depth_cap_and_first_log(tmp_path):
    complete(tmp_path)
    project = tmp_path / "example project"
    project.mkdir()
    (project / "deep").mkdir()
    (project / "deep/deeper").mkdir()
    (project / "deep/deeper/hidden.txt").write_text("hidden")
    (project / "deep/seen.txt").write_text("seen")
    for number in range(205):
        (project / f"f{number:03}.txt").write_text("data")
    for key in ("what", "type_stack", "rules"):
        pack = Pack(tmp_path)
        pack.answer(
            {
                "project": project.name,
                "question_id": f"project/{project.name}/{key}",
                "answer": "Project details",
            }
        )
        pack.commit()
    pack = Pack(tmp_path)
    pack.initialize(project.name)
    pack.commit()
    content = (project / "_project/INDEX.md").read_text()
    assert "Truncated at 200" in content and "hidden.txt" not in content
    assert "deep/seen.txt" in content
    pack = Pack(tmp_path, "sol_engineer")
    pack.append(
        "changelog",
        {"changed": "Updated a file", "files": ["example project/f000.txt"]},
        project.name,
    )
    pack.commit()
    assert (project / "_project/CHANGELOG.md").exists()


def test_escape_and_structural_injection(tmp_path):
    for relative in ("../escaped.md", str(tmp_path.parent / "escaped.md")):
        with pytest.raises(SecurityError):
            Pack(tmp_path).put(relative, "bad")
    with pytest.raises(ValueError):
        Pack(tmp_path).answer(
            {"question_id": "purpose", "answer": "Inline <!-- intake:purpose:end -->"}
        )
    with pytest.raises(ValueError):
        Pack(tmp_path).initialize("../bad")


def test_symlink_escape(tmp_path):
    outside = tmp_path.parent / (tmp_path.name + "-outside")
    outside.mkdir()
    try:
        (tmp_path / "_workspace").symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("Windows symlink privilege unavailable")
    with pytest.raises((SecurityError, ValueError)):
        Pack(tmp_path).put("_workspace/README.md", "bad")
    assert not list(outside.iterdir())


def test_proposal_rejects_changed_file_before_any_write(tmp_path):
    complete(tmp_path)
    pack = Pack(tmp_path)
    pack.answer({"question_id": "purpose", "answer": "Changed purpose"})
    intake = tmp_path / "_workspace/INTAKE.md"
    before = intake.read_bytes()
    (tmp_path / "_workspace/README.md").write_text("Concurrent edit")
    with pytest.raises(ValueError, match="changed since approval"):
        pack.commit()
    assert intake.read_bytes() == before


def test_notes_approval_minimal_pack_and_once_only_migration(tool_context, tmp_path):
    ctx = tool_context
    ctx.agent_id = "sol_engineer"
    ctx.memory_root = tmp_path / "memory"
    ctx.workspace_id = "test"
    legacy = ctx.memory_root / "test/notes.md"
    legacy.parent.mkdir(parents=True)
    legacy.write_text("Original notes\n" + "long " * 600, encoding="utf-8")
    original = legacy.read_bytes()
    args = {"content": "A program and how to edit it"}
    with pytest.raises(ApprovalRequired) as caught:
        workspace_notes_write(ctx, args)
    assert not (ctx.workspace_root / "_workspace").exists()
    request = caught.value.request
    assert {row["path"] for row in request.arguments["files"]} == {
        "_workspace/README.md",
        "_workspace/CONVERSATIONS.md",
    }
    result = workspace_notes_write(ctx, {**args, "approval_id": request.approval_id})
    assert result["written"]
    approve(workspace_notes_write, ctx, {"content": "A second tip"})
    conversation = (ctx.workspace_root / "_workspace/CONVERSATIONS.md").read_text()
    assert conversation.count("| migrated") == 1
    assert "long " * 500 in conversation
    assert legacy.read_bytes() == original
    assert args["content"] in workspace_notes_read(ctx, {})["content"]


def test_role_enforcement_direct_calls_and_schema(tool_context):
    root = Path(__file__).resolve().parents[2]
    registry = build_tool_registry()
    for agent in AGENTS:
        tool_context.agent_id = agent
        names = resolve_session_tools(root, agent, registry.names())
        assert "workspace_pack_append" in names
        if agent != "sol_pa":
            assert "workspace_pack_init" not in names
            with pytest.raises(PermissionDenied):
                workspace_pack_init(tool_context, {})
    assert "workspace_pack_init" in permitted_tools("set up the workspace", None)
    assert "workspace_pack_init" in permitted_tools("add a project to the workspace", None)
    assert "workspace_pack_append" in _PROOF_TOOLS
    assert len(registry.ollama_schemas(["workspace_pack_append"])) == 1


def test_approval_input_cannot_be_changed(tool_context):
    tool_context.agent_id = "sol_pa"
    args = {"question_id": "purpose", "answer": "One"}
    with pytest.raises(ApprovalRequired) as caught:
        workspace_pack_intake(tool_context, args)
    with pytest.raises(PermissionDenied):
        workspace_pack_intake(
            tool_context,
            {**args, "answer": "Other", "approval_id": caught.value.request.approval_id},
        )
    assert not (tool_context.workspace_root / "_workspace").exists()


def test_approved_tool_intake_end_to_end(tool_context):
    tool_context.agent_id = "sol_pa"
    for identity in QUESTIONS:
        result = approve(
            workspace_pack_intake, tool_context, {"question_id": identity, "answer": "User answer"}
        )
    assert result["complete"]
    result = approve(workspace_pack_init, tool_context, {})
    assert "_workspace/README.md" in result["written"]
    assert not workspace_pack_status(tool_context, {})["missing"]
    result = approve(
        workspace_pack_append,
        tool_context,
        {
            "kind": "plan_routine",
            "fields": {
                "title": "Review",
                "status": "active",
                "owner": "sol_pa",
                "schedule": "Mondays 09:00",
            },
        },
    )
    assert result["entry_id"] == "R-0001"


def test_non_utf8_preserved_and_reported(tmp_path):
    complete(tmp_path)
    path = tmp_path / "_workspace/CONVERSATIONS.md"
    path.write_bytes(b"\xff\xfe")
    pack = Pack(tmp_path)
    pack.initialize()
    pack.commit()
    assert path.read_bytes() == b"\xff\xfe"
    assert Pack(tmp_path).status()["errors"]


def test_orientation_index_first_and_generic_writes_blocked(tool_context):
    ctx = tool_context
    ctx.agent_id = "sol_engineer"
    complete(ctx.workspace_root)
    content = orientation(ctx)
    assert content.index("_workspace/INDEX.md") < content.index("_workspace/README.md")
    assert "UNTRUSTED" in content
    with pytest.raises(PermissionDenied, match="pack tools"):
        write_workspace_file(ctx, {"path": "_workspace/PLAN.md", "content": "overwrite"})
    with pytest.raises(PermissionDenied, match="pack tools"):
        edit_workspace_file(
            ctx, {"path": "_workspace/README.md", "old_string": "Purpose", "new_string": "Override"}
        )


def test_source_pack_audit_excludes_scratch_and_runtime_trees(tmp_path):
    import runpy

    root = Path(__file__).resolve().parents[2]
    audit = runpy.run_path(str(root / "scripts/audit-pack.py"))
    for relative in (
        ".work/nested/scratch.txt",
        ".git/config",
        "data/state/cache.json",
        "portable-stick/brain/workspace/user-notes.md",
        "src/sol_lite/pack.py",
    ):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("data", encoding="utf-8")
    assert audit["payload_files"](tmp_path) == [Path("src/sol_lite/pack.py")]
