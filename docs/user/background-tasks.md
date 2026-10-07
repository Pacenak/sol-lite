# Background Tasks

`/background <prompt>` creates an independent session and runs an agent task concurrently with the foreground chat.

```text
/background inspect the repository test failures
/tasks
/tasks cancel <id>
```

Task states are `QUEUED`, `RUNNING`, `CANCELLING`, `COMPLETED`, `FAILED` and `CANCELLED`. A queued task can be cancelled before execution; a running task requests cancellation through its agent runtime and reaches `CANCELLED` when that runtime returns.

The task manager uses a bounded `ThreadPoolExecutor`. The configured maximum is four concurrent agents by default.
