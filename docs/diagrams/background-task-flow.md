# Background Task Flow

```mermaid
flowchart TD
    A[/background prompt] --> B[Create independent session]
    B --> C[Submit bounded task]
    C --> D[Worker thread]
    D --> E[Agent runtime]
    E --> F[Retain result/error/status]
    F --> G[/tasks]
```
