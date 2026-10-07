from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.metadata
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import traceback
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

try:
    import ollama
except ImportError:
    ollama = None


# ============================================================================
# CONFIGURATION
# ============================================================================

SAFE_DIRECTORY = os.path.realpath(
    r"E:\dSeek-workpace\local_workspace\PLG_Ai_Interface-main"
)

PROMPT_DIRECTORY = os.path.realpath(
    r"E:\dSeek-workpace\prompts"
)

LOG_FILE_PATH = os.path.join(
    SAFE_DIRECTORY,
    "engineering_fault_log.json",
)

OLLAMA_HOST = os.environ.get(
    "OLLAMA_HOST",
    "http://127.0.0.1:11434",
).rstrip("/")

TARGET_MODEL = os.environ.get(
    "OLLAMA_MODEL",
    "qwen3-coder:30b",
)

MAX_TOOL_ROUNDS = int(
    os.environ.get(
        "OLLAMA_MAX_TOOL_ROUNDS",
        "40",
    )
)

HEARTBEAT_SECONDS = float(
    os.environ.get(
        "OLLAMA_HEARTBEAT_SECONDS",
        "10",
    )
)

STALL_SECONDS = float(
    os.environ.get(
        "OLLAMA_STALL_SECONDS",
        "90",
    )
)

MAX_FILE_READ_BYTES = int(
    os.environ.get(
        "OLLAMA_MAX_FILE_READ_BYTES",
        str(2 * 1024 * 1024),
    )
)

MAX_BATCH_FILE_READ_BYTES = int(
    os.environ.get(
        "OLLAMA_MAX_BATCH_FILE_READ_BYTES",
        str(8 * 1024 * 1024),
    )
)

MAX_SEARCH_RESULTS = int(
    os.environ.get(
        "OLLAMA_MAX_SEARCH_RESULTS",
        "500",
    )
)

MAX_TOOL_RESULT_CHARS = int(
    os.environ.get(
        "OLLAMA_MAX_TOOL_RESULT_CHARS",
        "50000",
    )
)

COMMAND_TIMEOUT_SECONDS = int(
    os.environ.get(
        "OLLAMA_COMMAND_TIMEOUT_SECONDS",
        "120",
    )
)


# ============================================================================
# ENGINEERING PHASES
# ============================================================================

PHASES = {
    "00_workspace_discovery.md": "WORKSPACE DISCOVERY",
    "01_verification_reproduction.md": "VERIFICATION / REPRODUCTION",
    "02_root_cause_investigation.md": "ROOT CAUSE INVESTIGATION",
    "03_fix_planning.md": "FIX PLANNING",
    "04_implementation.md": "IMPLEMENTATION",
    "05_validation.md": "VALIDATION",
    "06_end_to_end_proof.md": "END-TO-END PROOF",
    "07_final_engineering_report.md": "FINAL ENGINEERING REPORT",
}


EVIDENCE_DOMAINS = {
    "LIVE",
    "GITEA",
    "WORKSPACE",
    "TEST",
    "DOCS",
}


# ============================================================================
# TERMINAL SAFETY
# ============================================================================

DESTRUCTIVE_COMMAND_PATTERNS = [
    r"\brm\s+-rf\b",
    r"\brmdir\b",
    r"\bdel\s+/[sqf]+\b",
    r"\berase\b",
    r"\bformat\b",
    r"\bdiskpart\b",
    r"\bshutdown\b",
    r"\breboot\b",
    r"\bpoweroff\b",
    r"\btaskkill\b",
    r"\bsc\s+(delete|stop|config)\b",
    r"\bnet\s+(stop|start)\b",
    r"\bRemove-Item\b.*-Recurse",
    r"\bRemove-Item\b.*-Force",
    r"\bSet-ExecutionPolicy\b",
    r"\breg\s+(delete|add)\b",
    r"\bmklink\b",
    r"\bfsutil\b",
    r"\bwbadmin\b",
    r"\bDiskPart\b",
]


# ============================================================================
# ACTIVITY STATE
# ============================================================================

@dataclass
class ActivityState:
    status: str = "IDLE"
    phase: str = "IDLE"
    activity: str = "Waiting for task"

    model: str = TARGET_MODEL

    round_number: int = 0
    max_rounds: int = MAX_TOOL_ROUNDS

    task_name: str = ""

    tool_name: str = ""
    tool_started_at: float | None = None

    started_at: float | None = None
    last_activity: float = field(
        default_factory=time.monotonic
    )

    tool_calls: int = 0
    tools_completed: int = 0

    files_read: int = 0
    files_written: int = 0

    commands_executed: int = 0
    errors: int = 0

    stop_requested: bool = False

    _lock: threading.Lock = field(
        default_factory=threading.Lock,
        repr=False,
    )

    def update(
        self,
        **kwargs: Any,
    ) -> None:
        with self._lock:
            for key, value in kwargs.items():
                if hasattr(self, key):
                    setattr(
                        self,
                        key,
                        value,
                    )

            self.last_activity = time.monotonic()

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            now = time.monotonic()

            return {
                "status": self.status,
                "phase": self.phase,
                "activity": self.activity,
                "model": self.model,
                "round_number": self.round_number,
                "max_rounds": self.max_rounds,
                "task_name": self.task_name,
                "tool_name": self.tool_name,
                "tool_started_at": self.tool_started_at,
                "started_at": self.started_at,
                "last_activity": self.last_activity,
                "idle_seconds": max(
                    0.0,
                    now - self.last_activity,
                ),
                "elapsed_seconds": (
                    max(
                        0.0,
                        now - self.started_at,
                    )
                    if self.started_at
                    else 0.0
                ),
                "tool_calls": self.tool_calls,
                "tools_completed": self.tools_completed,
                "files_read": self.files_read,
                "files_written": self.files_written,
                "commands_executed": self.commands_executed,
                "errors": self.errors,
                "stop_requested": self.stop_requested,
            }


# ============================================================================
# ACTIVITY MONITOR
# ============================================================================

class ActivityMonitor:
    """
    Runtime-generated status monitor.

    The model does not control these messages.

    This means:
      WORKING
      WAITING
      TOOL
      COMMAND
      POSSIBLY STALLED
      COMPLETE
      ERROR
      CANCELLED

    are determined by the Python runtime rather than by model claims.
    """

    def __init__(
        self,
        state: ActivityState,
    ) -> None:
        self.state = state

        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        self._stop.clear()

        self._thread = threading.Thread(
            target=self._run,
            name="agent-heartbeat",
            daemon=True,
        )

        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

        if (
            self._thread is not None
            and self._thread.is_alive()
        ):
            self._thread.join(
                timeout=2
            )

        self._thread = None

    def _run(self) -> None:
        while not self._stop.wait(
            HEARTBEAT_SECONDS
        ):
            snapshot = self.state.snapshot()

            if snapshot["status"] not in {
                "WORKING",
                "TOOL",
                "COMMAND",
                "WAITING",
            }:
                continue

            idle = snapshot["idle_seconds"]

            display_status = snapshot["status"]

            if idle >= STALL_SECONDS:
                display_status = "POSSIBLY STALLED"

            print(
                f"\n[{now_text()}] "
                f"STATUS {display_status} | "
                f"PHASE {snapshot['phase']} | "
                f"ACTIVITY {snapshot['activity']} | "
                f"IDLE {format_duration(idle)} | "
                f"ROUND "
                f"{snapshot['round_number']}/"
                f"{snapshot['max_rounds']}"
            )


# ============================================================================
# GENERAL UTILITIES
# ============================================================================

def now_text() -> str:
    return (
        datetime.now()
        .astimezone()
        .strftime("%H:%M:%S")
    )


def iso_now() -> str:
    return (
        datetime.now()
        .astimezone()
        .isoformat(
            timespec="seconds"
        )
    )


def format_duration(
    seconds: float,
) -> str:
    seconds = max(
        0,
        int(seconds),
    )

    hours, remainder = divmod(
        seconds,
        3600,
    )

    minutes, seconds = divmod(
        remainder,
        60,
    )

    if hours:
        return (
            f"{hours:02d}:"
            f"{minutes:02d}:"
            f"{seconds:02d}"
        )

    return (
        f"{minutes:02d}:"
        f"{seconds:02d}"
    )


