"""Real local renderer acceptance; set SOL_REQUIRE_ARTIFACT_RENDERERS=1 in CI."""

import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from sol_lite.permissions.approvals import ApprovalManager
from sol_lite.permissions.engine import PermissionEngine
from sol_lite.permissions.policy import PermissionPolicy
from sol_lite.tools import build_tool_registry
from sol_lite.tools.artifacts import discover_dependencies


@pytest.mark.integration
def test_real_office_and_diagram_exports(tmp_path):
    if sys.platform == "darwin" and os.environ.get("SOL_REQUIRE_ARTIFACT_RENDERERS") == "1":
        assert not any(
            (Path("/Applications") / name).exists()
            for name in ("Microsoft Word.app", "Microsoft Excel.app", "Microsoft PowerPoint.app")
        ), "Run acceptance on macOS without Microsoft Office installed."
    dependencies = discover_dependencies()
    ready = (
        all(dependencies["python"].values())
        and dependencies["libreoffice"]
        and dependencies["mermaid_command"]
    )
    if not ready:
        if os.environ.get("SOL_REQUIRE_ARTIFACT_RENDERERS") == "1":
            pytest.fail(f"Artifact acceptance dependencies missing: {dependencies}")
        pytest.skip("Optional artifact authoring/rendering dependencies are not installed.")
    workspace = Path(os.environ.get("SOL_ARTIFACT_ACCEPTANCE_OUTPUT", str(tmp_path))).resolve()
    workspace.mkdir(parents=True, exist_ok=True)
    permission_engine = PermissionEngine(
        PermissionPolicy(
            {
                "filesystem": {
                    "read": {"enabled": True, "approval_required": False},
                    "write": {"enabled": True, "approval_required": False},
                }
            }
        ),
        ApprovalManager(),
    )
    ctx = SimpleNamespace(
        workspace_root=workspace,
        permission_engine=permission_engine,
        audit=SimpleNamespace(record=lambda *args, **kwargs: None),
    )
    examples = {
        "report.docx": {
            "title": "Milestone review",
            "sections": [
                {"heading": "Decision", "paragraphs": ["Approve the next delivery milestone."]},
                {"heading": "Evidence", "table": [["Check", "Result"], ["Validation", "Passed"]]},
            ],
        },
        "review.pptx": {
            "title": "Delivery review",
            "slides": [
                {
                    "title": "Delivery is ready",
                    "bullets": ["Validation completed", "Confirm rollout timing"],
                    "notes": "Review dependencies.",
                }
            ],
        },
        "budget.xlsx": {
            "title": "Budget review",
            "sheets": [
                {
                    "name": "Budget",
                    "rows": [
                        ["Month", "Cost"],
                        ["January", 10],
                        ["February", 20],
                        ["Total", "=SUM(B2:B3)"],
                    ],
                    "charts": [{"title": "Monthly cost", "first_row": 1, "last_row": 3}],
                }
            ],
        },
        "architecture.mmd": {
            "title": "Architecture",
            "mermaid": "flowchart LR\n A[Client] -->|Request| B[Service]\n B -->|Persist| C[Database]",
        },
        "sequence.mmd": {
            "title": "Request sequence",
            "mermaid": "sequenceDiagram\n participant Client\n participant Service\n Client->>Service: Request\n Service-->>Client: Response",
        },
    }
    registry = build_tool_registry()
    for filename, spec in examples.items():
        result = registry.execute("artifact_create", {"path": filename, "spec": spec}, ctx)
        assert result["status"] == "rendered_unreviewed", result
        assert all(Path(path).is_file() for path in result["outputs"])
        assert result["previews"]
        assert result["validation"]["visual_review"] == "not_performed"
        expected = ".svg" if filename.endswith(".mmd") else ".pdf"
        assert any(path.endswith(expected) for path in result["outputs"])
    # Verify the exported workbook's formula independently through PDF text.
    import fitz

    with fitz.open(workspace / "budget.pdf") as pdf:
        text = "\n".join(page.get_text() for page in pdf)
        assert "30" in text, text
