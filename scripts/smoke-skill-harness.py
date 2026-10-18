"""Bounded SOL-Lite engineering acceptance, with real tools and immutable checks.

Runs matched control/curated fixtures. The scripted provider tests runtime
wiring only; --provider ollama exercises a configured local model. No model
downloads, external writes or arbitrary terminal commands are permitted.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import subprocess
import sys
import time
from types import SimpleNamespace
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sol_lite.agents.runtime import AgentRuntime
from sol_lite.audit.logger import AuditLogger
from sol_lite.core.exceptions import PermissionDenied
from sol_lite.faults.log import FaultLog
from sol_lite.permissions.approvals import ApprovalManager
from sol_lite.permissions.engine import PermissionEngine
from sol_lite.permissions.policy import PermissionPolicy
from sol_lite.platform import get_platform_adapter
from sol_lite.skills.manager import SkillManager
from sol_lite.tools import build_tool_registry
from sol_lite.tools.base import ToolContext

CHECKS = "from src.calc import add, double\nassert add(3, 2) == 5\nassert add(-2, 2) == 0\nassert double(7) == 14\nassert double(-3) == -6\nprint('fixture checks passed')\n"
FIXED = "def add(a, b):\n    return a + b\n\ndef double(value):\n    return add(value, value)\n"
REQUEST = (
    "Fix broken code in src/calc.py: add(a,b) must add its arguments. "
    "Create double(value) using add(value,value), preserving add's public signature. "
    "Inspect the files, state a short plan, make the change and run python checks.py. "
    "checks.py is immutable. The only permitted terminal command is python checks.py. "
    "Report actual validation results; do not invent APIs or claim unrun checks."
)


class Models:
    def __init__(self, provider, model):
        self.provider, self.model = provider, model
        self.calls, self.tokens = 0, 0

    def profile(self, name):
        return SimpleNamespace(model=self.model, temperature=0, timeout_seconds=120)

    def chat(self, profile, messages, tools):
        self.calls += 1
        if self.provider == "scripted":
            calls = [
                ("read_workspace_file", {"path": "src/calc.py"}),
                ("write_workspace_file", {"path": "src/calc.py", "content": FIXED}),
                ("execute_terminal_command", {"command": "python checks.py"}),
            ]
            if self.calls <= len(calls):
                name, arguments = calls[self.calls - 1]
                return {"message": {"content": "", "tool_calls": [{"function": {"name": name, "arguments": arguments}}]}}
            return {"message": {"content": "Implemented. Tests pass.", "tool_calls": []}}
        payload = {"model": self.model, "messages": messages, "tools": tools, "stream": False,
                   "options": {"temperature": 0, "num_ctx": 16384, "num_predict": 1600}}
        request = urllib.request.Request("http://127.0.0.1:11434/api/chat", data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(request, timeout=120) as response:
            result = json.loads(response.read())
        self.tokens += int(result.get("prompt_eval_count", 0))
        return result


def trial(directory, provider, model, curated):
    directory.mkdir(parents=True, exist_ok=False)
    (directory / "src").mkdir()
    (directory / "src/calc.py").write_text("def add(a, b):\n    return a - b\n", encoding="utf-8")
    (directory / "checks.py").write_text(CHECKS, encoding="utf-8")
    native_platform = get_platform_adapter()

    class FixturePlatform:
        name = native_platform.name
        def available_shells(self):
            return native_platform.available_shells()
        def run_shell(self, command, cwd, timeout, shell=None):
            if command.strip() != "python checks.py" or Path(cwd).resolve() != directory.resolve():
                raise PermissionDenied("Only the fixture validation command is permitted")
            return subprocess.run([sys.executable, "checks.py"], cwd=cwd, capture_output=True, text=True, timeout=30)

    policy = PermissionPolicy({"filesystem": {"read": {"enabled": True, "approval_required": False}, "write": {"enabled": True, "approval_required": False}},
                               "terminal": {"read": {"enabled": True, "approval_required": False}, "write": {"enabled": True, "approval_required": False}, "allowed_commands": ["python"], "blocked_commands": []}})
    fault_log = FaultLog(directory / "faults.json")
    context = ToolContext(directory, PermissionEngine(policy, ApprovalManager()), AuditLogger(directory / "audit.jsonl"), fault_log,
                          FixturePlatform(), agent_id="sol_engineer", session_id="acceptance", state_root=directory / "state")
    tools = build_tool_registry()
    for name in ("write_workspace_file", "edit_workspace_file"):
        native = tools.get(name).handler
        def bounded(ctx, args, handler=native):
            if args.get("path", "").replace("\\", "/") != "src/calc.py":
                raise PermissionDenied("Acceptance checks and other files are immutable")
            return handler(ctx, args)
        tools.get(name).handler = bounded
    manager = SkillManager(ROOT, directory / "state")
    skill_context = manager.prompt_context("sol_engineer", task="$sol-engineering-evidence") if curated else ""
    model_manager = Models(provider, model)
    runtime = AgentRuntime(model_manager, tools, context, fault_log, max_tool_rounds=10,
                           skill_context=skill_context)
    system = (ROOT / "src/sol_lite/agents/engineer/prompt.md").read_text(encoding="utf-8")
    system += "\nAvailable shells: " + ", ".join(native_platform.available_shells()) + ". Python is a command, not a shell. Omit shell to use the default.\n"
    started = time.monotonic()
    result = runtime.run(profile="engineer", messages=[{"role": "system", "content": system}, {"role": "user", "content": REQUEST}],
                         allowed_tools=("read_workspace_file", "write_workspace_file", "edit_workspace_file", "execute_terminal_command",
                                        "inventory_workspace", "list_workspace_directories", "list_project_structure", "find_workspace_files", "runtime_get_context"))
    # The evaluator executes the immutable oracle independently of model claims.
    completed = subprocess.run([sys.executable, "checks.py"], cwd=directory, capture_output=True, text=True, timeout=30)
    return {"provider": provider, "model": model, "runtime": "sol-lite", "curated": curated,
            "oracle_passed": completed.returncode == 0 and (directory / "checks.py").read_text(encoding="utf-8") == CHECKS,
            "oracle_exit_code": completed.returncode, "oracle_stdout": completed.stdout, "oracle_stderr": completed.stderr,
            "result": asdict(result), "model_calls": model_manager.calls, "prompt_tokens": model_manager.tokens,
            "skill_context_chars": len(skill_context), "duration_seconds": round(time.monotonic() - started, 2)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--provider", choices=["scripted", "ollama"], default="scripted")
    parser.add_argument("--model", default="qwen3-coder:30b")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    results = []
    for mode in ("control", "curated"):
        print("Starting", args.provider, mode, flush=True)
        try:
            result = trial(args.output / mode, args.provider, args.model, mode == "curated")
        except Exception as error:
            result = {"provider": args.provider, "curated": mode == "curated", "oracle_passed": False, "error": type(error).__name__ + ": " + str(error)}
        results.append(result)
        (args.output / "results.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(result), flush=True)
    return 0 if all(result["oracle_passed"] and not result.get("result", {}).get("stopped_reason") for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
