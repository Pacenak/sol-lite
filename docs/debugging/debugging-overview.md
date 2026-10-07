# Debugging Overview

Use evidence in this order:

1. reproduce the failure;
2. inspect runtime status/events;
3. inspect audit/fault logs;
4. verify the exact workspace/session context;
5. verify native model tool calls;
6. inspect permissions and approvals;
7. change the smallest responsible layer;
8. rerun the relevant test and then the full suite.

Do not infer successful execution from model prose.


## Evidence rule

Treat runtime results, audit records, structured events and command output as evidence. Model prose is not evidence that a tool executed, a file changed, or a task completed. Raw tool-like model text is rejected by the runtime.
