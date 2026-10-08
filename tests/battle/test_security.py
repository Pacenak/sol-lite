import pytest

from sol_lite.core.exceptions import (
    PermissionDenied,
    SecurityError,
)
from sol_lite.security.command_guard import (
    validate_command,
)
from sol_lite.security.path_guard import (
    resolve_workspace_path,
)


def test_traversal():
    with pytest.raises(SecurityError):
        resolve_workspace_path(
            "../../etc/passwd",
            "/tmp/sol-workspace",
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
def test_destructive(command):
    with pytest.raises(PermissionDenied):
        validate_command(
            command,
            [
                "git",
                "python",
                "sudo",
            ],
            [
                "rm",
                "sudo",
                "shutdown",
                "git reset --hard",
                "git clean -fdx",
            ],
        )