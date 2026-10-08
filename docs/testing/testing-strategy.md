# Testing Strategy

Unit tests cover pure security/runtime behavior. Integration tests cover local filesystem and
runtime behavior. Battle tests cover traversal, symlink escape, destructive commands, approval
bypass, raw JSON tool syntax, repeated tools, maximum rounds and corrupted fault logs.

Ollama integration is opt-in with `SOL_RUN_OLLAMA_TESTS=1`.

Interns doing end-to-end manual validation should follow the [Intern Battle-Test Guide](battle-test-guide.md), which includes disposable test setup, expected safety behavior, optional integrations, and a defect-report template.


## Pack integrity audit

`python scripts/audit-pack.py` verifies required files, version consistency, generated-file hygiene and the SHA-256 build manifest without requiring third-party packages. `sol-lite battle-test` runs this audit before compilation, pytest and Ruff.
