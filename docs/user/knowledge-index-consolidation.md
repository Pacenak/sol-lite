# Exact knowledge retrieval and inbox consolidation

These tools operate on Markdown files inside the selected workspace. They
do not use embeddings, model memory or fuzzy semantic retrieval. They do not
move, archive or delete inbox files, and never create a missing target.

## Ask a documentation question

Ask any agent “What does the doc say about …”, “Find in the docs …”, or
“List items in …”. `search_knowledge_index` returns source text with a
workspace-relative path, absolute path, header breadcrumb and inclusive
one-based line numbers. The agent should quote the selected `rendered` text
verbatim. There is no runtime paraphrase detector in this version: the tool
guarantees exact output, while the skill directs how the model presents it.

The search accepts:

- `query`: required nonblank text.
- `target_dir`: workspace-relative directory, default `.`. Use `docs` or
  another narrow directory for large repositories.
- `mode`: `text` (default), `regex`, or `header`.
- `match`: `all` (default) or `any` whitespace-separated keywords on one line.
  Header mode applies these keywords to the header text rather than its body.
- `case_sensitive`: false by default. Text matching uses Unicode casefolding.
- `context_lines`: 0–10, default 0. Context lines have `match: false`.
- `max_results`: 1–100, default 20; `max_block_lines`: 1–400, default 80.
- `include_inbox`: false by default. Unconsolidated inbox content is not SOT.

ATX headings and backtick/tilde fences are understood. Setext and HTML
headings are ordinary text. A header search returns its entire subtree,
subject to the block cap; matching nested headers do not duplicate the outer
result. Text/regex blocks merge adjacent matches and context within a section,
never across the next header boundary. Returned citation lines retain their
exact decoded content, including tabs, Unicode separators and any leading
BOM; physical line boundaries are CRLF, LF or CR only.

Traversal skips `.git`, `node_modules`, `.venv`, `venv` and `__pycache__`.
Workspace-pack documentation is searchable. Links are not followed and are
reported as skipped. Strict UTF-8 decoding, a 2 MiB per-file limit and a
5,000-file read limit bound eligible input. A metadata-only walk counts
excluded inbox Markdown without reading its contents. A 256-document LRU
cache is in memory only and keyed by real path, modification time and size.

Read `complete`, `files_skipped`, `total_blocks`, `returned` and each block's
`truncated` flag. Skips and output caps make `complete` false. An empty result
only means no match was found among the eligible files actually scanned;
an incomplete search never establishes absence. Complex regex anchors and
lookarounds use a conservative positive file precheck so a per-line match
cannot be silently missed.

## Preview inbox additions

Only SOL PA and SOL Docs receive consolidation tools. Put new Markdown in
an `inbox` subfolder and select an existing Markdown target outside every
`inbox` folder. Ask “Consolidate inbox … into …” or “Merge inbox …”. The agent
first calls `consolidate_inbox_preview` with `source_file`, `target_file`, and
optionally `similarity_threshold` from 0.5 to 1.0 (default 0.85).

The result is `ready`, `no_changes`, or `needs_reconciliation`. It includes
raw source/target SHA-256 values, additions with source line numbers,
duplicate counts/examples, conflicts, and a target-to-merged diff capped at
400 lines. A conflict produces no merged hash and blocks the entire apply.
Reconcile the source with the user, then preview again; never accept just the
nonconflicting additions while conflicts remain.

Comparison uses Unicode NFC, casefolding and collapsed whitespace; leading
`-`, `*` and `+` bullets compare equally. These comparison forms are never
written. Sections match by normalized header breadcrumbs. Duplicate paths
are `ambiguous_header` conflicts. In matched own bodies, exact normalized
duplicates are skipped. Key/value and table-key changes conflict; repeated
ambiguous keys conflict. Similar non-keyed text of at least 12 normalized
characters may produce `possible_edit`. An unclosed fence conservatively
blocks merging because its atomic boundary is not known.

Added own-body text goes after existing own-body content, before children.
New table rows go after the last row of the last actual table. Missing
sections are inserted after an existing parent's subtree or flagged as
`end_of_file` additions. Source order and blank lines between consecutive
added items are retained; leading/trailing blank-only additions are dropped.
Fenced code is compared and added atomically. Existing target lines are never
removed, edited or reordered.

## Approve and apply

`consolidate_inbox_apply` requires both paths, both preview hashes, a concrete
`plan` and `approval_id`. For a first request the agent supplies the empty
string `approval_id: ""`; that requests the ordinary permission-engine
approval. It never grants permission. The runtime retries with the actual
approved ID. The source/target hashes bind approval to the reviewed bytes.

Apply reads both files fresh, refuses stale hashes/conflicts, checks the
preservation invariant, and rechecks paths and bytes after approval and
immediately before replacement. It stages in the target directory, flushes
and fsyncs, then uses atomic replacement. Failed staging/replacement retains
the target and removes only this operation's temporary file. The inbox is
untouched. Audit records contain paths, hashes and counts, never document text.

Original target line endings are retained individually, including mixed styles.
New lines use the target's first recorded style, or LF for an empty target.
The target BOM and final-newline state are retained. A BOM is encoding metadata:
when prepending content it remains at the start rather than moving into the
middle of the file. Appending to an unterminated last line adds the necessary
separator while keeping the final merged file unterminated.

Re-preview after apply returns `no_changes`. Applying a fresh `no_changes`
preview is a no-op (`applied: false`) and never evidence of a mutation.
After successful apply, the agent logs the change through
`workspace_pack_append` when a pack exists; that is a separate approval.
Managed `_workspace` and `_project` files remain governed by their existing
pack contracts and must be changed with the pack tools.

In-process applies are serialized. External editors and other processes do
not participate in that lock; avoid concurrent edits while applying. The
hash rechecks are not a cross-process compare-and-swap storage service.

## Python and MCP

The dispatcher uses the sync `search_knowledge_index_sync`,
`consolidate_inbox_preview` and `consolidate_inbox_apply` handlers. Python
callers may use `await search_knowledge_index(query, ..., ctx=ctx)` or
`await consolidate_inbox_payload(source, target, ..., ctx=ctx)`. Wrappers use
`asyncio.to_thread` and enforce the same validation, paths and approvals.

MCP sees the same registered capabilities. Search and preview are read-only;
apply is mutating and is not exposed under the default read-only risk policy.
Explicit deployment authorization, risk allowance and the filesystem approval
engine still apply. MCP consolidation context must identify SOL PA or SOL Docs.
The skill and document contents cannot broaden any permission.
