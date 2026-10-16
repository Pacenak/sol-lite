"""PA tools that turn workspace source files into a Studio Odoo import pack."""
from __future__ import annotations

from ..capabilities.risk import RiskClass
from ..integrations.studio_odoo import (
    StudioError,
    adopt_source,
    copy_catalogs,
    inventory_sources,
    pack_status,
    verify_studio_root,
    write_import,
)
from .base import ToolDefinition

_READ = (RiskClass.READ_ONLY,)
_WRITE = (RiskClass.MUTATING,)
_APPROVAL = {"approval_id": {"type": "string", "description": "Exact approval token returned by SOL-Lite."}}


def _bound_root(ctx) -> str:
    saved = str(getattr(ctx, "studio_root", "") or "").strip()
    if saved:
        return saved
    manager = getattr(ctx, "workspace_manager", None)
    workspace_id = getattr(ctx, "workspace_id", None)
    if manager is None or not workspace_id:
        return ""
    workspace = manager.get(workspace_id)
    return str(getattr(workspace, "studio_root", "") or "").strip()


def _catalog(ctx):
    root = _bound_root(ctx)
    if not root:
        raise RuntimeError("This workspace has no studio root. Ask for the studio repository path and call studio_odoo_bind.")
    try:
        return verify_studio_root(root)
    except StudioError as exc:
        raise RuntimeError(str(exc)) from exc


def _authorize(ctx, scope, operation, target, arguments, plan, approval_id):
    ctx.permission_engine.check(
        scope,
        approval_id=approval_id,
        operation=operation,
        target=target,
        arguments=arguments,
        plan=plan,
    )


def _audit(ctx, event):
    audit = getattr(ctx, "audit", None)
    if audit is not None:
        audit.record(event)


def _workspace(ctx):
    root = getattr(ctx, "workspace_root", None)
    if not root:
        raise RuntimeError("This session has no workspace.")
    return root


def _status(ctx, args):
    del args
    root = _bound_root(ctx)
    catalog = None
    if root:
        try:
            catalog = verify_studio_root(root)
        except StudioError as exc:
            return {
                "bound": True,
                "studio_root": root,
                "templates_ok": False,
                "error": str(exc),
                "odoo_api": "not used",
                "myir_filing": "not performed",
            }
    return pack_status(_workspace(ctx), catalog, root)


def _bind(ctx, args):
    studio_root = str(args.get("studio_root") or "").strip()
    arguments = {"studio_root": studio_root}
    _authorize(
        ctx, "studio.write", "studio_odoo_bind", studio_root or "studio root",
        arguments, "Bind a Studio Odoo checkout to this workspace", args.get("approval_id"),
    )
    try:
        catalog = verify_studio_root(studio_root)
    except StudioError as exc:
        raise RuntimeError(str(exc)) from exc
    manager = getattr(ctx, "workspace_manager", None)
    workspace_id = getattr(ctx, "workspace_id", None)
    if manager is None or not workspace_id:
        raise RuntimeError("This session has no workspace to store the studio root on.")
    saved = manager.set_studio_root(workspace_id, str(catalog.root))
    ctx.studio_root = saved
    _audit(ctx, "studio_odoo.bind")
    return {
        "ok": True,
        "studio_root": saved,
        "templates": sorted(catalog.headers),
        "odoo_api": "not used",
    }


def _schema(ctx, args):
    template = str(args.get("template") or "").strip()
    arguments = {"template": template}
    _authorize(
        ctx, "studio.read", "studio_odoo_schema", template or "all templates",
        arguments, "Read Studio Odoo gather-pack column names", args.get("approval_id"),
    )
    catalog = _catalog(ctx)
    payload = catalog.public_schemas()
    if template:
        if template not in catalog.headers:
            raise RuntimeError(f"{template} is not a studio gather-pack file")
        payload["templates"] = {template: payload["templates"][template]}
    _audit(ctx, "studio_odoo.schema")
    return payload


def _inventory(ctx, args):
    arguments = {}
    _authorize(
        ctx, "studio.read", "studio_odoo_inventory", "studio-odoo/sources",
        arguments, "List workspace source files for the Studio Odoo import pack", args.get("approval_id"),
    )
    root = _bound_root(ctx)
    catalog = None
    if root:
        try:
            catalog = verify_studio_root(root)
        except StudioError as exc:
            raise RuntimeError(str(exc)) from exc
    result = inventory_sources(_workspace(ctx), catalog)
    result["studio_bound"] = catalog is not None
    _audit(ctx, "studio_odoo.inventory")
    return result


def _copy(ctx, args):
    arguments = {}
    _authorize(
        ctx, "studio.write", "studio_odoo_copy_catalogs", "studio-odoo/import",
        arguments, "Copy Studio Odoo catalog CSVs unchanged into this workspace", args.get("approval_id"),
    )
    try:
        result = copy_catalogs(_workspace(ctx), _catalog(ctx))
    except StudioError as exc:
        raise RuntimeError(str(exc)) from exc
    _audit(ctx, "studio_odoo.copy_catalogs")
    return result


