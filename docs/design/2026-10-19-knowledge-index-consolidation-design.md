# Knowledge Index and Inbox Consolidation - Design

Date: 2026-10-19
Repo: Pacenak/sol-lite (v0.2.6)
Status: Draft for review (design approved in conversation, awaiting spec approval)
Related: `2026-10-19-workspace-starter-pack-design.md` (shares integration points)

## 1. Purpose

Give the PA (and `sol_docs`) two deterministic capabilities over a workspace's
markdown documentation:

1. **Exact retrieval.** Answer documentation questions by locating the Source of
   Truth (SOT) and returning the matching text verbatim, with file path, header,
   and exact line numbers. Never summarise, never answer from model memory.
2. **Non-destructive inbox consolidation.** Merge new material from an `inbox/`
   file into an existing target file without overwriting, omitting, or
   duplicating anything. On any conflict, stop and ask the user.

### Success criteria

1. Every search result's `lines` equal the file's exact lines at the reported
   line numbers (byte-for-byte after UTF-8 decoding, line terminators removed).
2. A search that finds nothing, or that was incomplete, says so explicitly and
   never implies absence.
3. A consolidation never changes, removes or reorders any existing target line.
4. With any conflict, nothing is written.
5. Re-running a consolidation after it was applied reports `no_changes`.
6. The tools follow SOL-Lite conventions: sync `(ctx, args)` handlers,
   `ToolDefinition` schemas, `resolve_workspace_path`, the permission engine and
   the audit log.

## 2. Decisions already made

| Topic | Decision |
|---|---|
| Build approach | Repo-native module with sync handlers and `ToolDefinition` schemas, plus async wrappers (the "best for SOL-Lite, performance and accuracy" option) |
| Location | `src/sol_lite/tools/indexing.py` (not `core/tools/`, which does not exist) |
| Async | Wrappers call the sync handlers through `asyncio.to_thread`; the dispatcher stays sync |
| "Semantic" search | Not deterministic, so not offered. Modes: `text`, `regex`, `header` |
| Inbox in search | Excluded by default (unconsolidated material is not SOT) |
| Persistent manifest | None in v1; bounded in-memory cache only |
| Conflict policy | Any conflict blocks the whole apply; nothing is written |
| Preview vs apply | Separate tools, because a JSON schema cannot make approval fields required only when applying |

## 3. Non-goals (v1)

- Embeddings or fuzzy semantic retrieval.
- Resolving conflicts automatically or accepting "additions only" while
  conflicts exist. The user edits the inbox file or decides; the agent re-runs
  the preview.
- Moving, archiving or deleting inbox files.
- Non-markdown files; setext (`===`/`---`) headers; HTML headers.
- Creating missing target files.
- A runtime guard that rejects paraphrased answers. The tool output and skill
  guidance carry the "quote verbatim" rule; a runtime check is a possible
  follow-up.

## 4. Architecture

`src/sol_lite/tools/indexing.py` has four layers.

1. **Pure core** (no `ctx`, no side effects beyond reading bytes it is given):
   `parse_markdown`, `search_documents`, `plan_merge`, `apply_merge_text`.
   Most tests target this layer.
2. **Sync handlers** `(ctx, args) -> dict`, in the style of `repository.py`.
3. **Async wrappers** with the requested names (section 8).
4. **`indexing_tools() -> list[ToolDefinition]`** returning
   `search_knowledge_index`, `consolidate_inbox_preview` and
   `consolidate_inbox_apply`.

Errors use the existing `ToolExecutionError`, `SecurityError` (via the path
guard) and `ValueError` for bad arguments. A per-file failure during search is
collected into `files_skipped`, never raised.

## 5. Markdown model

- Text is decoded as strict UTF-8. A leading BOM is preserved on write. A file
  that fails to decode is skipped with reason `not_utf8`; replacement
  characters are never used.
- Lines are split on `\r\n`, `\n` or `\r` only. `str.splitlines()` is not used.
  Line numbers are 1-based and inclusive. The line-ending style and whether the
  file ends with a newline are recorded for writing.
