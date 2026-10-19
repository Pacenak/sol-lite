import asyncio
import hashlib
import re
import time
from pathlib import Path

import jsonschema
import pytest

from sol_lite.core.exceptions import (
    ApprovalRequired,
    PermissionDenied,
    SecurityError,
    ToolExecutionError,
)
from sol_lite.tools import build_tool_registry
from sol_lite.tools import indexing as mod


@pytest.fixture(autouse=True)
def empty_cache():
    with mod._CACHE_LOCK:
        mod._CACHE.clear()
    yield
    with mod._CACHE_LOCK:
        mod._CACHE.clear()


def write(root, relative, value):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(value.encode("utf-8") if isinstance(value, str) else value)
    return path


def merge(source, target, **kwargs):
    return mod.plan_merge(source, target, **kwargs)


def prepare(ctx, source="# World\n- New item\n", target="# World\n- Old item\n"):
    ctx.agent_id = "sol_pa"
    write(ctx.workspace_root, "inbox/new.md", source)
    write(ctx.workspace_root, "docs/target.md", target)
    args = {"source_file": "inbox/new.md", "target_file": "docs/target.md"}
    preview = mod.consolidate_inbox_preview(ctx, args)
    return {
        **args,
        "expected_source_sha256": preview["source_sha256"],
        "expected_target_sha256": preview["target_sha256"],
        "plan": "Add reviewed inbox content",
        "approval_id": "",
    }


def apply_approved(ctx, args):
    with pytest.raises(ApprovalRequired) as caught:
        mod.consolidate_inbox_apply(ctx, args)
    return mod.consolidate_inbox_apply(
        ctx, {**args, "approval_id": caught.value.request.approval_id}
    )


def test_parser_physical_lines_bom_fences_and_hierarchy():
    source = (
        "\ufeffPreamble\r\n# World\rBody\n```md\n## Not a header\n```\n## Child\ntext\u2028more"
    )
    doc = mod.parse_markdown(source.encode("utf-8"))
    assert doc.lines[0] == "\ufeffPreamble"
    assert doc.endings[:3] == ("\r\n", "\r", "\n")
    assert doc.lines[-1] == "text\u2028more"
    assert [section.path for section in doc.sections] == [(), ("World",), ("World", "Child")]
    assert doc.sections[1].end == len(doc.lines)
    assert doc.sections[1].own_end == doc.sections[2].start
    assert doc.fences == ((3, 6),)
    assert doc.bom and not doc.trailing_newline
    assert mod.apply_merge_text(doc, []) == source
    with pytest.raises(UnicodeError):
        mod.parse_markdown(b"\xff")


def test_tilde_long_fence_and_setext_ignored():
    doc = mod.parse_markdown("Title\n===\n~~~~\n# Hidden\n~~~\n~~~~\n# Real\n")
    assert [section.path for section in doc.sections] == [(), ("Real",)]
    assert not doc.unclosed_fence
    assert mod.parse_markdown("```\n# hidden").unclosed_fence
    assert mod.parse_markdown("# World ###\n").sections[1].path == ("World",)


@pytest.mark.parametrize(
    "mode,query,extra",
    [
        ("text", "IRON key", {}),
        ("text", "absent key", {"match": "any"}),
        ("regex", r"^Iron.*key$", {}),
        ("header", "World", {}),
    ],
)
def test_search_exact_lines_every_mode(tool_context, mode, query, extra):
    raw = "\ufeff# World\r\nIron key\rOther text\n## Child\nIron key again\n".encode("utf-8")
    path = write(tool_context.workspace_root, "docs/example.md", raw)
    result = mod.search_knowledge_index_sync(
        tool_context,
        {"query": query, "mode": mode, "target_dir": "docs", "context_lines": 1, **extra},
    )
    assert result["results"]
    exact, _ = mod._physical_lines(raw.decode("utf-8"))
    for block in result["results"]:
        assert block["absolute_path"] == str(path)
        assert [row["text"] for row in block["lines"]] == list(
            exact[block["start_line"] - 1 : block["end_line"]]
        )
        assert [row["n"] for row in block["lines"]] == list(
            range(block["start_line"], block["end_line"] + 1)
        )
        assert block["verbatim"] == "\n".join(row["text"] for row in block["lines"])
    if mode == "header":
        assert len(result["results"]) == 1  # Parent contains its matching subtree.


