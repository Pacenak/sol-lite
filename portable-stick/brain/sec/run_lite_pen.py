"""Lite pen-tester for studio-owner authorized lab hosts.

Allowlist + I_OWN_THIS_LAB required. Performs recon-only checks:
TCP ports, TLS, short HTTP HEAD (no exploit payloads, no credential stuffing).
"""

from __future__ import annotations

import argparse
import json
import socket
import ssl
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import sys

_SEC = Path(__file__).resolve().parent
if str(_SEC) not in sys.path:
    sys.path.insert(0, str(_SEC))

from allowlist import (  # noqa: E402
    assert_target_allowed,
    default_ports,
    load_allowlist,
    require_lab_ack,
)


def _brain_root() -> Path:
    return Path(__file__).resolve().parents[1]


def banner_probe(host: str, port: int, timeout: float = 2.0) -> Dict[str, Any]:
    """Read a short banner if the service speaks first — recon only."""
    row: Dict[str, Any] = {"host": host, "port": port, "open": False, "banner": "", "error": ""}
    try:
        with socket.create_connection((host, port), timeout=timeout) as sock:
            row["open"] = True
            sock.settimeout(1.0)
            try:
                data = sock.recv(128)
                row["banner"] = data.decode("utf-8", errors="replace").strip()[:120]
            except OSError:
                pass
    except OSError as exc:
        row["error"] = str(exc)
    return row


def http_head(host: str, port: int = 80, use_tls: bool = False, timeout: float = 3.0) -> Dict[str, Any]:
    scheme = "https" if use_tls else "http"
    url = f"{scheme}://{host}:{port}/"
    row: Dict[str, Any] = {"url": url, "status": None, "server": "", "error": ""}
    try:
        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            row["status"] = getattr(resp, "status", None) or resp.getcode()
            row["server"] = str(resp.headers.get("Server") or "")
    except urllib.error.HTTPError as exc:
        row["status"] = exc.code
        row["server"] = str(exc.headers.get("Server") or "") if exc.headers else ""
    except Exception as exc:  # noqa: BLE001 — report honestly
        row["error"] = str(exc)
    return row


def tls_summary(host: str, port: int = 443) -> Dict[str, Any]:
    row: Dict[str, Any] = {"host": host, "port": port, "tls_ok": False, "expires": "", "error": ""}
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((host, port), timeout=3.0) as raw:
            with ctx.wrap_socket(raw, server_hostname=host) as sock:
                cert = sock.getpeercert()
                row["tls_ok"] = True
                row["expires"] = str((cert or {}).get("notAfter") or "")
    except OSError as exc:
        row["error"] = str(exc)
    return row


def run(hosts: List[str], ports: List[int], allow: set[str]) -> Dict[str, Any]:
    results: List[Dict[str, Any]] = []
    for h in hosts:
        host = assert_target_allowed(h, allow)
        for p in ports:
            results.append({"kind": "banner", **banner_probe(host, p)})
        if 443 in ports:
            results.append({"kind": "tls", **tls_summary(host, 443)})
            results.append({"kind": "http_head", **http_head(host, 443, use_tls=True)})
        if 80 in ports:
            results.append({"kind": "http_head", **http_head(host, 80, use_tls=False)})
        if 3000 in ports:
            results.append({"kind": "http_head", **http_head(host, 3000, use_tls=False)})
    return {
        "mode": "lite_pen",
        "scope": "studio_owner_authorized_lab",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "results": results,
        "note": "Recon only. No exploits, brute force, or destructive checks.",
    }


def main() -> int:
    brain = _brain_root()
    ap = argparse.ArgumentParser(
        description="Lite pen-tester — allowlist + I_OWN_THIS_LAB (studio owner)"
    )
    ap.add_argument("--allowlist", type=Path, default=brain / "sec" / "hosts.allow")
    ap.add_argument("--ack", type=Path, default=brain / "sec" / "I_OWN_THIS_LAB")
    ap.add_argument("--host", action="append", default=[])
    ap.add_argument("--ports", default=",".join(str(p) for p in default_ports()))
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    require_lab_ack(args.ack)
    allow = load_allowlist(args.allowlist)
    hosts = args.host or sorted(allow)
    ports = [int(x) for x in str(args.ports).split(",") if x.strip()]
    report = run(hosts, ports, allow)

    out = args.out
    if out is None:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out_dir = brain / "workspace" / "sec-reports"
        out_dir.mkdir(parents=True, exist_ok=True)
        out = out_dir / f"lite-pen-{stamp}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
