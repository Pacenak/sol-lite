# Shell Security

Shell access is explicit and platform-aware.

```mermaid
flowchart TD
    A[Requested shell + command] --> B[Detect shell]
    B --> C{Shell available?}
    C -- No --> D[Reject]
    C -- Yes --> E[Classify command]
    E --> F{Blocked/destructive/nested?}
    F -- Yes --> G[Reject]
    F -- No --> H{Mutation?}
    H -- No --> I[terminal.read policy]
    H -- Yes --> J[terminal.write + exact approval]
    I --> K[Execute explicit shell]
    J --> K
```

The runtime does not silently replace an unavailable explicitly requested shell with another shell.


Compound shell syntax (`;`, `&&`, `||`, pipes and input/output redirection) requires approval rather than being treated as independently safe. This is intentional: SOL-Lite does not claim to perform a complete shell-language security proof across CMD, PowerShell, zsh and Bash.

The same blocked-command list applies to `remote_execute`. A production node, or a node with no `environment`, accepts a read and rejects a write before SSH starts. Staff setup for hosts, secrets, and backups is [Studio change gate](../user/studio-change.md).
