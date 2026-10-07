"""Tool registry."""
class ToolRegistry:
    def __init__(self):
        self._tools = {}

    def register(self, tool):
        if tool.name in self._tools:
            raise ValueError(f"Duplicate tool: {tool.name}")
        self._tools[tool.name] = tool

    def get(self, name):
        return self._tools[name]

    def names(self):
        return sorted(self._tools)

    def ollama_schemas(self):
        return [
            {"type": "function", "function": {
                "name": t.name, "description": t.description, "parameters": t.parameters
            }}
            for t in self._tools.values()
        ]

    def execute(self, name, arguments, context):
        return self.get(name).handler(context, arguments)
