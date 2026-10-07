"""Controlled cross-platform terminal tool."""
from __future__ import annotations

import time
from pathlib import Path

from ..core.exceptions import PermissionDenied, ToolExecutionError
from ..permissions.scopes import TERMINAL_READ, TERMINAL_WRITE
from ..security.command_guard import classify_command, validate_command
from ..security.path_guard import resolve_workspace_path
from .base import ToolDefinition


def execute_terminal_command(ctx, args):
    root = Path(ctx.workspace_root).resolve()
    cwd = resolve_workspace_path(args.get("cwd", "."), root, must_exist=True)
    if not cwd.is_dir():
        raise NotADirectoryError(cwd)
    command = str(args["command"])
    shell = str(args.get("shell") or ctx.platform.available_shells()[0])
    if shell not in ctx.platform.available_shells():
        raise PermissionDenied(f"Requested shell '{shell}' is not available on this machine.")
    allowed, blocked = ctx.permission_engine.policy.terminal_lists()
    validate_command(command, allowed, blocked, shell)
    classification = classify_command(command, shell)
    scope = TERMINAL_READ if classification == "read" else TERMINAL_WRITE
    plan = str(args.get("plan", ""))
    ctx.permission_engine.check(
        scope,
        approval_id=args.get("approval_id"),
        operation="execute_terminal_command",
        target=command,
        arguments={"command": command, "cwd": str(cwd), "shell": shell},
        plan=plan,
    )
    timeout = float(args.get("timeout_seconds", 120))
    started = time.monotonic()
    try:
        result = ctx.platform.run_shell(command, cwd, timeout, shell=shell)
    except Exception as exc:
        ctx.fault_log.log(category="terminal", code="EXECUTION_ERROR", command=command, shell=shell, error=str(exc))
        raise ToolExecutionError(str(exc)) from exc
    duration = time.monotonic() - started
    ctx.audit.record("terminal.execute", command=command, cwd=str(cwd), shell=shell,
                     exit_code=result.returncode, duration_seconds=duration, classification=classification,
                     session_id=ctx.session_id)
    return {"command": command, "cwd": str(cwd), "shell": shell, "classification": classification,
            "exit_code": result.returncode, "stdout": result.stdout, "stderr": result.stderr,
            "duration_seconds": duration}


def terminal_tools():
    return [ToolDefinition(
        "execute_terminal_command",
        "Execute a command in an explicitly selected available shell. Read-only commands may run without approval; mutating commands require exact human approval; destructive or nested-shell commands are blocked.",
        {"type": "object", "properties": {
            "command": {"type": "string"},
            "cwd": {"type": "string"},
            "shell": {"type": "string", "enum": ["cmd", "powershell", "pwsh", "bash", "zsh"]},
            "timeout_seconds": {"type": "number", "minimum": 1, "maximum": 900},
            "plan": {"type": "string"}, "approval_id": {"type": "string"}},
         "required": ["command"]}, execute_terminal_command
    )]
