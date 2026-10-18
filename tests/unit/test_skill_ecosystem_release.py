"""Regression checks for the shared upstream release in SOL-Lite."""
import json

import pytest

from sol_lite.skills.manager import SkillManager


def test_large_release_is_available_without_dumping_every_description(tmp_path):
    root = tmp_path / "app"
    directory = root / "skills" / "ecosystem"
    entries = []
    for index in range(1100):
        name = f"fixture-{index}"
        skill = directory / name
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(f"---\nname: {name}\ndescription: Fixture workflow\n---\n\nDetailed fixture instructions {index}", encoding="utf-8")
        entries.append({"name": name, "repository": "fixture/skills", "commit": "a" * 40})
    (root / "config").mkdir()
    (root / "config" / "sol-ecosystem-catalog.json").write_text(json.dumps({"schema_version": 1, "skills": entries}), encoding="utf-8")
    manager = SkillManager(root, tmp_path / "state")
    assert len(manager.for_agent("sol_engineer")) == 1100
    prompt = manager.prompt_context("sol_engineer", task="Use $fixture-1099")
    assert "of 1100 skills" in prompt
    assert sum(line.startswith("- fixture-") for line in prompt.splitlines()) <= 48
    assert "DETAILED SKILL: fixture-1099" in prompt
    assert "Detailed fixture instructions 1099" in prompt
    assert "path=" in prompt
    assert "DETAILED SKILL: fixture-0\n" not in prompt


def test_release_manifest_cannot_escape_its_skill_directory(tmp_path):
    root = tmp_path / "app"
    (root / "config").mkdir(parents=True)
    (root / "config" / "sol-ecosystem-catalog.json").write_text(json.dumps({"schema_version": 1, "skills": [{"name": "../../escape"}]}), encoding="utf-8")
    manager = SkillManager(root, tmp_path / "state")
    with pytest.raises(ValueError, match="escapes its root"):
        manager.for_agent("sol_engineer")
