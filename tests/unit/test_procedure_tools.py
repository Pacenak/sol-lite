import pytest

from sol_lite.audit.logger import AuditLogger
from sol_lite.core.exceptions import ApprovalRequired, PermissionDenied
from sol_lite.faults.log import FaultLog
from sol_lite.permissions.approvals import ApprovalManager
from sol_lite.permissions.engine import PermissionEngine
from sol_lite.permissions.policy import PermissionPolicy
from sol_lite.platform import get_platform_adapter
from sol_lite.tools import ToolContext, build_tool_registry
from sol_lite.tools.procedure import procedure_advance, procedure_load, procedure_status


def _context(root, audit_path, fault_path):
    policy = PermissionPolicy({"permissions": {
        "filesystem": {"read": {"enabled": True, "approval_required": False}},
        "terminal": {
            "enabled": True,
            "approval_required": False,
            "allowed_commands": ["echo"],
            "blocked_commands": ["sudo", "rm"],
            "read": {"enabled": True, "approval_required": False},
            "write": {"enabled": True, "approval_required": True},
        },
    }})
    return ToolContext(
        workspace_root=root,
        permission_engine=PermissionEngine(policy, ApprovalManager()),
        audit=AuditLogger(audit_path),
        fault_log=FaultLog(fault_path),
        platform=get_platform_adapter(),
    )


def test_procedure_tools_load_and_advance_only_the_current_row(tmp_path):
    root = tmp_path / "workspace"
    root.mkdir()
    (root / "checklist.md").write_text(
        """| Step | Action | Validate |
|------|--------|----------|
| A1 | `echo alpha` | `echo ok` |
| A2 | `sudo bash scripts/install/plg-install-host.sh` | `echo ok` |
""",
        encoding="utf-8",
    )
    ctx = _context(root, tmp_path / "audit.jsonl", tmp_path / "faults.json")

    loaded = procedure_load(ctx, {"path": "checklist.md"})
    assert loaded["complete"] is False
    assert loaded["steps"][0]["classification"] == "read_only"
    assert loaded["steps"][1]["classification"] == "needs_approval"

    advanced = procedure_advance(ctx, {})
    assert advanced["steps"][0]["outcome"] == "verified"
    assert advanced["stop_reason"] is None

    with pytest.raises(PermissionDenied):
        procedure_advance(ctx, {})
    assert ctx.procedure_session.status()["steps"][1]["evidence"] == {}

    status = procedure_status(ctx, {})
    assert status["complete"] is False
    assert "procedure_load" in build_tool_registry().names()


def test_mutating_row_raises_approval_without_running(tmp_path):
    root = tmp_path / "workspace"
    root.mkdir()
    (root / "checklist.md").write_text(
        """| Step | Action | Validate |
|------|--------|----------|
| W1 | `echo hello > out.txt` | `echo ok` |
""",
        encoding="utf-8",
    )
    ctx = _context(root, tmp_path / "audit.jsonl", tmp_path / "faults.json")
    procedure_load(ctx, {"path": "checklist.md"})

    with pytest.raises(ApprovalRequired):
        procedure_advance(ctx, {})

    assert not (root / "out.txt").exists()
    assert ctx.procedure_session.status()["steps"][0]["evidence"] == {}
