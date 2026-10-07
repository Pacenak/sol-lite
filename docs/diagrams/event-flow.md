# Event Flow

```mermaid
flowchart LR
    Runtime --> EventBus
    EventBus --> Status
    EventBus --> Audit
    EventBus --> FutureUI
```