def _adopt(ctx, args):
    source = str(args.get("source") or "").strip()
    template = str(args.get("template") or "").strip()
    arguments = {"source": source, "template": template}
    _authorize(
        ctx, "studio.write", "studio_odoo_adopt_source", template or source,
        arguments, "Adopt a source CSV whose header already matches a studio template", args.get("approval_id"),
    )
    try:
        result = adopt_source(_workspace(ctx), _catalog(ctx), source, template)
    except StudioError as exc:
        raise RuntimeError(str(exc)) from exc
    _audit(ctx, "studio_odoo.adopt_source")
    return result


def _write(ctx, args):
    template = str(args.get("template") or "").strip()
    rows = args.get("rows")
    source_files = args.get("source_files") or []
    if not isinstance(rows, list):
        raise TypeError("rows must be a list of objects")
    if not isinstance(source_files, list):
        raise TypeError("source_files must be a list of workspace paths")
    arguments = {
        "template": template,
        "rows": rows,
        "source_files": [str(item) for item in source_files],
    }
    _authorize(
        ctx, "studio.write", "studio_odoo_write_import", template or "import file",
        arguments, "Write one Studio Odoo import CSV from workspace source values", args.get("approval_id"),
    )
    try:
        result = write_import(
            _workspace(ctx), _catalog(ctx), template, rows, arguments["source_files"],
        )
    except StudioError as exc:
        raise RuntimeError(str(exc)) from exc
    _audit(ctx, "studio_odoo.write_import")
    return result


def studio_odoo_tools():
    return [
        ToolDefinition(
            "studio_odoo_status",
            "Report whether this workspace is bound to a Studio Odoo checkout and which gather-pack files are still missing. Does not call Odoo.",
            {"type": "object", "properties": {}},
            _status,
            locality="host",
        ),
        ToolDefinition(
            "studio_odoo_bind",
            "Save the Studio Odoo repository path for this workspace after the gather-pack templates are verified. Does not guess a path.",
            {
                "type": "object",
                "properties": {
                    "studio_root": {"type": "string", "description": "Absolute path of the plg-odooacc checkout the user supplied."},
                    **_APPROVAL,
                },
                "required": ["studio_root"],
            },
            _bind,
            permissions=("studio.write",),
            risk=_WRITE,
            mutability=True,
            locality="host",
        ),
        ToolDefinition(
            "studio_odoo_schema",
            "Read gather-pack column names, catalog codes, and import rules from the bound Studio Odoo templates.",
            {
                "type": "object",
                "properties": {
                    "template": {"type": "string", "description": "One CSV file name. Omit to return every template."},
                    **_APPROVAL,
                },
            },
            _schema,
            permissions=("studio.read",),
            risk=_READ,
            locality="host",
        ),
        ToolDefinition(
            "studio_odoo_inventory",
            "List files the user placed in studio-odoo/sources. A CSV matches a template only when its header is exactly the same.",
            {"type": "object", "properties": {**_APPROVAL}},
            _inventory,
            permissions=("studio.read",),
            risk=_READ,
            locality="host",
        ),
        ToolDefinition(
            "studio_odoo_copy_catalogs",
            "Copy products, tax codes, analytics, fiscal positions, journals, and extra accounts unchanged from the studio templates into studio-odoo/import.",
            {"type": "object", "properties": {**_APPROVAL}},
            _copy,
            permissions=("studio.write",),
            risk=_WRITE,
            mutability=True,
            locality="host",
        ),
        ToolDefinition(
            "studio_odoo_adopt_source",
            "Validate and copy one source CSV into studio-odoo/import when its header already equals the named studio template. No column mapping is applied.",
            {
                "type": "object",
                "properties": {
                    "source": {"type": "string", "description": "Workspace path under studio-odoo/sources."},
                    "template": {"type": "string", "description": "Gather-pack CSV file name."},
                    **_APPROVAL,
                },
                "required": ["source", "template"],
            },
            _adopt,
            permissions=("studio.write",),
            risk=_WRITE,
            mutability=True,
            locality="host",
        ),
        ToolDefinition(
            "studio_odoo_write_import",
            "Write one data CSV in studio-odoo/import. Every cell must be a string copied from a named source file. Catalog files cannot be written here.",
            {
                "type": "object",
                "properties": {
                    "template": {"type": "string"},
                    "rows": {"type": "array", "items": {"type": "object"}},
                    "source_files": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Workspace paths under studio-odoo/sources that contain the cell values.",
                    },
                    **_APPROVAL,
                },
                "required": ["template", "rows", "source_files"],
            },
            _write,
            permissions=("studio.write",),
            risk=_WRITE,
            mutability=True,
            locality="host",
        ),
    ]
