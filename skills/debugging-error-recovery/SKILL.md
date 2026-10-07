---
name: debugging-error-recovery
description: Recover from failed tools, commands, model responses, partial changes, and ambiguous errors using evidence instead of guessing.
---

# Debugging and Error Recovery

## Procedure
1. Capture the exact failure, command, inputs, environment, and timestamp.
2. Reproduce before changing code when reproduction is safe.
3. Separate primary failure from secondary symptoms.
4. Test the smallest plausible hypothesis.
5. Preserve evidence before cleanup.
6. Apply the smallest root-cause fix that explains the evidence.
7. Re-run the failed test and adjacent regression tests.
8. If recovery is partial, state exactly what remains unresolved.


## SOL-Lite boundary
This skill provides reasoning guidance only. It does not grant filesystem, terminal, repository, network, skill-install, or application permissions. Runtime policy and explicit approvals remain authoritative.
