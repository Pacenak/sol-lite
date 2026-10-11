import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from sol_lite.agents.tool_allowlist import resolve_session_tools
from sol_lite.core.exceptions import SecurityError
from sol_lite.skills.manager import SkillManager
from sol_lite.tools import artifacts as a
from sol_lite.tools import build_tool_registry

ROOT = Path(__file__).resolve().parents[2]


class Permissions:
    def __init__(self, deny=False):
        self.calls = []
        self.deny = deny

    def check(self, scope, **kwargs):
        self.calls.append((scope, kwargs))
        if self.deny:
            raise PermissionError("denied")


@pytest.fixture
def ctx(tmp_path, monkeypatch):
    monkeypatch.setattr(a.tempfile, "tempdir", str(tmp_path))
    monkeypatch.setattr(
        a,
        "discover_dependencies",
        lambda: {"libreoffice": None, "mermaid_command": None, "python": {"fitz": False}},
    )
    return SimpleNamespace(
        workspace_root=tmp_path,
        permission_engine=Permissions(),
        audit=SimpleNamespace(record=lambda *args, **kwargs: None),
    )


def create(ctx, name, spec, **kwargs):
    return build_tool_registry().execute(
        "artifact_create", {"path": name, "spec": spec, **kwargs}, ctx
    )


@pytest.mark.parametrize(
    "extension,spec",
    [
        (
            "docx",
            {
                "title": "Operations report",
                "sections": [
                    {
                        "heading": "Decision",
                        "paragraphs": ["Approve the next milestone."],
                        "table": [["Owner", "Status"], ["Team", "Ready"]],
                    }
                ],
            },
        ),
        (
            "pptx",
            {
                "title": "Milestone review",
                "slides": [
                    {
                        "title": "Delivery is ready",
                        "bullets": ["Validation passed", "Review the rollout"],
                        "notes": "Confirm timing.",
                    }
                ],
            },
        ),
        (
            "xlsx",
            {
                "title": "Budget",
                "sheets": [
                    {
                        "name": "Budget",
                        "rows": [
                            ["Month", "Cost"],
                            ["Jan", 10],
                            ["Feb", 20],
                            ["Total", "=SUM(B2:B3)"],
                        ],
                        "charts": [{"title": "Costs", "first_row": 1, "last_row": 3}],
                    }
                ],
            },
        ),
        ("mmd", {"title": "Architecture", "mermaid": "flowchart LR\n  A[Client] --> B[Service]"}),
    ],
)
def test_native_authoring_and_evidence(ctx, extension, spec):
    module = {"docx": "docx", "pptx": "pptx", "xlsx": "openpyxl"}.get(extension)
    if module:
        pytest.importorskip(module)
    result = create(ctx, f"report.{extension}", spec)
    assert result["ok"] and result["status"] == "authored_unverified"
    assert result["validation"]["visual_review"] == "not_performed"
    assert Path(result["outputs"][0]).is_file()
    assert result["validation"]["warnings"]
    assert ctx.permission_engine.calls[0][1]["operation"] == "artifact_create"
    assert (
        build_tool_registry().execute("artifact_validate", {"path": f"report.{extension}"}, ctx)[
            "structural"
        ]
        == "passed"
    )


def test_editable_content_and_layout(ctx):
    docx = pytest.importorskip("docx")
    pptx = pytest.importorskip("pptx")
    openpyxl = pytest.importorskip("openpyxl")
    create(
        ctx,
        "report.docx",
        {"title": "Report", "sections": [{"heading": "Summary", "paragraphs": ["Editable text"]}]},
    )
    document = docx.Document(ctx.workspace_root / "report.docx")
    assert any(p.text == "Editable text" for p in document.paragraphs)
    assert round(document.sections[0].page_width / 36000) == 210
    create(
        ctx,
        "slides.pptx",
        {"title": "Review", "slides": [{"title": "Ready", "notes": "Speaker notes"}]},
    )
    deck = pptx.Presentation(ctx.workspace_root / "slides.pptx")
    assert deck.slides[0].shapes[0].text == "Ready"
    assert "Speaker notes" in deck.slides[0].notes_slide.notes_text_frame.text
    create(
        ctx,
        "budget.xlsx",
        {
            "title": "Budget",
            "sheets": [{"name": "Costs", "rows": [["Cost"], [10], ["=SUM(A2:A2)"]]}],
        },
    )
    book = openpyxl.load_workbook(ctx.workspace_root / "budget.xlsx")
    assert book["Costs"]["A3"].value == "=SUM(A2:A2)"
    assert book["Costs"].freeze_panes == "A2"
    book.close()


