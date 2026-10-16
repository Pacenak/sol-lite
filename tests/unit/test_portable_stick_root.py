"""Portable BRAIN / SOLLITE stick path resolution (no USB hardware required)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load_resolve():
    root = Path(__file__).resolve().parents[2]
    path = root / "portable-stick" / "brain" / "launch" / "resolve_stick_root.py"
    spec = importlib.util.spec_from_file_location("resolve_stick_root", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["resolve_stick_root"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_find_brain_root_from_launch(tmp_path: Path):
    mod = _load_resolve()
    brain = tmp_path / "brain"
    (brain / "launch").mkdir(parents=True)
    (brain / "data").mkdir()
    (brain / "workspace").mkdir()
    marker = brain / "launch" / "x.py"
    marker.write_text("#\n", encoding="utf-8")
    found = mod.find_brain_root(marker)
    assert found.resolve() == brain.resolve()


def test_env_for_brain_sets_roots(tmp_path: Path, monkeypatch):
    mod = _load_resolve()
    brain = tmp_path / "usb"
    (brain / "launch").mkdir(parents=True)
    monkeypatch.delenv("SOL_OLLAMA_URL", raising=False)
    monkeypatch.delenv("SOL_LITE_REPO", raising=False)
    monkeypatch.delenv("SOL_LITE_VOLUME", raising=False)
    env = mod.env_for_brain(brain)
    assert env["SOL_DATA_ROOT"] == str((brain / "data").resolve())
    assert env["SOL_WORKSPACE_ROOT"] == str((brain / "workspace").resolve())
    assert "11434" in env["SOL_OLLAMA_URL"]
    assert (brain / "data").is_dir()
    assert (brain / "workspace").is_dir()
    assert "SOL_LITE_REPO" not in env


def test_settings_file_when_present(tmp_path: Path, monkeypatch):
    mod = _load_resolve()
    brain = tmp_path / "usb"
    (brain / "launch").mkdir(parents=True)
    monkeypatch.delenv("SOL_LITE_REPO", raising=False)
    monkeypatch.delenv("SOL_LITE_VOLUME", raising=False)
    settings = brain / "settings" / "settings.yaml"
    settings.parent.mkdir(parents=True)
    settings.write_text("general: {}\n", encoding="utf-8")
    env = mod.env_for_brain(brain)
    assert env["SOL_LITE_SETTINGS_FILE"] == str(settings.resolve())


def test_find_lite_repo_legacy_on_brain(tmp_path: Path, monkeypatch):
    mod = _load_resolve()
    brain = tmp_path / "SOLBRAIN"
    (brain / "launch").mkdir(parents=True)
    legacy = brain / "sol-lite-src"
    legacy.mkdir()
    (legacy / "pyproject.toml").write_text("[project]\nname='sol-lite'\n", encoding="utf-8")
    monkeypatch.delenv("SOL_LITE_REPO", raising=False)
    monkeypatch.delenv("SOL_LITE_VOLUME", raising=False)
    found = mod.find_lite_repo(brain)
    assert found is not None
    assert found.resolve() == legacy.resolve()


def test_find_lite_repo_sibling_sollite(tmp_path: Path, monkeypatch):
    mod = _load_resolve()
    brain = tmp_path / "SOLBRAIN"
    lite_vol = tmp_path / "SOLLITE"
    (brain / "launch").mkdir(parents=True)
    lite_vol.mkdir()
    (lite_vol / "pyproject.toml").write_text("[project]\nname='sol-lite'\n", encoding="utf-8")
    monkeypatch.delenv("SOL_LITE_REPO", raising=False)
    monkeypatch.delenv("SOL_LITE_VOLUME", raising=False)
    found = mod.find_lite_repo(brain)
    assert found is not None
    assert found.resolve() == lite_vol.resolve()


def test_env_sets_sol_lite_repo_from_volume(tmp_path: Path, monkeypatch):
    mod = _load_resolve()
    brain = tmp_path / "SOLBRAIN"
    lite_vol = tmp_path / "SOLLITE"
    (brain / "launch").mkdir(parents=True)
    lite_vol.mkdir()
    (lite_vol / "pyproject.toml").write_text("[project]\nname='sol-lite'\n", encoding="utf-8")
    monkeypatch.delenv("SOL_LITE_REPO", raising=False)
    monkeypatch.setenv("SOL_LITE_VOLUME", str(lite_vol))
    env = mod.env_for_brain(brain)
    assert env["SOL_LITE_REPO"] == str(lite_vol.resolve())
