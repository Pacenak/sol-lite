# Workspace Flow

```mermaid
flowchart TD
    A[Chat start] --> B[Select workspace]
    B --> C[Normalize real path]
    C --> D[Register workspace]
    D --> E[Create session]
    E --> F[Session ToolContext]
```