def test_workbook_charts_are_printed_and_themed(ctx):
    openpyxl = pytest.importorskip("openpyxl")
    create(
        ctx,
        "chart.xlsx",
        {
            "title": "Costs",
            "theme": {"accent": "116644"},
            "sheets": [
                {
                    "name": "Costs",
                    "rows": [["Month", "Cost"], ["Jan", 10], ["Feb", 20]],
                    "charts": [{"title": "Cost", "first_row": 1, "last_row": 3}],
                }
            ],
        },
    )
    book = openpyxl.load_workbook(ctx.workspace_root / "chart.xlsx")
    sheet = book["Costs"]
    assert "$E$22" in str(sheet.print_area)
    assert sheet["A1"].fill.fgColor.rgb.endswith("116644")
    assert len(sheet._charts) == 1
    book.close()


def test_content_type_mismatch_is_rejected(ctx):
    with pytest.raises(ValueError, match="does not belong"):
        a.artifact_create(
            ctx,
            {"path": "bad.docx", "spec": {"title": "Wrong format", "slides": [{"title": "Slide"}]}},
        )
    assert not (ctx.workspace_root / "bad.docx").exists()


def test_corrupt_package_returns_tool_error(ctx):
    from sol_lite.core.exceptions import ToolExecutionError

    (ctx.workspace_root / "corrupt.docx").write_bytes(b"not an Office package")
    with pytest.raises(ToolExecutionError, match="Invalid artifact package"):
        build_tool_registry().execute("artifact_validate", {"path": "corrupt.docx"}, ctx)


def test_denial_escape_and_overwrite(ctx):
    with pytest.raises(SecurityError):
        a.artifact_create(ctx, {"path": "../outside.mmd", "spec": {"title": "Bad"}})
    ctx.permission_engine.deny = True
    with pytest.raises(PermissionError):
        a.artifact_create(ctx, {"path": "denied.mmd", "spec": {"title": "Bad"}})
    assert not (ctx.workspace_root / "denied.mmd").exists()
    ctx.permission_engine.deny = False
    spec = {"title": "Flow", "mermaid": "flowchart LR\n A --> B"}
    create(ctx, "flow.mmd", spec)
    with pytest.raises(FileExistsError):
        a.artifact_create(ctx, {"path": "flow.mmd", "spec": spec})


@pytest.mark.parametrize(
    "source",
    [
        "flowchart LR\nclick A callback",
        "%%{init: {}}%%\nflowchart LR",
        "flowchart LR\nA[<img src='file:///secret'>]",
    ],
)
def test_malicious_diagrams_are_rejected(ctx, source):
    with pytest.raises(ValueError):
        a.artifact_create(ctx, {"path": "bad.mmd", "spec": {"title": "Bad", "mermaid": source}})
    assert not (ctx.workspace_root / "bad.mmd").exists()


def test_renderer_failure_preserves_source(ctx, monkeypatch):
    monkeypatch.setattr(
        a, "_render", lambda *args: (_ for _ in ()).throw(RuntimeError("renderer failed"))
    )
    result = create(ctx, "flow.mmd", {"title": "Flow", "mermaid": "flowchart LR\n A --> B"})
    assert result["status"] == "authored_unverified"
    assert "renderer failed" in result["validation"]["warnings"]
    assert len(result["outputs"]) == 1


