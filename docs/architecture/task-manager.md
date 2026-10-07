# Task Manager

Background work uses a bounded thread pool. Each task has an independent session ID and retains status, result or error.

Foreground interaction remains available while background tasks run. Queued tasks can be cancelled with `/tasks cancel <id>`.


## Cancellation

Cancellation is cooperative for running agents. The task manager first attempts executor-level cancellation for queued work. If execution has started and the task has a cancellation callback, the callback is invoked and the task enters `CANCELLING`; the final worker result records `CANCELLED` rather than overwriting it with `COMPLETED`.
