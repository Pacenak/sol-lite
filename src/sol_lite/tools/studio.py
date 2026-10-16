"""Structured studio checks and file changes. The model does not supply the command."""
from __future__ import annotations

import shlex
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from ..capabilities.risk import RiskClass
from ..core.exceptions import PermissionDenied, ToolExecutionError
from ..permissions.scopes import READ, REMOTE_LIST, WRITE
from ..security.path_guard import resolve_workspace_path
from ..studio.gate import (
    git_tracks,
    http_host_allowed,
    safe_probe_host,
    safe_remote_path,
    snapshot_relative,
    snapshot_untracked,
    write_snapshot,
)
from .base import ToolDefinition
from .filesystem import _approve_workspace_write, _rel


def _nodes(ctx):
    manager = getattr(ctx, "remote_manager", None)
    if manager is None:
        return []
    return list(manager.nodes.values())


def _node(ctx, node_id: str):
    manager = getattr(ctx, "remote_manager", None)
    if manager is None:
        raise RuntimeError("Remote execution is not configured. Add hosts in config/remote-nodes.yaml.")
    return manager.get(str(node_id or "").strip())


def _style(node) -> str:
    transport = node.transport.value
    if transport == "powershell":
        return "powershell"
    if node.platform == "linux" and transport == "ssh":
        return "linux"
    raise ValueError(
        "This host has no file-command style. Linux uses ssh. Windows uses powershell transport."
    )


