# Curated skills for SOL-Lite and SOL-Full

**Status:** Approved and implemented as release 2026.10.18.1: catalogue, native adapters, baseline and optional instruction packs. Engineering fixture acceptance is recorded in `docs/testing/shared-skill-catalogue.md`; live Full/provider and domain-service acceptance remains explicitly unverified.
**Outcome:** Both runtimes consume the same reviewed skill releases through their existing loaders, with bounded context, provenance, correct permissions and observable task validation.
**Already true:** Lite has local manifests, external imports, agent assignment and task-based body injection. Full's local checkout is `PLG_Ai_Interface`: its README identifies SOL Command/Outpost; it has seed installation, owner/sector filtering, session pins and a feature-flagged skill router. Existing source registrations are references, not proof of imported upstream packages. Existing game-engine procedures also need live acceptance evidence.
**Not on this trip:** Bulk installation, replacing either runtime, enabling every MCP server, or claiming complete game production from Markdown. Domain adapters follow the catalogue foundation as separately reviewable work.

## Route

1. **Audit and select.** Compare existing skills against the source list below. Select exact upstream folders and commits; inspect bodies, scripts, dependencies and file-level licences. Record each as reused, adapted, reference-only or deferred. Done when every selected package has a concrete capability gap and no competing default procedure.
2. **Define the shared release contract.** Add a versioned catalogue/lock manifest to Lite's existing `config/skill-sources.yaml` workflow; export immutable packs for Full. Record namespaced ID, upstream URL/path/commit, original and adapted content hashes, licence/attribution, supported runtimes, dependencies, tool requirements, role/sector visibility and evaluation results. Done when both adapters validate the same release and reject invalid or mismatched content.
3. **Wire existing loaders.** Lite uses `src/sol_lite/skills/manager.py`; Full uses its existing seed/startup installer, `services/memory/skills.py`, session invocation and `src/platform/skills/` router. Preserve Full's owner/sector isolation and skip-existing policy. New optional seeds belong in Full's existing `seed/skills/general/` or established domain-pack source trees, with branch JSON pins; do not create a competing branch-body store. Done when installation, restart, update and rollback preserve user edits and assignments.
4. **Load only the task's procedure.** Show concise descriptions, load selected bodies and resolve supporting resources within the installed package. Explicit invocation has priority; automatic matches stay bounded. Expose missing tools and unmet dependencies. Preserve Lite's `$skill-id` invocation and Full's existing invocation semantics; add slash aliases only through tested command routing. Done when explicit, natural-language, irrelevant, duplicate-ID and missing-resource cases behave correctly in each runtime.
5. **Pilot engineering first.** Start with inspection/specification, bounded planning, debugging, appropriate regression tests, implementation, diff review and validation. Reconcile overlapping sources into one default procedure per job. Done when real fixtures demonstrate creation, repair and refactoring, and ambiguous requirements or failed validation never produce a successful completion state. Compare runs with/without the pack and record model/version, failures, tool results and context cost.
6. **Release optional domain packs.** Add business/production, web/design, science, defensive security and game workflows after the pilot. Each pack needs at least one successful task, missing-dependency case and failure case in each supported runtime. Unsupported packs remain visible as unavailable with a reason. Done when docs distinguish instructions, adapters and measured capabilities; release pins and a rollback path exist.

## Proposed skill sources

These are repository-level selections for review and adaptation, not approval to install every skill. Exact folders, commits and redistribution terms are outputs of stop 1.

**Shared engineering and production foundation**

