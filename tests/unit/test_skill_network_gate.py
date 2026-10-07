from __future__ import annotations

import pytest

from sol_lite.core.exceptions import ApprovalRequired
from sol_lite.permissions.approvals import ApprovalManager
from sol_lite.permissions.engine import PermissionEngine
from sol_lite.permissions.policy import PermissionPolicy
from sol_lite.tools.skills import skill_install


class _Ctx:
    def __init__(self, permissions):
        self.permission_engine = permissions
        self.skill_manager = None


def test_github_skill_install_requires_network_permission():
    config = {
        "permissions": {
            "network": {"enabled": True, "approval_required": True},
            "skills": {"install": {"enabled": True, "approval_required": True}},
        }
    }
    permissions = PermissionEngine(PermissionPolicy(config), ApprovalManager())
    ctx = _Ctx(permissions)
    with pytest.raises(ApprovalRequired) as exc:
        skill_install(ctx, {"source": "https://github.com/example/skill", "skill_id": "x", "plan": "inspect"})
    assert "network" in str(exc.value).lower()
