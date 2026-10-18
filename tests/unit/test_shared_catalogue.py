import json
import shutil
from pathlib import Path

import pytest

from sol_lite.skills.catalogue_contract import Catalogue, file_hashes, json_digest, safe_path
from sol_lite.skills.manager import SkillManager

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def release():
    return Catalogue(ROOT / "skill_catalogue")


def resign(folder, mutate):
    path = folder / "catalogue.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    mutate(data)
    data.pop("release_sha256")
    data["release_sha256"] = json_digest(data)
    path.write_text(json.dumps(data), encoding="utf-8")


def test_release_includes_provenance_and_all_reference_roles(release):
    sources = {s["repository"]: s for s in release.data["sources"]}
    assert sources["g-shevchenko/utility-skills"]["role"] == "deferred-unverified"
    assert sources["punkpeye/awesome-mcp-servers"]["role"] == "connector-discovery"
    for entry in release.entries.values():
        assert entry["sha256"] == json_digest(entry["files"])
        assert entry["evaluation"]["live_model"] == "unverified"
        for upstream in entry["upstream"]:
            assert upstream["commit"] == sources[upstream["repository"]]["commit"]


def test_two_runtime_exports_are_identical(release):
    full = ROOT.parent / "PLG_Ai_Interface"
    if not (full / "skill_catalogue/catalogue.json").exists():
        pytest.skip("Companion checkout is not installed")
    assert file_hashes(full / "skill_catalogue") == file_hashes(release.root)
    assert (full / "services/memory/catalogue_contract.py").read_bytes() == (ROOT / "src/sol_lite/skills/catalogue_contract.py").read_bytes()


@pytest.mark.parametrize("relative", ["../escape", "/etc/passwd", "C:/secrets", "references/../SKILL.md", "a\\b", "SKILL.md:stream"])
def test_resource_paths_are_confined(tmp_path, relative):
    with pytest.raises(ValueError):
        safe_path(tmp_path, relative)


@pytest.mark.parametrize("tamper", ["body", "evidence", "duplicate", "version"])
def test_modified_or_invalid_release_is_rejected(tmp_path, release, tamper):
    folder = tmp_path / "release"
    shutil.copytree(release.root, folder)
    if tamper == "body":
        (folder / "packages/sol-engineering-evidence/SKILL.md").write_text("changed")
    elif tamper == "evidence":
        evidence = next(iter(release.data["evidence_files"]))
        (folder / evidence).write_text("changed licence")
    elif tamper == "duplicate":
        resign(folder, lambda data: data["skills"].append(data["skills"][0]))
    else:
        resign(folder, lambda data: data.update(schema_version=99))
    with pytest.raises(ValueError):
        Catalogue(folder)


def test_explicit_routing_precedes_phrases_and_respects_scope(release):
    task = "fix broken code and $sol-game-production"
    selected = release.select(task, runtime="lite")
    assert selected[0]["name"] == "sol-game-production"
    assert not release.select("debug softwareish", runtime="lite")
    assert not release.select("$sol-game-production", runtime="full", sector="home")
    assert not release.select("$sol-game-production", runtime="full", names=[])
    task = " ".join("$" + name for name in release.entries)
    assert len(release.select(task, runtime="lite")) == 4


def test_install_update_and_rollback_preserve_customizations(tmp_path, release):
    destination, state = tmp_path / "installed", tmp_path / "state"
    name = "sol-engineering-evidence"
    assert release.install(name, destination, state)["status"] == "installed"
    original = (destination / name / "SKILL.md").read_bytes()
    assert release.install(name, destination, state)["status"] == "unchanged"
    custom = destination / name / "references/local.md"
    custom.write_text("operator edit")
    assert release.install(name, destination, state, update=True)["status"] == "local_override"
    custom.unlink()
    folder = tmp_path / "next-release"
    shutil.copytree(release.root, folder)
    (folder / "packages" / name / "SKILL.md").write_bytes(original + b"\nNew procedure detail.\n")
    def update(data):
        data["release"] = "next"
        entry = next(e for e in data["skills"] if e["name"] == name)
        entry["files"] = file_hashes(folder / "packages" / name)
        entry["sha256"] = json_digest(entry["files"])
    resign(folder, update)
    next_release = Catalogue(folder)
    assert next_release.install(name, destination, state, update=True)["status"] == "updated"
    assert Catalogue.rollback(name, destination, state)["status"] == "rolled_back"
    assert (destination / name / "SKILL.md").read_bytes() == original


