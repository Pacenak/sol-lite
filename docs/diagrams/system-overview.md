# System Overview Diagram

```mermaid
flowchart LR
    User --> Terminal
    Terminal --> Session
    Session --> Agent
    Agent --> Model
    Agent --> ToolRegistry
    ToolRegistry --> Permissions
    ToolRegistry --> Platform
    Permissions --> Approval
    Agent --> Skills
    Agent --> Tasks
    Agent --> Events
    Events --> Audit
```
