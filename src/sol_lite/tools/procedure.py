"""Tools that load and advance a parsed studio checklist."""
from __future__ import annotations

from ..capabilities.risk import RiskClass
from ..core.exceptions import PermissionDenied, ToolExecutionError
from ..permissions.scopes import READ
from ..procedures import parse_procedure
from ..procedures.runner import ProcedureSession
from ..security.path_guard import resolve_workspace_path
from .base import ToolDefinition
from .terminal import execute_terminal_command


def procedure_load(ctx, args):
    ctx.permission_engine.check(READ)
    path = resolve_workspace_path(
        str(args["path"]),
        ctx.workspace_root,
        must_exist=True,
    )
    if path.suffix.casefold() != ".md":
        raise ValueError("Procedure file must be a Markdown file.")
    document = parse_procedure(
        path.read_text(encoding="utf-8"),
        source=path.name,
    )
    session = ProcedureSession(document)
    ctx.procedure_session = session
    ctx.audit.record(
        "procedure.load",
        source=path.name,
        steps=len(document.steps),
    )
    return session.status()


def procedure_status(ctx, args):
    ctx.permission_engine.check(READ)
    session = getattr(ctx, "procedure_session", None)
    if session is None:
        return {
            "ok": False,
            "error": "No procedure is loaded.",
            "complete": False,
            "steps": [],
        }
    return session.status()


def procedure_advance(ctx, args):
    session = getattr(ctx, "procedure_session", None)
    if session is None:
        raise ValueError("No procedure is loaded.")
    approval_id = args.get("approval_id") or None
    step = session._current()
    plan = f"Procedure step in {session.document.source}"
    if step is not None:
        plan = f"Procedure step {step.step_id} in {session.document.source}"
    if (
        step is not None
        and step.classification == "needs_approval"
        and not approval_id
        and step.action_command
        and session.stop_reason not in {"failed", "blocked", "unverifiable"}
    ):
        # Ask through the terminal policy before the runner starts the row.
        # Blocked commands fail here. Approval-gated commands raise and the
        # runtime retries this tool with an approval id.
        execute_terminal_command(ctx, {"command": step.action_command, "plan": plan})

    def execute(command):
        try:
            return execute_terminal_command(ctx, {
                "command": command,
                "approval_id": approval_id,
                "plan": plan,
            })
        except (PermissionDenied, ToolExecutionError) as exc:
            return {
                "exit_code": 1,
                "stdout": "",
                "stderr": str(exc),
                "error": str(exc),
            }

    return session.advance(execute, approval_id=approval_id)


def procedure_tools():
    read_only = (RiskClass.READ_ONLY,)
    path_schema = {
        "type": "object",
        "properties": {"path": {"type": "string"}},
        "required": ["path"],
    }
    return [
        ToolDefinition(
            "procedure_load",
            "Parse a workspace Markdown checklist into classified steps. "
            "This does not run commands.",
            path_schema,
            procedure_load,
            permissions=("filesystem.read",),
            risk=read_only,
        ),
        ToolDefinition(
            "procedure_status",
            "Return the loaded checklist, the current row, and whether every "
            "required row is verified or an explicit human gate.",
            {"type": "object", "properties": {}},
            procedure_status,
            permissions=("filesystem.read",),
            risk=read_only,
        ),
        ToolDefinition(
            "procedure_advance",
            "Run only the current checklist row through the terminal policy. "
            "Mutating rows do not run unless approval_id is present, and a "
            "failed validate stops the checklist.",
            {
                "type": "object",
                "properties": {"approval_id": {"type": "string"}},
            },
            procedure_advance,
            permissions=("filesystem.read",),
            risk=read_only,
        ),
    ]
