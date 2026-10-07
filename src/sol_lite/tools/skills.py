"""Agent-accessible skill discovery and installation tools."""
from __future__ import annotations

from ..permissions.scopes import NETWORK, SKILL_INSPECT, SKILL_INSTALL
from .base import ToolDefinition


def _requires_network(source: str) -> bool:
    return source.casefold().startswith(("https://github.com/", "http://github.com/"))


def _check_network(ctx, source: str, approval_id: str | None = None) -> None:
    if _requires_network(source):
        ctx.permission_engine.check(
            NETWORK,
            approval_id=approval_id,
            operation="network.skill_source_access",
            target=source,
            arguments={"source": source},
            plan=f"Inspect external Agent Skill source: {source}",
        )


def _serialize(records):
    return [{
        "skill_id": record.skill_id,
        "name": record.name,
        "description": record.description,
        "source": record.source,
        "source_type": record.source_type,
        "source_ref": record.source_ref,
        "sha256": record.sha256,
        "warnings": record.warnings,
    } for record in records]


def skill_discover(ctx, args):
    ctx.permission_engine.check(SKILL_INSPECT)
    source = str(args["source"])
    _check_network(ctx, source, args.get("approval_id"))
    return _serialize(ctx.skill_manager.discover(source))


def skill_install(ctx, args):
    source = str(args["source"])
    skill_id = str(args["skill_id"])
    plan = str(args.get("plan", ""))
    agent_id = str(args.get("agent_id", ""))
    _check_network(ctx, source, args.get("approval_id"))
    ctx.permission_engine.check(SKILL_INSPECT)
    records = ctx.skill_manager.discover(source)
    matches = [record for record in records if record.skill_id == skill_id]
    if not matches:
        raise FileNotFoundError(f"Skill '{skill_id}' was not found in source.")
    record = matches[0]
    ctx.permission_engine.check(
        SKILL_INSTALL,
        approval_id=args.get("approval_id"),
        operation="skill_install",
        target=skill_id,
        arguments={"skill_id": skill_id, "source": source, "agent_id": agent_id},
        plan=plan,
    )
    if record.warnings:
        quarantined = ctx.skill_manager.quarantine(record)
        return {"ok": False, "status": quarantined.status, "skill_id": skill_id, "warnings": record.warnings}
    installed = ctx.skill_manager.install(
        record, trust="REVIEWED", agent_ids=[agent_id] if agent_id else []
    )
    return {"ok": True, "status": installed.status, "skill_id": installed.skill_id, "sha256": installed.sha256}


def skill_tools():
    return [
        ToolDefinition(
            "skill_discover",
            "Inspect an Agent Skill source without installing or executing it.",
            {"type": "object", "properties": {"source": {"type": "string"}, "approval_id": {"type": "string"}}, "required": ["source"]},
            skill_discover,
        ),
        ToolDefinition(
            "skill_install",
            "Install one inspected Agent Skill after exact human approval. Suspicious skills are quarantined and never executed.",
            {"type": "object", "properties": {
                "source": {"type": "string"}, "skill_id": {"type": "string"}, "agent_id": {"type": "string"},
                "plan": {"type": "string"}, "approval_id": {"type": "string"},
            }, "required": ["source", "skill_id", "plan"]},
            skill_install,
        ),
    ]