def safe_realpath(
    path: str,
) -> str:
    return os.path.realpath(
        os.path.abspath(
            os.path.expandvars(
                os.path.expanduser(
                    path
                )
            )
        )
    )


def is_within(
    base: str,
    candidate: str,
) -> bool:
    base_real = safe_realpath(
        base
    )

    candidate_real = safe_realpath(
        candidate
    )

    try:
        return (
            os.path.commonpath(
                [
                    base_real,
                    candidate_real,
                ]
            )
            == base_real
        )
    except ValueError:
        return False


def require_workspace_path(
    path: str,
    allow_missing: bool = False,
) -> str:
    candidate = safe_realpath(
        path
    )

    if not is_within(
        SAFE_DIRECTORY,
        candidate,
    ):
        raise PermissionError(
            "Path is outside the approved "
            f"workspace: {path}"
        )

    if (
        not allow_missing
        and not os.path.exists(candidate)
    ):
        raise FileNotFoundError(
            candidate
        )

    return candidate


def require_prompt_path(
    path: str,
) -> str:
    candidate = safe_realpath(
        path
    )

    if not is_within(
        PROMPT_DIRECTORY,
        candidate,
    ):
        raise PermissionError(
            "Prompt path is outside the approved "
            f"prompt directory: {path}"
        )

    if not os.path.isfile(candidate):
        raise FileNotFoundError(
            candidate
        )

    return candidate


def truncate_text(
    value: str,
    limit: int = MAX_TOOL_RESULT_CHARS,
) -> str:
    if len(value) <= limit:
        return value

    omitted = len(value) - limit

    return (
        value[:limit]
        + "\n\n"
        + f"[TRUNCATED: {omitted} "
        + "characters omitted by tool output limit]"
    )


def json_dumps(
    value: Any,
) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        indent=2,
        default=str,
    )


# ============================================================================
# FAULT LOG
# ============================================================================

def load_fault_log() -> list[dict[str, Any]]:
    path = require_workspace_path(
        LOG_FILE_PATH,
        allow_missing=True,
    )

    if not os.path.exists(path):
        return []

    with open(
        path,
        "r",
        encoding="utf-8",
    ) as handle:
        data = json.load(handle)

    if not isinstance(
        data,
        list,
    ):
        raise ValueError(
            "engineering_fault_log.json "
            "must contain a JSON array"
        )

    return data


def save_fault_log(
    entries: list[dict[str, Any]],
) -> None:
    path = require_workspace_path(
        LOG_FILE_PATH,
        allow_missing=True,
    )

    os.makedirs(
        os.path.dirname(path),
        exist_ok=True,
    )

    temp_path = path + ".tmp"

    with open(
        temp_path,
        "w",
        encoding="utf-8",
        newline="\n",
    ) as handle:
        json.dump(
            entries,
            handle,
            ensure_ascii=False,
            indent=2,
        )

        handle.write("\n")

    os.replace(
        temp_path,
        path,
    )


# ============================================================================
# FILE OPERATIONS
# ============================================================================

def read_text_file(
    path: str,
    max_bytes: int = MAX_FILE_READ_BYTES,
) -> str:
    size = os.path.getsize(
        path
    )

    if size > max_bytes:
        raise ValueError(
            f"File is {size} bytes, above "
            f"configured read limit of {max_bytes} bytes"
        )

    with open(
        path,
        "r",
        encoding="utf-8",
        errors="replace",
    ) as handle:
        return handle.read()


def inventory_workspace() -> dict[str, Any]:
    root = require_workspace_path(
        SAFE_DIRECTORY
    )

    files: list[dict[str, Any]] = []
    directories: list[str] = []

    total_bytes = 0

    for current_root, dirnames, filenames in os.walk(
        root
    ):
        dirnames.sort()
        filenames.sort()

        relative_root = os.path.relpath(
            current_root,
            root,
        )

        relative_root = (
            "."
            if relative_root == "."
            else relative_root.replace(
                os.sep,
                "/",
            )
        )

        if relative_root != ".":
            directories.append(
                relative_root
            )

        for filename in filenames:
            full_path = os.path.join(
                current_root,
                filename,
            )

            try:
                stat = os.stat(
                    full_path
                )

                size = stat.st_size

            except OSError as exc:
                files.append(
                    {
                        "path": os.path.relpath(
                            full_path,
                            root,
                        ).replace(
                            os.sep,
                            "/",
                        ),
                        "error": str(exc),
                    }
                )

                continue

            relative_path = os.path.relpath(
                full_path,
                root,
            ).replace(
                os.sep,
                "/",
            )

            total_bytes += size

            files.append(
                {
                    "path": relative_path,
                    "size": size,
                    "extension": Path(
                        filename
                    ).suffix.lower(),
                }
            )

    return {
        "root": root,
        "directories": directories,
        "files": files,
        "file_count": len(files),
        "directory_count": len(directories),
        "total_bytes": total_bytes,
    }


def list_project_structure(
    path: str = ".",
    max_depth: int = 6,
) -> dict[str, Any]:
    if max_depth < 0:
        raise ValueError(
            "max_depth must be >= 0"
        )

    if os.path.isabs(path):
        root = require_workspace_path(
            path
        )
    else:
        root = require_workspace_path(
            os.path.join(
                SAFE_DIRECTORY,
                path,
            )
        )

    lines: list[str] = [
        (
            os.path.relpath(
                root,
                SAFE_DIRECTORY,
            ).replace(
                os.sep,
                "/",
            )
            or "."
        )
    ]

    base_depth = root.count(
        os.sep
    )

    for current_root, dirs, files in os.walk(
        root
    ):
        dirs.sort()
        files.sort()

        depth = (
            current_root.count(
                os.sep
            )
            - base_depth
        )

        if depth >= max_depth:
            dirs[:] = []

        entries = (
            [(directory, True) for directory in dirs]
            + [(filename, False) for filename in files]
        )

        for name, is_directory in entries:
            indent = "  " * (
                depth + 1
            )

            suffix = "/" if is_directory else ""

            lines.append(
                f"{indent}{name}{suffix}"
            )

    return {
        "root": root,
        "max_depth": max_depth,
        "tree": "\n".join(lines),
    }


def find_workspace_files(
    pattern: str,
    case_sensitive: bool = False,
    max_results: int = MAX_SEARCH_RESULTS,
) -> dict[str, Any]:
    if not pattern:
        raise ValueError(
            "pattern is required"
        )

    root = require_workspace_path(
        SAFE_DIRECTORY
    )

    needle = (
        pattern
        if case_sensitive
        else pattern.lower()
    )

    matches: list[str] = []

    for current_root, _, filenames in os.walk(
        root
    ):
        for filename in sorted(
            filenames
        ):
            candidate = (
                filename
                if case_sensitive
                else filename.lower()
            )

            if needle in candidate:
                matches.append(
                    os.path.relpath(
                        os.path.join(
                            current_root,
                            filename,
                        ),
                        root,
                    ).replace(
                        os.sep,
                        "/",
                    )
                )

                if len(matches) >= max_results:
                    return {
                        "pattern": pattern,
                        "case_sensitive": case_sensitive,
                        "matches": matches,
                        "truncated": True,
                    }

    return {
        "pattern": pattern,
        "case_sensitive": case_sensitive,
        "matches": matches,
        "truncated": False,
    }


def read_workspace_file(
    path: str,
    start_line: int = 1,
    end_line: int | None = None,
) -> dict[str, Any]:
    if os.path.isabs(path):
        full_path = require_workspace_path(
            path
        )
    else:
        full_path = require_workspace_path(
            os.path.join(
                SAFE_DIRECTORY,
                path,
            )
        )

    if start_line < 1:
        raise ValueError(
            "start_line must be >= 1"
        )

    text = read_text_file(
        full_path
    )

    lines = text.splitlines()

    end = (
        len(lines)
        if end_line is None
        else min(
            end_line,
            len(lines),
        )
    )

    if end < start_line:
        return {
            "path": os.path.relpath(
                full_path,
                SAFE_DIRECTORY,
            ).replace(
                os.sep,
                "/",
            ),
            "lines": [],
            "start_line": start_line,
            "end_line": end,
        }

    selected = [
        f"{index}: {lines[index - 1]}"
        for index in range(
            start_line,
            end + 1,
        )
    ]

    return {
        "path": os.path.relpath(
            full_path,
            SAFE_DIRECTORY,
        ).replace(
            os.sep,
            "/",
        ),
        "start_line": start_line,
        "end_line": end,
        "total_lines": len(lines),
        "content": truncate_text(
            "\n".join(selected)
        ),
    }


