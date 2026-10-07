# Runtime

`src/sol_lite/core/runtime.py` owns lifecycle, runtime roots, event bus and the background task manager.

Lifecycle states are created, starting, running, stopping, stopped and failed.

Runtime data is separate from the selected project workspace. The project workspace is session-scoped; runtime state lives under the application data root.
