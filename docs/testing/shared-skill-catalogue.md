# Shared catalogue acceptance — 2026-10-18

Release `2026.10.18.1` contains 15 native SOL procedures with reviewed evidence
from 11 pinned source repositories, plus reference/discovery/deferred entries.
Both exports contain identical release files and the same contract implementation.
Original evidence and licence notices are not loaded as executable procedures.

The contract tests cover schema/version rejection, duplicate identities, altered
package/evidence content, path traversal, explicit/phrase routing, selection
limits, missing tools, optional activation, role/sector filtering, owner privacy,
reference access and managed install/update/rollback with local edits preserved.
These are deterministic integrity/adapter checks, not model-quality benchmarks.

The engineering pilot uses `scripts/smoke-skill-harness.py`. It gives the model a
broken addition function, requests a new doubling function using the existing
public signature, permits real workspace reads/edits, and permits only the fixed
terminal command `python checks.py`. The checks cannot be edited by the model.
An independent process reruns the checks after the turn to verify the files.
The scripted provider exercises the real registry, filesystem and terminal path;
it is explicitly distinguished from a live model run.

The installed local model was `qwen3-coder:30b` (Ollama inventory ID
`06c1097efce0`). The final matched control/curated run completed cleanly in both
modes: six model rounds, five native tool calls, zero tool failures, successful
independent checks and no runtime stop reason. Control took 20.08 seconds with
20,720 aggregate prompt tokens; curated took 22.19 seconds with 31,474 aggregate
prompt tokens and 6,937 characters of skill context. This single fixture does
not demonstrate a general reliability or efficiency improvement.

Earlier trials are retained in `shared-skill-acceptance-results.json`:

- The first curated trial repaired the files but exhausted the deliberately
  small eight-round budget. It attempted a redundant echo command, which the
  fixture denied; it did not produce a successful final completion state.
- The second guessed `tests/checks.py`, then requested read-only browsing tools
  excluded from that fixture. It stopped with `tool_not_allowed`; independent
  checks failed. This is a failed trial, not a passing workflow.
- The fixture was corrected to expose SOL Engineer's normal read-only browsing
  tools. The procedure now emphasizes exact supplied paths. Prompts clarify that
  Python is a command rather than a shell and that echoing success is not a test.
  The final trial then completed in both modes. These changed conditions mean
  the earlier attempts must not be pooled into a comparative success-rate claim.

Lite runtime checks also keep skill material out of trusted system policy,
exclude quarantined skills, reject unsafe imported identifiers, require command
evidence for passing-test claims, and invalidate completion evidence after a
subsequent failed write/validation operation. These checks cannot detect every
possible misleading natural-language claim.

The live comparison used the shared working tree while a separate upstream
ecosystem integration was being developed concurrently. Final regression suites
run from isolated copies of this chat's exact staged versions, so unrelated
working-tree changes cannot silently become part of the local commits.

Full's native library, sector pins, admin-only installation API and routing are
covered by deterministic tests. No live Full provider run, engine build,
accounting posting, scientific workload or external service is certified by this
report. Optional dependencies remain uninstalled unless separately selected.

The broad Full regression selection also exposed existing privilege-fixture and
untracked runtime-data failures in the clean snapshot; the unchanged-HEAD
comparison and final suite outcomes are recorded with the acceptance results.
They must not be represented as a clean full-product test pass.
