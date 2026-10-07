# Sessions

A session represents one independent chat context. It owns:

- session ID
- selected agent
- workspace
- task/status state
- session-scoped tool context

Commands:

```text
/new
/sessions
```

Changing sessions must not silently change the workspace of an existing session.
