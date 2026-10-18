"""Native tools for the deterministic workspace starter pack."""

from __future__ import annotations

import json
import threading
import time
from collections import OrderedDict

from ..core.exceptions import ApprovalRequired, PermissionDenied
from ..permissions.scopes import READ, WRITE
from ..workspace_pack.pack import AGENTS, Pack
from .base import ToolDefinition

# Exact proposals survive the human approval round trip, including timestamps.
# Bounded, process-local and short-lived; never an authorization store.
_PENDING = OrderedDict()
_LOCK = threading.RLock()
_PA_ONLY = {"workspace_pack_intake", "workspace_pack_init", "workspace_pack_index_refresh"}


def pack_for(ctx, operation):
    agent = getattr(ctx, "agent_id", None)
    if agent not in AGENTS or (operation in _PA_ONLY and agent != "sol_pa"):
        raise PermissionDenied(f"Agent {agent!r} cannot use {operation}")
    ctx.permission_engine.check(READ)
    return Pack(ctx.workspace_root, agent)


def mutate(ctx, args, operation, build):
    """Approve one exact batch, then preflight all paths before writing anything."""
    with _LOCK:
        now = time.monotonic()
        for key, item in list(_PENDING.items()):
            if now - item[0] > 900:
                del _PENDING[key]
        pack = pack_for(ctx, operation)
        clean = {key: value for key, value in args.items() if key != "approval_id"}
        binding = (
            id(ctx.permission_engine),
            str(pack.root),
            pack.agent,
            getattr(ctx, "session_id", None),
            operation,
            json.dumps(clean, sort_keys=True),
        )
        approval_id = args.get("approval_id")
        cached = _PENDING.get(approval_id) if approval_id else None
        if cached:
            _, original_binding, pack, extra = cached
            if binding != original_binding:
                raise PermissionDenied("Approved pack request does not match this operation")
        else:
            extra = build(pack) or {}
        proposal = pack.proposal()
        if not proposal:
            return {
                "ok": True,
                "written": [],
                "skipped": pack.skipped,
                "errors": pack.errors,
                **extra,
            }
        plan = operation + "\n" + "\n".join(f"{row['mode']}: {row['path']}" for row in proposal)
        try:
            ctx.permission_engine.check(
                WRITE,
                operation=operation,
                target=str(pack.root),
                arguments={"input": clean, "files": proposal},
                plan=plan,
                approval_id=approval_id,
                session_id=getattr(ctx, "session_id", None),
                agent_id=pack.agent,
                allow_session=False,
            )
        except ApprovalRequired as exc:
            _PENDING[exc.request.approval_id] = (now, binding, pack, extra)
            while len(_PENDING) > 128:
                _PENDING.popitem(last=False)
            raise
        if approval_id:
            _PENDING.pop(approval_id, None)
        result = pack.commit()
        ctx.audit.record(operation, agent_id=pack.agent, files=result["written"])
        return {**result, **extra}


def workspace_pack_status(ctx, args):
    return pack_for(ctx, "workspace_pack_status").status()


def workspace_pack_intake(ctx, args):
    return mutate(ctx, args, "workspace_pack_intake", lambda pack: pack.answer(args))


def workspace_pack_init(ctx, args):
    return mutate(
        ctx, args, "workspace_pack_init", lambda pack: pack.initialize(args.get("project"))
    )


def workspace_pack_append(ctx, args):
    def build(pack):
        identity = pack.append(args.get("kind"), args.get("fields", {}), args.get("project"))
        return {"entry_id": identity} if identity else {}

    return mutate(ctx, args, "workspace_pack_append", build)


def workspace_pack_index_refresh(ctx, args):
    return mutate(
        ctx, args, "workspace_pack_index_refresh", lambda pack: pack.refresh(args.get("project"))
    )


def workspace_pack_tools():
    common = {"approval_id": {"type": "string"}}
    field_properties = {
        name: {"type": "string"}
        for name in (
            "title",
            "status",
            "owner",
            "due",
            "schedule",
            "tags",
            "notes",
            "changed",
            "tag",
            "content",
        )
    }
    field_properties["files"] = {"type": "array", "items": {"type": "string"}}
    definitions = [
        (
            "workspace_pack_status",
            "Inspect pack state, index drift and malformed plan entries.",
            {},
            [],
        ),
        (
            "workspace_pack_intake",
            (
                "PA only. Get the next fixed question or record one answer/skip. "
                "Ask one question per message. Followups are optional, maximum two, after the core interview."
            ),
            {
                "question_id": {"type": "string"},
                "answer": {"type": "string"},
                "skip": {"type": "boolean"},
                "question": {"type": "string"},
                "project": {"type": "string"},
                **common,
            },
            [],
        ),
        (
            "workspace_pack_init",
            "PA only. After intake, create missing pack files; never overwrite.",
            {"project": {"type": "string"}, **common},
            [],
        ),
        (
            "workspace_pack_append",
            (
                "Append validated agent log, shared tip, task or routine. "
                "Schedules are stored only and never executed."
            ),
            {
                "kind": {
                    "type": "string",
                    "enum": ["changelog", "conversation", "plan_task", "plan_routine"],
                },
                "fields": {
                    "type": "object",
                    "properties": field_properties,
                    "additionalProperties": False,
                },
                "project": {"type": "string"},
                **common,
            },
            ["kind", "fields"],
        ),
        (
            "workspace_pack_index_refresh",
            (
                "PA only. Reconcile workspace and project indexes; "
                "preserve purpose text; mark removed items for one refresh cycle."
            ),
            {"project": {"type": "string"}, **common},
            [],
        ),
    ]
    result = []
    for name, description, properties, required in definitions:
        readonly = name == "workspace_pack_status"
        result.append(
            ToolDefinition(
                name,
                description,
                {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                    "additionalProperties": False,
                },
                globals()[name],
                permissions=(READ,) if readonly else (READ, WRITE),
                risk=("READ_ONLY",) if readonly else ("MUTATING",),
                mutability=not readonly,
            )
        )
    return result
