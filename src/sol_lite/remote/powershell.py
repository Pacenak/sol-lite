"""Windows PowerShell remoting transport."""
from __future__ import annotations

import shutil
import subprocess

from ..core.exceptions import ToolExecutionError
from .nodes import RemoteNode
from .ssh import RemoteCommandResult


class PowerShellTransport:
    def __init__(self, executable: str | None = None):
        self.executable = executable or shutil.which("pwsh") or shutil.which("powershell")
        if not self.executable:
            raise ToolExecutionError("PowerShell was not found on PATH.")

    def run(self, node: RemoteNode, command: str, *, timeout: float = 120.0) -> RemoteCommandResult:
        if node.transport.value != "powershell":
            raise ValueError("PowerShellTransport requires a PowerShell node")
        target = node.hostname
        script = f"Invoke-Command -ComputerName {target!r} -ScriptBlock {{ {command} }}"
        try:
            result = subprocess.run([self.executable, "-NoProfile", "-NonInteractive", "-Command", script],
                                    capture_output=True, text=True, encoding="utf-8",
                                    errors="replace", timeout=timeout, check=False)
        except (OSError, subprocess.SubprocessError, TimeoutError) as exc:
            raise ToolExecutionError(f"PowerShell remoting failed: {exc}") from exc
        return RemoteCommandResult(command, result.returncode, result.stdout, result.stderr)