def read_workspace_files(
    paths: list[str],
) -> dict[str, Any]:
    if not isinstance(
        paths,
        list,
    ) or not paths:
        raise ValueError(
            "paths must be a non-empty list"
        )

    results: list[dict[str, Any]] = []

    total = 0

    for path in paths:
        if os.path.isabs(path):
            full_path = require_workspace_path(
                path
            )
        else:
            full_path = require_workspace_path(
                os.path.join(
                    SAFE_DIRECTORY,
                    path,
                )
            )

        size = os.path.getsize(
            full_path
        )

        if (
            total + size
            > MAX_BATCH_FILE_READ_BYTES
        ):
            results.append(
                {
                    "path": path,
                    "error": (
                        "Batch byte limit reached "
                        "before this file was read"
                    ),
                }
            )

            continue

        total += size

        try:
            results.append(
                {
                    "path": path,
                    "content": read_text_file(
                        full_path
                    ),
                }
            )
        except Exception as exc:
            results.append(
                {
                    "path": path,
                    "error": (
                        f"{type(exc).__name__}: "
                        f"{exc}"
                    ),
                }
            )

    return {
        "results": results,
        "total_bytes": total,
    }


# ============================================================================
# CODE SEARCH
# ============================================================================

def search_codebase(
    query: str,
    extensions: list[str] | None = None,
    case_sensitive: bool = False,
    max_results: int = MAX_SEARCH_RESULTS,
) -> dict[str, Any]:
    if not query:
        raise ValueError(
            "query is required"
        )

    root = require_workspace_path(
        SAFE_DIRECTORY
    )

    normalized_extensions = None

    if extensions:
        normalized_extensions = {
            (
                extension.lower()
                if extension.startswith(".")
                else "." + extension.lower()
            )
            for extension in extensions
        }

    needle = (
        query
        if case_sensitive
        else query.lower()
    )

    results: list[dict[str, Any]] = []

    for current_root, _, filenames in os.walk(
        root
    ):
        for filename in sorted(
            filenames
        ):
            if (
                normalized_extensions
                and Path(
                    filename
                ).suffix.lower()
                not in normalized_extensions
            ):
                continue

            full_path = os.path.join(
                current_root,
                filename,
            )

            try:
                if (
                    os.path.getsize(
                        full_path
                    )
                    > MAX_FILE_READ_BYTES
                ):
                    continue

                with open(
                    full_path,
                    "r",
                    encoding="utf-8",
                    errors="replace",
                ) as handle:
                    for number, line in enumerate(
                        handle,
                        1,
                    ):
                        haystack = (
                            line
                            if case_sensitive
                            else line.lower()
                        )

                        if needle in haystack:
                            results.append(
                                {
                                    "path": os.path.relpath(
                                        full_path,
                                        root,
                                    ).replace(
                                        os.sep,
                                        "/",
                                    ),
                                    "line": number,
                                    "text": line.rstrip(
                                        "\r\n"
                                    ),
                                }
                            )

                            if (
                                len(results)
                                >= max_results
                            ):
                                return {
                                    "query": query,
                                    "results": results,
                                    "truncated": True,
                                }

            except (
                OSError,
                UnicodeError,
            ):
                continue

    return {
        "query": query,
        "results": results,
        "truncated": False,
    }


# ============================================================================
# FILE METADATA
# ============================================================================

def get_workspace_file_metadata(
    path: str,
) -> dict[str, Any]:
    if os.path.isabs(path):
        full_path = require_workspace_path(
            path
        )
    else:
        full_path = require_workspace_path(
            os.path.join(
                SAFE_DIRECTORY,
                path,
            )
        )

    stat = os.stat(
        full_path
    )

    sha256 = hashlib.sha256()

    with open(
        full_path,
        "rb",
    ) as handle:
        for chunk in iter(
            lambda: handle.read(
                1024 * 1024
            ),
            b"",
        ):
            sha256.update(
                chunk
            )

    return {
        "path": os.path.relpath(
            full_path,
            SAFE_DIRECTORY,
        ).replace(
            os.sep,
            "/",
        ),
        "size": stat.st_size,
        "modified": (
            datetime.fromtimestamp(
                stat.st_mtime
            )
            .astimezone()
            .isoformat(
                timespec="seconds"
            )
        ),
        "sha256": sha256.hexdigest(),
    }


# ============================================================================
# ARCHITECTURE INVENTORY
# ============================================================================

def analyze_architecture_drift() -> dict[str, Any]:
    root = require_workspace_path(
        SAFE_DIRECTORY
    )

    documentation: list[str] = []
    source: list[str] = []
    configuration: list[str] = []

    for current_root, _, filenames in os.walk(
        root
    ):
        for filename in filenames:
            relative_path = os.path.relpath(
                os.path.join(
                    current_root,
                    filename,
                ),
                root,
            ).replace(
                os.sep,
                "/",
            )

            extension = Path(
                filename
            ).suffix.lower()

            if extension in {
                ".md",
                ".mdx",
                ".txt",
                ".rst",
            }:
                documentation.append(
                    relative_path
                )

            elif extension in {
                ".py",
                ".ts",
                ".tsx",
                ".js",
                ".jsx",
                ".cs",
                ".cpp",
                ".h",
                ".hpp",
                ".java",
                ".go",
                ".rs",
            }:
                source.append(
                    relative_path
                )

            elif extension in {
                ".json",
                ".yaml",
                ".yml",
                ".toml",
                ".ini",
                ".env",
                ".config",
            }:
                configuration.append(
                    relative_path
                )

    return {
        "docs": sorted(
            documentation
        ),
        "source": sorted(
            source
        ),
        "config": sorted(
            configuration
        ),
        "note": (
            "This tool reports file-category inventory only. "
            "It does not claim semantic documentation drift "
            "without evidence."
        ),
    }


# ============================================================================
# FAULT TOOL
# ============================================================================

def get_engineering_fault_log() -> dict[str, Any]:
    return {
        "entries": load_fault_log()
    }


def log_engineering_fault(
    entry: dict[str, Any],
    plan_id: str | None = None,
) -> dict[str, Any]:
    if not plan_id:
        raise PermissionError(
            "plan_id is required to modify "
            "the engineering fault log"
        )

    if not isinstance(
        entry,
        dict,
    ):
        raise ValueError(
            "entry must be an object"
        )

    entries = load_fault_log()

    record = copy.deepcopy(
        entry
    )

    record.setdefault(
        "timestamp",
        iso_now(),
    )

    record.setdefault(
        "status",
        "OPEN",
    )

    entries.append(
        record
    )

    save_fault_log(
        entries
    )

    return {
        "saved": True,
        "entry": record,
        "count": len(entries),
        "plan_id": plan_id,
    }


# ============================================================================
# TERMINAL COMMAND SAFETY
# ============================================================================

def check_command_safety(
    command: str,
) -> tuple[bool, str]:
    lowered = command.lower()

    for pattern in DESTRUCTIVE_COMMAND_PATTERNS:
        if re.search(
            pattern,
            lowered,
            flags=re.IGNORECASE,
        ):
            return (
                False,
                (
                    "Command matches blocked "
                    f"destructive pattern: {pattern}"
                ),
            )

    return (
        True,
        "allowed",
    )


