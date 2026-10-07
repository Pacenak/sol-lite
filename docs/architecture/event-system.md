# Event System

Important runtime transitions use structured events such as:

`agent.started`, `agent.thinking`, `model.waiting`, `model.responded`, `tool.requested`, `tool.started`, `tool.completed`, `tool.rejected`, `approval.requested`, `approval.granted`, `approval.denied`, `agent.completed`, `agent.failed`, `agent.cancelled`, `agent.stalled`.

The terminal UI consumes state; the runtime does not print terminal-specific status heartbeat lines.


The `AgentRuntime` publishes the agent/model/tool/approval lifecycle events through the runtime event bus. The event bus is observational: terminal presentation remains in `TerminalUI`, while runtime logic emits structured event data. Event consumers must not be treated as permission authorities.