def test_bounded_subprocess_and_failure(monkeypatch):
    calls = []

    def run(command, **kwargs):
        calls.append(kwargs)
        raise subprocess.TimeoutExpired(command, 60)

    monkeypatch.setattr(a.subprocess, "run", run)
    with pytest.raises(RuntimeError, match="60 seconds"):
        a._run(["renderer", "path with spaces"])
    assert calls[0]["shell"] is False
    assert calls[0]["timeout"] == 60
    monkeypatch.setattr(
        a.subprocess, "run", lambda *args, **kwargs: SimpleNamespace(returncode=1, stderr="failed")
    )
    with pytest.raises(RuntimeError, match="failed"):
        a._run(["renderer"])


def test_mac_and_windows_discovery(monkeypatch):
    monkeypatch.setattr(a.shutil, "which", lambda name: None)
    monkeypatch.setattr(
        Path,
        "is_file",
        lambda path: (
            str(path).replace("\\", "/").endswith("LibreOffice.app/Contents/MacOS/soffice")
        ),
    )
    assert (
        a.discover_dependencies()["libreoffice"]
        .replace("\\", "/")
        .endswith("/Applications/LibreOffice.app/Contents/MacOS/soffice")
    )
    monkeypatch.setenv("PROGRAMFILES", "C:/Program Files")
    monkeypatch.setattr(
        Path,
        "is_file",
        lambda path: (
            str(path).replace("\\", "/") == "C:/Program Files/LibreOffice/program/soffice.exe"
        ),
    )
    assert "Program Files" in a.discover_dependencies()["libreoffice"]


def test_skill_selection_and_allowlists(tmp_path):
    manager = SkillManager(ROOT, tmp_path)
    context = manager.prompt_context(
        "sol_docs", task="Create document slides workbook and diagrams"
    )
    for name in (
        "documentation-engineering",
        "document-layout",
        "presentation-design",
        "spreadsheet-reporting",
        "diagram-design",
        "mermaid-diagrams",
    ):
        assert f"DETAILED SKILL: {name}" in context
    registry = build_tool_registry()
    for agent in ("sol_pa", "sol_business", "sol_docs", "sol_engineer"):
        assert "artifact_create" in resolve_session_tools(ROOT, agent, registry.names())
    assert registry.get("artifact_create").mutability
    assert not registry.get("artifact_dependencies").mutability


def test_exact_approval_retry(ctx):
    from sol_lite.core.exceptions import ApprovalRequired
    from sol_lite.permissions.approvals import ApprovalManager
    from sol_lite.permissions.engine import PermissionEngine
    from sol_lite.permissions.policy import PermissionPolicy

    ctx.permission_engine = PermissionEngine(
        PermissionPolicy({"filesystem": {"write": {"enabled": True, "approval_required": True}}}),
        ApprovalManager(),
    )
    args = {
        "path": "approved.mmd",
        "spec": {"title": "Flow", "mermaid": "flowchart LR\n A --> B"},
        "plan": "Create diagram",
    }
    with pytest.raises(ApprovalRequired) as exc:
        a.artifact_create(ctx, args)
    args["approval_id"] = exc.value.request.approval_id
    assert a.artifact_create(ctx, args)["ok"]


def test_renderer_outputs_and_no_overwrite(ctx, monkeypatch):
    create(ctx, "flow.mmd", {"title": "Flow", "mermaid": "sequenceDiagram\n A->>B: Request"})
    monkeypatch.setattr(a, "discover_dependencies", lambda: {"mermaid_command": ["node", "cli.js"]})
    calls = []

    def render(command):
        calls.append(command)
        Path(command[command.index("-o") + 1]).write_bytes(b"rendered")

    monkeypatch.setattr(a, "_run", render)
    args = {"path": "flow.mmd", "output_directory": "exports with spaces"}
    result = a.artifact_render(ctx, args)
    assert result["ok"] and len(result["outputs"]) == 2
    assert result["previews"][0].endswith(".png")
    assert result["visual_review"] == "not_performed"
    assert all("-c" in command for command in calls)
    with pytest.raises(FileExistsError):
        a.artifact_render(ctx, args)


