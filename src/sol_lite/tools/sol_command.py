"""Read-only, sector-scoped SOL-Command context tools."""
from __future__ import annotations

from ..capabilities.risk import RiskClass
from ..permissions.scopes import NETWORK
from .base import ToolDefinition


def _client(ctx):
    client = getattr(ctx, "sol_command", None)
    if client is None:
        raise RuntimeError("SOL-Command is not configured. Local SOL-Lite features remain available.")
    return client


def _status(ctx, _args):
    ctx.permission_engine.check(NETWORK, operation="sol_command_status",
                                target="paired SOL-Command", arguments={},
                                plan="Check paired SOL-Command connection status")
    result = _client(ctx).status()
    ctx.audit.record("sol_command.status", instance_id=result.get("instance_id"))
    return result


def _memories(ctx, args):
    sector = str(args.get("sector_id") or "").strip()
    if not sector:
        raise ValueError("sector_id is required")
    ctx.permission_engine.check(NETWORK, operation="sol_shared_memories",
                                target=sector, arguments={"sector_id": sector},
                                plan=f"Read approved shared memories for sector {sector}")
    result = _client(ctx).list_memories(sector)
    ctx.audit.record("sol_command.memories.read", sector_id=sector,
                     result_count=len(result.get("items") or []))
    return result


def _rag_search(ctx, args):
    sector = str(args.get("sector_id") or "").strip()
    query = str(args.get("query") or "").strip()
    if not sector or not query:
        raise ValueError("sector_id and query are required")
    ctx.permission_engine.check(NETWORK, operation="sol_shared_rag_search",
                                target=sector, arguments={"sector_id": sector, "query": query,
                                                         "limit": int(args.get("limit") or 10)},
                                plan=f"Search shared SOL data in sector {sector}")
    result = _client(ctx).search_rag(sector, query, int(args.get("limit") or 10))
    ctx.audit.record("sol_command.rag.search", sector_id=sector)
    return result


def _jarvis_propose(ctx, args):
    sector = str(args.get("sector_id") or "").strip()
    title = str(args.get("title") or "").strip()
    body = str(args.get("body") or "").strip()
    domain = str(args.get("domain") or "skills").strip()
    if not sector or not title or not body:
        raise ValueError("sector_id, title and body are required")
    ctx.permission_engine.check(NETWORK, operation="sol_command_jarvis_propose",
                               target=f"{sector}:{domain}",
                               arguments={"sector_id": sector, "domain": domain,
                                          "title": title, "body": body}, plan=title)
    result = _client(ctx).propose_to_jarvis(sector_id=sector, title=title,
                                            body=body, domain=domain)
    ctx.audit.record("sol_command.jarvis.proposal", sector_id=sector,
                     domain=domain, request_id=(result.get("ticket") or {}).get("id"))
    return result


def sol_command_tools():
    net_risk = (RiskClass.READ_ONLY, RiskClass.NETWORK)
    net_permission = ("network",)
    return [
        ToolDefinition("sol_command_status", "Check the paired SOL-Command connection and assigned sectors.",
                       {"type": "object", "properties": {}}, _status,
                       permissions=net_permission, risk=net_risk, locality="network"),
        ToolDefinition("sol_shared_memories", "Read shared memories from a Command-assigned sector.",
                       {"type": "object", "properties": {"sector_id": {"type": "string"}},
                        "required": ["sector_id"]}, _memories,
                       permissions=net_permission, risk=net_risk, locality="network"),
        ToolDefinition("sol_shared_rag_search", "Search shared RAG content in a Command-assigned sector.",
                       {"type": "object", "properties": {"sector_id": {"type": "string"},
                        "query": {"type": "string"}, "limit": {"type": "integer", "minimum": 1, "maximum": 50}},
                        "required": ["sector_id", "query"]}, _rag_search,
                       permissions=net_permission, risk=net_risk, locality="network"),
        ToolDefinition("sol_jarvis_propose", "Submit a proposal to SOL Jarvis for Command-side review; this never approves or applies a change.",
                       {"type": "object", "properties": {"sector_id": {"type": "string"},
                        "title": {"type": "string", "maxLength": 200},
                        "body": {"type": "string", "maxLength": 12000},
                        "domain": {"type": "string", "enum": ["meal_plans", "fitness_plans", "skills", "memories", "home_pa", "code_fix"]}},
                        "required": ["sector_id", "title", "body"]}, _jarvis_propose,
                       permissions=net_permission,
                       risk=(RiskClass.MUTATING, RiskClass.NETWORK),
                       mutability=True, locality="network"),
    ]
