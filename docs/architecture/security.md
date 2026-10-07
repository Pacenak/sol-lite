# Security

Workspace containment uses canonical paths and `os.path.commonpath`; string-prefix checks are not
used.

Writes and shell execution require operation-specific approval bound to operation, target, arguments
and plan hash.

Repository mutations (branch creation, checkout, staging, commits, bundle/patch creation, bundle
import/merge, patch application and local cloning) require the repository-write scope and exact
approval. Remote clone, remote configuration, fetch and push require the repository-remote scope,
which is disabled by default.

Git commands in the repository layer are executed directly with argument vectors rather than through
a shell. Remote URLs returned to the model/operator are credential-redacted. The implementation does
not place credentials into audit records intentionally.

Deletion is disabled by default. Destructive terminal commands are blocked.

Only native structured Ollama tool calls are executable. Tool-shaped JSON appearing in ordinary
assistant content is never executed.
