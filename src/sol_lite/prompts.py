"""Engineering prompt loader."""

import os
from datetime import UTC, datetime
from pathlib import Path


class PromptLoader:
    def __init__(self, directory, workspace, fault_log):
        self.directory = Path(directory).resolve()
        self.workspace = Path(workspace).resolve()
        self.fault_log = Path(fault_log).resolve()

    def _resolve(self, name):
        candidate = (self.directory / name).resolve()
        if os.path.commonpath([str(candidate), str(self.directory)]) != str(self.directory):
            raise ValueError("Prompt path escapes prompt directory.")
        if not candidate.is_file():
            raise FileNotFoundError(candidate)
        return candidate

    def list(self):
        return sorted(p.name for p in self.directory.glob("*.md") if p.is_file())

    def load(self, name):
        text = self._resolve(name).read_text(encoding="utf-8-sig")
        replacements = {
            "{{WORKSPACE}}": str(self.workspace),
            "{{PROMPT_DIRECTORY}}": str(self.directory),
            "{{FAULT_LOG}}": str(self.fault_log),
            "{{DATE}}": datetime.now(UTC).astimezone().strftime("%Y-%m-%d"),
            "{{DATETIME}}": datetime.now(UTC).astimezone().isoformat(timespec="seconds"),
        }
        for key, value in replacements.items():
            text = text.replace(key, value)
        return text
