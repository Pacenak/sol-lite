"""Windows command-shell adapter."""
import shutil
import subprocess
from pathlib import Path

from .base import PlatformAdapter


class WindowsAdapter(PlatformAdapter):
    name = "windows"

    def available_shells(self):
        shells = []
        if shutil.which("cmd.exe"):
            shells.append("cmd")
        if shutil.which("powershell.exe"):
            shells.append("powershell")
        if shutil.which("pwsh.exe"):
            shells.append("pwsh")
        if shutil.which("bash.exe"):
            shells.append("bash")
        return shells

    def run_shell(self, command: str, cwd: Path, timeout: float, shell: str | None = None):
        selected = shell or "powershell"
        if selected == "cmd":
            argv = ["cmd.exe", "/d", "/s", "/c", command]
        elif selected == "powershell":
            argv = ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command]
        elif selected == "pwsh":
            argv = ["pwsh.exe", "-NoProfile", "-NonInteractive", "-Command", command]
        elif selected == "bash":
            argv = ["bash.exe", "-lc", command]
        else:
            raise ValueError(f"Unsupported Windows shell: {selected}")
        return subprocess.run(argv, cwd=str(cwd), capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=timeout, check=False)
