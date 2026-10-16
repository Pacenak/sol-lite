"""Studio change gate: discover, copy, then change. These tests use the tools."""
from __future__ import annotations

import hashlib
import json
import subprocess
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from types import SimpleNamespace

import pytest

from sol_lite.audit.logger import AuditLogger
from sol_lite.core.exceptions import PermissionDenied, ToolExecutionError
from sol_lite.credentials.manager import CredentialReference
from sol_lite.faults.log import FaultLog
from sol_lite.permissions.approvals import ApprovalManager
from sol_lite.permissions.engine import PermissionEngine
from sol_lite.permissions.policy import PermissionPolicy
from sol_lite.platform import get_platform_adapter
from sol_lite.procedures import parse_procedure
from sol_lite.procedures.runner import ProcedureSession
from sol_lite.remote import RemoteNode, RemoteNodeManager, RemoteTransport
from sol_lite.studio.gate import bind_hosts
from sol_lite.tools import ToolContext
from sol_lite.tools.filesystem import edit_workspace_file
from sol_lite.tools.procedure import procedure_acknowledge, procedure_advance, procedure_load
from sol_lite.tools.remote import _execute
from sol_lite.tools.studio import studio_create, studio_edit, studio_inspect, studio_quarantine

VOLUME = """
## Steam upload agent

```bash
ping {{GW_SANDBOX}}
curl -sI http://10.10.66.10:8080
```

| Host | IP | Role |
|------|----|------|
| plg-edge01 | 10.10.66.11 | edge |
"""

POLICY = {
    "permissions": {
        "filesystem": {
            "read": {"enabled": True, "approval_required": False},
            "write": {"enabled": True, "approval_required": False},
        },
        "terminal": {
            "enabled": True,
            "approval_required": False,
            "allowed_commands": ["echo", "ping", "python", "python3"],
            "blocked_commands": ["rm", "del", "Remove-Item"],
            "read": {"enabled": True, "approval_required": False},
            "write": {"enabled": True, "approval_required": True},
        },
        "remote": {
            "list": {"enabled": True, "approval_required": False},
            "execute": {"enabled": True, "approval_required": False},
        },
    }
}


class _Memory:
    def __init__(self, values):
        self.values = values

    def resolve(self, reference: CredentialReference):
        if reference.provider == "plg-studio" and reference.key in self.values:
            return self.values[reference.key]
        raise KeyError(reference.key)


class _QuietHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(204)
        self.end_headers()

    def log_message(self, format, *args):
        return


def _context(root, tmp_path, *, nodes=(), credentials=None):
    engine = PermissionEngine(POLICY and PermissionPolicy(POLICY), ApprovalManager())
    manager = RemoteNodeManager(engine, AuditLogger(tmp_path / "remote-audit.jsonl"), nodes)
    return ToolContext(
        workspace_root=root,
        permission_engine=engine,
        audit=AuditLogger(tmp_path / "audit.jsonl"),
        fault_log=FaultLog(tmp_path / "faults.json"),
        platform=get_platform_adapter(),
        remote_manager=manager,
        credential_manager=_Memory(credentials or {}),
        state_root=tmp_path / "state",
    )


def _workspace(tmp_path):
    root = tmp_path / "workspace"
    root.mkdir()
    return root


def test_volume_shape_lists_the_fenced_step_and_runs_nothing():
    document = parse_procedure(VOLUME, source="46.md")
    assert any(step.classification == "candidate" and "10.10.66.10" in step.action_command
               for step in document.steps)
    calls = []
    session = ProcedureSession(document)
    status = session.advance(lambda command: calls.append(command))
    assert calls == []
    assert status["stop_reason"] == "candidate"
    assert "was not run" in status["ask"]


def test_host_is_bound_only_when_a_configured_node_has_that_name():
    nodes = [RemoteNode("edge", "10.10.66.10", "linux", RemoteTransport.SSH, environment="lab")]
    bound = bind_hosts("curl -sI http://10.10.66.10:8080", nodes)
    assert bound["bound"] == ["10.10.66.10"]
    assert bound["unbound"] == []
    missing = bind_hosts("curl -sI http://10.10.66.11:8080", nodes)
    assert missing["unbound"] == ["10.10.66.11"]
    assert "10.10.66.11" not in missing["bound"]


def test_existing_path_is_not_created(tmp_path):
    root = _workspace(tmp_path)
    target = root / "already.txt"
    target.write_text("keep\n", encoding="utf-8")
    ctx = _context(root, tmp_path)
    result = studio_create(ctx, {"path": "already.txt", "content": "new\n", "plan": "create"})
    assert result["result"] == "exists"
    assert target.read_text(encoding="utf-8") == "keep\n"


def test_untracked_edit_keeps_a_hash_matched_copy(tmp_path):
    root = _workspace(tmp_path)
    target = root / "live.conf"
    original = b"port=1\n"
    target.write_bytes(original)
    ctx = _context(root, tmp_path)
    result = edit_workspace_file(ctx, {
        "path": "live.conf",
        "old_string": "port=1",
        "new_string": "port=2",
        "plan": "change the port",
    })
    assert b"port=2" in target.read_bytes()
    copies = list((tmp_path / "state" / "backups").rglob("live.conf"))
    assert len(copies) == 1
    assert copies[0].read_bytes() == original
    assert hashlib.sha256(copies[0].read_bytes()).hexdigest() == hashlib.sha256(original).hexdigest()
    assert result["snapshot"] == str(copies[0])


