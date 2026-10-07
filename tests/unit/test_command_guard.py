import pytest

from sol_lite.core.exceptions import PermissionDenied
from sol_lite.security.command_guard import command_name, validate_command


def test_command_name():
    assert command_name("python.exe -V") == "python"

def test_allow_list():
    assert validate_command("python -V", ["python"], []) == "python"

@pytest.mark.parametrize("command", [
    "rm -rf .", "Remove-Item -Recurse .", "del *",
    "shutdown /s", "git reset --hard", "git clean -fdx"
])
def test_dangerous_commands(command):
    with pytest.raises(PermissionDenied):
        validate_command(command, ["python", "git"],
                         ["rm", "Remove-Item", "del", "shutdown",
                          "git reset --hard", "git clean -fdx"])


def test_mutating_or_arbitrary_code_requires_approval():
    from sol_lite.security.command_guard import classify_command
    assert classify_command("git status") == "read"
    assert classify_command("git checkout main") == "approval"
    assert classify_command("python -c \"open('x','w').write('x')\"") == "approval"
    assert classify_command("echo hi > out.txt") == "approval"
    assert classify_command("echo hi && echo bye") == "approval"
    assert classify_command("git status | git diff") == "approval"
