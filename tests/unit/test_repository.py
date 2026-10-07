from pathlib import Path
from types import SimpleNamespace

import pytest

from sol_lite.audit.logger import AuditLogger
from sol_lite.core.exceptions import PermissionDenied
from sol_lite.faults.log import FaultLog
from sol_lite.permissions.approvals import ApprovalManager
from sol_lite.permissions.engine import PermissionEngine
from sol_lite.permissions.policy import PermissionPolicy
from sol_lite.tools.base import ToolContext
from sol_lite.tools.repository import (
    repository_branches,
    repository_create_branch,
    repository_create_bundle,
    repository_import_bundle,
    repository_set_remote,
    repository_stage,
    repository_status,
)


@pytest.fixture
def repository_context(tmp_path):
    root = tmp_path / "workspace"
    root.mkdir()
    (root / "src").mkdir()
    (root / "src" / "example.py").write_text("answer = 42\n", encoding="utf-8")
    policy = PermissionPolicy({"permissions": {
        "repository": {
            "read": {"enabled": True, "approval_required": False},
            "write": {"enabled": True, "approval_required": True},
            "remote": {"enabled": False, "approval_required": True},
        }
    }})
    return ToolContext(
        workspace_root=root,
        permission_engine=PermissionEngine(policy, ApprovalManager()),
        audit=AuditLogger(tmp_path / "audit.jsonl"),
        fault_log=FaultLog(tmp_path / "faults.json"),
        platform=SimpleNamespace(),
    )


def _git(cwd, *args):
    import subprocess

    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


def _approve(ctx, operation, target, arguments, plan):
    request = ctx.permission_engine.approvals.request(operation, target, arguments, plan)
    return request.approval_id


def test_repository_status_and_branch(repository_context):
    tool_context = repository_context
    root = Path(tool_context.workspace_root)
    _git(root, "init", "-b", "main")
    _git(root, "config", "user.name", "SOL Test")
    _git(root, "config", "user.email", "sol-test@example.invalid")
    _git(root, "add", "src/example.py")
    _git(root, "commit", "-m", "initial")

    status = repository_status(tool_context, {})
    assert status["branch"] == "main"
    assert status["clean"] is True

    arguments = {"path": str(root), "name": "offline-fix", "start_point": None}
    plan = "create offline-fix branch"
    approval_id = _approve(tool_context, "repository_create_branch", str(root), arguments, plan)
    result = repository_create_branch(
        tool_context,
        {"name": "offline-fix", "plan": plan, "approval_id": approval_id},
    )
    assert result["branch"] == "offline-fix"
    assert any(
        item["name"] == "offline-fix"
        for item in repository_branches(tool_context, {})["branches"]
    )


def test_repository_stage_requires_exact_approval(repository_context):
    tool_context = repository_context
    root = Path(tool_context.workspace_root)
    _git(root, "init", "-b", "main")
    _git(root, "config", "user.name", "SOL Test")
    _git(root, "config", "user.email", "sol-test@example.invalid")
    _git(root, "add", "src/example.py")
    _git(root, "commit", "-m", "initial")
    (root / "src/example.py").write_text("answer = 43\n", encoding="utf-8")

    plan = "stage exact file"
    arguments = {"path": str(root), "paths": ["src/example.py"]}
    approval_id = _approve(tool_context, "repository_stage", str(root), arguments, plan)
    result = repository_stage(
        tool_context,
        {"paths": ["src/example.py"], "plan": plan, "approval_id": approval_id},
    )
    assert result["staged"] == ["src/example.py"]


def test_offline_bundle_round_trip(repository_context):
    tool_context = repository_context
    root = Path(tool_context.workspace_root)
    _git(root, "init", "-b", "main")
    _git(root, "config", "user.name", "SOL Test")
    _git(root, "config", "user.email", "sol-test@example.invalid")
    _git(root, "add", ".")
    _git(root, "commit", "-m", "initial")
    _git(root, "switch", "-c", "offline-fix")
    (root / "src/example.py").write_text("answer = 43\n", encoding="utf-8")
    _git(root, "add", "src/example.py")
    _git(root, "commit", "-m", "offline fix")

    bundle = root / "offline-fix.bundle"
    plan = "create offline bundle"
    arguments = {"path": str(root), "output": str(bundle), "ref": "refs/heads/offline-fix"}
    approval_id = _approve(tool_context, "repository_create_bundle", str(bundle), arguments, plan)
    result = repository_create_bundle(
        tool_context,
        {"output": "offline-fix.bundle", "plan": plan, "approval_id": approval_id},
    )
    assert result["commit"]
    assert bundle.is_file()

    destination = root / "destination"
    _git(root, "clone", str(root), str(destination))
    import_args = {"path": str(destination), "bundle": str(bundle), "branch": "offline-fix"}
    plan2 = "import offline bundle"
    approval2 = _approve(tool_context, "repository_import_bundle", str(destination), import_args, plan2)
    imported = repository_import_bundle(
        tool_context,
        {"path": str(destination), "bundle": str(bundle), "branch": "offline-fix",
         "plan": plan2, "approval_id": approval2},
    )
    assert imported["import_ref"] == "refs/remotes/sol-offline/offline-fix"


def test_remote_operations_are_disabled_by_default(repository_context):
    root = Path(repository_context.workspace_root)
    _git(root, "init", "-b", "main")
    plan = "set origin"
    arguments = {"path": str(root), "name": "origin", "url": "https://example.invalid/repo.git"}
    approval_id = _approve(repository_context, "repository_set_remote", "https://example.invalid/repo.git", arguments, plan)
    with pytest.raises(PermissionDenied, match="Permission scope disabled"):
        repository_set_remote(
            repository_context,
            {"name": "origin", "url": "https://example.invalid/repo.git",
             "plan": plan, "approval_id": approval_id},
        )


def test_repository_status_handles_empty_repository(repository_context):
    root = Path(repository_context.workspace_root)
    _git(root, "init", "-b", "main")
    status = repository_status(repository_context, {})
    assert status["branch"] == "main"
    assert status["head"] is None
    assert status["clean"] is False


def test_remote_url_with_embedded_credentials_is_rejected(repository_context):
    root = Path(repository_context.workspace_root)
    _git(root, "init", "-b", "main")
    plan = "reject credential URL"
    arguments = {"path": str(root), "name": "origin", "url": "https://user:secret@example.invalid/repo.git"}
    approval_id = _approve(
        repository_context,
        "repository_set_remote",
        "https://example.invalid/repo.git",
        arguments,
        plan,
    )
    with pytest.raises(ValueError, match="Embedded credentials"):
        repository_set_remote(
            repository_context,
            {"name": "origin", "url": "https://user:secret@example.invalid/repo.git",
             "plan": plan, "approval_id": approval_id},
        )
