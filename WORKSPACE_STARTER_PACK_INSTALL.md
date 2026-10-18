# SOL-Lite workspace starter pack — Stage 1 overlay

Built for SOL-Lite v0.2.6 at baseline commit
`c6bfce4bb3a6b36de83e466882a824aaa6101b40` from the user-authorized local checkout.
This ZIP contains complete added and updated files. It is an overlay, not a
standalone SOL-Lite distribution. Every archive entry is relative to the
SOL-Lite application base directory; there is no extra enclosing directory.

## Install

1. Stop SOL-Lite. Back up your local checkout, especially any locally edited
   files named in `WORKSPACE_STARTER_PACK_FILES.json`. Extraction replaces those
   files. Compare the recorded `before_sha256` values if your checkout has diverged.
2. Open the ZIP and extract **all** its contents into the SOL-Lite base directory
   containing `pyproject.toml`, `src`, `skills`, `config` and `docs`. Allow replacement
   of the named existing files. Do not extract it into a selected user workspace
   or into `src` itself.
3. Start SOL-Lite normally. There are no new runtime dependencies and no
   configuration, credential, database or model changes. A normal source-based
   SOL-Lite installation picks up the files; a separately copied/non-editable
   Python installation must be refreshed through its normal installation process.
4. Select a test workspace. Ask SOL PA: “Set up the workspace starter pack.”
   Answer the seven questions one at a time, or explicitly skip. Review any
   filesystem approval request. The final files appear under that workspace's
   `_workspace` folder, not in the SOL-Lite application directory.

Stage 1 stores schedules in PLAN but never executes them. Do not expect
background tasks or reminders to be registered from this pack.

## Verify

From the SOL-Lite base directory, using its Python environment:

```powershell
.venv\Scripts\python.exe -m compileall -q src tests
.venv\Scripts\python.exe -m pytest -q tests/unit/test_workspace_pack.py tests/integration/test_workspace_pack_runtime.py
.venv\Scripts\python.exe scripts/audit-pack.py
```

On macOS/Linux, use `.venv/bin/python` with the same arguments.
The full repository suite has known baseline failures in this environment;
see `docs/testing/workspace-starter-pack-validation.md` for actual results
and baseline comparison. A passing package audit verifies source inventory and
hashes; it does not prove that a local Ollama model behaves correctly.

During delivery verification, Windows antivirus blocked/quarantined an
unchanged upstream security-training Markdown file in the existing repository.
That file is not part of this overlay and has not been restored or redistributed.
The full-source manifest retains its recorded provenance digest; the full
source audit remains blocked until the baseline file is accessible through
your normal host security process. See the inventory's `host_blocked_baseline_files`
and the delivery receipt. Every file actually delivered in this ZIP was readable,
directly hashed, and verified after extraction.

The replacement `BUILD_MANIFEST.json` describes the complete expected source
tree after applying this overlay to the recorded baseline. Unrelated local
source edits or extra source files may make that audit fail and require a
reviewed reconciliation. The `.work` scratch directory is excluded from source
audits and is not distributed in this ZIP.

## Included references

- `WORKSPACE_STARTER_PACK_FILES.json`: every delivered path, added/replaced
  classification, original digest where applicable, and delivered digest.
  That inventory and BUILD_MANIFEST are listed as metadata exclusions to avoid
  circular self-hashes. BUILD_MANIFEST independently hashes the inventory.
- `docs/superpowers/plans/2026-10-19-workspace-starter-pack.md`: verified source
  contracts and implementation route.
- `docs/user/workspace-starter-pack.md`: operator guide and file contracts.
- `docs/testing/workspace-starter-pack-validation.md`: validation results and
  the complete integration file map.
- `docs/design/2026-10-19-workspace-starter-pack-design.md`: unchanged supplied
  Stage 1 design, retained as specification input.

To undo the overlay, stop SOL-Lite and restore the replaced application files
from your backup; remove only the newly added paths listed in the inventory.
Workspace `_workspace` and `_project` documentation is user data and should
be retained unless you explicitly choose to remove it.
