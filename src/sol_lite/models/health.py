"""Ollama diagnostics via HTTP API."""

import json
import shutil
import subprocess
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass(slots=True)
class DiagnosticResult:
    ok: bool
    data: dict

def _get_json(url, timeout=5):
    with urlopen(Request(url, method="GET"), timeout=timeout) as response:
        return response.status, json.loads(response.read().decode("utf-8"))

def diagnose_ollama(host, requested_models):
    data = {"host": host, "python_client": {}, "api_version": {},
            "models": {}, "executable": {}}
    try:
        data["python_client"] = {"installed": True, "version": version("ollama")}
    except PackageNotFoundError:
        data["python_client"] = {"installed": False}

    exe = shutil.which("ollama")
    if exe:
        try:
            r = subprocess.run([exe, "--version"], capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=10, check=False)
            data["executable"] = {"path": exe, "returncode": r.returncode,
                                  "version": r.stdout.strip() or r.stderr.strip()}
        except (OSError, subprocess.SubprocessError, TimeoutError) as exc:
            data["executable"] = {"path": exe, "error": str(exc)}
    else:
        data["executable"] = {"path": None, "available": False}

    try:
        status, body = _get_json(host.rstrip("/") + "/api/version")
        data["api_version"] = {"ok": status == 200, "status": status, "data": body}
    except (HTTPError, URLError, OSError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
        data["api_version"] = {"ok": False, "error": str(exc)}

    try:
        status, body = _get_json(host.rstrip("/") + "/api/tags")
        available = [m["name"] for m in body.get("models", [])
                     if isinstance(m, dict) and m.get("name")]
        data["models"] = {
            "ok": status == 200, "status": status,
            "available": available, "requested": requested_models,
            "missing": [m for m in requested_models if m not in available],
        }
    except (HTTPError, URLError, OSError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
        data["models"] = {"ok": False, "error": str(exc)}

    ok = bool(data["python_client"].get("installed")
              and data["api_version"].get("ok")
              and data["models"].get("ok"))
    return DiagnosticResult(ok, data)
