import pytest

from sol_lite.core.exceptions import PermissionDenied
from sol_lite.security.command_guard import (
    classify_command,
    validate_command,
)


@pytest.mark.parametrize(
    "command",
    [
        "rm -rf /",
        "sudo reboot",
        "shutdown /s /t 0",
        "git reset --hard HEAD",
        "git clean -fdx",
    ],
)
def test_destructive_commands_are_blocked(command):
    with pytest.raises(PermissionDenied):
        validate_command(
            command,
            [
                "git",
                "python",
                "sudo",
                "rm",
                "shutdown",
            ],
            [
                "rm",
                "sudo",
                "shutdown",
                "git reset --hard",
                "git clean -fdx",
            ],
        )


@pytest.mark.parametrize(
    "command",
    [
        "cmd /c whoami",
        "powershell -Command whoami",
        "pwsh -Command whoami",
        "bash -c whoami",
        "zsh -c whoami",
        "sh -c whoami",
    ],
)
def test_nested_shells_are_blocked(command):
    with pytest.raises(PermissionDenied):
        validate_command(
            command,
            [
                "cmd",
                "powershell",
                "pwsh",
                "bash",
                "zsh",
                "sh",
            ],
            [],
        )


@pytest.mark.parametrize(
    "command",
    [
        "echo hello > output.txt",
        "echo one && echo two",
        "echo one | grep one",
        "git add file.txt",
        "python -c \"print('test')\"",
    ],
)
def test_compound_or_mutating_commands_require_approval(
    command,
):
    assert classify_command(command) == "approval"


@pytest.mark.parametrize(
    "command",
    [
        "pwd",
        "ls",
        "git status",
        "git diff",
        "git log",
        "whoami",
    ],
)
def test_known_read_commands_are_read_only(command):
    assert classify_command(command) == "read"