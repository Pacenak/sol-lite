"""Tools that load and advance a parsed studio checklist."""
from __future__ import annotations

from pathlib import Path

from ..capabilities.risk import RiskClass
from ..core.exceptions import PermissionDenied, ToolExecutionError
from ..permissions.scopes import READ
from ..procedures import parse_procedure
from ..procedures.runner import ProcedureSession
from ..procedures.store import read_store, write_store
from ..security.path_guard import resolve_workspace_path
from ..studio.gate import bind_hosts
from .base import ToolDefinition
from .terminal import execute_terminal_command


def _source_name(path, root) -> str:
    return str(path.resolve().relative_to(Path(root).resolve())).replace("\\", "/")


def _persist(ctx) -> None:
    session = getattr(ctx, "procedure_session", None)
    state_root = getattr(ctx, "state_root", None)
    source = getattr(session, "source_name", "") if session is not None else ""
    if session is None or not state_root or not source:
        return
    write_store(state_root, ctx.workspace_root, session.snapshot_state(source))


def procedure_load(ctx, args):
    ctx.permission_engine.check(READ)
    path = resolve_workspace_path(
        str(args["path"]),
        ctx.workspace_root,
        must_exist=True,
    )
    if path.suffix.casefold() != ".md":
        raise ValueError("Procedure file must be a Markdown file.")
    source = _source_name(path, ctx.workspace_root)
    existing = read_store(getattr(ctx, "state_root", None), ctx.workspace_root)
    if existing and existing.get("corrupt"):
        raise ValueError("state_corrupt")
    if (
        existing
        and existing.get("source")
        and existing.get("source") != source
        and not args.get("replace_confirmed")
    ):
        return {
            "ok": False,
            "replace_required": True,
            "ask": f"A checklist for {existing['source']} is already open. Confirm before replacing it.",
            "source": existing["source"],
            "complete": False,
            "steps": [],
        }
    document = parse_procedure(
        path.read_text(encoding="utf-8"),
        source=path.name,
    )
    session = ProcedureSession(document)
    session.source_name = source
    if existing and existing.get("source") == source and not args.get("replace_confirmed"):
        session.restore(existing)
    ctx.procedure_session = session
    ctx.audit.record(
        "procedure.load",
        source=source,
        steps=len(document.steps),
    )
    _persist(ctx)
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
        if step.classification == "candidate":
            manager = getattr(ctx, "remote_manager", None)
            nodes = list(manager.nodes.values()) if manager is not None else []
            step.evidence["binding"] = bind_hosts(step.action_command, nodes)
        if step.classification == "human_gate" and not step.evidence.get("asked_turn"):
            step.evidence["pending_turn"] = int(getattr(ctx, "turn_id", 0) or 0)
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

    result = session.advance(execute, approval_id=approval_id)
    _persist(ctx)
    return result


def procedure_acknowledge(ctx, args):
    session = getattr(ctx, "procedure_session", None)
    if session is None:
        raise ValueError("No procedure is loaded.")
    step_id = str(args.get("step_id") or "").strip()
    if not step_id:
        raise ValueError("step_id is required")
    result = session.acknowledge(
        step_id,
        str(getattr(ctx, "user_text", "") or ""),
        int(getattr(ctx, "turn_id", 0) or 0),
    )
    _persist(ctx)
    return result


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
        ToolDefinition(
            "procedure_acknowledge",
            "Settle the current human-gate row after a later user reply says it is done. "
            "The reply is taken from the user message, not from the model.",
            {
                "type": "object",
                "properties": {"step_id": {"type": "string"}},
                "required": ["step_id"],
            },
            procedure_acknowledge,
            permissions=("filesystem.read",),
            risk=read_only,
        ),
    ]
