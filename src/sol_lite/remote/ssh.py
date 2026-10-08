"""SSH transport using the system OpenSSH client."""
from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass

from ..core.exceptions import ToolExecutionError
from .nodes import RemoteNode


@dataclass(frozen=True, slots=True)
class RemoteCommandResult:
    command: str
    exit_code: int
    stdout: str
    stderr: str


class SSHTransport:
    def __init__(self, executable: str | None = None):
        self.executable = executable or shutil.which("ssh")
        if not self.executable:
            raise ToolExecutionError("OpenSSH client was not found on PATH.")

    def run(self, node: RemoteNode, command: str, *, timeout: float = 120.0) -> RemoteCommandResult:
        if node.transport.value != "ssh":
            raise ValueError("SSHTransport requires an SSH node")
        destination = f"{node.username}@{node.hostname}" if node.username else node.hostname
        argv = [self.executable]
        if node.port is not None:
            argv += ["-p", str(node.port)]
        argv += [destination, "--", command]
        try:
            result = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8",
                                    errors="replace", timeout=timeout, check=False)
        except (OSError, subprocess.SubprocessError, TimeoutError) as exc:
            raise ToolExecutionError(f"SSH execution failed: {exc}") from exc
        return RemoteCommandResult(command, result.returncode, result.stdout, result.stderr)
