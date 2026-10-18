# Workspace starter pack — Stage 1 implementation

**Outcome:** SOL-Lite's four standard agents share a deterministic, approved
workspace documentation pack, delivered as complete files in an extraction-ready overlay ZIP.

**Already true:** The user authorized the local SOL-Lite v0.2.6 checkout as the
authoritative source on 2026-10-19. Baseline commit:
`c6bfce4bb3a6b36de83e466882a824aaa6101b40`.
The working tree was clean at inspection. Its origin is the corporate
`plg-sol/PLG_Ai_Lite` repository. GitHub could not be reached, so equivalence to
GitHub main is not claimed. The supplied draft is a specification input;
its “awaiting spec approval” status does not override the user's implementation request.

**Not on this trip:** Stage 2 scheduling, background execution, session/workspace
state changes, voice, MCP, or integration changes. Schedule strings are stored only.

## Verified source contracts

- V1: `src/sol_lite/tools/notes.py` implements the existing content-only write
  signature. `memory/notes.py` stores notes at
  `<memory_root>/<sanitized workspace_id>/notes.md`. The pack imports the full
  UTF-8 file once per source path, preserving its original bytes.
- V2: `agents/registry.py` supplies role definitions, not tool lists. Actual
  allowlists are the four agent directories' `tools.yaml`, resolved by
  `agents/tool_allowlist.py`. Registration must change those YAML files.
- V3: `agents/task_fit.py` unions matching task classes and intersects the
  agent allowlist. Pack setup has its own class; status and shared logging
  support other tasks. Runtime continuation retains interview tools for short answers.
- V4: `skills/manager.py` automatically discovers top-level `skills/*/SKILL.md`
  as built-ins. The new skill follows existing YAML frontmatter and phrase
  conventions. The four agent prompts also carry the short always-on conventions.
- V5: `permissions/engine.py` accepts exact operation, target, arguments and
  plan bindings. A batch is one operation containing every proposed file,
  mode, content and previous digest. No permission engine extension is needed.
  Proposal contents survive the runtime approval callback and retry unchanged.
- V6: `tools/__init__.py` builds native definitions; `ToolDefinition` metadata
  generates capabilities and Ollama schemas. Handlers explicitly invoke the
  permission engine; registry metadata alone does not enforce approvals.
- V7: User documentation belongs under `docs/user/`; tests use pytest in
  `tests/unit` and `tests/integration`; Ruff uses `pyproject.toml` plus the
  installed configuration. The source-pack audit checks complete file inventory
  and SHA-256 hashes in `BUILD_MANIFEST.json`.

## Route

1. Add `src/sol_lite/workspace_pack/` for guarded reads, fixed intake,
   code-defined templates, append writers, PLAN parsing and index reconciliation.
   Verify preservation, ordering, skips, malformed input and path containment.
2. Add `tools/workspace_pack.py`, register its five tools, and replace the
   existing notes internals while preserving the tool name and content schema.
   Verify denied approval causes no writes, and approved retries use the same proposal.
3. Update four allowlists, task fit, permission-scope mapping, runtime proof
   tools and orientation. Remove legacy notes from the trusted shell system
   prompt. Verify INDEX precedes README and pack content remains reference data.
4. Add the built-in skill, role guidance, user documentation, regression tests
   and template golden files. Verify intake through real tool dispatch with
   a stubbed model; live Ollama remains a manual check.
5. Run compileall, targeted and complete pytest, Ruff, and the source-pack audit.
   Record pre-existing failures separately using baseline evidence. Build a
   clean source payload from tracked baseline files plus the complete changed
   files, regenerate its build manifest, and audit that exact extraction tree.
6. Create the overlay ZIP with root-relative paths, the full replacement
   files, installation guide, implementation report and checksums. Verify
   archive entries and hashes, and replay extraction onto the baseline.

## Resolved implementation details

- Templates are Python strings packaged with the module, avoiding external
  resource installation changes or runtime dependencies.
- Intake updates replace marked README regions only. Existing arbitrary
  READMEs without unambiguous markers remain intact and produce diagnostics.
- To honor append-only PLAN storage while alternating task/routine writes,
  append a `## Tasks` or `## Routines` heading whenever the active section
  changes. The parser supports repeated section headings and never rewrites
  existing entries. IDs reserve malformed existing four-digit IDs too.
- The unchanged notes signature has no content category. Preserve the complete
  supplied note in the README editing section and shared tip entries, quoting
  text so it cannot become pack structure. Split shared tips into at most five lines.
- A minimal notes-created pack contains README and CONVERSATIONS; full intake
  later refreshes only managed README sections and adds missing pack files.
- Approved multi-file batches are preflighted before any write. Filesystem
  failures during commit can still leave a partial batch; retry safely creates
  only missing files. This is not a cross-process transaction system.

## Ask before driving

None. The user authorized the local baseline and Stage 1 implementation.

## Done when

- Every added/edited file is listed in the delivery inventory and stored at
  its correct SOL-Lite-relative path, with complete contents rather than patches.
- The delivered overlay reproduces the tested source and passes the source
  audit after extraction onto the recorded baseline.
- Validation results and environment limitations are recorded accurately.