def test_pdf_and_previews(ctx, monkeypatch):
    pytest.importorskip("docx")
    fitz = pytest.importorskip("fitz")
    create(ctx, "report.docx", {"title": "Report"}, render=False)
    monkeypatch.setattr(
        a, "discover_dependencies", lambda: {"libreoffice": "soffice", "python": {"fitz": True}}
    )

    def render(command):
        assert "--headless" in command
        assert any(arg.startswith("-env:UserInstallation=file:") for arg in command)
        directory = Path(command[command.index("--outdir") + 1])
        with fitz.open() as pdf:
            pdf.new_page().insert_text((50, 50), "Review")
            pdf.save(directory / "report.pdf")

    monkeypatch.setattr(a, "_run", render)
    result = a.artifact_render(ctx, {"path": "report.docx", "output_directory": "preview"})
    assert result["ok"]
    assert len(result["previews"]) == 1
    assert all(Path(path).is_file() for path in result["outputs"])


def test_external_office_relationship_rejected(ctx):
    import zipfile

    path = ctx.workspace_root / "unsafe.docx"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types />")
        archive.writestr(
            "word/_rels/document.xml.rels",
            '<Relationships><Relationship TargetMode="External" Target="file:///secret"/></Relationships>',
        )
    with pytest.raises(ValueError, match="External"):
        a.artifact_render(ctx, {"path": "unsafe.docx", "output_directory": "exports"})
    assert not (ctx.workspace_root / "exports").exists()


def test_active_formula_rejected(ctx):
    pytest.importorskip("openpyxl")
    with pytest.raises(ValueError, match="formulas"):
        a.artifact_create(
            ctx,
            {
                "path": "bad.xlsx",
                "spec": {
                    "title": "Bad",
                    "sheets": [{"name": "Data", "rows": [['=WEBSERVICE("https://example.com")']]}],
                },
            },
        )
    assert not (ctx.workspace_root / "bad.xlsx").exists()


def test_windows_mermaid_shim_uses_node(monkeypatch):
    monkeypatch.setattr(
        a.shutil,
        "which",
        lambda name: {"mmdc": "C:/Tools/mmdc.cmd", "node": "C:/Tools/node.exe"}.get(name),
    )
    monkeypatch.setattr(
        Path,
        "is_file",
        lambda path: str(path).replace("\\", "/").endswith("mermaid-cli/src/cli.js"),
    )
    command = a.discover_dependencies()["mermaid_command"]
    assert command[0] == "C:/Tools/node.exe"
    assert command[1].endswith("cli.js")


def test_tool_schema_references_resolve():
    schema = build_tool_registry().get("artifact_create").parameters
    assert "$defs" in schema and "$defs" not in schema["properties"]["spec"]
    assert schema["properties"]["spec"]["properties"]["theme"]["$ref"] == "#/$defs/Theme"


def test_native_agent_loop(ctx):
    import json

    from sol_lite.agents.runtime import AgentRuntime
    from sol_lite.faults.log import FaultLog

    registry = build_tool_registry()

    class Models:
        calls = 0

        def profile(self, name):
            return SimpleNamespace(model="fake", temperature=0, timeout_seconds=10)

        def chat(self, profile, messages, tools):
            self.calls += 1
            if self.calls == 1:
                call = SimpleNamespace(
                    function=SimpleNamespace(
                        name="artifact_create",
                        arguments={
                            "path": "native.mmd",
                            "spec": {"title": "Flow", "mermaid": "flowchart LR\n A --> B"},
                        },
                    )
                )
                return SimpleNamespace(message=SimpleNamespace(content="", tool_calls=[call]))
            evidence = json.loads(
                next(
                    message["content"]
                    for message in reversed(messages)
                    if message["role"] == "tool"
                )
            )
            assert evidence["status"] == "authored_unverified"
            return SimpleNamespace(
                message=SimpleNamespace(
                    content="Created Mermaid source. Exports remain unverified.", tool_calls=[]
                )
            )

    runner = AgentRuntime(
        Models(),
        registry,
        ctx,
        FaultLog(ctx.workspace_root / "faults.json"),
        tool_names=resolve_session_tools(ROOT, "sol_docs", registry.names()),
    )
    result = runner.run(
        profile="reviewer", messages=[{"role": "user", "content": "Create a flowchart artifact"}]
    )
    assert result.tool_calls == 1 and result.stopped_reason is None
    assert "unverified" in result.content
    assert (ctx.workspace_root / "native.mmd").is_file()
