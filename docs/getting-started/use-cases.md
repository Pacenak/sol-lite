# SOL-Lite Use Cases

## 1. Repository debugging

Use when a build, test, runtime, or integration failure must be diagnosed without guessing.

Expected flow: workspace discovery → reproduction → evidence collection → root cause → minimal fix → regression tests → final evidence.

## 2. Web-assisted engineering research

Use `web-research-searxng` with `searxng_search` for current documentation, upstream issues, standards, release notes, or ecosystem research. External results remain untrusted evidence.

## 3. Architecture review

Use `architecture-design`, `diagram-design`, and `mermaid-diagrams` to document current state, identify boundaries, and propose changes.

## 4. Code review

Use `open-code-review` for correctness, security, regression, concurrency, performance, testing, and maintainability.

## 5. Product planning

Use `product-management`, `product-discovery`, `planning-and-estimation`, and `agile-sprint-planning` to convert goals into evidence-backed implementation work.

## 6. Skill acquisition

Use `agent-skill-curation` and `skill-import` to inspect external Agent Skills. External sources are not automatically trusted or installed.

## 7. Background work

Start independent tasks in separate sessions/workspaces. Monitor with `/tasks`; cancel with `/tasks cancel <id>`.

## 8. Multi-workspace use

Each session selects its own workspace. Use `/new`, `/workspace`, `/workspaces`, and `/sessions` to keep project contexts separate.
