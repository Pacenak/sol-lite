# Testing Strategy

For the Personal Assistant Planner's embedded primitives, independent JSON/ICS validation and production adapter acceptance requirements, see the [planner testing runbook](personal-assistant-planner.md) and [recorded testing round](personal-assistant-planner-results.md).

Unit tests cover pure security/runtime behavior. Integration tests cover local filesystem and
runtime behavior. Battle tests cover traversal, symlink escape, destructive commands, approval
bypass, raw JSON tool syntax, repeated tools, maximum rounds and corrupted fault logs.

Ollama integration is opt-in with `SOL_RUN_OLLAMA_TESTS=1`.

Visual manifest routing, dependency-free asset validation and renderer acceptance use the [Visual skills test round](visual-agent-skills.md). It records automated results separately from actual browser/export inspection and release-pack gates.

Interns doing end-to-end manual validation should follow the [Intern Battle-Test Guide](battle-test-guide.md), which includes disposable test setup, expected safety behavior, optional integrations, and a defect-report template. Workspace answers, notes, proof-before-done, OS shells, remote hosts, and the terminal co-pilot use the [Competence and Terminal Co-Pilot Battle Guide](competence-terminal-battle-guide.md).


## Pack integrity audit

`python scripts/audit-pack.py` verifies required files, version consistency, generated-file hygiene and the SHA-256 build manifest without requiring third-party packages. `sol-lite battle-test` runs this audit before compilation, pytest and Ruff.
