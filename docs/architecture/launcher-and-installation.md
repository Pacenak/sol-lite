# Launcher and Installation Architecture

The launcher is deliberately thin. It locates the already-installed runtime and invokes the existing venv Python directly.

```mermaid
flowchart TD
    A[Windows SOL-Lite.cmd / macOS SOL-Lite.app] --> B[Locate installation root]
    B --> C{Existing .venv Python?}
    C -- No --> D[Stop with install/repair instruction]
    C -- Yes --> E[python -m sol_lite start]
    E --> F[Runtime bootstrap]
```

Installation and repair are separate from daily startup. This prevents repeated setup work and reduces the chance of modifying the environment during normal use.
