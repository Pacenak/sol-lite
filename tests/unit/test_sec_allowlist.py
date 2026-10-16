"""Allowlist + lab ack gates for portable SecCheck / lite-pen."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


def _load(name: str, rel: str):
    root = Path(__file__).resolve().parents[2]
    path = root / "portable-stick" / "brain" / "sec" / rel
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_empty_allowlist_refuses(tmp_path: Path):
    al = _load("stick_allowlist", "allowlist.py")
    p = tmp_path / "hosts.allow"
    p.write_text("# only comments\n", encoding="utf-8")
    with pytest.raises(ValueError, match="empty"):
        al.load_allowlist(p)


def test_target_must_be_listed(tmp_path: Path):
    al = _load("stick_allowlist", "allowlist.py")
    p = tmp_path / "hosts.allow"
    p.write_text("192.168.1.10\n", encoding="utf-8")
    allowed = al.load_allowlist(p)
    assert al.assert_target_allowed("192.168.1.10", allowed) == "192.168.1.10"
    with pytest.raises(PermissionError):
        al.assert_target_allowed("evil.example", allowed)


def test_lite_pen_requires_ack(tmp_path: Path):
    al = _load("stick_allowlist", "allowlist.py")
    missing = tmp_path / "I_OWN_THIS_LAB"
    with pytest.raises(PermissionError):
        al.require_lab_ack(missing)
    missing.write_text("nope\n", encoding="utf-8")
    with pytest.raises(PermissionError):
        al.require_lab_ack(missing)
    missing.write_text("I OWN THIS LAB\n", encoding="utf-8")
    al.require_lab_ack(missing)
