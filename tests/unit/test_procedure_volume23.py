from pathlib import Path

import pytest

from sol_lite.procedures import parse_procedure
from sol_lite.procedures.follow import dry_follow, format_report
from sol_lite.procedures.runner import ProcedureSession

VOLUME = Path(r"E:\git\plg-studio\plg-infrastructure\23-PHASE-1-INIT-MORNING.md")


@pytest.mark.skipif(not VOLUME.is_file(), reason="studio infrastructure manual is not present")
def test_volume_23_is_classified_without_running_install_commands():
    document = parse_procedure(
        VOLUME.read_text(encoding="utf-8"),
        source=VOLUME.name,
    )
    rows = {step.step_id: step for step in document.steps}

    assert {f"A{number}" for number in range(1, 9)} <= set(rows)
    assert rows["A1"].classification == "needs_approval"
    assert rows["A4"].classification == "human_gate"
    for step_id in ("B1", "B2", "B3", "B4"):
        assert rows[step_id].classification == "human_gate"
    assert rows["D1"].classification == "unverifiable"
    assert document.complete is False

    session = ProcedureSession(document)
    report = format_report(session.status())
    assert "scripts/install" in report
    assert "No approval-gated command was executed." in report
    assert session.status()["steps"][0]["evidence"] == {}


def test_dry_follow_prints_classification_and_executes_nothing(tmp_path):
    from tests.unit.test_procedure_tools import _context

    root = tmp_path / "workspace"
    root.mkdir()
    (root / "checklist.md").write_text(
        """| Step | Action | Validate |
|------|--------|----------|
| A1 | `sudo bash scripts/install/plg-install-docker-official.sh` | `echo ok` |
""",
        encoding="utf-8",
    )
    ctx = _context(root, tmp_path / "audit.jsonl", tmp_path / "faults.json")
    report = dry_follow(ctx, "checklist.md")

    assert "A1  needs_approval" in report
    assert "No approval-gated command was executed." in report
    assert ctx.procedure_session.status()["steps"][0]["evidence"] == {}
    assert ctx.procedure_session.status()["complete"] is False
