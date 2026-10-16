# Workspaces

Workspaces are hard boundaries for filesystem and shell operations.

The runtime normalizes workspace paths and uses containment checks before filesystem access. Agents receive the authoritative workspace path through `runtime_get_context`.

Useful commands:

```text
/workspace
/workspaces
/new
```

Different sessions can point at different repositories and operate concurrently.

A Studio Odoo import workspace keeps source documents in `studio-odoo/sources` and finished CSVs in `studio-odoo/import`. Use a folder outside the `plg-odooacc` checkout. See [Studio Odoo import: beginner guide](dummies-studio-odoo.md).

A studio manual can be loaded only from the workspace `/workspace` prints. Point the session at the infrastructure checkout, or copy the volume into the folder you already opened. See [Studio change gate](studio-change.md).