def execute_terminal_command(
    command: str,
    cwd: str = ".",
    timeout_seconds: int = COMMAND_TIMEOUT_SECONDS,
    plan_id: str | None = None,
) -> dict[str, Any]:
    if not command.strip():
        raise ValueError(
            "command is required"
        )

    allowed, reason = check_command_safety(
        command
    )

    if not allowed:
        raise PermissionError(
            reason
        )

    if os.path.isabs(cwd):
        working_directory = require_workspace_path(
            cwd
        )
    else:
        working_directory = require_workspace_path(
            os.path.join(
                SAFE_DIRECTORY,
                cwd,
            )
        )

    if (
        timeout_seconds < 1
        or timeout_seconds > 3600
    ):
        raise ValueError(
            "timeout_seconds must be "
            "between 1 and 3600"
        )

    started = time.monotonic()

    completed = subprocess.run(
        command,
        cwd=working_directory,
        shell=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout_seconds,
    )

    return {
        "command": command,
        "cwd": os.path.relpath(
            working_directory,
            SAFE_DIRECTORY,
        ).replace(
            os.sep,
            "/",
        ),
        "plan_id": plan_id,
        "returncode": completed.returncode,
        "stdout": truncate_text(
            completed.stdout
        ),
        "stderr": truncate_text(
            completed.stderr
        ),
        "duration_seconds": round(
            time.monotonic() - started,
            3,
        ),
    }


# ============================================================================
# CONTROLLED WORKSPACE WRITE
# ============================================================================

def write_workspace_file(
    path: str,
    content: str,
    plan_id: str | None = None,
    create_dirs: bool = False,
) -> dict[str, Any]:
    if not plan_id:
        raise PermissionError(
            "plan_id is required for workspace writes"
        )

    if os.path.isabs(path):
        full_path = require_workspace_path(
            path,
            allow_missing=True,
        )
    else:
        full_path = require_workspace_path(
            os.path.join(
                SAFE_DIRECTORY,
                path,
            ),
            allow_missing=True,
        )

    parent_directory = os.path.dirname(
        full_path
    )

    if create_dirs:
        os.makedirs(
            parent_directory,
            exist_ok=True,
        )

    elif not os.path.isdir(
        parent_directory
    ):
        raise FileNotFoundError(
            parent_directory
        )

    temporary_path = (
        full_path
        + ".agent-tmp"
    )

    with open(
        temporary_path,
        "w",
        encoding="utf-8",
        newline="\n",
    ) as handle:
        handle.write(
            content
        )

    os.replace(
        temporary_path,
        full_path,
    )

    return {
        "written": True,
        "path": os.path.relpath(
            full_path,
            SAFE_DIRECTORY,
        ).replace(
            os.sep,
            "/",
        ),
        "bytes": len(
            content.encode(
                "utf-8"
            )
        ),
        "plan_id": plan_id,
    }


# ============================================================================
# TOOL REGISTRY
# ============================================================================

TOOLS: dict[str, Callable[..., Any]] = {
    "inventory_workspace":
        inventory_workspace,

    "list_project_structure":
        list_project_structure,

    "find_workspace_files":
        find_workspace_files,

    "read_workspace_file":
        read_workspace_file,

    "read_workspace_files":
        read_workspace_files,

    "search_codebase":
        search_codebase,

    "analyze_architecture_drift":
        analyze_architecture_drift,

    "get_engineering_fault_log":
        get_engineering_fault_log,

    "log_engineering_fault":
        log_engineering_fault,

    "get_workspace_file_metadata":
        get_workspace_file_metadata,

    "write_workspace_file":
        write_workspace_file,

    "execute_terminal_command":
        execute_terminal_command,
}


# ============================================================================
# OLLAMA TOOL SCHEMAS
# ============================================================================

TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "inventory_workspace",
            "description": (
                "Recursively inventory the approved workspace. "
                "Read-only."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "list_project_structure",
            "description": (
                "List a bounded recursive tree of the "
                "approved workspace. Read-only."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                    },
                    "max_depth": {
                        "type": "integer",
                    },
                },
                "required": [],
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "find_workspace_files",
            "description": (
                "Find workspace files whose filename "
                "contains a supplied pattern. Read-only."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                    },
                    "case_sensitive": {
                        "type": "boolean",
                    },
                    "max_results": {
                        "type": "integer",
                    },
                },
                "required": [
                    "pattern"
                ],
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "read_workspace_file",
            "description": (
                "Read an approved workspace text file, "
                "optionally by line range. Read-only."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                    },
                    "start_line": {
                        "type": "integer",
                    },
                    "end_line": {
                        "type": "integer",
                    },
                },
                "required": [
                    "path"
                ],
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "read_workspace_files",
            "description": (
                "Read multiple approved workspace text files "
                "within the configured batch byte limit. "
                "Read-only."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "paths": {
                        "type": "array",
                        "items": {
                            "type": "string",
                        },
                    },
                },
                "required": [
                    "paths"
                ],
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "search_codebase",
            "description": (
                "Search text in readable source/config files "
                "in the approved workspace. Read-only."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                    },
                    "extensions": {
                        "type": "array",
                        "items": {
                            "type": "string",
                        },
                    },
                    "case_sensitive": {
                        "type": "boolean",
                    },
                    "max_results": {
                        "type": "integer",
                    },
                },
                "required": [
                    "query"
                ],
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "analyze_architecture_drift",
            "description": (
                "Inventory documentation, source, and config "
                "categories. Does not claim semantic drift "
                "without evidence. Read-only."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "get_engineering_fault_log",
            "description": (
                "Read the workspace engineering fault log. "
                "Read-only."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "log_engineering_fault",
            "description": (
                "Append an evidence-based engineering fault "
                "record to the workspace fault log. Requires "
                "an exact human-approved plan_id because this "
                "modifies the workspace."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "entry": {
                        "type": "object",
                    },
                    "plan_id": {
                        "type": "string",
                    },
                },
                "required": [
                    "entry",
                    "plan_id",
                ],
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "get_workspace_file_metadata",
            "description": (
                "Get size, modified time, and SHA-256 for "
                "an approved workspace file. Read-only."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                    },
                },
                "required": [
                    "path"
                ],
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "write_workspace_file",
            "description": (
                "Write a workspace file. REQUIRES an exact "
                "human-approved plan_id matching the active "
                "approval. Do not call without approval."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                    },
                    "content": {
                        "type": "string",
                    },
                    "plan_id": {
                        "type": "string",
                    },
                    "create_dirs": {
                        "type": "boolean",
                    },
                },
                "required": [
                    "path",
                    "content",
                    "plan_id",
                ],
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "execute_terminal_command",
            "description": (
                "Execute a terminal command inside the approved "
                "workspace. Requires an exact human-approved "
                "plan_id matching the active approval. "
                "Destructive command patterns are blocked."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                    },
                    "cwd": {
                        "type": "string",
                    },
                    "timeout_seconds": {
                        "type": "integer",
                    },
                    "plan_id": {
                        "type": "string",
                    },
                },
                "required": [
                    "command",
                    "plan_id",
                ],
            },
        },
    },
]


# ============================================================================
# SYSTEM PROMPT
# ============================================================================

SYSTEM_PROMPT = r"""
You are the PLG Engineering Agent.

You are operating against an explicitly approved local workspace.

NON-NEGOTIABLE ENGINEERING RULES:

1. Never invent files, symbols, endpoints, runtime results,
   configuration, versions, commits, or test outcomes.

2. Treat evidence domains separately:
   [WORKSPACE]
   [LIVE]
   [GITEA]
   [TEST]
   [DOCS]

   Never silently merge these domains.

3. Label conclusions:
   [VERIFIED]
   [INFERRED]
   [UNKNOWN]

4. Documentation describes intended behavior.
   Documentation does not prove runtime behavior.

5. Source code proves implementation.
   Source code does not prove deployment/runtime behavior.

6. A passing build or test proves only what that build/test
   actually exercises.

7. Do not call a defect resolved unless the original failure
   condition has been reproduced or otherwise established and
   the corrected behavior has been demonstrated.

8. During discovery, verification, root-cause investigation,
   planning, validation, and proof, do not modify application
   files unless the current phase explicitly permits it and an
   exact human-approved plan_id exists.

9. Never execute raw JSON in assistant content as a tool call.
   Only native structured tool_calls supplied by Ollama are
   executable.

10. When a tool returns incomplete or truncated evidence, state
    that limitation and gather more evidence instead of guessing.

11. If evidence contradicts the current hypothesis, stop following
    the hypothesis and reassess.

12. Compare failing paths against at least two known working paths
    when the defect concerns one sector/component behaving
    differently from others.

13. For Anvil/persona issues, trace:

       source definitions
            ->
       registration/registry
            ->
       discovery
            ->
       backend API
            ->
       client
            ->
       frontend state
            ->
       filtering
            ->
       rendering
            ->
       selection
            ->
       policy/config/lifecycle

    only where those layers are actually evidenced.

    Do not assume a layer exists.

14. Before implementation, produce a concrete plan with exact
    files/symbols and a PLAN ID.

15. Wait for human approval before implementation.

16. For implementation tools, pass the exact approved plan_id.

17. If approval is absent or mismatched, do not write or execute
    the command.

18. Do not perform unrelated refactors, dependency upgrades,
    generated-file changes, or test weakening unless explicitly
    part of the approved plan.

19. When stalled or uncertain, gather evidence or report UNKNOWN.
    Do not fabricate progress.

20. If a tool operation fails, report the actual failure and use
    evidence to determine the next step.

21. Never describe a tool call as successful merely because the
    model requested it. The Python runtime result is authoritative.

22. Never treat the number of model rounds as proof of progress.

23. If repeated tool operations produce no new evidence, stop
    repeating them and reassess.

24. Runtime proof must identify the actual runtime/build/service
    identity when that information is available.

25. Never claim [LIVE] evidence unless an actual live system was
    queried.

26. Never claim [GITEA] evidence unless Gitea was actually queried.

27. Never claim [TEST] evidence unless the test was actually run
    and its result was observed.

28. Never claim [DOCS] evidence unless the relevant documentation
    was actually inspected.

29. Never claim [WORKSPACE] evidence unless the relevant local
    workspace files were actually inspected.

30. A model conclusion is not evidence by itself.
""".strip()