def test_search_all_any_case_and_no_split_on_nonmatch(tool_context, monkeypatch):
    write(tool_context.workspace_root, "a.md", "first\nAlpha item\nBeta\n")

    def forbidden(value):
        raise AssertionError("Non-matching text must not be parsed into lines")

    original = mod.parse_markdown
    monkeypatch.setattr(mod, "parse_markdown", forbidden)
    result = mod.search_knowledge_index_sync(tool_context, {"query": "absent"})
    assert result["results"] == [] and result["complete"]
    monkeypatch.setattr(mod, "parse_markdown", original)
    assert not mod.search_knowledge_index_sync(tool_context, {"query": "Alpha Beta"})["results"]
    assert (
        len(
            mod.search_knowledge_index_sync(tool_context, {"query": "Alpha Beta", "match": "any"})[
                "results"
            ]
        )
        == 1
    )
    assert not mod.search_knowledge_index_sync(
        tool_context, {"query": "alpha", "case_sensitive": True}
    )["results"]


@pytest.mark.parametrize("pattern", [r"\Asecond\Z", r"^second$", r"(?<=^)second(?=$)"])
def test_regex_precheck_never_hides_per_line_anchor_matches(tool_context, pattern):
    write(tool_context.workspace_root, "a.md", "first\r\nsecond\rlast")
    result = mod.search_knowledge_index_sync(tool_context, {"query": pattern, "mode": "regex"})
    assert result["results"][0]["start_line"] == 2


def test_search_blocks_boundaries_context_caps_and_dynamic_fence(tool_context):
    write(tool_context.workspace_root, "z.md", "# A\nmatch\nmatch\n# B\nmatch ``` content\nend\n")
    result = mod.search_knowledge_index_sync(tool_context, {"query": "match", "context_lines": 1})
    assert [(row["start_line"], row["end_line"]) for row in result["results"]] == [(1, 3), (4, 6)]
    assert result["results"][0]["lines"][0]["match"] is False
    assert "````" in result["results"][1]["rendered"]
    capped = mod.search_knowledge_index_sync(
        tool_context, {"query": "match", "max_results": 1, "max_block_lines": 1, "context_lines": 2}
    )
    assert capped["total_blocks"] == 2 and capped["returned"] == 1
    assert capped["results"][0]["truncated"] and not capped["complete"]
    assert capped["results"][0]["lines"][0]["match"] is True


def test_search_inbox_exclusion_skips_limits_and_order(tool_context, monkeypatch):
    root = tool_context.workspace_root
    write(root, "z.md", "needle")
    write(root, "a.md", "needle")
    write(root, "inbox/nested/new.md", "needle")
    write(root, "_workspace/README.md", "needle")
    write(root, ".git/ignored.md", "needle")
    result = mod.search_knowledge_index_sync(tool_context, {"query": "needle"})
    assert [row["path"] for row in result["results"]] == ["_workspace/README.md", "a.md", "z.md"]
    assert result["inbox_files_excluded"] == 1 and result["complete"]
    assert (
        len(
            mod.search_knowledge_index_sync(
                tool_context, {"query": "needle", "include_inbox": True}
            )["results"]
        )
        == 4
    )
    assert not mod.search_knowledge_index_sync(
        tool_context, {"query": "needle", "target_dir": "inbox"}
    )["results"]
    write(root, "bad.md", b"\xff")
    write(root, "large.md", b"x" * (mod.MAX_FILE_BYTES + 1))
    result = mod.search_knowledge_index_sync(tool_context, {"query": "absent"})
    assert {row["reason"] for row in result["files_skipped"]} == {"not_utf8", "too_large"}
    assert not result["complete"] and "absence is not established" in result["notice"]
    monkeypatch.setattr(mod, "MAX_FILES", 2)
    result = mod.search_knowledge_index_sync(tool_context, {"query": "needle"})
    assert any(
        row["reason"] == "file_limit" and row["count"] > 0 for row in result["files_skipped"]
    )


