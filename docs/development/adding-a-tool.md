# Adding a Tool

1. Define a `ToolDefinition`.
2. Validate all arguments.
3. Use `ToolContext` rather than global workspace state.
4. Enforce the required permission scope.
5. Use path containment for workspace filesystem access.
6. Audit successful and rejected operations.
7. Add unit and adversarial tests.
8. Ensure the Ollama schema accurately describes the tool.