def _ps(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def studio_inspect(ctx, args):
    check = str(args.get("check") or "").strip()
    ctx.permission_engine.check(
        READ,
        operation="studio_inspect",
        target=check,
        arguments={"check": check},
        plan="Inspect before a studio change",
    )
    if check == "path":
        return _inspect_path(ctx, str(args.get("path") or ""))
    if check == "ping":
        return _inspect_ping(ctx, str(args.get("node_id") or ""))
    if check == "remote_path":
        return _inspect_remote_path(ctx, str(args.get("node_id") or ""), str(args.get("path") or ""))
    if check == "http":
        return _inspect_http(ctx, str(args.get("url") or ""))
    raise ValueError("check must be path, ping, remote_path, or http.")


def _inspect_path(ctx, raw: str):
    root = Path(ctx.workspace_root).resolve()
    path = resolve_workspace_path(raw, root)
    if not path.exists():
        return {"check": "path", "path": _rel(path, root), "exists": False, "tracked": False, "kind": "missing"}
    kind = "dir" if path.is_dir() else "file" if path.is_file() else "other"
    tracked = git_tracks(root, path) if path.is_file() else False
    return {"check": "path", "path": _rel(path, root), "exists": True, "tracked": tracked, "kind": kind}


def _inspect_ping(ctx, node_id: str):
    node = _node(ctx, node_id)
    host = safe_probe_host(node.hostname)
    ctx.permission_engine.check(
        REMOTE_LIST,
        operation="studio_inspect",
        target=node.id,
        arguments={"node_id": node.id},
        plan=f"Ping {node.id}",
    )
    platform = getattr(ctx.platform, "name", "")
    if platform == "windows":
        command = f"ping -n 1 -w 1000 {host}"
    else:
        command = f"ping -c 1 -W 1 {host}"
    result = ctx.platform.run_shell(command, Path(ctx.workspace_root), 15, shell=None)
    ctx.audit.record("studio.inspect", check="ping", node=node.id, command=command, exit_code=result.returncode)
    return {
        "check": "ping",
        "node_id": node.id,
        "hostname": host,
        "environment": node.environment,
        "exit_code": result.returncode,
        "reachable": result.returncode == 0,
        "stdout": result.stdout,
    }


def _inspect_remote_path(ctx, node_id: str, raw_path: str):
    node = _node(ctx, node_id)
    path = safe_remote_path(raw_path)
    style = _style(node)
    if style == "linux":
        command = "test -e " + shlex.quote(path)
    else:
        command = "Test-Path -LiteralPath " + _ps(path)
    result = ctx.remote_manager.run_prepared(
        node.id,
        command,
        audit_command=f"test -e {path}",
        session_id=str(getattr(ctx, "session_id", "") or ""),
    )
    return {
        "check": "remote_path",
        "node_id": node.id,
        "path": path,
        "environment": node.environment,
        "exists": result.exit_code == 0,
        "exit_code": result.exit_code,
    }


def _inspect_http(ctx, url: str):
    if not http_host_allowed(url, _nodes(ctx)):
        raise PermissionDenied("HTTP probe host is not localhost or a configured node.")
    request = Request(url, method="GET")
    try:
        with urlopen(request, timeout=5) as response:
            status = int(response.status)
    except HTTPError as exc:
        status = int(exc.code)
    except URLError as exc:
        raise ToolExecutionError(f"HTTP probe failed: {exc.reason}") from exc
    ctx.audit.record("studio.inspect", check="http", url=url, status=status)
    return {"check": "http", "url": url, "status": status}


def studio_create(ctx, args):
    root = Path(ctx.workspace_root).resolve()
    path = resolve_workspace_path(str(args.get("path") or ""), root)
    if path.exists():
        return {"ok": False, "result": "exists", "path": _rel(path, root)}
    content = str(args.get("content", ""))
    plan = str(args.get("plan") or "Create a file that is not already there")
    _approve_workspace_write(
        ctx,
        path,
        root,
        operation="studio_create",
        arguments={"path": str(path), "content": content},
        plan=plan,
        approval_id=args.get("approval_id"),
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    ctx.audit.record("studio.create", path=str(path), bytes=len(content.encode("utf-8")))
    return {"ok": True, "result": "created", "path": _rel(path, root)}


def studio_edit(ctx, args):
    node_id = str(args.get("node_id") or "").strip()
    if node_id:
        return _edit_remote(ctx, node_id, args)
    return _edit_local(ctx, args)


def _edit_local(ctx, args):
    from .filesystem import edit_workspace_file

    return edit_workspace_file(ctx, args)


def _edit_remote(ctx, node_id: str, args):
    node = _node(ctx, node_id)
    if node.environment != "lab":
        raise PermissionDenied(f"Remote node {node.id} is inspect-only until environment is lab.")
    path = safe_remote_path(str(args.get("path") or ""))
    content = str(args.get("content", ""))
    plan = str(args.get("plan") or f"Edit {path} on {node.id}")
    ctx.permission_engine.check(
        WRITE,
        approval_id=args.get("approval_id"),
        operation="studio_edit",
        target=f"{node.id}:{path}",
        arguments={"node_id": node.id, "path": path},
        plan=plan,
        session_id=getattr(ctx, "session_id", None),
        agent_id=getattr(ctx, "agent_id", None),
    )
    current = _read_remote(ctx, node, path)
    state_root = getattr(ctx, "state_root", None)
    if not state_root:
        raise ToolExecutionError("Remote edit requires the SOL-Lite state directory.")
    snapshot = write_snapshot(Path(state_root), node.id, snapshot_relative(path), current)
    _write_remote(ctx, node, path, content.encode("utf-8"))
    ctx.audit.record("studio.edit", node=node.id, path=path, snapshot=str(snapshot))
    return {"ok": True, "node_id": node.id, "path": path, "snapshot": str(snapshot)}


def studio_quarantine(ctx, args):
    node_id = str(args.get("node_id") or "").strip()
    if node_id:
        return _quarantine_remote(ctx, node_id, args)
    return _quarantine_local(ctx, args)


def _quarantine_local(ctx, args):
    root = Path(ctx.workspace_root).resolve()
    path = resolve_workspace_path(str(args.get("path") or ""), root, must_exist=True)
    if not path.is_file():
        raise ToolExecutionError("Quarantine accepts a file. Directories stay in place.")
    plan = str(args.get("plan") or "Move the file into the backup store")
    _approve_workspace_write(
        ctx,
        path,
        root,
        operation="studio_quarantine",
        arguments={"path": str(path)},
        plan=plan,
        approval_id=args.get("approval_id"),
    )
    original = path.read_bytes()
    snapshot = snapshot_untracked(ctx, path)
    if snapshot is None:
        state_root = getattr(ctx, "state_root", None)
        if not state_root:
            raise ToolExecutionError("Quarantine requires the SOL-Lite state directory.")
        destination = write_snapshot(
            Path(state_root),
            "local",
            snapshot_relative(str(path.resolve().relative_to(root))),
            original,
        )
        snapshot = str(destination)
    path.unlink()
    ctx.audit.record("studio.quarantine", path=str(path), snapshot=snapshot)
    return {"ok": True, "path": _rel(path, root), "snapshot": snapshot, "removed": True}


def _quarantine_remote(ctx, node_id: str, args):
    node = _node(ctx, node_id)
    if node.environment != "lab":
        raise PermissionDenied(f"Remote node {node.id} is inspect-only until environment is lab.")
    path = safe_remote_path(str(args.get("path") or ""))
    plan = str(args.get("plan") or f"Quarantine {path} on {node.id}")
    ctx.permission_engine.check(
        WRITE,
        approval_id=args.get("approval_id"),
        operation="studio_quarantine",
        target=f"{node.id}:{path}",
        arguments={"node_id": node.id, "path": path},
        plan=plan,
        session_id=getattr(ctx, "session_id", None),
        agent_id=getattr(ctx, "agent_id", None),
    )
    state_root = getattr(ctx, "state_root", None)
    if not state_root:
        raise ToolExecutionError("Remote quarantine requires the SOL-Lite state directory.")
    current = _read_remote(ctx, node, path)
    snapshot = write_snapshot(Path(state_root), node.id, snapshot_relative(path), current)
    style = _style(node)
    if style == "linux":
        command = "rm -- " + shlex.quote(path)
    else:
        command = "Remove-Item -LiteralPath " + _ps(path)
    result = ctx.remote_manager.run_prepared(
        node.id,
        command,
        audit_command=f"quarantine {path}",
        session_id=str(getattr(ctx, "session_id", "") or ""),
    )
    if result.exit_code != 0:
        raise ToolExecutionError(result.stderr or "Remote quarantine did not remove the file.")
    ctx.audit.record("studio.quarantine", node=node.id, path=path, snapshot=str(snapshot))
    return {"ok": True, "node_id": node.id, "path": path, "snapshot": str(snapshot), "removed": True}


def _read_remote(ctx, node, path: str) -> bytes:
    style = _style(node)
    if style == "linux":
        command = "cat -- " + shlex.quote(path)
    else:
        command = "Get-Content -Raw -LiteralPath " + _ps(path)
    result = ctx.remote_manager.run_prepared(
        node.id,
        command,
        audit_command=f"read {path}",
        session_id=str(getattr(ctx, "session_id", "") or ""),
    )
    if result.exit_code != 0:
        raise ToolExecutionError(result.stderr or "Remote read failed.")
    data = (result.stdout or "").encode("utf-8")
    if len(data) > 1_000_000:
        raise ToolExecutionError("Remote file is larger than the studio edit limit.")
    return data


def _write_remote(ctx, node, path: str, data: bytes) -> None:
    import base64

    payload = base64.b64encode(data).decode("ascii")
    style = _style(node)
    if style == "linux":
        command = (
            "python3 -c "
            + shlex.quote(
                "import base64,pathlib,sys; "
                "pathlib.Path(sys.argv[1]).write_bytes(base64.b64decode(sys.argv[2]))"
            )
            + " "
            + shlex.quote(path)
            + " "
            + shlex.quote(payload)
        )
    else:
        command = (
            "Set-Content -LiteralPath "
            + _ps(path)
            + " -Value ([Text.Encoding]::UTF8.GetString([Convert]::FromBase64String("
            + _ps(payload)
            + "))) -NoNewline"
        )
    result = ctx.remote_manager.run_prepared(
        node.id,
        command,
        audit_command=f"write {path} bytes={len(data)}",
        session_id=str(getattr(ctx, "session_id", "") or ""),
    )
    if result.exit_code != 0:
        raise ToolExecutionError(result.stderr or "Remote write failed.")


def studio_tools():
    read_only = (RiskClass.READ_ONLY,)
    mutating = (RiskClass.MUTATING,)
    return [
        ToolDefinition(
            "studio_inspect",
            "Check one fact before a studio change: path, ping, remote_path, or http. "
            "The check is fixed. A missing host, a production node, and an unknown address "
            "are reported and not changed.",
            {"type": "object", "properties": {
                "check": {"type": "string", "enum": ["path", "ping", "remote_path", "http"]},
                "path": {"type": "string"},
                "node_id": {"type": "string"},
                "url": {"type": "string"},
            }, "required": ["check"]},
            studio_inspect,
            permissions=(READ,),
            risk=read_only,
        ),
        ToolDefinition(
            "studio_create",
            "Create a workspace file that is not already there. An existing path is left unchanged.",
            {"type": "object", "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"},
                "plan": {"type": "string"},
                "approval_id": {"type": "string"},
            }, "required": ["path", "content", "plan"]},
            studio_create,
            permissions=(WRITE,),
            risk=mutating,
            mutability=True,
        ),
        ToolDefinition(
            "studio_edit",
            "Edit a file. Git-tracked workspace files use Git history. Other files are copied "
            "into the SOL-Lite backup store first. Production and unlabelled remote hosts are refused.",
            {"type": "object", "properties": {
                "path": {"type": "string"},
                "old_string": {"type": "string"},
                "new_string": {"type": "string"},
                "content": {"type": "string"},
                "replace_all": {"type": "boolean"},
                "node_id": {"type": "string"},
                "plan": {"type": "string"},
                "approval_id": {"type": "string"},
            }, "required": ["path", "plan"]},
            studio_edit,
            permissions=(WRITE,),
            risk=mutating,
            mutability=True,
        ),
        ToolDefinition(
            "studio_quarantine",
            "Move a file into the SOL-Lite backup store. This is the only remove. "
            "Directories, production hosts, and hosts with no environment stay in place.",
            {"type": "object", "properties": {
                "path": {"type": "string"},
                "node_id": {"type": "string"},
                "plan": {"type": "string"},
                "approval_id": {"type": "string"},
            }, "required": ["path", "plan"]},
            studio_quarantine,
            permissions=(WRITE,),
            risk=mutating,
            mutability=True,
        ),
    ]
