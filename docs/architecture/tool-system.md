# Tool System

Tools are declared as `ToolDefinition` objects and registered in `ToolRegistry`. The registry supplies both native Ollama schemas and runtime execution.

A tool receives `ToolContext`, which includes session ID, workspace/project root, permission engine, audit logger, fault log, platform adapter and skill manager.