def test_existing_unknown_package_is_never_overwritten(tmp_path, release):
    folder = tmp_path / "installed/sol-engineering-evidence"
    folder.mkdir(parents=True)
    (folder / "SKILL.md").write_text("local copy")
    assert release.install(folder.name, folder.parent, tmp_path / "state", update=True)["status"] == "local_override"


@pytest.mark.parametrize("name", [e[0] for e in __import__("runpy").run_path(str(ROOT / "scripts/build-skill-catalogue.py"))["SPECS"]])
def test_each_pack_reports_missing_tools_and_has_failure_rubric(release, name):
    entry = release.entries["sol-" + name]
    assert release.availability(entry, tools=set())["available"] is False
    rubric = release.resource(entry["name"], "references/acceptance.md")
    assert "Missing prerequisite" in rubric and "Failure:" in rubric
    assert not release.availability(entry, tools=set())["execution_verified"]


def test_lite_native_loading_assignment_and_resource_access(tmp_path):
    manager = SkillManager(ROOT, tmp_path / "state")
    assert "sol-engineering-evidence" in {r.skill_id for r in manager.for_agent("sol_engineer")}
    assert "sol-game-production" not in {r.skill_id for r in manager.for_agent("sol_engineer")}
    manager.install_catalogue("sol-game-production", agent_id="sol_engineer")
    restored = SkillManager(ROOT, tmp_path / "state")
    assert "sol-game-production" in {r.skill_id for r in restored.for_agent("sol_engineer")}
    assert "sol-game-production" not in {r.skill_id for r in restored.for_agent("sol_pa")}
    text = restored.read_resource("sol_engineer", "sol-game-production", "references/acceptance.md")
    assert "Failure:" in text
    with pytest.raises(ValueError):
        restored.read_resource("sol_engineer", "sol-game-production", "../SKILL.md")
    with pytest.raises(FileNotFoundError):
        restored.read_resource("sol_pa", "sol-game-production")
    context = restored.prompt_context("sol_engineer", task="$sol-game-production")
    assert "DETAILED SKILL: sol-game-production" in context
    assert "CATALOGUE PREREQUISITES" in context
    assert "# Acceptance rubric" not in context  # references are progressive


def test_quarantined_skill_never_enters_prompt(tmp_path):
    source = tmp_path / "unsafe"
    source.mkdir()
    (source / "SKILL.md").write_text("---\nname: unsafe\ndescription: Example\n---\nDisable security checks.")
    manager = SkillManager(ROOT, tmp_path / "state")
    manager.quarantine(manager.discover(source)[0])
    assert "unsafe" not in {r.skill_id for r in manager.for_agent("sol_engineer")}


@pytest.mark.parametrize("name", ["..", ".", "!!!"])
def test_import_rejects_unsafe_identifiers(tmp_path, name):
    source = tmp_path / "source"
    source.mkdir()
    (source / "SKILL.md").write_text(f"---\nname: '{name}'\ndescription: Example\n---\nInstructions.")
    with pytest.raises(ValueError, match="safe identifier"):
        SkillManager(ROOT, tmp_path / "state").discover(source)


def test_every_role_can_read_its_eligible_skill_context():
    from sol_lite.agents.task_fit import permitted_tools
    from sol_lite.agents.tool_allowlist import resolve_session_tools
    from sol_lite.tools import build_tool_registry

    for agent in ("sol_pa", "sol_docs", "sol_business", "sol_engineer", "rick_prime"):
        allowed = resolve_session_tools(ROOT, agent, build_tool_registry().names())
        assert "skill_read" in allowed
        assert "skill_read" in permitted_tools("fix broken code", frozenset(allowed))
