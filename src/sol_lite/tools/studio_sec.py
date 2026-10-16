"""Studio-owner SecCheck / lite-pen tools (allowlist + unlock gated)."""

from __future__ import annotations

import importlib.util
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from ..capabilities.risk import RiskClass
from ..core.exceptions import PermissionDenied, ToolExecutionError
from ..permissions.scopes import NETWORK, READ
from ..security.studio_owner import find_unlock_file, require_studio_owner, studio_owner_unlocked
from .base import ToolDefinition


def _load_stick_module(name: str, filename: str):
    root = Path(__file__).resolve().parents[2]
    path = root / "portable-stick" / "brain" / "sec" / filename
    if not path.is_file():
        raise ToolExecutionError(f"portable sec module missing: {path}")
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ToolExecutionError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _data_root(ctx) -> Path:
    env = (os.environ.get("SOL_DATA_ROOT") or "").strip()
    if env:
        return Path(env).expanduser().resolve()
    state = getattr(ctx, "state_root", None)
    if state:
        # state often .../data/state → parent is data
        p = Path(state).resolve()
        return p.parent if p.name == "state" else p
    return Path(ctx.workspace_root).resolve().parent / "data"


def _sec_dir(ctx) -> Path:
    ws = Path(ctx.workspace_root).resolve()
    cand = ws.parent / "sec"
    if cand.is_dir():
        return cand
    return Path(__file__).resolve().parents[2] / "portable-stick" / "brain" / "sec"


def _reports_dir(ctx) -> Path:
    out = Path(ctx.workspace_root).resolve() / "sec-reports"
    out.mkdir(parents=True, exist_ok=True)
    return out


def _require_owner(ctx) -> None:
    try:
        require_studio_owner(
            data_root=_data_root(ctx),
            workspace_root=ctx.workspace_root,
        )
    except PermissionError as exc:
        raise PermissionDenied(str(exc)) from exc


def studio_seccheck(ctx, args):
    _require_owner(ctx)
    ctx.permission_engine.check(READ, operation="studio_seccheck")
    ctx.permission_engine.check(NETWORK, operation="studio_seccheck")

    al = _load_stick_module("stick_allowlist", "allowlist.py")
    runner = _load_stick_module("stick_seccheck", "run_seccheck.py")
    sec = _sec_dir(ctx)
    allow_path = sec / "hosts.allow"
    if not allow_path.is_file():
        raise ToolExecutionError(
            f"missing {allow_path} — copy hosts.allow.example on your BRAIN stick"
        )
    allow = al.load_allowlist(allow_path)
    hosts = args.get("hosts") or sorted(allow)
    if isinstance(hosts, str):
        hosts = [hosts]
    ports = args.get("ports") or al.default_ports()
    if isinstance(ports, str):
        ports = [int(x) for x in ports.split(",") if x.strip()]
    report = runner.run(list(hosts), list(ports), allow)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = _reports_dir(ctx) / f"seccheck-{stamp}.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return {"ok": True, "report": str(out), "count": len(report.get("results") or [])}


def studio_lite_pen(ctx, args):
    _require_owner(ctx)
    ctx.permission_engine.check(READ, operation="studio_lite_pen")
    ctx.permission_engine.check(NETWORK, operation="studio_lite_pen")

    al = _load_stick_module("stick_allowlist", "allowlist.py")
    runner = _load_stick_module("stick_lite_pen", "run_lite_pen.py")
    sec = _sec_dir(ctx)
    allow_path = sec / "hosts.allow"
    ack_path = sec / "I_OWN_THIS_LAB"
    try:
        al.require_lab_ack(ack_path)
    except PermissionError as exc:
        raise PermissionDenied(str(exc)) from exc
    if not allow_path.is_file():
        raise ToolExecutionError(f"missing {allow_path}")
    allow = al.load_allowlist(allow_path)
    hosts = args.get("hosts") or sorted(allow)
    if isinstance(hosts, str):
        hosts = [hosts]
    ports = args.get("ports") or al.default_ports()
    if isinstance(ports, str):
        ports = [int(x) for x in ports.split(",") if x.strip()]
    report = runner.run(list(hosts), list(ports), allow)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = _reports_dir(ctx) / f"lite-pen-{stamp}.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return {"ok": True, "report": str(out), "count": len(report.get("results") or [])}


def studio_owner_status(ctx, args):
    data = _data_root(ctx)
    unlocked = studio_owner_unlocked(
        data_root=data, workspace_root=ctx.workspace_root
    )
    unlock = find_unlock_file(data, Path(ctx.workspace_root))
    return {
        "unlocked": unlocked,
        "unlock_file": str(unlock) if unlock else "",
        "agent_hint": "sol_studio_admin is listed only when unlocked",
    }


def studio_sec_tools():
    return [
        ToolDefinition(
            name="studio_owner_status",
            description="Check whether the admin-only studio feature + owner unlock are active.",
            parameters={"type": "object", "properties": {}, "required": []},
            handler=studio_owner_status,
            permissions=(READ,),
            risk=(RiskClass.READ_ONLY,),
            mutability=False,
        ),
        ToolDefinition(
            name="studio_seccheck",
            description=(
                "Defensive SecCheck (TCP/TLS) on hosts.allow only. "
                "Requires studio-owner unlock. No exploits."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "hosts": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Subset of allowlisted hosts (default: all)",
                    },
                    "ports": {
                        "type": "array",
                        "items": {"type": "integer"},
                    },
                },
                "required": [],
            },
            handler=studio_seccheck,
            permissions=(READ, NETWORK),
            risk=(RiskClass.NETWORK,),
            mutability=False,
        ),
        ToolDefinition(
            name="studio_lite_pen",
            description=(
                "Lite pen recon (banners/HTTP HEAD/TLS) on allowlisted studio hosts. "
                "Requires studio-owner unlock + I_OWN_THIS_LAB. No exploits."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "hosts": {"type": "array", "items": {"type": "string"}},
                    "ports": {"type": "array", "items": {"type": "integer"}},
                },
                "required": [],
            },
            handler=studio_lite_pen,
            permissions=(READ, NETWORK),
            risk=(RiskClass.NETWORK,),
            mutability=False,
        ),
    ]