- Headers are ATX `#` to `######` followed by a space. Lines inside fenced code
  blocks (``` or ~~~) are never headers.
- A **section** runs from its header line to the line before the next header of
  the same or higher level, so it includes its subsections. A section's **own
  body** is its lines before its first subsection header. Text before the first
  header is the `(preamble)` section.
- `header_path` is the breadcrumb of header texts from the top level down.
- A fenced code block is one atomic unit during consolidation.

## 6. Search: `search_knowledge_index`

### 6.1 Arguments

| Name | Type | Default | Notes |
|---|---|---|---|
| `query` | string | required | Non-empty |
| `target_dir` | string | `"."` | Workspace-relative directory; resolved with `resolve_workspace_path(..., must_exist=True)`; must be a directory |
| `mode` | `text` / `regex` / `header` | `text` | |
| `match` | `all` / `any` | `all` | `text` mode: all or any whitespace-separated keywords on the same line |
| `case_sensitive` | bool | false | |
| `context_lines` | int 0-10 | 0 | Extra lines around a match; marked `match: false` |
| `max_results` | int 1-100 | 20 | |
| `max_block_lines` | int 1-400 | 80 | |
| `include_inbox` | bool | false | |

### 6.2 Behaviour

- **Walk.** `os.scandir`, pruning `.git`, `node_modules`, `.venv`, `venv`,
  `__pycache__` and (unless `include_inbox`) any directory named `inbox`.
  Directory and file symlinks are not followed and are reported as skipped
  (`symlink`). Only `.md` files are read. `_workspace/` is included.
- **Limits.** 2 MB per file (`too_large`), 5,000 files in total (excess counted
  as `file_limit`). Any skip sets `complete: false`.
- **Pre-check.** For `text` and `regex`, one pattern search on the whole decoded
  text decides whether the file is split into lines at all.
- **`text`.** Tokens are matched as case-insensitive substrings on one line;
  `match` decides all or any. **`regex`.** `re.compile`; an invalid pattern is a
  `ValueError`. A pattern is applied per line. **`header`.** The same matching is
  applied to header text only; the whole section is returned. When a parent and
  a child section both match, only the outermost is returned.
- **Blocks.** In `text` and `regex`, consecutive matching lines (plus context)
  merge into one block, and a block never crosses a section boundary. The block's
  `section_header` is the innermost header at its first line.
- **Order.** Sorted by path, then start line. Deterministic.
- **Cache.** A lock-protected LRU of 256 parsed documents keyed by
  `(realpath, mtime_ns, size)`. Search uses it; consolidation never does.

### 6.3 Result

```json
{
  "query": "...", "mode": "text", "target_dir": "docs",
  "results": [{
    "path": "docs/world/areas.md",
    "absolute_path": "/abs/docs/world/areas.md",
    "section_header": "## Area XYZ",
    "header_path": ["World", "Area XYZ"],
    "start_line": 45, "end_line": 52, "truncated": false,
    "lines": [{"n": 45, "text": "...", "match": true}],
    "verbatim": "line 45\nline 46\n...",
    "rendered": "**File Path:** docs/world/areas.md\n**Section Header:** ## Area XYZ\n**Lines:** 45-52\n**Verbatim Text:**\n```\n...\n```"
  }],
  "total_blocks": 3, "returned": 3,
  "files_scanned": 120,
  "files_skipped": [{"path": "x.md", "reason": "not_utf8"}],
  "inbox_files_excluded": 4,
  "complete": true,
  "notice": "Quote `rendered` verbatim. Do not summarise, reorder or add to it."
}
```

When `results` is empty the notice states that no match was found in
`files_scanned` files and, if `complete` is false, that the search was
incomplete and absence is not established. If a block is truncated by
`max_block_lines`, `truncated` is true and `end_line` is the last line returned.

## 7. Consolidation

### 7.1 Tools

| Tool | Scope | Arguments |
|---|---|---|
| `consolidate_inbox_preview` | read | `source_file`, `target_file`, `similarity_threshold` (0.5-1.0, default 0.85) |
| `consolidate_inbox_apply` | write, approval | the same, plus `expected_source_sha256`, `expected_target_sha256`, `plan`, `approval_id` (all required) |

### 7.2 Path rules

- Both paths are resolved with `resolve_workspace_path(..., must_exist=True)`.
- The source must have an `inbox` path component and be a `.md` file.
- The target must be an existing `.md` file with no `inbox` component. It is
  never created.
- Source and target must differ.

### 7.3 Algorithm (`plan_merge`)

Both files are read fresh as bytes, hashed (SHA-256 over the raw bytes), decoded
and parsed.

**Normalisation (comparison only; never written):** Unicode NFC, strip, collapse
whitespace runs to one space, casefold, and treat leading `-`, `*`, `+` bullet
markers as equal. Blank lines are ignored in comparisons.

**Section matching:** by normalised `header_path`. If either file has two
sections with the same normalised path, that path yields an
`ambiguous_header` conflict and is not merged.

**Per source line in a matched section's own body**, in order:

1. Normalised text equals a target own-body line (or, for a fenced block,
   the whole block) -> **duplicate**, skipped.
2. The line is **keyed**: `key: value` or `key = value` (optionally bulleted or
   bold key), or a table row keyed by its first cell where the target section
   also contains a table.
   - Key absent in the target section -> **addition**.
   - Key present with a different normalised line -> conflict `value_changed`.
   - Key repeated in the target section or repeated in the source with different
     values -> conflict `ambiguous_key`.
3. Otherwise, if its normalised length is at least 12 and its similarity to any
   target own-body line is at least `similarity_threshold` (cheap
   `quick_ratio` check first, then `ratio`) -> conflict `possible_edit`.
4. Otherwise -> **addition**.

False conflicts are the safe failure direction; a false merge is not. Prose with
a colon (for example `Note: ...`) may therefore be treated as keyed.

**Sections missing from the target:** added whole, with their headers.
Placement is after the last non-blank line of the parent's subtree when the
parent exists in the target (`under_parent`), otherwise at the end of the file
(`end_of_file`, flagged in the result).

**Placement of added lines in a matched section:** immediately after the last
non-blank line of the section's own body, or immediately after the header line
if the body is empty. Added lines keep their source text, including bullet
markers. Blank source lines between two added lines are carried over; leading
and trailing blanks are dropped. A new table row goes after the last row of the
last table in the section.

**Status:** `no_changes` (nothing to add, no conflicts), `ready` (additions
only), `needs_reconciliation` (at least one conflict).

### 7.4 Preview result

```json
{
  "status": "ready",
  "source_file": "inbox/new.md", "target_file": "docs/world.md",
  "source_sha256": "...", "target_sha256": "...", "merged_sha256": "...",
  "additions": [{"section_path": ["World","Area XYZ"], "placement": "end_of_section",
                 "source_lines": [12,13], "lines": ["- Iron key", "- Map"]}],
  "skipped_duplicates": {"count": 7, "examples": ["..."]},
  "conflicts": [{"kind": "value_changed", "section_path": ["World","Area XYZ"],
                 "source_line": 14, "source_text": "- Level: 5",
                 "target_line": 21, "target_text": "- Level: 3"}],
  "diff": "unified diff of target -> merged, truncated to 400 lines",
  "notice": "Conflicts block apply. Ask the user to reconcile."
}
```
`merged_sha256` is `null` when status is `needs_reconciliation`.

### 7.5 Apply

1. Recompute the plan from fresh bytes. Refuse if the source or target SHA-256
   differs from the expected values, or the status is not `ready`.
2. Call the permission engine with the write scope, `operation`
   `consolidate_inbox_apply`, the target path and the arguments, and `plan`
   and `approval_id`.
3. **Invariant check:** every original target line appears in the merged text,
   in the same order, with identical content. If not, abort with
   `ToolExecutionError`; nothing is written.
4. Write atomically: temp file in the target's directory, flush, fsync,
   `os.replace`. The target's line endings, BOM and trailing-newline state are
   preserved. A failure leaves the original untouched and removes the temp file.
5. Audit-log `indexing.consolidate_apply` with the paths, hashes and counts
   (never the content). Return the new SHA-256 and lines added.

The inbox file is never modified, moved or deleted.

## 8. Async wrappers

```python
async def search_knowledge_index(query: str, target_dir: str = ".", *, ctx,
    mode: str = "text", match: str = "all", case_sensitive: bool = False,
    context_lines: int = 0, max_results: int = 20, max_block_lines: int = 80,
    include_inbox: bool = False) -> dict: ...

async def consolidate_inbox_payload(source_file: str, target_file: str, *, ctx,
    apply: bool = False, similarity_threshold: float = 0.85,
    expected_source_sha256: str | None = None,
    expected_target_sha256: str | None = None,
    plan: str = "", approval_id: str | None = None) -> dict: ...
```
`ctx` is keyword-only because workspace-root enforcement needs it. Each wrapper
validates arguments identically to the sync handler and runs it through
`asyncio.to_thread`. `apply=True` routes to the apply handler and requires the
same approval fields.

## 9. Integration

- Register `indexing_tools()` wherever the other tool lists are aggregated.
- `task_fit.py`: new tasks for retrieval ("what does the doc say about",
  "list items in", "find in the docs") and consolidation ("consolidate inbox",
  "merge inbox"), so the tools are offered.
- Agent registry: all three tools for `sol_pa` and `sol_docs`; the search tool
  for the other agents.
- `agents/runtime.py`: add `consolidate_inbox_apply` to the proof-of-change tool
  set, as for the starter-pack tools.
- A short built-in skill note: quote `rendered` verbatim; on
  `needs_reconciliation`, show the conflicts and ask the user; after a
  successful apply, log it with `workspace_pack_append` when a pack exists.
- Tool descriptions avoid the words "procedure", "checklist" and "runbook".

## 10. Testing

- **Parser:** fences containing `#` lines, CRLF and mixed line endings, BOM,
  preamble, duplicate header paths, no trailing newline, non-UTF-8.
- **Search:** each mode; `all` vs `any`; context lines; block merging and
  section-boundary splitting; header mode with nested matches; caps and
  truncation flags; inbox exclusion and `include_inbox`; symlinks skipped; size
  and file limits setting `complete: false`; deterministic ordering; and, for
  every result, `lines` equal to the file's exact lines at the reported numbers.
- **Merge:** additions, duplicates, `value_changed`, `possible_edit`,
  `ambiguous_key`, `ambiguous_header`, table rows, fenced blocks as atoms,
  missing section with and without parent, blank-line carry-over, idempotency
  (second run -> `no_changes`), conflict blocks apply, stale hashes refused,
  invariant check tripping on a deliberately corrupted merge, atomic write
  failure leaves the original untouched, line-ending and BOM preservation.
- **Safety:** path escapes for every path argument, source outside `inbox`,
  target inside `inbox`, source equal to target, missing target.
- **Async wrappers:** run through `asyncio.run`, results equal to the sync
  handlers, approval fields enforced on apply.
- **Schemas:** each `ToolDefinition` schema is valid JSON Schema; required
  fields match section 7.1.
- **Performance smoke:** about 2,000 markdown files, bounded wall time and
  confirmation that non-matching files are not line-split.
- **Repo checks:** `compileall`, `pytest -q`, `ruff check src tests`,
  `scripts/audit-pack.py`.

## 11. Verification items before implementation

These files were not readable during brainstorming. The implementation plan
starts by reading them and recording the result.

| # | Item | Fallback if it differs |
|---|---|---|
| V1 | `permissions/scopes.py`: correct read and write scope for workspace files | Add `WORKSPACE_READ` / `WORKSPACE_WRITE` equivalents following the existing naming |
| V2 | `tools/base.py`: `ToolDefinition` fields and conventions | Follow an existing tool module |
| V3 | Where tool lists are aggregated and how `ollama_schemas` filters them | Register in the same place as `repository_tools()` |
| V4 | `mcp/server.py`: how registered tools are exposed over MCP | If tools are exposed from the registry automatically, no work; otherwise add them in the same way as existing tools |
| V5 | Existing `read_workspace_file`, `inventory_workspace` and notes tools | Reuse their helpers; do not duplicate behaviour |
| V6 | `task_fit.py` and the agent registry formats | Add entries in the existing style |
| V7 | Repo conventions: `docs/user`, `tests/`, `CHANGELOG.md`, ruff config | Follow existing patterns |
