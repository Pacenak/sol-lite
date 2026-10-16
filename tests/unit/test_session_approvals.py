import pytest

from sol_lite.core.exceptions import ApprovalRequired
from sol_lite.permissions.approvals import ApprovalManager
from sol_lite.permissions.engine import PermissionEngine
from sol_lite.permissions.policy import PermissionPolicy
from sol_lite.permissions.scopes import WRITE


def test_session_grant_covers_later_checks_and_exact_stays_single_use(tool_context):
    engine = tool_context.permission_engine
    engine.approvals.grant_session(session_id="sess", scope=WRITE, agent_id="sol_docs")
    with engine.execution_context(session_id="sess", agent_id="sol_docs"):
        first = engine.check(WRITE, operation="write_workspace_file", target="docs/a.md", plan="notes")
        second = engine.check(WRITE, operation="edit_workspace_file", target="docs/a.md", plan="fix")
    assert first.allowed and second.allowed
    assert "Session approval" in second.reason

    exact = ApprovalManager()
    request = exact.request("write", "/a", {"content": "A"}, "plan A")
    assert exact.consume(request.approval_id, "write", "/a", {"content": "A"}, "plan A")
    assert not exact.consume(request.approval_id, "write", "/a", {"content": "A"}, "plan A")


def test_session_grant_does_not_cover_another_scope():
    policy = PermissionPolicy({"permissions": {
        "filesystem": {"write": {"enabled": True, "approval_required": True}},
        "terminal": {"write": {"enabled": True, "approval_required": True}},
    }})
    engine = PermissionEngine(policy, ApprovalManager())
    engine.approvals.grant_session(session_id="sess", scope=WRITE, agent_id="sol_docs")
    with engine.execution_context(session_id="sess", agent_id="sol_docs"):
        with pytest.raises(ApprovalRequired):
            engine.check(
                "terminal.write",
                operation="execute_terminal_command",
                target="echo hi",
                plan="say hi",
            )


def test_outside_role_ignores_session_grant(tool_context, tmp_path):
    from sol_lite.tools.filesystem import write_workspace_file

    tool_context.agent_id = "sol_docs"
    tool_context.session_id = "sess"
    tool_context.permission_engine.approvals.grant_session(
        session_id="sess", scope=WRITE, agent_id="sol_docs"
    )
    target = tool_context.workspace_root / "src" / "not-docs.py"
    try:
        write_workspace_file(tool_context, {
            "path": "src/not-docs.py",
            "content": "x = 1\n",
            "plan": "outside role",
        })
    except ApprovalRequired:
        assert not target.exists()
        return
    raise AssertionError("a docs agent session grant must not write src/")


def test_role_path_write_does_not_need_approval(tool_context):
    """Agents create role files when asked — no y/s click for in-role paths."""
    from sol_lite.tools.filesystem import write_workspace_file

    tool_context.agent_id = "sol_docs"
    tool_context.session_id = "sess"
    out = write_workspace_file(tool_context, {
        "path": "plans/sprint.md",
        "content": "# Sprint\n",
        "plan": "new plan",
    })
    assert out["path"] == "plans/sprint.md"
    assert (tool_context.workspace_root / "plans" / "sprint.md").is_file()


def test_unbound_agent_write_still_needs_approval(tool_context):
    from sol_lite.tools.filesystem import write_workspace_file

    with pytest.raises(ApprovalRequired):
        write_workspace_file(tool_context, {
            "path": "src/new.py",
            "content": "x=1\n",
            "plan": "create",
        })
