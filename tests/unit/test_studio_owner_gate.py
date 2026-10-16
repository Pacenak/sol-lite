"""Admin-only feature + studio-owner unlock gates sol_studio_admin."""

from __future__ import annotations

from pathlib import Path

import yaml

from sol_lite.agents.registry import AgentRegistry
from sol_lite.security.studio_owner import admin_unlocked, studio_owner_unlocked


def _admin_agent_raw():
    return {
        "agents": {
            "sol_pa": {
                "name": "PA",
                "enabled": True,
                "role": "primary",
                "description": "x",
                "model_profile": "fast",
            },
            "sol_studio_admin": {
                "name": "Admin",
                "enabled": True,
                "requires_admin": True,
                "requires_studio_owner": True,
                "role": "specialist",
                "description": "admin only",
                "model_profile": "engineer",
            },
        }
    }


def test_admin_agent_hidden_by_default(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("SOL_STUDIO_OWNER", raising=False)
    monkeypatch.delenv("SOL_STUDIO_ADMIN_FEATURE", raising=False)
    reg = AgentRegistry(
        _admin_agent_raw(),
        data_root=tmp_path / "data",
        workspace_root=tmp_path / "ws",
        application_config={"features": {"studio_admin": False}},
    )
    assert "sol_pa" in reg.names()
    assert "sol_studio_admin" not in reg.names()


def test_feature_alone_not_enough(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("SOL_STUDIO_ADMIN_FEATURE", "1")
    monkeypatch.delenv("SOL_STUDIO_OWNER", raising=False)
    assert (
        admin_unlocked(data_root=tmp_path / "data", workspace_root=tmp_path / "ws")
        is False
    )


def test_admin_agent_visible_with_feature_and_unlock(tmp_path: Path, monkeypatch):
    data = tmp_path / "data"
    state = data / "state"
    state.mkdir(parents=True)
    (state / "studio_owner.unlock").write_text(
        "I OWN THIS LAB\nowner_id: pacer\n", encoding="utf-8"
    )
    monkeypatch.setenv("SOL_STUDIO_ADMIN_FEATURE", "1")
    monkeypatch.setenv("SOL_STUDIO_OWNER", "1")
    monkeypatch.setenv("SOL_STUDIO_OWNER_ID", "pacer")
    assert admin_unlocked(data_root=data, workspace_root=tmp_path / "ws") is True

    raw = yaml.safe_load(
        """
agents:
  sol_studio_admin:
    name: Admin
    enabled: true
    requires_admin: true
    role: specialist
    description: admin only
    model_profile: engineer
"""
    )
    reg = AgentRegistry(raw, data_root=data, workspace_root=tmp_path / "ws")
    assert "sol_studio_admin" in reg.names()


def test_owner_id_mismatch_blocks(tmp_path: Path, monkeypatch):
    data = tmp_path / "data" / "state"
    data.mkdir(parents=True)
    (data / "studio_owner.unlock").write_text(
        "I OWN THIS LAB\nowner_id: pacer\n", encoding="utf-8"
    )
    monkeypatch.setenv("SOL_STUDIO_ADMIN_FEATURE", "1")
    monkeypatch.setenv("SOL_STUDIO_OWNER", "1")
    monkeypatch.setenv("SOL_STUDIO_OWNER_ID", "someone-else")
    assert studio_owner_unlocked(data_root=tmp_path / "data", workspace_root=tmp_path / "ws") is False