def test_search_lru_reuses_and_invalidates_parsed_documents(tool_context, monkeypatch):
    root = tool_context.workspace_root
    path = write(root, "a.md", "needle")
    mod.search_knowledge_index_sync(tool_context, {"query": "needle"})
    original = mod.parse_markdown
    monkeypatch.setattr(mod, "parse_markdown", lambda value: pytest.fail("Cache should be reused"))
    assert mod.search_knowledge_index_sync(tool_context, {"query": "needle"})["returned"] == 1
    monkeypatch.setattr(mod, "parse_markdown", original)
    path.write_bytes(b"needle updated")
    assert (
        "updated"
        in mod.search_knowledge_index_sync(tool_context, {"query": "needle"})["results"][0][
            "verbatim"
        ]
    )
    monkeypatch.setattr(mod, "CACHE_SIZE", 2)
    write(root, "b.md", "needle")
    write(root, "c.md", "needle")
    mod.search_knowledge_index_sync(tool_context, {"query": "needle"})
    assert len(mod._CACHE) == 2


def test_nested_header_matches_return_outermost_only():
    doc = mod.parse_markdown("# Topic\nbody\n## Topic child\nmore\n# Other\nend\n")
    result = mod.search_documents([("a.md", "/a.md", doc)], "Topic", mode="header")
    assert result["returned"] == 1
    assert result["results"][0]["end_line"] == 4


def test_search_link_skips_and_unreadable_file(tool_context, monkeypatch):
    root = tool_context.workspace_root
    path = write(root, "linked.md", "needle")
    actual = mod._is_link
    monkeypatch.setattr(mod, "_is_link", lambda item: item == path or actual(item))
    result = mod.search_knowledge_index_sync(tool_context, {"query": "needle"})
    assert not result["complete"] and result["files_skipped"][0]["reason"] == "symlink"
    monkeypatch.setattr(mod, "_is_link", actual)
    opening = Path.open

    def fail(item, *args, **kwargs):
        if item == path:
            raise PermissionError("fixture unreadable")
        return opening(item, *args, **kwargs)

    monkeypatch.setattr(Path, "open", fail)
    result = mod.search_knowledge_index_sync(tool_context, {"query": "needle"})
    assert result["files_skipped"][0]["reason"] == "unreadable" and not result["complete"]


def test_target_directory_link_ancestor_is_not_followed(tool_context, monkeypatch):
    root = tool_context.workspace_root
    write(root, "alias/nested/a.md", "needle")
    original = mod._is_link
    monkeypatch.setattr(mod, "_is_link", lambda item: item == root / "alias" or original(item))
    result = mod.search_knowledge_index_sync(
        tool_context, {"query": "needle", "target_dir": "alias/nested"}
    )
    assert result["files_scanned"] == 0 and result["files_skipped"][0]["reason"] == "symlink"


@pytest.mark.parametrize(
    "args",
    [
        {"query": " "},
        {"query": "x", "mode": "semantic"},
        {"query": "[", "mode": "regex"},
        {"query": "x", "max_results": True},
        {"query": "x", "context_lines": 11},
        {"query": "x", "include_inbox": "yes"},
    ],
)
def test_search_argument_validation(tool_context, args):
    with pytest.raises(ValueError):
        mod.search_knowledge_index_sync(tool_context, args)


def test_merge_duplicates_additions_blanks_and_idempotence():
    source = "# Items\n+ Existing\n\n- New one\n\n- New two\n\n"
    target = "# Items\n- Existing\n\n## Child\nKeep\n"
    result = merge(source, target)
    assert result["status"] == "ready" and result["skipped_duplicates"]["count"] == 1
    assert "- New one\n\n- New two" in result["merged_text"]
    assert result["merged_text"].index("New two") < result["merged_text"].index("## Child")
    mod._invariant(target, result["merged_text"])
    assert merge(source, result["merged_text"])["status"] == "no_changes"


