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
    assert {"architecture-diagrams", "slide-deck-generator", "image-markup-ui"} <= {
        r.skill_id for r in records if r.source_type == "builtin"
    }
    assert any(r.skill_id == "readable-plans" for r in records)
    assert any(r.skill_id == "systematic-debugging" for r in records)


def test_visual_intents_inject_complete_skills_for_each_agent(tmp_path):
    manager = SkillManager(Path(__file__).resolve().parents[2], tmp_path)
    task = "Create an Excalidraw architecture diagram, slide deck and annotate screenshot"
    for agent in ("sol_pa", "sol_docs", "sol_business", "sol_engineer"):
        context = manager.prompt_context(agent, task=task)
        for name in ("architecture-diagrams", "slide-deck-generator", "image-markup-ui"):
            assert f"DETAILED SKILL: {name}\n---" in context


def test_manifest_intent_boundaries_and_explicit_invocation(tmp_path):
    manager = SkillManager(Path(__file__).resolve().parents[2], tmp_path)
    context = manager.prompt_context("sol_pa", task="Inspect slideshow_cache and diagrammatic variables")
    assert "DETAILED SKILL: slide-deck-generator" not in context
    assert "DETAILED SKILL: architecture-diagrams" not in context
    context = manager.prompt_context("sol_pa", task="Use $image-markup-ui for this")
    assert "DETAILED SKILL: image-markup-ui" in context


def test_workspace_manifest_routes_without_code_registration(tmp_path):
    folder = tmp_path / "workspace" / ".agents" / "skills" / "custom-visual"
    folder.mkdir(parents=True)
    (folder / "SKILL.md").write_text(
        '---\nname: custom-visual\ndescription: Local visualization.\nmetadata:\n'
        '  trigger-phrases: "render topology"\n---\nSpecific topology procedure.', encoding="utf-8"
    )
    manager = SkillManager(tmp_path / "app", tmp_path / "state")
    context = manager.prompt_context("sol_engineer", tmp_path / "workspace", "RENDER  topology")
    assert "Specific topology procedure." in context


def test_manifest_rejects_non_string_triggers(tmp_path):
    import pytest

    source = tmp_path / "bad-metadata"
    source.mkdir()
    (source / "SKILL.md").write_text(
        '---\nname: bad-metadata\ndescription: Invalid trigger type.\nmetadata:\n'
        '  trigger-phrases: [slides, diagrams]\n---\nInstructions.', encoding="utf-8"
    )
    manager = SkillManager(tmp_path / "app", tmp_path / "state")
    with pytest.raises(TypeError, match="pipe-separated string"):
        manager.inspect_directory(source)
