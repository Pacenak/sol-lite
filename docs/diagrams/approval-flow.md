# Approval Flow

```mermaid
flowchart TD
    A[Operation] --> B[Build exact approval request]
    B --> C[Human review]
    C -->|Approve| D[Consume approval]
    C -->|Deny| E[Reject]
    D --> F[Execute]
```