@pytest.mark.parametrize(
    "source,target,kind",
    [
        ("# A\n- Level: 5\n", "# A\n- Level: 3\n", "value_changed"),
        ("# A\n**Level:** 5\n", "# A\n**Level**: 3\n", "value_changed"),
        ("# A\nKey=2\n", "# A\nKey=1\nKey=1\n", "ambiguous_key"),
        ("# A\nKey: 1\nKey: 2\n", "# A\n", "ambiguous_key"),
        (
            "# A\nThe very long existing line changes.\n",
            "# A\nThe very long existing line changes!\n",
            "possible_edit",
        ),
        ("# A\n# A\n", "# A\n", "ambiguous_header"),
        ("# A\n", "# A\n# A\n", "ambiguous_header"),
        ("# A\n```\ncode", "# A\n", "unclosed_fence"),
    ],
)
def test_conflict_families(source, target, kind):
    result = merge(source, target)
    assert result["status"] == "needs_reconciliation" and result["merged_text"] is None
    assert kind in {item["kind"] for item in result["conflicts"]}


def test_merge_tables_after_last_table_and_fences_as_atoms():
    target = "# A\n| Key | Value |\n| --- | --- |\n| One | 1 |\n\nProse retained.\n"
    source = "# A\n| Key | Value |\n| --- | --- |\n| Two | 2 |\n"
    result = merge(source, target)
    assert result["status"] == "ready"
    assert result["merged_text"].index("| Two") < result["merged_text"].index("Prose")
    assert merge(source, result["merged_text"])["status"] == "no_changes"
    piped_prose = target + "\nNot a table | ordinary prose\n"
    extra = merge("# A\n| Two | 2 |\n", piped_prose)
    assert extra["merged_text"].index("| Two |") < extra["merged_text"].index("Prose retained")
    assert merge(source.replace("Two", "One"), target)["status"] == "needs_reconciliation"
    fenced = merge("# A\n```text\n# Not header\nline\n```\n", "# A\n")
    assert len(fenced["additions"]) == 1
    assert len(fenced["additions"][0]["lines"]) == 4
    assert (
        merge("# A\n```text\n# Not header\nline\n```\n", fenced["merged_text"])["status"]
        == "no_changes"
    )


def test_missing_sections_under_parent_and_eof():
    result = merge(
        "# A\n## New child\ncontent\n### Nested\nmore\n# New root\nextra\n",
        "# A\n## Old child\nkeep\n\n# B\nleave\n",
    )
    assert result["status"] == "ready"
    assert [item["placement"] for item in result["additions"]] == ["under_parent", "end_of_file"]
    assert result["merged_text"].index("## New child") < result["merged_text"].index("# B")
    assert result["merged_text"].count("### Nested") == 1


def test_shared_insertion_boundary_keeps_own_bodies_and_subtrees_correct():
    source = "# A\n## New sibling\nnew sibling body\n## Existing\nexisting addition\n### New grandchild\ngrandchild body\n# New root\nroot body\n"
    target = "# A\n## Existing\nold content\n"
    result = merge(source, target)
    assert result["status"] == "ready"
    sections = {
        section.path: section for section in mod.parse_markdown(result["merged_text"]).sections
    }
    doc = mod.parse_markdown(result["merged_text"])
    own = sections[("A", "Existing")]
    assert "existing addition" in doc.lines[own.body_start : own.own_end]
    assert ("A", "Existing", "New grandchild") in sections
    assert ("A", "New sibling") in sections and ("New root",) in sections
    assert merge(source, result["merged_text"])["status"] == "no_changes"


def test_table_rows_precede_prose_added_at_the_same_boundary():
    target = "# A\n| Key | Value |\n| --- | --- |\n| Old | 1 |\n"
    source = "# A\nNew prose\n| New | 2 |\n"
    result = merge(source, target)
    assert result["merged_text"].index("| New |") < result["merged_text"].index("New prose")
    assert merge(source, result["merged_text"])["status"] == "no_changes"