# ============================================================================
# OLLAMA MESSAGE NORMALIZATION
# ============================================================================

def normalize_arguments(
    arguments: Any,
) -> dict[str, Any]:
    if arguments is None:
        return {}

    if isinstance(
        arguments,
        dict,
    ):
        return arguments

    if isinstance(
        arguments,
        str,
    ):
        parsed = json.loads(
            arguments
        )

        if not isinstance(
            parsed,
            dict,
        ):
            raise ValueError(
                "Tool arguments JSON must "
                "decode to an object"
            )

        return parsed

    if hasattr(
        arguments,
        "model_dump",
    ):
        dumped = arguments.model_dump()

        if isinstance(
            dumped,
            dict,
        ):
            return dumped

    if hasattr(
        arguments,
        "dict",
    ):
        dumped = arguments.dict()

        if isinstance(
            dumped,
            dict,
        ):
            return dumped

    raise TypeError(
        "Unsupported tool argument type: "
        f"{type(arguments).__name__}"
    )


def extract_tool_calls(
    message: Any,
) -> list[dict[str, Any]]:
    calls = getattr(
        message,
        "tool_calls",
        None,
    )

    if (
        calls is None
        and isinstance(
            message,
            dict,
        )
    ):
        calls = message.get(
            "tool_calls"
        )

    if not calls:
        return []

    normalized: list[dict[str, Any]] = []

    for call in calls:
        function = getattr(
            call,
            "function",
            None,
        )

        if (
            function is None
            and isinstance(
                call,
                dict,
            )
        ):
            function = call.get(
                "function",
                {},
            )

        if function is None:
            continue

        if isinstance(
            function,
            dict,
        ):
            name = function.get(
                "name"
            )

            arguments = function.get(
                "arguments"
            )

        else:
            name = getattr(
                function,
                "name",
                None,
            )

            arguments = getattr(
                function,
                "arguments",
                None,
            )

        normalized.append(
            {
                "name": name,
                "arguments": normalize_arguments(
                    arguments
                ),
            }
        )

    return normalized


def message_to_dict(
    message: Any,
) -> dict[str, Any]:
    if isinstance(
        message,
        dict,
    ):
        return message

    if hasattr(
        message,
        "model_dump",
    ):
        return message.model_dump(
            exclude_none=True
        )

    if hasattr(
        message,
        "dict",
    ):
        return message.dict(
            exclude_none=True
        )

    return {
        "role": getattr(
            message,
            "role",
            "assistant",
        ),
        "content": getattr(
            message,
            "content",
            "",
        ),
    }


# ============================================================================
# RAW JSON TOOL SAFETY
# ============================================================================

def classify_content_tool_syntax(
    content: str,
) -> str | None:
    if not content or not content.strip():
        return None

    try:
        value = json.loads(
            content
        )
    except json.JSONDecodeError:
        return None

    if (
        isinstance(
            value,
            dict,
        )
        and (
            (
                "name" in value
                and "arguments" in value
            )
            or "tool_calls" in value
        )
    ):
        return "RAW_JSON_IN_CONTENT"

    return None


# ============================================================================
# OLLAMA HTTP API
# ============================================================================

def get_api_json(
    path: str,
) -> tuple[int, Any]:
    url = (
        OLLAMA_HOST
        + path
    )

    request = urllib.request.Request(
        url,
        method="GET",
        headers={
            "Accept": "application/json"
        },
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=10,
        ) as response:
            body = response.read().decode(
                "utf-8",
                errors="replace",
            )

            return (
                response.status,
                json.loads(body),
            )

    except urllib.error.HTTPError as exc:
        body = exc.read().decode(
            "utf-8",
            errors="replace",
        )

        try:
            parsed = json.loads(
                body
            )
        except json.JSONDecodeError:
            parsed = body

        return (
            exc.code,
            parsed,
        )


# ============================================================================
# NATIVE TOOL-CALL DIAGNOSTIC
# ============================================================================

def run_native_tool_test(
    client: Any,
    model: str,
) -> dict[str, Any]:
    test_tool = [
        {
            "type": "function",
            "function": {
                "name": "test_tool",
                "description": (
                    "Test native structured "
                    "tool calling."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {},
                },
            },
        }
    ]

    try:
        response = client.chat(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Use the available "
                        "tool now."
                    ),
                }
            ],
            tools=test_tool,
            stream=False,
        )

        message = getattr(
            response,
            "message",
            None,
        )

        calls = extract_tool_calls(
            message
        )

        content = (
            getattr(
                message,
                "content",
                "",
            )
            if message is not None
            else ""
        )

        classification = (
            "STRUCTURED_TOOL_CALL"
            if calls
            else (
                classify_content_tool_syntax(
                    content
                )
                or "NO_TOOL_CALL"
            )
        )

        return {
            "ok": True,
            "model": model,
            "classification": classification,
            "message": (
                message_to_dict(
                    message
                )
                if message is not None
                else None
            ),
        }

    except Exception as exc:
        return {
            "ok": False,
            "model": model,
            "error": (
                f"{type(exc).__name__}: "
                f"{exc}"
            ),
        }


# ============================================================================
# DIAGNOSTICS
# ============================================================================

def diagnose(
    client: Any,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "host": OLLAMA_HOST,
        "selected_model": TARGET_MODEL,

        "python_client": {
            "installed": ollama is not None,
        },

        "api_version": {},

        "models": {},

        "native_tool_test": {},

        "configuration": {
            "workspace": SAFE_DIRECTORY,
            "prompt_directory": PROMPT_DIRECTORY,
            "fault_log": LOG_FILE_PATH,
            "max_tool_rounds": MAX_TOOL_ROUNDS,
            "heartbeat_seconds": HEARTBEAT_SECONDS,
            "stall_seconds": STALL_SECONDS,
        },

        "safety_rule": (
            "RAW_JSON_IN_CONTENT is evidence "
            "of attempted semantic tool syntax, "
            "not permission to execute the content "
            "as a tool call."
        ),
    }

    if ollama is not None:
        try:
            result[
                "python_client"
            ][
                "module"
            ] = ollama.__file__

        except Exception:
            pass

        try:
            result[
                "python_client"
            ][
                "version"
            ] = importlib.metadata.version(
                "ollama"
            )

        except importlib.metadata.PackageNotFoundError:
            result[
                "python_client"
            ][
                "version"
            ] = "unknown"

    executable = shutil.which(
        "ollama"
    )

    if executable:
        result[
            "ollama_executable"
        ] = executable

    status, data = get_api_json(
        "/api/version"
    )

    result[
        "api_version"
    ] = {
        "ok": status == 200,
        "status": status,
        "url": (
            OLLAMA_HOST
            + "/api/version"
        ),
        "data": data,
    }

    status, data = get_api_json(
        "/api/tags"
    )

    result[
        "models"
    ] = {
        "ok": status == 200,
        "status": status,
        "url": (
            OLLAMA_HOST
            + "/api/tags"
        ),
        "data": data,
    }

    if client is not None:
        result[
            "native_tool_test"
        ][
            TARGET_MODEL
        ] = run_native_tool_test(
            client,
            TARGET_MODEL,
        )

        if TARGET_MODEL != "qwen2.5-coder:7b":
            result[
                "native_tool_test"
            ][
                "qwen2.5-coder:7b"
            ] = run_native_tool_test(
                client,
                "qwen2.5-coder:7b",
            )

    return result


