# Adding an Agent

1. Add the agent definition to `config/agents.yaml`.
2. Add its prompt under `src/sol_lite/agents/<agent>/prompt.md`.
3. Add tools metadata if required.
4. Define delegation explicitly.
5. Assign relevant skills rather than granting broad capabilities.
6. Add unit tests for registry and runtime behaviour.
7. Run compileall, pytest and Ruff.
