# Workspace Failures

Use `/workspace` and `runtime_get_context` to verify the session boundary.

For filesystem operations, verify normalized real paths and containment. If the model reports a path different from runtime context, runtime context is authoritative.
