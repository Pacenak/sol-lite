"""Studio Odoo gather-pack import: schemas come from the templates, not guesses."""
import ast
import csv
import json
from pathlib import Path

import pytest

from sol_lite.agents.task_fit import apply_studio_workspace_gate, permitted_tools
from sol_lite.agents.tool_allowlist import resolve_session_tools
from sol_lite.core.exceptions import ApprovalRequired
from sol_lite.core.session import WorkspaceManager
from sol_lite.integrations.studio_odoo import (
    REQUIRED_KEY,
    StudioError,
    verify_studio_root,
    write_import,
)
from sol_lite.tools import build_tool_registry
from sol_lite.tools.studio_odoo import _bind, _status

ROOT = Path(__file__).resolve().parents[2]
STUDIO = Path(r"E:\git\plg-studio\plg-odooacc")

INVOICE = [
    "partner", "invoice_date", "ref", "product_default_code", "description", "qty",
    "price_unit_exclusive", "tax_code", "analytic", "account_code", "fiscal_position", "notes",
]
GST = [
    "period_start", "period_end", "box5", "box6", "box8", "box9", "box11", "box12",
    "box13", "box15", "myir_pdf_filename", "odoo_matched", "tax_locked", "notes",
]
COMPANY = [
    "legal_name", "nzbn", "ird", "gst_number", "gst_status", "gst_registered_from",
    "gst_basis", "gst_frequency", "sol_sector", "odoo_company_id", "notes",
]


class Permit:
    def check(self, scope, **kwargs):
        if not kwargs.get("approval_id"):
            raise ApprovalRequired("need approval", request=None)


