from types import SimpleNamespace
from unittest.mock import patch

import pytest

from sol_lite.audit.logger import AuditLogger
from sol_lite.core.exceptions import ToolExecutionError
from sol_lite.faults.log import FaultLog
from sol_lite.permissions.approvals import ApprovalManager
from sol_lite.permissions.engine import PermissionEngine
from sol_lite.permissions.policy import PermissionPolicy
from sol_lite.repository.trust import RepositoryTrust
from sol_lite.tools.base import ToolContext
from sol_lite.tools import hosting as hosting_mod


def _git(cwd, *args):
    import subprocess

    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )


def _ctx(tmp_path, root, trust):
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


def test_hosting_pr_create_uses_gh_when_trusted(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init")
    _git(root, "config", "user.email", "sol@example.com")
    _git(root, "config", "user.name", "SOL")
    (root / "a.txt").write_text("a\n", encoding="utf-8")
    _git(root, "add", "a.txt")
    _git(root, "commit", "-m", "init")

    trust = RepositoryTrust([tmp_path], tmp_path / "trusted-repos.json")
    trust.confirm(root)
    ctx = _ctx(tmp_path, root, trust)

    class Result:
        returncode = 0
        stdout = "https://github.com/example/repo/pull/1\n"
        stderr = ""

    with patch.object(hosting_mod, "_run_gh", return_value=Result()) as run:
        out = hosting_mod.hosting_pr_create(
            ctx,
            {
                "title": "Ship it",
                "body": "notes",
                "plan": "open pr",
                "approval_id": "unused",
            },
        )
    assert out["created"] is True
    assert "pull/1" in out["url"]
    assert run.called


def test_hosting_pr_merge_requires_write_approval_even_when_trusted(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init")
    _git(root, "config", "user.email", "sol@example.com")
    _git(root, "config", "user.name", "SOL")
    (root / "a.txt").write_text("a\n", encoding="utf-8")
    _git(root, "add", "a.txt")
    _git(root, "commit", "-m", "init")

    trust = RepositoryTrust([tmp_path], tmp_path / "trusted-repos.json")
    trust.confirm(root)
    ctx = _ctx(tmp_path, root, trust)

    with pytest.raises(Exception):
        hosting_mod.hosting_pr_merge(
            ctx,
            {"method": "squash", "plan": "merge pr", "approval_id": "missing"},
        )


def test_missing_gh_is_clear(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init")
    trust = RepositoryTrust([tmp_path], tmp_path / "trusted-repos.json")
    trust.confirm(root)
    ctx = _ctx(tmp_path, root, trust)
    with patch.object(
        hosting_mod,
        "_gh_executable",
        side_effect=ToolExecutionError("GitHub CLI (gh) was not found on PATH."),
    ):
        with pytest.raises(ToolExecutionError, match="gh"):
            hosting_mod.hosting_pr_status(
                ctx, {"plan": "status", "approval_id": "x"}
            )