# ============================================================================
# ENGINEERING AGENT
# ============================================================================

class EngineeringAgent:

    def __init__(self) -> None:
        if ollama is None:
            raise RuntimeError(
                "Python package 'ollama' is not "
                "installed in this Python environment."
            )

        self.client = ollama.Client(
            host=OLLAMA_HOST
        )

        self.activity = ActivityState(
            model=TARGET_MODEL
        )

        self.monitor = ActivityMonitor(
            self.activity
        )

        self.messages: list[dict[str, Any]] = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            }
        ]

        self.loaded_prompt_name: str | None = None
        self.loaded_prompt_content: str | None = None

        self.current_phase = "IDLE"

        self.approved_plan_id: str | None = None
        self.last_plan_id: str | None = None

        self.last_result: str = ""

        self.running = False


    # ------------------------------------------------------------------------
    # PROMPTS
    # ------------------------------------------------------------------------

    def reset_conversation(self) -> None:
        self.messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            }
        ]

        self.last_result = ""
        self.last_plan_id = None

        print(
            "Conversation context cleared. "
            "Approval state was not changed."
        )


    def set_phase_from_prompt(
        self,
        filename: str,
    ) -> None:
        self.current_phase = PHASES.get(
            os.path.basename(filename),
            os.path.basename(filename),
        )

        self.activity.update(
            phase=self.current_phase
        )


    def expand_prompt(
        self,
        content: str,
    ) -> str:
        current_time = (
            datetime.now()
            .astimezone()
        )

        replacements = {
            "{{WORKSPACE}}":
                SAFE_DIRECTORY,

            "{{PROMPT_DIRECTORY}}":
                PROMPT_DIRECTORY,

            "{{FAULT_LOG}}":
                LOG_FILE_PATH,

            "{{DATE}}":
                current_time.strftime(
                    "%Y-%m-%d"
                ),

            "{{DATETIME}}":
                current_time.isoformat(
                    timespec="seconds"
                ),
        }

        for key, value in replacements.items():
            content = content.replace(
                key,
                value,
            )

        return content


    def load_prompt(
        self,
        prompt_path: str,
    ) -> str:
        if os.path.isabs(
            prompt_path
        ):
            full_path = require_prompt_path(
                prompt_path
            )
        else:
            full_path = require_prompt_path(
                os.path.join(
                    PROMPT_DIRECTORY,
                    prompt_path,
                )
            )

        content = read_text_file(
            full_path,
            max_bytes=2 * 1024 * 1024,
        )

        self.loaded_prompt_name = os.path.basename(
            full_path
        )

        self.loaded_prompt_content = (
            self.expand_prompt(
                content
            )
        )

        self.set_phase_from_prompt(
            self.loaded_prompt_name
        )

        return self.loaded_prompt_content


    def prompt_files(self) -> list[str]:
        if not os.path.isdir(
            PROMPT_DIRECTORY
        ):
            return []

        return sorted(
            name
            for name in os.listdir(
                PROMPT_DIRECTORY
            )
            if name.lower().endswith(
                ".md"
            )
        )


    # ------------------------------------------------------------------------
    # STATUS
    # ------------------------------------------------------------------------

    def status_line(self) -> str:
        snapshot = self.activity.snapshot()

        return (
            f"Status={snapshot['status']} | "
            f"Phase={snapshot['phase']} | "
            f"Activity={snapshot['activity']} | "
            f"Model={snapshot['model']} | "
            f"Round="
            f"{snapshot['round_number']}/"
            f"{snapshot['max_rounds']} | "
            f"Elapsed="
            f"{format_duration(snapshot['elapsed_seconds'])} | "
            f"Idle="
            f"{format_duration(snapshot['idle_seconds'])}"
        )


    def print_status(self) -> None:
        print(
            self.status_line()
        )

        snapshot = self.activity.snapshot()

        print(
            "  "
            f"Tool calls={snapshot['tool_calls']} "
            f"completed={snapshot['tools_completed']} "
            f"files_read={snapshot['files_read']} "
            f"files_written={snapshot['files_written']} "
            f"commands={snapshot['commands_executed']} "
            f"errors={snapshot['errors']}"
        )


    # ------------------------------------------------------------------------
    # HUMAN APPROVAL
    # ------------------------------------------------------------------------

    def approve(
        self,
        plan_id: str,
    ) -> None:
        if not plan_id.strip():
            raise ValueError(
                "plan_id is required"
            )

        self.approved_plan_id = (
            plan_id.strip()
        )

        print(
            "APPROVED PLAN: "
            f"{self.approved_plan_id}"
        )

        print(
            "Write/command tools may execute "
            "only when they supply this exact plan_id."
        )


    def deny(self) -> None:
        self.approved_plan_id = None

        print(
            "Approval cleared. "
            "No implementation plan is currently approved."
        )


    def validate_mutation_approval(
        self,
        supplied_plan_id: str | None,
    ) -> None:
        if not self.approved_plan_id:
            raise PermissionError(
                "No human-approved plan exists. "
                "Use /approve <plan_id> before mutation."
            )

        if (
            supplied_plan_id
            != self.approved_plan_id
        ):
            raise PermissionError(
                "Supplied plan_id does not exactly "
                "match the human-approved plan_id."
            )


    # ------------------------------------------------------------------------
    # TOOL DISPATCH
    # ------------------------------------------------------------------------

    def dispatch_tool(
        self,
        name: str,
        arguments: dict[str, Any],
    ) -> str:
        if name not in TOOLS:
            raise KeyError(
                f"Unknown tool: {name}"
            )

        if name in {
            "write_workspace_file",
            "execute_terminal_command",
            "log_engineering_fault",
        }:
            self.validate_mutation_approval(
                arguments.get(
                    "plan_id"
                )
            )

        started = time.monotonic()

        snapshot = self.activity.snapshot()

        self.activity.update(
            status="TOOL",
            activity=f"Running {name}",
            tool_name=name,
            tool_started_at=started,
            tool_calls=(
                snapshot["tool_calls"]
                + 1
            ),
        )

        print(
            f"\n[{now_text()}] "
            f"TOOL START | {name}"
        )

        print(
            "[ARGUMENTS] "
            + json_dumps(
                arguments
            )
        )

        try:
            result = TOOLS[name](
                **arguments
            )

            snapshot = self.activity.snapshot()

            if name == "read_workspace_file":
                self.activity.update(
                    files_read=(
                        snapshot["files_read"]
                        + 1
                    )
                )

            elif name == "read_workspace_files":
                count = len(
                    arguments.get(
                        "paths",
                        [],
                    )
                )

                self.activity.update(
                    files_read=(
                        snapshot["files_read"]
                        + count
                    )
                )

            elif name == "write_workspace_file":
                self.activity.update(
                    files_written=(
                        snapshot["files_written"]
                        + 1
                    )
                )

            elif name == "execute_terminal_command":
                self.activity.update(
                    commands_executed=(
                        snapshot[
                            "commands_executed"
                        ]
                        + 1
                    )
                )

            snapshot = self.activity.snapshot()

            self.activity.update(
                status="WORKING",
                activity=f"Completed {name}",
                tool_name="",
                tools_completed=(
                    snapshot[
                        "tools_completed"
                    ]
                    + 1
                ),
            )

            output = truncate_text(
                json_dumps(
                    result
                )
            )

            print(
                f"[{now_text()}] "
                f"TOOL COMPLETE | "
                f"{name} | "
                f"{format_duration(time.monotonic() - started)}"
            )

            print(
                "[TOOL RESULT] "
                + output
            )

            return output

        except Exception as exc:
            snapshot = self.activity.snapshot()

            self.activity.update(
                status="WORKING",
                activity=(
                    f"Tool {name} failed"
                ),
                tool_name="",
                errors=(
                    snapshot["errors"]
                    + 1
                ),
            )

            error = {
                "ok": False,
                "tool": name,
                "error_type": (
                    type(exc).__name__
                ),
                "error": str(exc),
            }

            print(
                f"[{now_text()}] "
                f"TOOL ERROR | "
                f"{name} | "
                f"{type(exc).__name__}: "
                f"{exc}"
            )

            return json_dumps(
                error
            )


    # ------------------------------------------------------------------------
    # MODEL CALL
    # ------------------------------------------------------------------------

    def call_model(
        self,
        round_number: int,
    ) -> Any:
        if self.activity.stop_requested:
            raise KeyboardInterrupt

        self.activity.update(
            status="WAITING",
            activity=(
                f"Waiting for "
                f"{TARGET_MODEL} response"
            ),
            round_number=round_number,
            tool_name="",
        )

        print(
            f"\n[{now_text()}] "
            f"MODEL ROUND "
            f"{round_number}/{MAX_TOOL_ROUNDS} | "
            f"{self.current_phase}"
        )

        print(
            f"[{now_text()}] "
            f"MODEL WAITING | "
            f"{TARGET_MODEL}"
        )

        return self.client.chat(
            model=TARGET_MODEL,
            messages=self.messages,
            tools=TOOL_SCHEMAS,
            stream=False,
        )


    # ------------------------------------------------------------------------
    # TASK EXECUTION
    # ------------------------------------------------------------------------

    def run_loaded_prompt(
        self,
    ) -> None:
        if not self.loaded_prompt_content:
            raise RuntimeError(
                "No prompt is loaded. "
                "Use /load <file> or /prompt <file>."
            )

        self.messages.append(
            {
                "role": "user",
                "content": (
                    self.loaded_prompt_content
                ),
            }
        )

        self.run_agent_loop()


    def run_text_task(
        self,
        task: str,
    ) -> None:
        if not task.strip():
            return

        self.messages.append(
            {
                "role": "user",
                "content": task,
            }
        )

        self.current_phase = (
            "INTERACTIVE ENGINEERING TASK"
        )

        self.activity.update(
            phase=self.current_phase
        )

        self.run_agent_loop()


    # ------------------------------------------------------------------------
    # MAIN MODEL / TOOL LOOP
    # ------------------------------------------------------------------------

    def run_agent_loop(
        self,
    ) -> None:
        if self.running:
            print(
                "An agent task is already running."
            )
            return

        self.running = True

        self.activity.update(
            status="WORKING",
            phase=self.current_phase,
            activity="Starting agent task",
            started_at=time.monotonic(),
            round_number=0,
            stop_requested=False,
        )

        self.monitor.start()

        try:
            identical_calls: dict[str, int] = {}

            for round_number in range(
                1,
                MAX_TOOL_ROUNDS + 1,
            ):
                if self.activity.stop_requested:
                    raise KeyboardInterrupt

                response = self.call_model(
                    round_number
                )

                message = getattr(
                    response,
                    "message",
                    None,
                )

                if message is None:
                    raise RuntimeError(
                        "Ollama returned a response "
                        "without a message object"
                    )

                message_dict = message_to_dict(
                    message
                )

                self.messages.append(
                    message_dict
                )

                content = (
                    getattr(
                        message,
                        "content",
                        "",
                    )
                    or ""
                )

                tool_calls = extract_tool_calls(
                    message
                )

                raw_classification = (
                    classify_content_tool_syntax(
                        content
                    )
                )

                if (
                    raw_classification
                    == "RAW_JSON_IN_CONTENT"
                    and not tool_calls
                ):
                    warning = (
                        "The model emitted tool-shaped JSON "
                        "as ordinary content. It was NOT "
                        "executed because native structured "
                        "tool_calls were absent."
                    )

                    print(
                        "\n[SECURITY] "
                        + warning
                    )

                if not tool_calls:
                    self.activity.update(
                        status="COMPLETE",
                        activity=(
                            "Model returned final response"
                        ),
                        tool_name="",
                    )

                    self.last_result = (
                        content
                    )

                    print(
                        "\n========== "
                        "AGENT RESPONSE =========="
                    )

                    print(
                        content
                    )

                    print(
                        "========== "
                        "END RESPONSE =========="
                    )

                    return

                for call in tool_calls:
                    name = call["name"]
                    arguments = call["arguments"]

                    signature = json.dumps(
                        {
                            "name": name,
                            "arguments": arguments,
                        },
                        sort_keys=True,
                        ensure_ascii=False,
                    )

                    identical_calls[
                        signature
                    ] = (
                        identical_calls.get(
                            signature,
                            0,
                        )
                        + 1
                    )

                    if (
                        identical_calls[
                            signature
                        ]
                        >= 4
                    ):
                        self.messages.append(
                            {
                                "role": "user",
                                "content": (
                                    "STOP: The same tool "
                                    "operation has been "
                                    "repeated at least four "
                                    "times without new evidence. "
                                    "Do not repeat it. "
                                    "Reassess the investigation "
                                    "and proceed using existing "
                                    "evidence or report UNKNOWN."
                                ),
                            }
                        )

                        print(
                            "\n[WARNING] "
                            "NO-PROGRESS LOOP DETECTED | "
                            f"{name} repeated "
                            f"{identical_calls[signature]} times"
                        )

                    result = self.dispatch_tool(
                        name,
                        arguments,
                    )

                    # Ollama tool messages identify the tool
                    # that produced the result.
                    self.messages.append(
                        {
                            "role": "tool",
                            "tool_name": name,
                            "content": result,
                        }
                    )

                self.activity.update(
                    status="WORKING",
                    activity=(
                        "Analysing tool results"
                    ),
                    round_number=round_number,
                )

            self.activity.update(
                status="STOPPED",
                activity=(
                    "Maximum tool rounds reached "
                    f"({MAX_TOOL_ROUNDS})"
                ),
            )

            self.last_result = (
                "Maximum tool rounds reached before "
                "the model returned a final response. "
                "This is not evidence that the task is resolved."
            )

            print(
                "\n[STOP] Maximum tool rounds reached: "
                f"{MAX_TOOL_ROUNDS}"
            )

        except KeyboardInterrupt:
            self.activity.update(
                status="CANCELLED",
                activity=(
                    "Human interrupted the agent"
                ),
            )

            print(
                "\n[STOP] "
                "Agent task cancelled by user."
            )

        except Exception as exc:
            snapshot = self.activity.snapshot()

            self.activity.update(
                status="ERROR",
                activity=(
                    f"Agent error: "
                    f"{type(exc).__name__}"
                ),
                errors=(
                    snapshot["errors"]
                    + 1
                ),
            )

            print(
                f"\n[AGENT ERROR] "
                f"{type(exc).__name__}: "
                f"{exc}"
            )

            traceback.print_exc()

        finally:
            self.monitor.stop()

            self.running = False

            self.print_status()


    # ------------------------------------------------------------------------
    # STOP
    # ------------------------------------------------------------------------

    def stop(self) -> None:
        self.activity.update(
            stop_requested=True,
            status="STOPPING",
            activity="Stop requested",
        )


    # ------------------------------------------------------------------------
    # CLI COMMANDS
    # ------------------------------------------------------------------------

    def handle_command(
        self,
        line: str,
    ) -> bool:
        stripped = line.strip()

        if not stripped:
            return True

        if not stripped.startswith("/"):
            self.run_text_task(
                stripped
            )
            return True

        parts = stripped.split(
            maxsplit=1
        )

        command = parts[0].lower()

        argument = (
            parts[1].strip()
            if len(parts) == 2
            else ""
        )

        # ------------------------------------------------------------
        # EXIT
        # ------------------------------------------------------------

        if command in {
            "/exit",
            "/quit",
            "/q",
            "/bye",
        }:
            return False

        # ------------------------------------------------------------
        # HELP
        # ------------------------------------------------------------

        if command == "/help":
            print(
                HELP_TEXT
            )

        # ------------------------------------------------------------
        # PROMPTS
        # ------------------------------------------------------------

        elif command == "/prompts":
            files = self.prompt_files()

            if files:
                print(
                    "\n".join(files)
                )
            else:
                print(
                    "No prompt files found."
                )

        # ------------------------------------------------------------
        # LOAD
        # ------------------------------------------------------------

        elif command == "/load":
            if not argument:
                print(
                    "Usage: /load <prompt-file>"
                )

            else:
                content = self.load_prompt(
                    argument
                )

                print(
                    f"Loaded: "
                    f"{self.loaded_prompt_name}"
                )

                print(
                    f"Phase: "
                    f"{self.current_phase}"
                )

                print(
                    f"Characters: "
                    f"{len(content)}"
                )

        # ------------------------------------------------------------
        # PROMPT
        # ------------------------------------------------------------

        elif command == "/prompt":
            if not argument:
                print(
                    "Usage: /prompt <prompt-file>"
                )

            else:
                content = self.load_prompt(
                    argument
                )

                print(
                    "Loaded and executing: "
                    f"{self.loaded_prompt_name}"
                )

                print(
                    f"Phase: "
                    f"{self.current_phase}"
                )

                print(
                    f"Characters: "
                    f"{len(content)}"
                )

                self.run_loaded_prompt()

        # ------------------------------------------------------------
        # SEND
        # ------------------------------------------------------------

        elif command == "/send":
            self.run_loaded_prompt()

        # ------------------------------------------------------------
        # READ
        # ------------------------------------------------------------

        elif command == "/read":
            if not argument:
                print(
                    "Usage: /read <workspace-file>"
                )

            else:
                try:
                    result = read_workspace_file(
                        argument
                    )

                    print(
                        result["content"]
                    )

                except Exception as exc:
                    print(
                        f"[ERROR] "
                        f"{type(exc).__name__}: "
                        f"{exc}"
                    )

        # ------------------------------------------------------------
        # SEARCH
        # ------------------------------------------------------------

        elif command == "/search":
            if not argument:
                print(
                    "Usage: /search <text>"
                )

            else:
                print(
                    json_dumps(
                        search_codebase(
                            argument
                        )
                    )
                )

        # ------------------------------------------------------------
        # FILE SEARCH
        # ------------------------------------------------------------

        elif command == "/files":
            if not argument:
                print(
                    "Usage: /files "
                    "<filename-substring>"
                )

            else:
                print(
                    json_dumps(
                        find_workspace_files(
                            argument
                        )
                    )
                )

        # ------------------------------------------------------------
        # TREE
        # ------------------------------------------------------------

        elif command == "/tree":
            print(
                json_dumps(
                    list_project_structure(
                        argument or "."
                    )
                )
            )

        # ------------------------------------------------------------
        # STATUS
        # ------------------------------------------------------------

        elif command == "/status":
            self.print_status()

            print(
                "Loaded prompt: "
                + (
                    self.loaded_prompt_name
                    or "none"
                )
            )

            print(
                "Approved plan: "
                + (
                    self.approved_plan_id
                    or "none"
                )
            )

        # ------------------------------------------------------------
        # APPROVE
        # ------------------------------------------------------------

        elif command == "/approve":
            if not argument:
                print(
                    "Usage: /approve "
                    "<exact-plan-id>"
                )

            else:
                self.approve(
                    argument
                )

        # ------------------------------------------------------------
        # DENY
        # ------------------------------------------------------------

        elif command == "/deny":
            self.deny()

        # ------------------------------------------------------------
        # CLEAR
        # ------------------------------------------------------------

        elif command == "/clear":
            self.reset_conversation()

        # ------------------------------------------------------------
        # FAULTS
        # ------------------------------------------------------------

        elif command == "/faults":
            try:
                print(
                    json_dumps(
                        load_fault_log()
                    )
                )

            except Exception as exc:
                print(
                    f"[ERROR] "
                    f"{type(exc).__name__}: "
                    f"{exc}"
                )

        # ------------------------------------------------------------
        # DIAGNOSE
        # ------------------------------------------------------------

        elif command == "/diagnose":
            try:
                print(
                    json_dumps(
                        diagnose(
                            self.client
                        )
                    )
                )

            except Exception as exc:
                print(
                    f"[ERROR] "
                    f"{type(exc).__name__}: "
                    f"{exc}"
                )

        # ------------------------------------------------------------
        # LIVE
        # ------------------------------------------------------------

        elif command == "/live":
            print(
                "Live diagnostics are not configured "
                "in this local implementation. "
                "No live endpoint is assumed or invented."
            )

        # ------------------------------------------------------------
        # UNKNOWN
        # ------------------------------------------------------------

        else:
            print(
                f"Unknown command: {command}. "
                "Use /help."
            )

        return True


