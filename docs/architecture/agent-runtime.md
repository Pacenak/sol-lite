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
    L -- No --> N{Tool-like ordinary text?}
    N -- No --> O[Fail: no tool call or response]
    N -- Yes --> P{Retry used?}
    P -- No --> Q[Ask for native tool format]
    Q --> C
    P -- Yes --> R[Fail: tool_call_not_native]
```

Raw JSON, `<function=...>` and `<tool_call>` are never interpreted as executable calls. If tool-like content appears in ordinary text, the runtime allows one bounded retry asking for a native structured call or a plain-text explanation. A repeated malformed response fails safely with `tool_call_not_native`. The normal repeat/progress, permission, and approval checks still govern valid native tool calls.
