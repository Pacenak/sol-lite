# Knowledge index and inbox consolidation

**Outcome:** Native SOL-Lite tools return exact Markdown citations and apply
conflict-free inbox additions without changing existing target lines.

**Already true:** The user-authorized local v0.2.6 checkout includes the workspace
starter pack. GitHub remains unreachable (DNS/cache fetch failure), so remote
main equivalence is not asserted. Existing changes are retained. The supplied
design is specification input, not an independent source of agent authority.

**Not on this trip:** Semantic search, generated answers from model memory,
automatic reconciliation, source deletion, missing target creation, scheduler
integration, or a runtime paraphrase detector.

## Verified source contracts

- V1: `permissions/scopes.py` defines `READ=filesystem.read` and
  `WRITE=filesystem.write`. Handlers must invoke the permission engine explicitly.
- V2: `tools/base.py` defines sync handlers, schemas, permissions, risk and
  mutability metadata. New tools use these existing fields without extension.
- V3: `tools/__init__.py` aggregates native definitions. The registry builds
  capabilities and filters Ollama schemas by permitted names.
- V4: `mcp/server.py` exposes the capability registry through its existing risk,
  allowlist and authorization policy. No separate MCP registration or policy
  broadening is needed; deployments must explicitly allow mutation when desired.
- V5: Filesystem tools normalize newlines through `read_text`, which cannot
  preserve this design's exact physical lines. Reuse the same path guard,
  permission scopes and audit interface, but read raw bytes in the new module.
  Existing inventory/notes behavior is retained; pack logging remains a separate
  approved call after a successful consolidation.
- V6: Tool access is declared in six agent `tools.yaml` files, not the role
  registry. PA and Docs receive all three tools; other agents receive search.
  `task_fit.py` unions matching tasks and intersects those allowlists.
- V7: User guides, pytest tests, CHANGELOG and Ruff follow the existing tree.
  Full source auditing already has one antivirus-quarantined baseline document;
  its existing recorded provenance digest is preserved without restoring it.

## Route

1. Add `tools/indexing.py`: pure physical-line/fence/section parsing and
   deterministic search, followed by a bounded lock-protected parse cache and
   contained filesystem search. Test exact lines and all scope/cap notices.
2. Implement pure merge planning, keyed/table/fence conflicts, placement and
   byte-preserving assembly. Verify idempotence and preservation of original
   target content/order, BOM, mixed endings and trailing-newline state.
3. Add sync preview/apply handlers and async wrappers. Bind fresh source/target
   hashes to approval, recheck after approval, and atomically replace only the
   existing target. Test denied approvals, stale input and write failures.
4. Register the tools, update agent allowlists, task routing, approval-scope
   mapping and runtime change evidence; add the built-in knowledge skill.
   Verify registry schemas, MCP policy metadata and scripted runtime dispatch.
5. Add operator documentation, the unchanged supplied design and validation
   evidence. Run focused tests, performance smoke, compileall, full pytest,
   Ruff and the source audit; distinguish baseline/environment failures.
6. Create a complete root-relative overlay with installation guidance, per-file
   before/after hashes and the full implementation plan. Keep the previous
   starter-pack ZIP unchanged. Verify every delivered byte after extraction.

## Decisions and edge contracts

- Existing local authorization is retained; no remote revision is guessed.
- Apply requires every schema field. An empty `approval_id` string requests
  approval through the existing engine; it is never an approval grant. The
  runtime retries with the actual granted ID. The caller must supply a real
  nonempty plan and both preview hashes.
- Arbitrary Python regex anchors/lookarounds can make a whole-file precheck
  unsound for per-line matching. Such expressions use a conservative positive
  precheck; exact matching is still per physical line. Simple patterns and text
  queries eliminate nonmatching files before parsing.
- Excluded inbox trees are not searched/read. A separate metadata-only count
  computes `inbox_files_excluded` without following links. Explicit exclusions
  do not imply incomplete search; skipped eligible files and output caps do.
- Original physical line terminators remain attached to original target lines;
  new lines use the target's first recorded ending (LF for an empty file).
  Appending to an unterminated last line necessarily adds a separator; the final
  file retains the original trailing-newline state.
- `no_changes` is an apply refusal/no-op with `applied: false`, not a mutation.
  Conflicts and stale hashes are refused without writing. Managed pack files
  retain their established append-only/marked-section contracts and are not
  generic consolidation targets.

## Ask before driving

None. Implementation and file creation are explicitly requested.

## Done when

- Exact citations, every conflict family, stale/denied approvals and atomic
  failure behavior have direct tests, including a 2,000-document smoke test.
- Complete added/edited files are applied locally and listed at their correct
  SOL-Lite-relative paths; delivery limitations are stated rather than hidden.