@pytest.mark.parametrize("target", ["# A\r\nold\r\n", "# A\rold", "\ufeff# A\r\nold\nlast\r", ""])
def test_merge_preserves_endings_bom_and_trailing_state(target):
    result = merge("# A\nBrand new material\n", target)
    assert result["status"] == "ready"
    merged = result["merged_text"]
    mod._invariant(target, merged)
    before, after = mod.parse_markdown(target), mod.parse_markdown(merged)
    assert before.trailing_newline == after.trailing_newline
    assert before.bom == after.bom
    if target.startswith("\ufeff"):
        assert merged.startswith("\ufeff") and merged.count("\ufeff") == 1


def test_bom_and_new_preamble_is_encoding_metadata():
    result = merge("Intro\n# A\nnew", "\ufeff# A\nold")
    assert result["status"] == "ready" and result["merged_text"].startswith("\ufeffIntro\n")
    mod._invariant("\ufeff# A\nold", result["merged_text"])


def test_preview_apply_approval_and_source_unchanged(tool_context):
    args = prepare(tool_context, "# World\nNew fact\n", "# World\nOld thing\n")
    target = tool_context.workspace_root / args["target_file"]
    source = tool_context.workspace_root / args["source_file"]
    before, inbox = target.read_bytes(), source.read_bytes()
    with pytest.raises(ApprovalRequired):
        mod.consolidate_inbox_apply(tool_context, args)
    assert target.read_bytes() == before
    result = apply_approved(tool_context, args)
    assert result["applied"] and result["lines_added"] == 1
    assert source.read_bytes() == inbox
    assert hashlib.sha256(target.read_bytes()).hexdigest() == result["new_sha256"]
    preview = mod.consolidate_inbox_preview(tool_context, args)
    assert preview["status"] == "no_changes"
    no_op = mod.consolidate_inbox_apply(
        tool_context, {**args, "expected_target_sha256": preview["target_sha256"]}
    )
    assert no_op["status"] == "no_changes" and no_op["applied"] is False


def test_conflict_blocks_whole_apply_and_stale_hashes(tool_context):
    args = prepare(tool_context, "# World\nLevel: 2\nNew unrelated item\n", "# World\nLevel: 1\n")
    target = tool_context.workspace_root / args["target_file"]
    before = target.read_bytes()
    result = mod.consolidate_inbox_apply(tool_context, args)
    assert result["status"] == "needs_reconciliation" and result["ok"] is False
    assert target.read_bytes() == before
    (tool_context.workspace_root / args["source_file"]).write_bytes(b"# World\nChanged")
    with pytest.raises(ToolExecutionError, match="Stale"):
        mod.consolidate_inbox_apply(tool_context, args)
    assert target.read_bytes() == before


def test_atomic_failure_and_corrupt_merge_leave_original(tool_context, monkeypatch):
    args = prepare(tool_context, "# World\nNew fact\n", "# World\nOld thing\n")
    target = tool_context.workspace_root / args["target_file"]
    before = target.read_bytes()
    monkeypatch.setattr(
        mod.os, "replace", lambda *a: (_ for _ in ()).throw(OSError("simulated write failure"))
    )
    with pytest.raises(ToolExecutionError, match="Atomic"):
        apply_approved(tool_context, args)
    assert target.read_bytes() == before and not list(target.parent.glob("*.tmp"))
    monkeypatch.setattr(mod, "apply_merge_text", lambda *a: "Corrupted output\n")
    with pytest.raises(ToolExecutionError, match="invariant"):
        apply_approved(tool_context, args)
    assert target.read_bytes() == before


