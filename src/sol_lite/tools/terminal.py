"""Controlled cross-platform terminal tool."""
from __future__ import annotations

import time
from pathlib import Path

from ..core.exceptions import PermissionDenied, ToolExecutionError
from ..permissions.scopes import TERMINAL_READ, TERMINAL_WRITE
from ..security.command_guard import classify_command, command_name, validate_command
from ..security.path_guard import resolve_workspace_path
from ..security.secrets import redact, resolve_command
from .base import ToolDefinition


def execute_terminal_command(ctx, args):
    root = Path(ctx.workspace_root).resolve()
    cwd = resolve_workspace_path(args.get("cwd", "."), root, must_exist=True)
    if not cwd.is_dir():
        raise NotADirectoryError(cwd)
    command = str(args["command"])
    template, rendered, secrets = resolve_command(command, ctx)
    shell = str(args.get("shell") or ctx.platform.available_shells()[0])
    if shell not in ctx.platform.available_shells():
        raise PermissionDenied(f"Requested shell '{shell}' is not available on this machine.")
    allowed, blocked = ctx.permission_engine.policy.terminal_lists()
    validate_command(rendered, allowed, blocked, shell)
    classification = classify_command(rendered, shell)
    listed = {str(item).casefold() for item in allowed}
    if command_name(rendered).casefold() not in listed and classification == "read":
        classification = "approval"
    scope = TERMINAL_READ if classification == "read" else TERMINAL_WRITE
    plan = str(args.get("plan", ""))
    ctx.permission_engine.check(
        scope,
        approval_id=args.get("approval_id"),
        operation="execute_terminal_command",
        target=template,
        arguments={"command": template, "cwd": str(cwd), "shell": shell},
        plan=plan,
        session_id=getattr(ctx, "session_id", None),
        agent_id=getattr(ctx, "agent_id", None),
    )
    timeout = float(args.get("timeout_seconds", 120))
    started = time.monotonic()
    try:
        result = ctx.platform.run_shell(rendered, cwd, timeout, shell=shell)
    except Exception as exc:
        ctx.fault_log.log(category="terminal", code="EXECUTION_ERROR", command=template, shell=shell, error=str(exc))
        raise ToolExecutionError(str(exc)) from exc
    duration = time.monotonic() - started
    ctx.audit.record("terminal.execute", command=template, cwd=str(cwd), shell=shell,
                     exit_code=result.returncode, duration_seconds=duration, classification=classification,
                     session_id=ctx.session_id)
    return {"command": template, "cwd": str(cwd), "shell": shell, "classification": classification,
            "exit_code": result.returncode, "stdout": redact(result.stdout, secrets),
            "stderr": redact(result.stderr, secrets),
            "duration_seconds": duration}


def terminal_tools():
    return [ToolDefinition(
        "execute_terminal_command",
        "Execute a command in an explicitly selected available shell (cmd, powershell, pwsh, bash, or zsh). Listed read-only commands may run without approval. Other non-blocked commands require human approval, and the user can let that approval last the session. Destructive commands and nested shells (bash -c, cmd /c, powershell -Command) stay blocked. Pick the shell with the shell argument instead.",
        {"type": "object", "properties": {
            "command": {"type": "string"},
            "cwd": {"type": "string"},
            "shell": {"type": "string", "enum": ["cmd", "powershell", "pwsh", "bash", "zsh"]},
            "timeout_seconds": {"type": "number", "minimum": 1, "maximum": 900},
            "plan": {"type": "string"}, "approval_id": {"type": "string"}},
         "required": ["command"]}, execute_terminal_command
    )]
