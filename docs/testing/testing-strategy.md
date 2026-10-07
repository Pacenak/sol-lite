# Testing Strategy

Unit tests cover pure security/runtime behavior. Integration tests cover local filesystem and
runtime behavior. Battle tests cover traversal, symlink escape, destructive commands, approval
bypass, raw JSON tool syntax, repeated tools, maximum rounds and corrupted fault logs.

Ollama integration is opt-in with `SOL_RUN_OLLAMA_TESTS=1`.


## Pack integrity audit

`python scripts/audit-pack.py` verifies required files, version consistency, generated-file hygiene and the SHA-256 build manifest without requiring third-party packages. `sol-lite battle-test` runs this audit before compilation, pytest and Ruff.