def test_failed_snapshot_leaves_the_source_unchanged(tmp_path, monkeypatch):
    root = _workspace(tmp_path)
    target = root / "live.conf"
    target.write_text("port=1\n", encoding="utf-8")
    ctx = _context(root, tmp_path)

    def boom(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr("sol_lite.studio.gate.write_snapshot", boom)
    with pytest.raises(OSError, match="disk full"):
        edit_workspace_file(ctx, {
            "path": "live.conf",
            "old_string": "port=1",
            "new_string": "port=2",
            "plan": "change the port",
        })
    assert target.read_text(encoding="utf-8") == "port=1\n"


def test_git_tracked_edit_does_not_write_a_backup(tmp_path):
    root = _workspace(tmp_path)
    target = root / "tracked.txt"
    target.write_text("one\n", encoding="utf-8")
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True)
    subprocess.run(["git", "add", "tracked.txt"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-m", "add"], cwd=root, check=True, capture_output=True)
    ctx = _context(root, tmp_path)
    edit_workspace_file(ctx, {
        "path": "tracked.txt",
        "old_string": "one",
        "new_string": "two",
        "plan": "edit tracked",
    })
    assert target.read_text(encoding="utf-8") == "two\n"
    assert list((tmp_path / "state" / "backups").rglob("*")) == []


def test_local_quarantine_moves_the_file_into_the_backup_store(tmp_path):
    root = _workspace(tmp_path)
    target = root / "old.conf"
    target.write_text("old\n", encoding="utf-8")
    ctx = _context(root, tmp_path)
    result = studio_quarantine(ctx, {"path": "old.conf", "plan": "retire the file"})
    assert result["removed"] is True
    assert not target.exists()
    copies = list((tmp_path / "state" / "backups").rglob("old.conf"))
    assert len(copies) == 1
    assert copies[0].read_text(encoding="utf-8") == "old\n"


def test_production_remote_edit_does_not_touch_the_host(tmp_path):
    root = _workspace(tmp_path)
    called = []
    node = RemoteNode("core", "10.0.0.8", "linux", RemoteTransport.SSH, environment="production")
    ctx = _context(root, tmp_path, nodes=[node])
    ctx.remote_manager._ssh = SimpleNamespace(run=lambda *args, **kwargs: called.append(args))
    with pytest.raises(PermissionDenied):
        studio_edit(ctx, {
            "node_id": "core",
            "path": "/etc/demo.conf",
            "content": "changed\n",
            "plan": "edit production",
        })
    assert called == []


def test_unlabelled_remote_node_rejects_a_write(tmp_path):
    root = _workspace(tmp_path)
    called = []
    node = RemoteNode("core", "10.0.0.8", "linux", RemoteTransport.SSH)
    ctx = _context(root, tmp_path, nodes=[node])
    ctx.remote_manager._ssh = SimpleNamespace(run=lambda *args, **kwargs: called.append(args))
    with pytest.raises(PermissionDenied):
        _execute(ctx, {"node_id": "core", "command": "echo hi > out.txt", "plan": "write"})
    assert called == []


def test_lab_quarantine_copies_the_remote_file_before_it_is_removed(tmp_path):
    root = _workspace(tmp_path)
    files = {"/etc/demo.conf": "live=1\n"}

    def run(node, command, timeout=120):
        if command.startswith("cat "):
            return SimpleNamespace(command=command, exit_code=0, stdout=files["/etc/demo.conf"], stderr="")
        if command.startswith("rm "):
            files.pop("/etc/demo.conf", None)
            return SimpleNamespace(command=command, exit_code=0, stdout="", stderr="")
        raise AssertionError(command)

    node = RemoteNode("build", "10.0.0.9", "linux", RemoteTransport.SSH, environment="lab")
    ctx = _context(root, tmp_path, nodes=[node])
    ctx.remote_manager._ssh = SimpleNamespace(run=run)
    result = studio_quarantine(ctx, {
        "node_id": "build",
        "path": "/etc/demo.conf",
        "plan": "retire the lab file",
    })
    assert "/etc/demo.conf" not in files
    snapshot = list((tmp_path / "state" / "backups").rglob("demo.conf"))
    assert len(snapshot) == 1
    assert snapshot[0].read_text(encoding="utf-8") == "live=1\n"
    assert result["snapshot"] == str(snapshot[0])
    audit = (tmp_path / "remote-audit.jsonl").read_text(encoding="utf-8")
    assert "rm --" not in audit
    assert "quarantine /etc/demo.conf" in audit


def test_secret_stays_out_of_the_audit_and_the_tool_result(tmp_path, monkeypatch):
    monkeypatch.delenv("STEAM_TOKEN", raising=False)
    root = _workspace(tmp_path)
    seen = []

    def run(node, command, timeout=120):
        seen.append(command)
        return SimpleNamespace(command=command, exit_code=0, stdout="token=steam-secret-value\n", stderr="")

    node = RemoteNode("build", "10.0.0.9", "linux", RemoteTransport.SSH, environment="lab")
    ctx = _context(root, tmp_path, nodes=[node], credentials={"STEAM_TOKEN": "steam-secret-value"})
    ctx.remote_manager._ssh = SimpleNamespace(run=run)
    result = _execute(ctx, {
        "node_id": "build",
        "command": "echo {{STEAM_TOKEN}}",
        "plan": "show the name only",
    })
    assert seen == ["echo steam-secret-value"]
    assert "steam-secret-value" not in result["stdout"]
    assert "{{STEAM_TOKEN}}" in result["stdout"]
    assert result["command"] == "echo {{STEAM_TOKEN}}"
    audit = (tmp_path / "remote-audit.jsonl").read_text(encoding="utf-8")
    assert "steam-secret-value" not in audit
    assert "{{STEAM_TOKEN}}" in audit


def test_missing_secret_runs_nothing(tmp_path, monkeypatch):
    monkeypatch.delenv("STEAM_TOKEN", raising=False)
    root = _workspace(tmp_path)
    called = []
    node = RemoteNode("build", "10.0.0.9", "linux", RemoteTransport.SSH, environment="lab")
    ctx = _context(root, tmp_path, nodes=[node])
    ctx.remote_manager._ssh = SimpleNamespace(run=lambda *args, **kwargs: called.append(args))
    with pytest.raises(ValueError, match="missing_secret: STEAM_TOKEN"):
        _execute(ctx, {"node_id": "build", "command": "echo {{STEAM_TOKEN}}", "plan": "missing"})
    assert called == []


def test_ping_and_http_use_fixed_targets(tmp_path):
    root = _workspace(tmp_path)
    node = RemoteNode("edge", "127.0.0.1", "linux", RemoteTransport.SSH, environment="lab")
    ctx = _context(root, tmp_path, nodes=[node])
    ping = studio_inspect(ctx, {"check": "ping", "node_id": "edge"})
    assert ping["hostname"] == "127.0.0.1"
    assert ping["reachable"] is True

    server = HTTPServer(("127.0.0.1", 0), _QuietHandler)
    port = server.server_address[1]
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        probed = studio_inspect(ctx, {"check": "http", "url": f"http://127.0.0.1:{port}/health"})
        assert probed["status"] == 204
        with pytest.raises(PermissionDenied):
            studio_inspect(ctx, {"check": "http", "url": "http://example.com/health"})
    finally:
        server.shutdown()


def test_checklist_progress_survives_a_new_session(tmp_path):
    root = _workspace(tmp_path)
    (root / "checklist.md").write_text(
        "| Step | Action | Validate |\n|------|--------|----------|\n| A1 | `echo alpha` | `echo ok` |\n",
        encoding="utf-8",
    )
    ctx = _context(root, tmp_path)
    procedure_load(ctx, {"path": "checklist.md"})
    advanced = procedure_advance(ctx, {})
    assert advanced["steps"][0]["outcome"] == "verified"
    again = _context(root, tmp_path)
    loaded = procedure_load(again, {"path": "checklist.md"})
    assert loaded["steps"][0]["outcome"] == "verified"
    assert loaded["complete"] is True
    stored = json.loads(next((tmp_path / "state" / "procedures").glob("*.json")).read_text(encoding="utf-8"))
    assert stored["source"] == "checklist.md"


def test_human_gate_ignores_a_same_turn_done_and_accepts_the_next_reply(tmp_path):
    root = _workspace(tmp_path)
    (root / "checklist.md").write_text(
        "| Step | Action | Validate |\n|------|--------|----------|\n"
        "| S1 | Create the admin password in Bitwarden `PLG Example` | login works |\n"
        "| A1 | `echo alpha` | `echo ok` |\n",
        encoding="utf-8",
    )
    ctx = _context(root, tmp_path)
    ctx.turn_id = 1
    ctx.user_text = "follow the checklist"
    procedure_load(ctx, {"path": "checklist.md"})
    waiting = procedure_advance(ctx, {})
    assert waiting["stop_reason"] == "awaiting_user"
    same = procedure_acknowledge(ctx, {"step_id": "S1"})
    assert same["ok"] is False
    ctx.turn_id = 2
    ctx.user_text = "not yet"
    refused = procedure_acknowledge(ctx, {"step_id": "S1"})
    assert refused["ok"] is False
    ctx.user_text = "done"
    accepted = procedure_acknowledge(ctx, {"step_id": "S1"})
    assert accepted["ok"] is True
    finished = procedure_advance(ctx, {})
    assert finished["steps"][1]["outcome"] == "verified"


def test_directory_quarantine_is_refused(tmp_path):
    root = _workspace(tmp_path)
    (root / "kept").mkdir()
    ctx = _context(root, tmp_path)
    with pytest.raises(ToolExecutionError, match="Directories stay in place"):
        studio_quarantine(ctx, {"path": "kept", "plan": "remove a directory"})
    assert (root / "kept").is_dir()
