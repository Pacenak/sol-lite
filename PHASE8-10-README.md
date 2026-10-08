# SOL-Lite AAA Phases 8–10

This package is an architecture tranche, not a replacement for the entire SOL-Lite repository.

It contains the Phase 1–7 architecture artifacts previously generated plus the Phase 8–10 integration replacements:

- native `ToolDefinition` capability metadata and conversion
- capability-backed native tool registry while retaining the existing `register/get/names/execute/ollama_schemas` API
- execution-context binding of session, agent, capability and risk into permission checks
- expiring, exact approval records bound to session/agent/capability/risk
- task-scoped session resource IDs
- OS credential-manager boundary using the established Python `keyring` interface
- unit tests for the new contracts

## Important integration rule

Apply these files to the current SOL-Lite repository after the Phase 1–7 architecture files. Do not copy this package over the repository wholesale: the package deliberately does not contain unrelated application files.

The existing tool handlers remain responsible for their operation-specific permission checks. `ToolRegistry.execute()` establishes the execution identity around those handlers so the existing checks receive the correct session/agent/capability/risk context automatically.

`KeyringBackend` is intentionally an adapter boundary. Installing the `keyring` package is required before using OS credential storage. Secrets are resolved only by the credential manager and are not part of model messages, tool schemas, or approval display data.

## Validation performed in this package

`PYTHONPATH=src python -m pytest -q tests/unit/test_phase8_10.py` -> 4 passed.

`PYTHONPATH=src python -m compileall -q src tests` -> passed.

The full repository Ruff/battle suite was not claimed here because this generated architecture package is not a complete checkout of the user's repository and the execution environment does not contain the project's Windows virtual environment.
