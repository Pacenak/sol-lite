"""Defensive studio SecCheck — TCP reachability + optional TLS on allowlisted hosts.

No exploit payloads. Targets must appear in hosts.allow.
"""

from __future__ import annotations

import argparse
import json
import socket
import ssl
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import sys

_SEC = Path(__file__).resolve().parent
if str(_SEC) not in sys.path:
    sys.path.insert(0, str(_SEC))

from allowlist import assert_target_allowed, default_ports, load_allowlist  # noqa: E402


def _brain_root() -> Path:
    return Path(__file__).resolve().parents[1]


def tcp_check(host: str, port: int, timeout: float = 2.0) -> Dict[str, Any]:
    row: Dict[str, Any] = {"host": host, "port": port, "open": False, "error": ""}
    try:
        with socket.create_connection((host, port), timeout=timeout):
            row["open"] = True
    except OSError as exc:
        row["error"] = str(exc)
    return row


def tls_check(host: str, port: int = 443, timeout: float = 3.0) -> Dict[str, Any]:
    row: Dict[str, Any] = {"host": host, "port": port, "tls_ok": False, "expires": "", "error": ""}
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((host, port), timeout=timeout) as raw:
            with ctx.wrap_socket(raw, server_hostname=host) as sock:
                cert = sock.getpeercert()
                row["tls_ok"] = True
                # notAfter like 'Jun 15 12:00:00 2027 GMT'
                row["expires"] = str((cert or {}).get("notAfter") or "")
    except OSError as exc:
        row["error"] = str(exc)
    return row


def run(hosts: List[str], ports: List[int], allow: set[str]) -> Dict[str, Any]:
    results: List[Dict[str, Any]] = []
    for h in hosts:
        host = assert_target_allowed(h, allow)
        for p in ports:
            results.append(tcp_check(host, p))
        if 443 in ports:
            results.append({"kind": "tls", **tls_check(host, 443)})
    return {
        "mode": "seccheck",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "results": results,
    }


def main() -> int:
    brain = _brain_root()
    ap = argparse.ArgumentParser(description="Studio defensive SecCheck (allowlisted hosts)")
    ap.add_argument(
        "--allowlist",
        type=Path,
        default=brain / "sec" / "hosts.allow",
        help="Path to hosts.allow",
    )
    ap.add_argument("--host", action="append", default=[], help="Host to check (must be allowlisted)")
    ap.add_argument("--ports", default=",".join(str(p) for p in default_ports()))
    ap.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Report JSON path (default workspace/sec-reports/)",
    )
    args = ap.parse_args()
    allow = load_allowlist(args.allowlist)
    hosts = args.host or sorted(allow)
    ports = [int(x) for x in str(args.ports).split(",") if x.strip()]
    report = run(hosts, ports, allow)
    out = args.out
    if out is None:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out_dir = brain / "workspace" / "sec-reports"
        out_dir.mkdir(parents=True, exist_ok=True)
        out = out_dir / f"seccheck-{stamp}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
