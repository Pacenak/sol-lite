# First Run and Workspace Selection

A workspace is selected for each chat/session. There is no permanent global active workspace.

## First launch

Starting without `--workspace` presents recent workspaces when available, followed by a new workspace path prompt.

```text
Recent workspaces:
  [1] RedEcho — E:\git\RedEcho
  [2] SOL-Lite — E:\git\plg-sol\PLG_Ai_Lite
  [n] New workspace
Workspace ❯
```

The selected path is normalized with real-path resolution and becomes the session's filesystem boundary.

## Explicit workspace

```powershell
sol-lite start --workspace E:\git\project
```

```bash
sol-lite start --workspace /Users/name/Developer/project
```

## Multiple sessions

Use `/new` to start another independent chat and select another workspace. Session-specific tool context, status and skills are kept separate.

```mermaid
flowchart TD
    A[Start SOL-Lite] --> B{Workspace supplied?}
    B -- Yes --> C[Normalize and register workspace]
    B -- No --> D[Show recent workspaces]
    D --> E[User selects existing or enters new path]
    E --> C
    C --> F[Create session]
    F --> G[Create session-scoped ToolContext]
    G --> H[Start agent chat]
    H --> I{Need another project?}
    I -- Yes --> J[/new]
    J --> D
    I -- No --> K[Continue current session]
```
