import pytest

from sol_lite.security.role_files import path_in_role
from sol_lite.security.command_guard import validate_command


def test_role_paths():
    assert path_in_role("sol_engineer", "src/app.py")
    assert path_in_role("sol_engineer", "network/vlan.md")
    assert path_in_role("sol_engineer", "plans/sprint.md")
    assert not path_in_role("sol_docs", "src/app.py")
    assert path_in_role("sol_docs", "docs/guide.md")
    assert path_in_role("sol_docs", "plans/sprint.md")
    assert path_in_role(None, "src/app.py")


def test_unlisted_command_is_not_a_hard_deny():
    assert validate_command("ping 127.0.0.1", ["ls"], []) == "ping"


def test_sudo_setup_needs_approval_and_disk_wipe_stays_blocked():
    from sol_lite.core.exceptions import PermissionDenied
    from sol_lite.security.command_guard import classify_command

    assert classify_command("sudo ufw status") == "approval"
    assert classify_command("chmod 600 /etc/netplan/01-plg.yaml") == "approval"
    with pytest.raises(PermissionDenied):
        validate_command("sudo reboot", ["sudo"], [])
