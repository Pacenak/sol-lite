# Sessions and Workspaces

```mermaid
flowchart TD
    S[SOL-Lite] --> M[Session Manager]
    M --> A[Session A]
    M --> B[Session B]
    M --> C[Session C]
    A --> WA[Workspace A]
    B --> WB[Workspace B]
    C --> WC[Workspace C]
    A --> CA[ToolContext A]
    B --> CB[ToolContext B]
    C --> CC[ToolContext C]
```

Each session gets an immutable-in-operation workspace boundary. A new workspace is selected when creating a new session rather than silently changing an active operation's root.
