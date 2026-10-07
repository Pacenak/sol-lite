# Skill Flow

```mermaid
flowchart TD
    Source --> Discover --> Validate --> Scan --> Provenance --> Review
    Review -->|unsafe| Quarantine
    Review -->|approved| Install
    Install --> Assign
```
