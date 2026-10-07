from pathlib import Path

from sol_lite.skills.manager import SkillManager


def test_skill_discovery_and_install(tmp_path):
    source = tmp_path / "source" / "debugging"
    source.mkdir(parents=True)
    (source / "SKILL.md").write_text(
        "---\nname: systematic-debugging\ndescription: Root cause debugging workflow.\n---\n\nReproduce before fixing.",
        encoding="utf-8",
    )
    manager = SkillManager(tmp_path / "app", tmp_path / "state")
    records = manager.discover(source)
    assert records[0].skill_id == "systematic-debugging"
    installed = manager.install(records[0], agent_ids=["sol_engineer"])
    assert installed.status == "INSTALLED"
    assert manager.for_agent("sol_engineer")[0].skill_id == "systematic-debugging"


def test_skill_import_rejects_zip_traversal(tmp_path):
    import zipfile
    archive = tmp_path / "bad.zip"
    with zipfile.ZipFile(archive, "w") as z:
        z.writestr("../../escape/SKILL.md", "---\nname: bad\ndescription: bad\n---")
    manager = SkillManager(tmp_path / "app", tmp_path / "state")
    import pytest
    with pytest.raises(ValueError):
        manager.discover(archive)


def test_builtin_skill_catalog_is_available_to_agent(tmp_path):
    manager = SkillManager(tmp_path / "app", tmp_path / "state")
    manager.root = Path(__file__).resolve().parents[2]
    records = manager.for_agent("sol_engineer", tmp_path)
    assert len([r for r in records if r.source_type == "builtin"]) == 33
    assert any(r.skill_id == "systematic-debugging" for r in records)
