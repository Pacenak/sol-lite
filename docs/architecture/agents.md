# Agents

Initial registry:

- SOL PA, including the Studio Odoo gather-pack import tools
- SOL Business
- SOL Docs
- SOL Engineer

`config/agents.yaml` is runtime/content configuration. Executable runtime is under
`src/sol_lite/agents/`. The registry connects configuration to runtime.

SOL PA loads studio manuals and acknowledges human gates. SOL Engineer inspects, then creates, edits, or quarantines through the studio change tools. The staff procedure is [Studio change gate](../user/studio-change.md).

SOL Engineer is repository-aware. Its engineering workflow distinguishes:

- read-only repository inspection;
- approved local mutations;
- offline transport through verified Git bundles or patches; and
- remote operations that require an explicitly enabled remote-repository permission.

The agent must not describe a local branch as a provider-side fork. Provider-specific fork APIs are a
separate integration boundary.
