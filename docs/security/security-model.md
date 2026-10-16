# Security Model

SOL-Lite uses defence in depth:

- session-scoped workspace containment;
- operation-scoped permissions;
- exact approvals;
- conservative shell classification;
- blocked destructive/nested shell operations;
- native-only model tool execution;
- skill inspection and provenance;
- quarantine of suspicious skills;
- audit and fault records.

Studio host changes add one more rule: a node is inspect-only until `config/remote-nodes.yaml` sets `environment: lab`. Production, and a missing environment, cannot be edited or quarantined. See [Studio change gate](../user/studio-change.md).

The model is not trusted as an execution authority.
