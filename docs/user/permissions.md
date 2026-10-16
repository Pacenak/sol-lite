# Permissions

Permissions are operation-scoped. Examples:

- `filesystem.read`
- `filesystem.write`
- `terminal.read`
- `terminal.write`
- `network`
- `skills.inspect`
- `skills.install`
- `repository.read`
- `repository.write`
- `repository.remote`

The policy is in `config/permissions.yaml`. `terminal.allowed_commands` is the list that can run as read-only when the command is also classified read-only. Other commands need approval unless they are on the blocked list, which always denies. A skill does not alter these permissions.

Session approval is stored in memory for that session only. It is not written back into `permissions.yaml`.

Role-path workspace writes (`write_workspace_file` / `edit_workspace_file` under that agent's roots) do not need a session grant. Outside-role paths still need an exact approval.

`rm`, `del`, and `Remove-Item` stay denied on the local terminal and on `remote_execute`, including when an approval id is present. A file leave is `studio_quarantine`, and only on a lab host or a local workspace file. Production hosts, and hosts with no `environment`, are inspect-only. Staff steps are in [Studio change gate](studio-change.md).
