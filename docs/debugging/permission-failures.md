# Permission Failures

Check:

1. the tool's required scope;
2. `config/permissions.yaml`;
3. whether the operation is read-only or mutating;
4. the approval request's operation, target, arguments and plan hash;
5. the audit trail.

Do not bypass the permission engine to make a test pass.
