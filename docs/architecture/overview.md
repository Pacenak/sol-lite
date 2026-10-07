# Architecture Overview

SOL-Lite separates presentation, runtime orchestration, agents, models, tools, permissions, skills, persistence and platform integration.

```mermaid
flowchart LR
    UI[Rich Terminal UI] --> SHELL[Agent Shell]
    SHELL --> SESSION[Session Manager]
    SESSION --> RUNTIME[Agent Runtime]
    RUNTIME --> MODEL[Model Manager]
    MODEL --> OLLAMA[Ollama]
    RUNTIME --> TOOLS[Tool Registry]
    TOOLS --> PERM[Permission Engine]
    PERM --> APPROVAL[Approval Manager]
    TOOLS --> PLATFORM[Platform Adapter]
    TOOLS --> FS[Filesystem/Search/Repository]
    RUNTIME --> EVENTS[Event Bus]
    EVENTS --> AUDIT[Audit/Fault/Status]
    RUNTIME --> TASKS[Background Task Manager]
    RUNTIME --> SKILLS[Skill Manager]
    SKILLS --> PROVENANCE[Validation/Provenance/Quarantine]
```

The runtime is intentionally independent of terminal-specific rendering.
