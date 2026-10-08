from types import SimpleNamespace

import pytest

from sol_lite.audit.logger import AuditLogger
from sol_lite.faults.log import FaultLog
from sol_lite.permissions.approvals import ApprovalManager
from sol_lite.permissions.engine import PermissionEngine
from sol_lite.permissions.policy import PermissionPolicy
from sol_lite.tools.base import ToolContext


@pytest.fixture
def repository_context(tmp_path):
    root = tmp_path / "workspace"
    root.mkdir()

    (root / "src").mkdir()

    (root / "src" / "example.py").write_text(
        "answer = 42\n",
        encoding="utf-8",
    )

    policy = PermissionPolicy(
        {
            "permissions": {
                "repository": {
                    "read": {
                        "enabled": True,
                        "approval_required": False,
                    },
                    "write": {
                        "enabled": True,
                        "approval_required": True,
                    },
                    "remote": {
                        "enabled": False,
                        "approval_required": True,
                    },
                }
            }
        }
    )

    return ToolContext(
        workspace_root=root,
        permission_engine=PermissionEngine(
            policy,
            ApprovalManager(),
        ),
        audit=AuditLogger(
            tmp_path / "audit.jsonl"
        ),
        fault_log=FaultLog(
            tmp_path / "faults.json"
        ),
        platform=SimpleNamespace(),
    )


def _git(cwd, *args):
    import subprocess

    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )


def _approve(
    ctx,
    operation,
    target,
    arguments,
    plan,
):
    request = (
        ctx.permission_engine.approvals.request(
            operation,
            target,
            arguments,
            plan,
            capability=operation,
        )
    )

    return request.approval_id