def _csv(path: Path, header, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def build_studio(root: Path) -> Path:
    templates = root / "docs" / "templates"
    templates.mkdir(parents=True)
    (root / "scripts").mkdir()
    (root / "scripts" / "init-gather-pack.ps1").write_text("# test\n", encoding="utf-8")
    (templates / "README.md").write_text("# templates\n", encoding="utf-8")
    _csv(templates / "products.csv", ["code", "name", "sale_tax_code", "purchase_tax_code", "income_or_expense_account", "notes"], [
        {"code": "PLG-NZ-DIGITAL", "name": "NZ digital", "sale_tax_code": "GST15_S", "purchase_tax_code": "", "income_or_expense_account": "", "notes": ""},
        {"code": "PLG-GRANT", "name": "Grant", "sale_tax_code": "GST15_S", "purchase_tax_code": "", "income_or_expense_account": "46100", "notes": "s 5(6D)"},
        {"code": "PLG-CONTRACTOR-NZ", "name": "Contractor", "sale_tax_code": "", "purchase_tax_code": "GST15_P", "income_or_expense_account": "61010", "notes": ""},
    ])
    _csv(templates / "tax-codes.csv", ["code", "odoo_tax_hint", "use", "gst101a", "notes"], [
        {"code": "GST15_S", "odoo_tax_hint": "sale", "use": "sales", "gst101a": "BOX5", "notes": ""},
        {"code": "GST15_P", "odoo_tax_hint": "purchase", "use": "purchases", "gst101a": "BOX11", "notes": ""},
        {"code": "GST_EXEMPT_S", "odoo_tax_hint": "exempt", "use": "exempt", "gst101a": "none", "notes": ""},
        {"code": "GST0_EX_S", "odoo_tax_hint": "export", "use": "export", "gst101a": "BOX6", "notes": ""},
    ])
    _csv(templates / "analytic-accounts.csv", ["plan", "code", "name", "notes"], [
        {"plan": "PLG Studio", "code": "REDECHO", "name": "Red Echo", "notes": ""},
    ])
    _csv(templates / "fiscal-positions.csv", ["name", "tax_map", "gst101a", "notes"], [
        {"name": "NZ domestic", "tax_map": "none", "gst101a": "BOX5", "notes": ""},
    ])
    _csv(templates / "journals.csv", ["journal", "use", "notes"], [
        {"journal": "Sales", "use": "invoices", "notes": ""},
    ])
    _csv(templates / "coa-extra.csv", ["code", "name", "typical_use"], [
        {"code": "61010", "name": "Contractors", "typical_use": "bills"},
    ])
    _csv(templates / "customer-invoices.csv", INVOICE, [invoice_row()])
    _csv(templates / "vendor-bills.csv", [
        "partner", "bill_date", "ref", "product_default_code", "description", "qty",
        "price_unit_exclusive", "tax_code", "analytic", "account_code", "fiscal_position", "notes",
    ], [{"partner": "NZ Contractor Ltd", "bill_date": "2024-04-10", "ref": "", "product_default_code": "PLG-CONTRACTOR-NZ", "description": "", "qty": "1", "price_unit_exclusive": "100.00", "tax_code": "GST15_P", "analytic": "REDECHO", "account_code": "61010", "fiscal_position": "NZ domestic", "notes": ""}])
    _csv(templates / "gst101a-periods.csv", GST, [{
        "period_start": "2024-04-01", "period_end": "2024-05-31", "box5": "115.00", "box6": "0.00",
        "box8": "15.00", "box9": "0.00", "box11": "0.00", "box12": "0.00", "box13": "0.00", "box15": "15.00",
        "myir_pdf_filename": "seed.pdf", "odoo_matched": "FALSE", "tax_locked": "", "notes": "",
    }])
    _csv(templates / "company-identifiers.csv", COMPANY, [{
        "legal_name": "Pacen Life Games Limited", "nzbn": "9429000000000", "ird": "000-000-000",
        "gst_number": "000-000-000", "gst_status": "registered", "gst_registered_from": "2024-04-01",
        "gst_basis": "invoice", "gst_frequency": "two_monthly", "sol_sector": "plg-studio",
        "odoo_company_id": "", "notes": "",
    }])
    _csv(templates / "fiscal-years.csv", ["name", "date_from", "date_to", "notes"], [
        {"name": "FY 2024-25", "date_from": "2024-04-01", "date_to": "2025-03-31", "notes": ""},
    ])
    _csv(templates / "partners.csv", ["name", "is_company", "country_code", "fiscal_position", "gst_or_ird", "email", "role", "notes"], [
        {"name": "NZ Customer Ltd", "is_company": "TRUE", "country_code": "NZ", "fiscal_position": "NZ domestic", "gst_or_ird": "", "email": "", "role": "customer", "notes": ""},
    ])
    _csv(templates / "tco-kwh.csv", ["period_start", "period_end", "meter_id", "kwh", "source_bill", "nzd_excl_per_kwh", "analytic_code", "nzd_excl_allocated", "notes"], [
        {"period_start": "2026-04-01", "period_end": "2026-05-31", "meter_id": "pdu", "kwh": "10", "source_bill": "BILL-POWER", "nzd_excl_per_kwh": "0.20", "analytic_code": "REDECHO", "nzd_excl_allocated": "2.00", "notes": "report"},
    ])
    for name, key in REQUIRED_KEY.items():
        path = templates / name
        if path.exists():
            continue
        _csv(path, [key], [{key: "seed"}])
    return root


def workspace(tmp_path: Path):
    root = tmp_path / "ws"
    root.mkdir()
    manager = WorkspaceManager(tmp_path / "workspaces.json")
    record = manager.register(root)
    return root, manager, record


def invoice_row(**overrides):
    row = {column: "" for column in INVOICE}
    row.update({
        "partner": "NZ Customer Ltd",
        "invoice_date": "2024-04-15",
        "product_default_code": "PLG-NZ-DIGITAL",
        "qty": "1",
        "price_unit_exclusive": "100.00",
        "tax_code": "GST15_S",
        "analytic": "REDECHO",
        "fiscal_position": "NZ domestic",
    })
    row.update(overrides)
    return row


def test_bind_requires_approval_and_stores_the_verified_root(tmp_path):
    studio = build_studio(tmp_path / "studio")
    root, manager, record = workspace(tmp_path)
    ctx = type("Ctx", (), {})()
    ctx.permission_engine = Permit()
    ctx.workspace_manager = manager
    ctx.workspace_id = record.workspace_id
    ctx.workspace_root = root
    ctx.studio_root = ""
    ctx.audit = None
    with pytest.raises(ApprovalRequired):
        _bind(ctx, {"studio_root": str(studio)})
    saved = _bind(ctx, {"studio_root": str(studio), "approval_id": "a1"})
    assert saved["ok"] is True
    assert Path(saved["studio_root"]) == studio.resolve()
    assert manager.get(record.workspace_id).studio_root == saved["studio_root"]
    status = _status(ctx, {})
    assert status["templates_ok"] is True
    assert "customer-invoices.csv" in status["missing_data_files"]
    assert status["odoo_api"] == "not used"


def test_old_workspace_record_loads_without_a_studio_root(tmp_path):
    path = tmp_path / "workspaces.json"
    root = tmp_path / "ws"
    root.mkdir()
    path.write_text(json.dumps({"workspaces": [{
        "workspace_id": "w1", "name": "ws", "root": str(root),
        "created_at": 1, "last_used_at": 1, "jira_projects": [],
    }]}), encoding="utf-8")
    manager = WorkspaceManager(path)
    assert manager.get("w1").studio_root == ""


def test_write_copies_source_values_and_rejects_invention(tmp_path):
    studio = verify_studio_root(build_studio(tmp_path / "studio"))
    root, _manager, _record = workspace(tmp_path)
    source = root / "studio-odoo" / "sources" / "invoices" / "april.txt"
    source.parent.mkdir(parents=True)
    source.write_text("NZ Customer Ltd 2024-04-15 PLG-NZ-DIGITAL 100.00 GST15_S\n", encoding="utf-8")
    relative = "studio-odoo/sources/invoices/april.txt"
    result = write_import(root, studio, "customer-invoices.csv", [invoice_row()], [relative])
    assert result["odoo_import"] is True
    assert result["rows"] == 1
    written = (root / "studio-odoo" / "import" / "customer-invoices.csv").read_text(encoding="utf-8")
    assert written.splitlines()[0] == ",".join(INVOICE)
    assert "PLG-NZ-DIGITAL" in written

    with pytest.raises(StudioError, match="EXAMPLE"):
        write_import(root, studio, "customer-invoices.csv", [invoice_row(partner="EXAMPLE customer")], [relative])
    with pytest.raises(StudioError, match="not a product code"):
        write_import(root, studio, "customer-invoices.csv", [invoice_row(product_default_code="SKU-NEW")], [relative])
    with pytest.raises(StudioError, match="Never GST0_EX_S"):
        write_import(root, studio, "customer-invoices.csv", [invoice_row(product_default_code="PLG-GRANT", tax_code="GST0_EX_S")], [relative])
    with pytest.raises(StudioError, match="project-spicy"):
        write_import(root, studio, "customer-invoices.csv", [invoice_row(notes="project-spicy")], [relative])
    with pytest.raises(StudioError, match="must be a string"):
        write_import(root, studio, "customer-invoices.csv", [invoice_row(qty=1)], [relative])
    warned = write_import(root, studio, "customer-invoices.csv", [invoice_row(account_code="11200")], [relative])
    assert any("11200" in item for item in warned["warnings"])
    allowed = write_import(
        root, studio, "customer-invoices.csv",
        [invoice_row(product_default_code="PLG-GRANT", tax_code="GST_EXEMPT_S")],
        [relative],
    )
    assert allowed["rows"] == 1


def test_gst_box_8_identity_and_missing_pdf(tmp_path):
    studio = verify_studio_root(build_studio(tmp_path / "studio"))
    root, _manager, _record = workspace(tmp_path)
    pdf = root / "studio-odoo" / "sources" / "gst-returns" / "GST101A-2024-04-05.pdf"
    pdf.parent.mkdir(parents=True)
    pdf.write_bytes(b"%PDF-test")
    row = {column: "" for column in GST}
    row.update({
        "period_start": "2024-04-01", "period_end": "2024-05-31",
        "box5": "115.00", "box6": "0.00", "box8": "15.00", "box9": "0.00",
        "box11": "0.00", "box12": "0.00", "box13": "0.00", "box15": "15.00",
        "myir_pdf_filename": "GST101A-2024-04-05.pdf",
    })
    result = write_import(root, studio, "gst101a-periods.csv", [row], ["studio-odoo/sources/gst-returns/GST101A-2024-04-05.pdf"])
    assert result["ok"] is True
    row["box8"] = "14.00"
    with pytest.raises(StudioError, match="Box 8"):
        write_import(root, studio, "gst101a-periods.csv", [row], ["studio-odoo/sources/gst-returns/GST101A-2024-04-05.pdf"])
    row["box8"] = "15.00"
    row["myir_pdf_filename"] = "missing.pdf"
    with pytest.raises(StudioError, match="not in studio-odoo/sources"):
        write_import(root, studio, "gst101a-periods.csv", [row], ["studio-odoo/sources/gst-returns/GST101A-2024-04-05.pdf"])


def test_tco_kwh_is_never_an_odoo_import(tmp_path):
    studio = verify_studio_root(build_studio(tmp_path / "studio"))
    root, _manager, _record = workspace(tmp_path)
    source = root / "studio-odoo" / "sources" / "bills" / "power.txt"
    source.parent.mkdir(parents=True)
    source.write_text("BILL-POWER\n", encoding="utf-8")
    header = list(studio.headers["tco-kwh.csv"])
    row = {column: "" for column in header}
    row.update({
        "period_start": "2026-04-01", "period_end": "2026-05-31", "meter_id": "pdu",
        "kwh": "10", "source_bill": "", "nzd_excl_per_kwh": "0.20",
        "analytic_code": "REDECHO", "nzd_excl_allocated": "2.00",
    })
    with pytest.raises(StudioError, match="source_bill is empty"):
        write_import(root, studio, "tco-kwh.csv", [row], ["studio-odoo/sources/bills/power.txt"])
    row["source_bill"] = "BILL-POWER"
    result = write_import(root, studio, "tco-kwh.csv", [row], ["studio-odoo/sources/bills/power.txt"])
    assert result["odoo_import"] is False
    assert result["never_import"] is True


def test_catalogs_are_copied_unchanged_and_cannot_be_rebuilt(tmp_path):
    studio_root = build_studio(tmp_path / "studio")
    studio = verify_studio_root(studio_root)
    root, _manager, _record = workspace(tmp_path)
    from sol_lite.integrations.studio_odoo import copy_catalogs

    copied = copy_catalogs(root, studio)
    assert copied["changed"] is True
    original = (studio_root / "docs" / "templates" / "products.csv").read_bytes()
    assert (root / "studio-odoo" / "import" / "products.csv").read_bytes() == original
    again = copy_catalogs(root, studio)
    assert again["changed"] is False
    with pytest.raises(StudioError, match="catalog file"):
        write_import(root, studio, "products.csv", [{"code": "SKU-NEW"}], [])


def test_adopt_requires_an_exact_header(tmp_path):
    studio = verify_studio_root(build_studio(tmp_path / "studio"))
    root, _manager, _record = workspace(tmp_path)
    from sol_lite.integrations.studio_odoo import adopt_source

    source = root / "studio-odoo" / "sources" / "partners.csv"
    _csv(source, ["name", "is_company"], [{"name": "NZ Customer Ltd", "is_company": "TRUE"}])
    with pytest.raises(StudioError, match="No mapping was applied"):
        adopt_source(root, studio, "studio-odoo/sources/partners.csv", "partners.csv")
    assert not (root / "studio-odoo" / "import" / "partners.csv").exists()
    header = list(studio.headers["partners.csv"])
    row = {column: "" for column in header}
    row["name"] = "NZ Customer Ltd"
    row["is_company"] = "TRUE"
    _csv(source, header, [row])
    adopted = adopt_source(root, studio, "studio-odoo/sources/partners.csv", "partners.csv")
    assert adopted["rows"] == 1


def test_fiscal_year_must_be_april_to_march(tmp_path):
    studio = verify_studio_root(build_studio(tmp_path / "studio"))
    root, _manager, _record = workspace(tmp_path)
    source = root / "studio-odoo" / "sources" / "years.txt"
    source.parent.mkdir(parents=True)
    source.write_text("2024-04-01 2025-03-31\n", encoding="utf-8")
    header = list(studio.headers["fiscal-years.csv"])
    row = {column: "" for column in header}
    row["date_from"] = "2024-01-01"
    row["date_to"] = "2024-12-31"
    with pytest.raises(StudioError, match="1 April"):
        write_import(root, studio, "fiscal-years.csv", [row], ["studio-odoo/sources/years.txt"])
    row["date_from"] = "2024-04-01"
    row["date_to"] = "2025-03-31"
    assert write_import(root, studio, "fiscal-years.csv", [row], ["studio-odoo/sources/years.txt"])["ok"] is True


def test_import_pack_cannot_be_written_inside_the_studio_repo(tmp_path):
    studio_root = build_studio(tmp_path / "studio")
    nested = studio_root / "workspace"
    nested.mkdir()
    studio = verify_studio_root(studio_root)
    with pytest.raises(StudioError, match="inside the studio repository"):
        write_import(nested, studio, "fiscal-years.csv", [], [])


def test_pa_receives_studio_tools_and_other_agents_do_not():
    available = build_tool_registry().names()
    pa = set(resolve_session_tools(ROOT, "sol_pa", available))
    engineer = set(resolve_session_tools(ROOT, "sol_engineer", available))
    assert {
        "studio_odoo_status", "studio_odoo_bind", "studio_odoo_schema",
        "studio_odoo_inventory", "studio_odoo_copy_catalogs",
        "studio_odoo_adopt_source", "studio_odoo_write_import",
    } <= pa
    assert not any(name.startswith("studio_odoo_") for name in engineer)


def test_studio_tools_stay_opt_in_until_the_root_is_bound():
    available = frozenset(build_tool_registry().names())
    quiet = permitted_tools("list the folders", available)
    assert "studio_odoo_bind" not in quiet
    asked = permitted_tools("build the odoo import files", available)
    assert "studio_odoo_bind" in asked
    assert "studio_odoo_write_import" not in apply_studio_workspace_gate(
        "build the odoo import files", asked, "",
    )
    assert "studio_odoo_write_import" in apply_studio_workspace_gate(
        "build the odoo import files", asked, r"E:\git\plg-studio\plg-odooacc",
    )


def test_real_studio_templates_match_the_contract():
    if not STUDIO.is_dir():
        pytest.skip("plg-odooacc is not available on this machine")
    catalog = verify_studio_root(STUDIO)
    assert catalog.products["PLG-GRANT"]["sale_tax_code"] == "GST15_S"
    assert catalog.products["PLG-EXPORT-DIGITAL"]["sale_tax_code"] == "GST0_EX_S"
    assert "REDECHO" in catalog.analytic_codes
    assert "GST15_S" in catalog.tax_codes
    tree = ast.parse((STUDIO / "tests" / "test_gather_pack_templates.py").read_text(encoding="utf-8"))
    found = None
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "REQUIRED_CSV" for target in node.targets):
            found = ast.literal_eval(node.value)
    assert found == REQUIRED_KEY
