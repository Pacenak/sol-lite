"""Approval-gated remote host tools (SSH / PowerShell remoting)."""
from __future__ import annotations

from ..capabilities.risk import RiskClass
from ..permissions.scopes import REMOTE_EXECUTE, REMOTE_LIST
from ..remote.manager import RemoteExecutionRequest
from ..security.secrets import redact, resolve_command
from .base import ToolDefinition


def _manager(ctx):
    manager = getattr(ctx, "remote_manager", None)
    if manager is None:
        raise RuntimeError(
            "Remote execution is not configured. Add hosts in config/remote-nodes.yaml."
        )
    return manager


def _list_nodes(ctx, _args):
    ctx.permission_engine.check(
        REMOTE_LIST, operation="remote_list_nodes", target="configured remote nodes",
        arguments={}, plan="List configured remote hosts",
    )
    manager = _manager(ctx)
    nodes = []
    for node in manager.nodes.values():
        nodes.append({
            "id": node.id,
            "hostname": node.hostname,
            "platform": node.platform,
            "transport": node.transport.value,
            "port": node.port,
            "username": node.username,
            "enabled": node.enabled,
            "environment": node.environment,
        })
    ctx.audit.record("remote.list", count=len(nodes))
    return {"nodes": nodes, "count": len(nodes)}


def _execute(ctx, args):
    node_id = str(args.get("node_id") or "").strip()
    command = str(args.get("command") or "").strip()
    plan = str(args.get("plan") or "").strip()
    if not node_id or not command or not plan:
        raise ValueError("node_id, command and plan are required")
    if len(command) > 8000 or "\x00" in command:
        raise ValueError("Remote command is empty, too large, or contains NUL")
    template, rendered, secrets = resolve_command(command, ctx)
    timeout = float(args.get("timeout_seconds") or 120)
    if not 1 <= timeout <= 900:
        raise ValueError("timeout_seconds must be between 1 and 900")
    manager = _manager(ctx)
    result = manager.execute(RemoteExecutionRequest(
        session_id=str(getattr(ctx, "session_id", "") or ""),
        node_id=node_id,
        command=template,
        plan=plan,
        approval_id=args.get("approval_id"),
        timeout_seconds=timeout,
        audit_command=template,
        rendered_command=rendered,
    ))
    return {
        "node_id": node_id,
        "command": template,
        "exit_code": result.exit_code,
        "stdout": redact(result.stdout, secrets),
        "stderr": redact(result.stderr, secrets),
    }


def remote_tools():
    return [
        ToolDefinition(
            "remote_list_nodes",
            "List configured remote hosts that SOL-Lite may reach over SSH or PowerShell remoting after approval.",
            {"type": "object", "properties": {}},
            _list_nodes,
            permissions=(REMOTE_LIST,),
            risk=(RiskClass.READ_ONLY,),
            locality="network",
        ),
        ToolDefinition(
            "remote_execute",
            "Run a command on a configured remote host. Requires exact human approval. Uses the local OpenSSH or PowerShell client; credentials are not taken from the model.",
            {"type": "object", "properties": {
                "node_id": {"type": "string"},
                "command": {"type": "string"},
                "plan": {"type": "string"},
                "timeout_seconds": {"type": "number", "minimum": 1, "maximum": 900},
                "approval_id": {"type": "string", "description": "Exact approval token returned by SOL-Lite."},
            }, "required": ["node_id", "command", "plan"]},
            _execute,
            permissions=(REMOTE_EXECUTE,),
            risk=(RiskClass.MUTATING, RiskClass.REMOTE, RiskClass.NETWORK),
            mutability=True,
            locality="network",
        ),
    ]