def test_change_during_approval_is_rejected(tool_context, monkeypatch):
    args = prepare(tool_context, "# World\nNew fact\n", "# World\nOld thing\n")
    target = tool_context.workspace_root / args["target_file"]
    source = tool_context.workspace_root / args["source_file"]
    before = target.read_bytes()
    original = tool_context.permission_engine.check

    def permission(scope, **kwargs):
        if scope == mod.WRITE:
            source.write_bytes(b"# World\nChanged while approving\n")
            return None
        return original(scope, **kwargs)

    monkeypatch.setattr(tool_context.permission_engine, "check", permission)
    with pytest.raises(ToolExecutionError, match="changed during approval"):
        mod.consolidate_inbox_apply(tool_context, args)
    assert target.read_bytes() == before


@pytest.mark.parametrize(
    "field,value",
    [
        ("source_file", "../escape.md"),
        ("target_file", "../escape.md"),
        ("source_file", "docs/target.md"),
        ("target_file", "inbox/new.md"),
        ("target_file", "docs/missing.md"),
        ("source_file", "docs/missing.md"),
    ],
)
def test_consolidation_path_rules(tool_context, field, value):
    args = prepare(tool_context)
    with pytest.raises((ValueError, SecurityError, FileNotFoundError)):
        mod.consolidate_inbox_preview(tool_context, {**args, field: value})


def test_search_escape_and_managed_target_protection(tool_context):
    with pytest.raises(SecurityError):
        mod.search_knowledge_index_sync(tool_context, {"query": "x", "target_dir": ".."})
    args = prepare(tool_context)
    write(tool_context.workspace_root, "_workspace/README.md", "Managed")
    with pytest.raises(ValueError, match="Managed"):
        mod.consolidate_inbox_preview(tool_context, {**args, "target_file": "_workspace/README.md"})
    tool_context.agent_id = "sol_engineer"
    with pytest.raises(PermissionDenied):
        mod.consolidate_inbox_preview(tool_context, args)


def test_async_wrappers_and_required_apply_fields(tool_context):
    args = prepare(tool_context)
    sync = mod.search_knowledge_index_sync(tool_context, {"query": "World"})
    assert asyncio.run(mod.search_knowledge_index("World", ctx=tool_context)) == sync
    assert asyncio.run(
        mod.consolidate_inbox_payload("inbox/new.md", "docs/target.md", ctx=tool_context)
    ) == mod.consolidate_inbox_preview(tool_context, args)
    with pytest.raises(ValueError, match="required"):
        asyncio.run(
            mod.consolidate_inbox_payload(
                "inbox/new.md", "docs/target.md", ctx=tool_context, apply=True
            )
        )
    for field in ("expected_source_sha256", "expected_target_sha256", "plan", "approval_id"):
        incomplete = {key: value for key, value in args.items() if key != field}
        with pytest.raises(ValueError):
            mod.consolidate_inbox_apply(tool_context, incomplete)


def test_schemas_and_capabilities():
    definitions = mod.indexing_tools()
    for definition in definitions:
        jsonschema.Draft202012Validator.check_schema(definition.parameters)
        assert not re.search(r"procedure|checklist|runbook", definition.description, re.IGNORECASE)
    schema = definitions[-1].parameters
    assert set(schema["required"]) == {
        "source_file",
        "target_file",
        "expected_source_sha256",
        "expected_target_sha256",
        "plan",
        "approval_id",
    }
    registry = build_tool_registry()
    assert registry.get("consolidate_inbox_apply").mutability
    assert len(registry.ollama_schemas(["search_knowledge_index"])) == 1


def test_performance_2000_markdown_files_no_nonmatch_parse(tool_context, monkeypatch):
    root = tool_context.workspace_root
    for number in range(2000):
        write(root, f"docs/{number:04}.md", "# Documentation\nNothing relevant here\n")
    monkeypatch.setattr(
        mod, "parse_markdown", lambda value: pytest.fail("Non-matching files parsed")
    )
    started = time.monotonic()
    result = mod.search_knowledge_index_sync(
        tool_context, {"query": "nonexistent-keyword", "target_dir": "docs"}
    )
    elapsed = time.monotonic() - started
    assert result["files_scanned"] == 2000 and result["complete"] and not result["results"]
    assert elapsed < 30, f"2,000-file search exceeded generous Windows smoke bound: {elapsed:.2f}s"
