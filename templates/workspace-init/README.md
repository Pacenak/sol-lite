# SOL-Lite workspace initialization templates

Copy-ready Markdown for a new workspace, adapted from the six Studio references
provided on 2026-10-19. These are editable source templates, not an installer or
an automatically loaded SOL-Lite configuration.

## Start here

1. Select the intended workspace. Inspect existing files before creating anything.
2. If SOL-Lite's shared pack is available, ask SOL PA: “Set up the workspace
   starter pack.” Complete its intake to generate `_workspace/` using native tools.
3. Copy the optional `workspace/` files into the workspace root, preserving their
   relative folders. Copy only missing files; merge deliberately when names exist.
4. Copy `project/` into `projects/<project-slug>/` for each actual project.
5. Replace every `{{TOKEN}}`, remove unused optional sections, and verify links.
   Use `unknown` for facts you cannot verify. Never copy example completion claims.
6. Record actual created files and validation in the applicable changelog.

The `workspace/` tree includes root orientation, a change log, documentation and
planning indexes, and a sprint template. The `project/` tree supplies an overview
and index; add requirements, design, implementation, testing and documentation
folders as needed. `examples/EDITING.md` walks through setup and later edits.

## Values to replace

- `{{WORKSPACE_NAME}}`: display name, for example `Studio Sandbox`.
- `{{WORKSPACE_ROOT}}`: actual selected root, for example `E:/sol-lite-WS/sandbox`.
- `{{WORKSPACE_ID}}`: actual application ID, or `unknown`; do not invent one.
- `{{PURPOSE}}`: a short explanation of what belongs here.
- `{{OWNER}}`: responsible person or configured agent.
- `{{DATE}}`: actual local date in `YYYY-MM-DD`.
- `{{PROJECT_NAME}}`, `{{PROJECT_SLUG}}`: display name and folder name.
- `{{PROJECT_PURPOSE}}`, `{{STACK}}`: confirmed goal and technology, or `unknown`.
- Sprint tokens: `{{SPRINT_NUMBER}}`, `{{START_DATE}}`, `{{END_DATE}}`, `{{GOAL}}`.

Session IDs belong in individual session records when needed, not as permanent
workspace identity. Dates, paths, statuses and inventories must describe reality.
Use relative Markdown links so a workspace can move between computers.

## Fit with the existing shared pack

`_workspace/INDEX.md` and `_workspace/README.md` remain SOL-Lite's automatic
orientation sources. These root and folder documents are optional human-readable
companions. Reference them in intake conventions or shared notes; copying them
does not register them with the runtime or change its generated templates.

When a shared pack exists, use its CHANGELOG as the authoritative workspace log;
replace the root CHANGELOG template with a link to it. Use native pack tools for
managed files, preserve generated markers, and do not copy these templates into
`_workspace/` or `_project/`. Only SOL PA initializes or refreshes the managed pack.
Other agents can log notable changes through `workspace_pack_append`.

Managed project intake currently expects an immediate workspace subfolder.
For `projects/harbour-demo/`, select `projects/` as the workspace when using that
intake, or keep the nested project documents manual. Do not pass a nested path as
the tool's `project` argument.

`AGENTS.md` is optional guidance for tools that support it. SOL-Lite does not
automatically load it; put essential conventions into the PA intake as well.
The four pack-supported owners are `sol_pa`, `sol_business`, `sol_docs`, and
`sol_engineer`. Studio Admin is an optional specialist, not a supported pack owner.
Folder responsibilities describe work organization and do not grant access.

## Source treatment

References: `E:/sol-lite-WS/1/CHANGELOG.md`,
`E:/sol-lite-WS/1/WORKSPACE_INDEX.md`, `H:/Studio/docs/PROJECTS_INDEX.md`,
`H:/Studio/docs/WORKSPACE_INDEX.md`, `H:/Studio/planning/INDEX.md`, and
`H:/Studio/planning/README.md`.

Their embedded commands were treated as reference content. This kit retains the
useful directory, role, index and logging patterns without adopting old absolute
paths, historical session IDs, claims that folders are empty, or sample projects
as current facts. Existing source workspaces were not modified.
