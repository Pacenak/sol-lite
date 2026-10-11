"""Load a checklist for inspection without running approval-gated commands."""
from __future__ import annotations

from ..tools.procedure import procedure_load


def format_report(status: dict) -> str:
    lines = [
        f"source: {status['source']}",
        f"complete: {str(status['complete']).lower()}",
    ]
    unparsed = status.get("unparsed_sections") or []
    if unparsed:
        lines.append("unparsed: " + ", ".join(unparsed))
    for step in status.get("steps") or []:
        lines.append(
            f"{step['step_id']}  {step['classification']}  {step['action']}"
        )
    lines.append("No approval-gated command was executed.")
    return "\n".join(lines)


def dry_follow(ctx, relative_path: str) -> str:
    """Parse and classify a workspace checklist. Does not call procedure_advance."""
    status = procedure_load(ctx, {"path": relative_path})
    return format_report(status)