# ============================================================================
# HELP
# ============================================================================

HELP_TEXT = r"""
Commands:

  /prompt <file>
      Load and execute a prompt from:
      E:\dSeek-workpace\prompts

  /load <file>
      Load a prompt without executing it.

  /send
      Execute the currently loaded prompt.

  /prompts
      List available prompt files.

  /read <file>
      Read a workspace file.

  /search <text>
      Search workspace source/config text.

  /files <pattern>
      Find workspace files by filename substring.

  /tree [path]
      Show the bounded workspace tree.

  /status
      Show live agent status, phase, counters and approval.

  /approve <plan_id>
      Approve exactly one implementation plan ID.

  /deny
      Clear the current plan approval.

  /faults
      Show the engineering fault log.

  /diagnose
      Diagnose Ollama, Python client, API and native tool calling.

  /clear
      Clear model conversation context.

  /live
      Report live-diagnostics configuration state.

  /help
      Show this help.

  /exit
      Exit.

Any line without a leading '/' is sent to the
engineering agent as an interactive task.


SAFETY:

  - Native structured Ollama tool_calls are executable.
  - Tool-shaped JSON emitted in message.content is NEVER executed.
  - Workspace paths are constrained with realpath/commonpath.
  - Workspace writes require an exact approved plan_id.
  - Fault-log writes require an exact approved plan_id.
  - Terminal execution requires an exact approved plan_id.
  - Destructive terminal command patterns are blocked.
  - The initial discovery prompt remains read-only by
    instruction and tool policy.
  - The Python runtime, not the model, controls activity status.
""".strip()


