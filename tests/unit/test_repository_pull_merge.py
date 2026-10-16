from types import SimpleNamespace

import pytest

from sol_lite.audit.logger import AuditLogger
from sol_lite.core.exceptions import ToolExecutionError
from sol_lite.faults.log import FaultLog
from sol_lite.permissions.approvals import ApprovalManager
from sol_lite.permissions.engine import PermissionEngine
from sol_lite.permissions.policy import PermissionPolicy
from sol_lite.repository.trust import RepositoryTrust
from sol_lite.tools.base import ToolContext
from sol_lite.tools.repository import (
    repository_conflict_status,
    repository_merge,
    repository_pull,
    repository_resolve_and_continue,
    repository_status,
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


def _ctx(tmp_path, root, *, trust=None):
    policy = PermissionPolicy(
        {
            "permissions": {
                "repository": {
                    "read": {"enabled": True, "approval_required": False},
                    "write": {"enabled": True, "approval_required": True},
                    "remote": {"enabled": True, "approval_required": True},
                }
            }
        }
    )
    return ToolContext(
        workspace_root=root,
        permission_engine=PermissionEngine(policy, ApprovalManager()),
        audit=AuditLogger(tmp_path / "audit.jsonl"),
        fault_log=FaultLog(tmp_path / "faults.json"),
        platform=SimpleNamespace(),
        repository_trust=trust,
    )


def _approve(ctx, operation, target, arguments, plan):
    request = ctx.permission_engine.approvals.request(
        operation, target, arguments, plan, capability=operation
    )
    return request.approval_id


@pytest.fixture
def twin_repos(tmp_path):
    workspace = tmp_path / "workspace"
    remote = tmp_path / "remote.git"
    workspace.mkdir()
    _git(tmp_path, "init", "--bare", str(remote))
    _git(workspace, "init")
    _git(workspace, "config", "user.email", "sol@example.com")
    _git(workspace, "config", "user.name", "SOL")
    (workspace / "README").write_text("one\n", encoding="utf-8")
    _git(workspace, "add", "README")
    _git(workspace, "commit", "-m", "init")
    _git(workspace, "branch", "-M", "main")
    _git(workspace, "remote", "add", "origin", str(remote))
    _git(workspace, "push", "-u", "origin", "main")
    return workspace, remote


def test_merge_and_conflict_continue(tmp_path, twin_repos):
    workspace, _remote = twin_repos
    trust = RepositoryTrust([tmp_path], tmp_path / "trusted-repos.json")
    trust.confirm(workspace, allowlist_exact=True)
    ctx = _ctx(tmp_path, workspace, trust=trust)

    _git(workspace, "checkout", "-b", "feature")
    (workspace / "README").write_text("feature\n", encoding="utf-8")
    _git(workspace, "add", "README")
    _git(workspace, "commit", "-m", "feature")
    _git(workspace, "checkout", "main")
    (workspace / "README").write_text("mainline\n", encoding="utf-8")
    _git(workspace, "add", "README")
    _git(workspace, "commit", "-m", "mainline")

    approval = _approve(
        ctx,
        "repository_merge",
        str(workspace),
        {"path": str(workspace), "ref": "feature"},
        "merge feature",
    )
    result = repository_merge(
        ctx,
        {
            "ref": "feature",
            "plan": "merge feature",
            "approval_id": approval,
        },
    )
    assert result["merged"] is False
    assert "README" in result["conflicts"]

    status = repository_conflict_status(ctx, {})
    assert status["in_merge"] is True
    (workspace / "README").write_text("resolved\n", encoding="utf-8")
    _git(workspace, "add", "README")

    from sol_lite.core.exceptions import ApprovalRequired

    try:
        repository_resolve_and_continue(
            ctx,
            {"plan": "finish merge", "approval_id": None},
        )
        raise AssertionError("expected ApprovalRequired")
    except ApprovalRequired as required:
        cont = required.request.approval_id
        done = repository_resolve_and_continue(
            ctx,
            {"plan": "finish merge", "approval_id": cont},
        )
    assert done["continued"] is True
    assert repository_status(ctx, {})["clean"] is True


def test_trusted_pull_ff_only(tmp_path, twin_repos):
    workspace, remote = twin_repos
    other = tmp_path / "other"
    _git(tmp_path, "clone", str(remote), str(other))
    _git(other, "config", "user.email", "sol@example.com")
    _git(other, "config", "user.name", "SOL")
    (other / "README").write_text("two\n", encoding="utf-8")
    _git(other, "add", "README")
    _git(other, "commit", "-m", "two")
    _git(other, "push", "origin", "main")

    trust = RepositoryTrust([tmp_path], tmp_path / "trusted-repos.json")
    trust.confirm(workspace)
    ctx = _ctx(tmp_path, workspace, trust=trust)

    result = repository_pull(
        ctx,
        {
            "plan": "pull",
            "approval_id": "unused-when-trusted",
            "strategy": "ff-only",
        },
    )
    assert result["pulled"] is True
    assert (workspace / "README").read_text(encoding="utf-8") == "two\n"


def test_untrusted_remote_denied(tmp_path, twin_repos):
    workspace, _remote = twin_repos
    trust = RepositoryTrust([], tmp_path / "trusted-repos.json")
    ctx = _ctx(tmp_path, workspace, trust=trust)
    with pytest.raises(ToolExecutionError, match="not allowlisted"):
        repository_pull(
            ctx,
            {"plan": "pull", "approval_id": "x"},
        )
