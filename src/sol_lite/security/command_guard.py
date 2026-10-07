"""Conservative, cross-platform terminal command classification."""
from __future__ import annotations

import re
import shlex

from ..core.exceptions import PermissionDenied

DANGEROUS = [
    re.compile(r"(?i)\bgit\s+reset\s+--hard\b"),
    re.compile(r"(?i)\bgit\s+clean\s+-[^\n]*f"),
    re.compile(r"(?i)\b(remove-item|rm|rmdir|del|erase)\b"),
    re.compile(r"(?i)\bformat(?:\.com)?\b"),
    re.compile(r"(?i)\bdiskpart\b"),
    re.compile(r"(?i)\b(sudo|shutdown|reboot|halt)\b"),
    re.compile(r"(?i)\bmkfs(?:\.[a-z0-9]+)?\b"),
    re.compile(r"(?i)\b(chmod|chown)\b"),
]

READ_ONLY_COMMANDS = {
    "python", "python3", "git", "ls", "dir", "pwd", "get-childitem", "get-location",
    "find", "grep", "rg", "cat", "type", "get-content", "head", "tail", "select-object",
    "which", "where", "get-command", "whoami", "uname", "sw_vers", "system_profiler",
    "tasklist", "get-process", "ps", "printenv", "env", "set", "echo", "git-status",
}


def command_name(command: str) -> str:
    try:
        tokens = shlex.split(command, posix=False)
    except ValueError:
        tokens = command.split()
    if not tokens:
        return ""
    token = tokens[0].strip('"\'')
    token = token.replace("\\", "/").rsplit("/", 1)[-1]
    return token[:-4] if token.lower().endswith(".exe") else token


def has_mutating_syntax(command: str) -> bool:
    low = command.casefold()
    if re.search(r"(^|[;&|])\s*(mkdir|md|new-item|cp|copy|copy-item|mv|move|move-item|touch)\b", low):
        return True
    # Shell control operators and redirection make the command compound or side-effect-capable.
    # We deliberately require approval rather than trying to prove safety across shell dialects.
    if any(operator in command for operator in (";", "&&", "||", "|", ">", "<")):
        return True
    if re.search(r"\b(git\s+(checkout|switch|add|commit|merge|rebase|stash|branch\s+-[dD]))\b", low):
        return True
    return bool(re.search(r"\b(pip|pip3|npm|pnpm|yarn|uv|cargo|brew)\s+(install|uninstall|remove|update|upgrade)\b", low))


def classify_command(command: str, shell: str | None = None) -> str:
    if not command.strip():
        raise PermissionDenied("Empty terminal command.")
    if any(pattern.search(command) for pattern in DANGEROUS):
        return "blocked"
    name = command_name(command).casefold()
    if not name:
        raise PermissionDenied("Unable to determine terminal command.")
    if name in {"cmd", "powershell", "pwsh", "bash", "zsh", "sh"}:
        return "blocked"
    if has_mutating_syntax(command):
        return "approval"
    tokens = command.split()
    if name in {"python", "python3"} and any(token in {"-c", "-m"} or token.endswith(".py") for token in tokens[1:]):
        return "approval"
    if name == "git":
        subcommand = next((token.casefold() for token in tokens[1:] if not token.startswith("-")), "")
        if subcommand in {"status", "diff", "log", "show", "branch", "remote", "tag", "rev-parse", "ls-files", "ls-tree", "describe", "cat-file", "grep", "shortlog"}:
            return "read"
        return "approval"
    return "read" if name in READ_ONLY_COMMANDS else "approval"


def validate_command(command, allowed_commands, blocked_commands, shell: str | None = None) -> str:
    if not command.strip():
        raise PermissionDenied("Empty terminal command.")
    low = command.casefold()
    if any(item.casefold() in low for item in blocked_commands):
        raise PermissionDenied("Terminal command is blocked by policy.")
    classification = classify_command(command, shell)
    if classification == "blocked":
        raise PermissionDenied("Terminal command matches a dangerous or nested-shell policy.")
    name = command_name(command)
    allowed = {x.casefold() for x in allowed_commands}
    if name.casefold() not in allowed:
        raise PermissionDenied(f"Command '{name}' is not in the allow-list.")
    return name
