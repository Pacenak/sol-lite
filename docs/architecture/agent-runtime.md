# Agent Runtime

The agent loop sends the current conversation and native Ollama tool schemas to the configured model provider.

```mermaid
flowchart TD
    A[User task] --> B[Build session system context]
    B --> C[Send model request + native tool schemas]
    C --> D{Native tool calls?}
    D -- Yes --> E[Normalize call]
    E --> F[Repeat/progress guard]
    F --> G[Permission check]
    G --> H{Approval required?}
    H -- Yes --> I[Human approval]
    I --> J[Execute exact operation]
    H -- No --> J
    J --> K[Append tool evidence]
    K --> C
    D -- No --> L{Final content?}
    L -- Yes --> M[Complete]
    L -- No --> N[Fail: no tool call or response]
    C --> O{Tool-like ordinary text?}
    O -- Yes --> P[Fail: tool_call_not_native]
```

Raw JSON, `<function=...>` and `<tool_call>` are never interpreted as executable calls.