- [anthropics/skills](https://github.com/anthropics/skills): selected skill-authoring, MCP-building, web testing, design and communication procedures. Target both runtimes. Check each licence: the upstream README distinguishes open-source examples from source-available DOCX/PDF/PPTX/XLSX skills; retain SOL's existing document tooling unless reuse terms and compatibility are established.
- [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills): spec → plan → incremental build → test → review, with measured web performance. Shared engineer pack; adapt tool names and gates instead of assuming upstream commands exist in SOL.
- [obra/superpowers](https://github.com/obra/superpowers): systematic debugging, appropriate TDD, verification and branch-finishing procedures. Upgrade the existing Lite mappings and Full seed skills rather than adding duplicate workflows.
- [mattpocock/skills](https://github.com/mattpocock/skills): requirements interrogation, implementation decomposition and engineering/refactoring practices. Shared engineer/planning pack; select against existing SOL coverage.
- [vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills): framework-specific frontend, React and web design guidance. Optional shared web pack, selected only when the target stack matches.
- [phuryn/pm-skills](https://github.com/phuryn/pm-skills): discovery, product strategy, prioritisation, execution and launch. Shared business/PA procedures; Full sector bindings differ from Lite agent assignments. This is not a financial-ledger integration.
- [JohnWayneeee/ai-agent-skills](https://github.com/JohnWayneeee/ai-agent-skills): secondary design/development candidates. Select only procedures that add measurable value beyond Anthropic/Vercel and current UI skills; do not assume the whole repository is a brand system.

**Optional specialist packs**

- [K-Dense-AI/scientific-agent-skills](https://github.com/K-Dense-AI/scientific-agent-skills): selected scientific analysis, statistics and reproducible research. Lite Rick Prime and corresponding Full research roles; install dependencies selectively and inspect individual skill licences.
- [Orchestra-Research/AI-Research-SKILLs](https://github.com/Orchestra-Research/AI-Research-SKILLs): AI/ML research, evaluation and optimisation. Optional research pack, with heavier execution on a configured Full worker or capable Lite host. It is not evidence of accounting or game-economy expertise.
- [trailofbits/skills](https://github.com/trailofbits/skills): code-audit and verification candidates for a shared defensive security pack.
- [mukul975/Anthropic-Cybersecurity-Skills](https://github.com/mukul975/Anthropic-Cybersecurity-Skills): selected defensive analysis, hardening and incident-response procedures. Preserve target allowlists and existing admin/owner boundaries. This is a community project, not an Anthropic-maintained repository.

**Deferred pending package verification**

- [g-shevchenko/utility-skills](https://github.com/g-shevchenko/utility-skills): the [author's page](https://gregshevchenko.com/research/utility-skills/) describes design, SEO, document, media and infrastructure utilities, but direct repository retrieval failed during this review. Keep as a candidate; verify the actual files, licence, services and credentials before selecting anything. Do not treat its existence as a verified remote-management adapter.

## Sources integrated as references or discovery inputs

- [VoltAgent/awesome-agent-skills](https://github.com/VoltAgent/awesome-agent-skills): discovery index; follow links to original packages and their licences. Already registered in Lite.
- [vercel-labs/skills](https://github.com/vercel-labs/skills): installer/source-resolution reference and possible optional interoperability adapter. Retain SOL's native review, quarantine and permission paths; no required Node-based replacement for Lite's importer.
- [VoltAgent/awesome-design-md](https://github.com/VoltAgent/awesome-design-md): DESIGN.md references for user-selected design briefs. Keep PLG's own design tokens authoritative.
- [ai-boost/awesome-harness-engineering](https://github.com/ai-boost/awesome-harness-engineering): harness/evaluation architecture references; not a bulk skill package.
- [Shubhamsaboo/awesome-llm-apps](https://github.com/Shubhamsaboo/awesome-llm-apps): application, agent and RAG examples; review individual examples rather than importing an entire framework stack.
- [punkpeye/awesome-mcp-servers](https://github.com/punkpeye/awesome-mcp-servers): MCP discovery directory. Every selected server is a separate adapter integration requiring transport, schemas, credentials, permission checks and a real invocation test.
- [ripienaar/free-for-dev](https://github.com/ripienaar/free-for-dev): service discovery for cost planning. Verify selected providers' current terms directly; listing does not create an account or guarantee zero cost.
- [Andrew Ng's engineering fundamentals article](https://www.linkedin.com/pulse/ai-engineering-skills-map-software-fundamentals-andrew-ng-7lnac/) and [AGNT's skills roundup](https://agnt.gg/articles/agents/100-best-ai-agent-skills): planning/discovery reading, not installable packages or proof of quality.

## SOL-native gaps to design after the foundation

- **Game development:** GDD/vertical-slice planning, actual engine build diagnostics, gameplay/netcode tests, asset validation and measured profiling. Reuse Full's existing Unreal pack and configured MCP path; engine version, project and tool availability come from the workspace. Unreal-specific material stays in the Studio domain. Other engines need their own adapters and fixtures.
- **Accounting and production finance:** source-grounded budgets, ledger reconciliation, invoice evidence and deterministic calculation tests. Use the existing Odoo path where appropriate. Select accounting tools and jurisdiction-specific rules separately; the listed research repositories do not supply a complete accounting system.
- **Infrastructure/OS:** host inventory, configuration diff, dry-run, approved change, health check and rollback using existing native terminal/remote policies. A utility skill or MCP directory does not provision these capabilities.
- **Context and fleet:** grounded task summaries, requirements IDs, source references and evidence-preserving handoffs; pack hash/conflict checks against actual sync code. Context reduction and cross-machine recovery require runtime implementation and tests, not just a `/minify-context` paragraph.

## Decisions

- One shared catalogue contract and release, two runtime adapters; no new repository or framework is required to start.
- Namespaced provenance prevents upstream name collisions. Local overrides are explicit and preserved.
- Metadata first, selected body next, supporting files on demand; no whole-catalogue prompt dump.
- Skills supply procedures. Runtime tools, permissions, approvals and evidence determine execution and completion.
- Pin before promotion; inspect changed content, compare evaluations and preserve rollback. Never auto-publish an agent-authored skill into a trusted shared pack.
- Star counts are discovery signals, not correctness evidence; this is a suitability shortlist, not a claimed popularity ranking.

## Ask before driving

- Implementation was approved on 2026-10-18. Existing installer/runtime fixes are included in the local Lite changes.
- Resolve engine/version and accounting integration choices when their domain packs are designed; these do not block the catalogue pilot.

## Done when

- The same pinned release installs through both existing loaders without overwriting operator edits or crossing owners/sectors.
- Users and agents can author, inspect, invoke, update and roll back a skill with traceable provenance and visible dependency gaps.
- Both runtimes demonstrate the engineering pilot with real tools; failure, ambiguity, missing prerequisites and denied actions cannot be reported as verified success.
- Domain packs are advertised only to the extent supported by recorded acceptance results. No claim of zero hallucinations or complete autonomy is made.
