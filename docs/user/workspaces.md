# Workspaces

Workspaces are hard boundaries for filesystem and shell operations.

The runtime normalizes workspace paths and uses containment checks before filesystem access. Agents receive the authoritative workspace path through `runtime_get_context`.

Useful commands:

```text
/workspace
/workspaces
/new
```

Different sessions can point at different repositories and operate concurrently.
