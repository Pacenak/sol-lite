# SOL-Lite knowledge index and inbox consolidation

The implementation is already applied to the local SOL-Lite checkout where
this work was requested. Restart SOL-Lite to load the registered tools.
No new runtime dependency, credential, model or configuration is required.

The delivery ZIP is a cumulative overlay for the user-authorized local SOL-Lite
v0.2.6 baseline, Git commit `c6bfce4bb3a6b36de83e466882a824aaa6101b40`.
It includes the preceding workspace starter-pack integration because shared
replacement files already reference that module. Extracting this overlay
onto that baseline therefore does not leave missing starter-pack imports.
GitHub main could not be reached and is not claimed to match this baseline.

## Install into another checkout

1. Stop SOL-Lite and back up local changes. Check the replacement paths in
   `KNOWLEDGE_INDEX_FILES.json`; extraction replaces each named existing file.
2. Extract all ZIP contents into the SOL-Lite application base directory
   containing `pyproject.toml`, `src`, `skills`, `config` and `docs`. There is no
   enclosing folder in the archive. Do not extract into a selected user workspace.
3. Restart normally. Source/editable installations load the changed code;
   refresh a separate non-editable Python installation through its normal
   installation process if applicable.
4. Select a test workspace and ask “What does the doc say about …”. All agents
   can search. SOL PA and SOL Docs can preview/consolidate an inbox file into
   an existing Markdown target after the normal permission and approval checks.

The user guide is `docs/user/knowledge-index-consolidation.md`; the source
analysis and full route are in
`docs/superpowers/plans/2026-10-19-knowledge-index-consolidation.md`.
The supplied design is retained unchanged under `docs/design/`.

## Verify

Using the checkout's Python environment, run:

```powershell
.venv\Scripts\python.exe -m compileall -q src tests
.venv\Scripts\python.exe -m pytest -q tests/unit/test_indexing.py tests/integration/test_indexing_runtime.py
.venv\Scripts\python.exe scripts/audit-pack.py
```

On macOS/Linux use `.venv/bin/python`. Python's Windows asyncio event loop
needs a working internal localhost socket pair; a network-restricted sandbox
can hang before the async tests reach application code. These wrappers were
verified with that local event-loop facility available.

The repository has documented pre-existing test/lint failures. Its full-source
audit also reports an unchanged upstream security-training Markdown file that
Windows antivirus quarantined during the prior task. This overlay does not
restore or distribute that blocked file. Its expected provenance digest is
retained in the full source manifest, without claiming a passing audit.

`KNOWLEDGE_INDEX_FILES.json` describes this cumulative delivery and is the
current payload inventory. The earlier `WORKSPACE_STARTER_PACK_FILES.json`
remains the historical inventory for the previous ZIP; its shared-file hashes
are not a claim about this newer delivery. The full build manifest describes
the resulting source tree. Existing user workspace/inbox data is not included.

To undo the overlay, stop SOL-Lite, restore replaced files from your backup
and remove only paths marked as additions in the inventory. Preserve user
`_workspace`, `_project`, inbox and target documents unless explicitly removing
them yourself.
