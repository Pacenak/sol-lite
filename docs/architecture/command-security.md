# Command Security

Shell commands are classified rather than granted solely by executable name.

The guard considers shell, command structure, blocked patterns, mutation characteristics, Python `-c`/`-m` execution and Git destructive operations.

Read-only commands can use `terminal.read` when policy allows. Mutating commands require `terminal.write`. Destructive and nested shell operations are blocked by default.