# ============================================================================
# MAIN
# ============================================================================

def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "PLG local Ollama "
            "engineering agent"
        )
    )

    parser.add_argument(
        "--diagnose",
        action="store_true",
        help=(
            "Run diagnostics and exit"
        ),
    )

    args = parser.parse_args()

    print(
        "PLG Engineering Agent"
    )

    print(
        f"Workspace: {SAFE_DIRECTORY}"
    )

    print(
        f"Prompt directory: {PROMPT_DIRECTORY}"
    )

    print(
        f"Ollama host: {OLLAMA_HOST}"
    )

    print(
        f"Model: {TARGET_MODEL}"
    )

    print(
        "Maximum tool rounds: "
        f"{MAX_TOOL_ROUNDS}"
    )

    print(
        "Heartbeat interval: "
        f"{HEARTBEAT_SECONDS}s"
    )

    print(
        "Stall threshold: "
        f"{STALL_SECONDS}s"
    )

    if ollama is None:
        print(
            "ERROR: Python package 'ollama' "
            "is not installed for this "
            "Python interpreter."
        )

        return 1

    try:
        agent = EngineeringAgent()

    except Exception as exc:
        print(
            f"ERROR: "
            f"{type(exc).__name__}: "
            f"{exc}"
        )

        return 1

    if args.diagnose:
        print(
            json_dumps(
                diagnose(
                    agent.client
                )
            )
        )

        return 0

    print(
        "Type /help for commands. "
        "Ctrl+C requests cancellation "
        "of a running agent task."
    )

    while True:
        try:
            line = input(
                "\nPLG> "
            )

        except KeyboardInterrupt:
            if agent.running:
                agent.stop()
                continue

            print(
                "\nExiting."
            )

            return 0

        except EOFError:
            print(
                "\nExiting."
            )

            return 0

        try:
            should_continue = (
                agent.handle_command(
                    line
                )
            )

            if not should_continue:
                return 0

        except KeyboardInterrupt:
            agent.stop()

            print(
                "\nStop requested."
            )

        except Exception as exc:
            print(
                f"[COMMAND ERROR] "
                f"{type(exc).__name__}: "
                f"{exc}"
            )


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    raise SystemExit(
        main()
    )