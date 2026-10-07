import pytest

from sol_lite.audit.logger import AuditLogger
from sol_lite.faults.log import FaultLog
from sol_lite.permissions.approvals import ApprovalManager
from sol_lite.permissions.engine import PermissionEngine
from sol_lite.permissions.policy import PermissionPolicy
from sol_lite.platform import get_platform_adapter
from sol_lite.tools import ToolContext


@pytest.fixture
def workspace(tmp_path):
    root = tmp_path / "workspace"
    root.mkdir()
    (root / "src").mkdir()
    (root / "src" / "example.py").write_text("answer = 42\n", encoding="utf-8")
    return root

@pytest.fixture
def tool_context(workspace, tmp_path):
    policy = PermissionPolicy({"permissions": {
        "filesystem": {
            "read": {"enabled": True, "approval_required": False},
            "write": {"enabled": True, "approval_required": True},
        },
        "terminal": {
            "enabled": True, "approval_required": True,
            "allowed_commands": ["python", "python3", "echo", "Write-Output"],
            "blocked_commands": ["rm", "del", "Remove-Item", "shutdown",
                                 "git reset --hard", "git clean -fdx"],
        },
    }})
    approvals = ApprovalManager()
    engine = PermissionEngine(policy, approvals)
    return ToolContext(
        workspace_root=workspace,
        permission_engine=engine,
        audit=AuditLogger(tmp_path / "audit.jsonl"),
        fault_log=FaultLog(tmp_path / "faults.json"),
        platform=get_platform_adapter(),
    )
