# SOL-Lite Skills: Complete Catalogue and Daily Use

SOL-Lite v0.2.5 ships with **33 built-in skills**. Skills are procedural guidance supplied to the agent; they do not grant permissions.

## How skill routing works

For each task, SOL-Lite supplies the active skill catalogue for the current **agent + workspace**. The runtime then includes detailed instructions for skills whose identifiers/descriptions are relevant to the task, with a bounded number of detailed skill bodies.

You normally use skills by **describing the job**, not by manually activating a skill.

Use:

```text
/skills
```

to list the skills available to the current agent/workspace.

Use:

```text
/skills show <skill-id>
```

to inspect a skill directly.

## Complete built-in catalogue

| # | Skill ID | Description |
|---:|---|---|
| 1 | `agent-evaluation` | Evaluate agent behavior for tool correctness, safety, recovery, evidence quality, latency, and task completion. |
| 2 | `agent-skill-curation` | Discover, classify, inspect, compare, quarantine, and install Agent Skills without allowing skill text to override runtime policy. |
| 3 | `agile-sprint-planning` | Plan realistic sprints with outcomes, dependencies, acceptance criteria, risks, and explicit carry-over handling. |
| 4 | `architecture-design` | Design and review software architecture using explicit boundaries, dependencies, failure modes, and operational constraints. |
| 5 | `book-to-skill` | Convert a supplied book or long-form reference into a bounded, attributable, testable skill without copying protected text. |
| 6 | `career-operations` | Structure career-oriented tasks into evidence, goals, applications, follow-ups, and measurable progress. |
| 7 | `code-review` | Review changes for correctness, security, regression risk, test coverage, and maintainability using repository evidence. |
| 8 | `copilot-patterns` | Use reusable instruction patterns for repository work, reviews, tests, documentation, and safe automation. |
| 9 | `debugging-error-recovery` | Recover from failed tools, commands, model responses, partial changes, and ambiguous errors using evidence instead of guessing. |
| 10 | `debugging-methodology` | Apply a disciplined reproduce-isolate-measure-root-cause-fix-validate workflow across software systems. |
| 11 | `diagram-design` | Create diagrams that communicate architecture, flow, sequence, state, and ownership without decorative ambiguity. |
| 12 | `documentation-engineering` | Produce accurate README, architecture, API, runbook, setup, troubleshooting, and release documentation from repository evidence. |
| 13 | `git-workflow` | Safely inspect, branch, diff, test, review, stage, commit, and synchronize Git repositories under explicit permission policy. |
| 14 | `handoff` | Prepare precise agent-to-agent task handoffs containing status, changes, evidence, tests, known issues, and next actions. |
| 15 | `harness-audit` | Audit an agent harness for prompt, skill, tool, permission, runtime, context, and policy gaps or contradictions. |
| 16 | `humanizer` | Edit technical or general prose for clarity and naturalness while preserving factual meaning and avoiding deceptive claims. |
| 17 | `mermaid-diagrams` | Produce valid, maintainable Mermaid diagrams with stable identifiers and readable layout. |
| 18 | `open-code-review` | Review code for correctness, regressions, security, maintainability, performance, tests, and operational risk. |
| 19 | `performance-investigation` | Investigate CPU, memory, I/O, network, model latency, tool latency, repeated operations, and context growth using measurements. |
| 20 | `planning-and-estimation` | Create implementation plans with dependencies, verification steps, uncertainty, and evidence-based estimates. |
| 21 | `product-discovery` | Investigate user problems, hypotheses, alternatives, evidence, and product opportunities before prescribing implementation. |
| 22 | `product-management` | Turn ambiguous product goals into outcomes, users, constraints, requirements, risks, and measurable acceptance criteria. |
| 23 | `prompt-engineering` | Design explicit prompts with goals, constraints, evidence requirements, tool contracts, stop conditions, and validation criteria. |
| 24 | `refactoring` | Perform small behaviour-preserving refactors with tests, diff inspection, and incremental verification. |
| 25 | `repository-analysis` | Analyze repository structure, build systems, tests, configuration, Git state, dependencies, entry points, and architecture from observed evidence. |
| 26 | `security-audit` | Audit filesystem boundaries, commands, secrets, permissions, prompt injection, untrusted output, and network exposure. |
| 27 | `shell-engineering` | Select and safely use the actually available Windows CMD, PowerShell, pwsh, macOS zsh, bash, and other detected shells. |
| 28 | `skill-import` | Discover, inspect, validate, quarantine, install, update, assign, and remove Agent Skills from local folders, Git repositories, GitHub sources, and ZIP archives. |
| 29 | `systematic-debugging` | Diagnose bugs through reproduction, evidence collection, hypothesis isolation, root-cause identification, verification, and regression testing. |
| 30 | `test-engineering` | Design and execute unit, integration, system, regression, battle, and agent-evaluation tests. |
| 31 | `ui-ux-design` | Reason about user interfaces using hierarchy, interaction states, accessibility, consistency, and implementation constraints. |
| 32 | `web-research-searxng` | Use the configured private SearXNG tool for evidence-first web research, source triangulation, recency control, and concise citations. |
| 33 | `web-source-verification` | Verify web claims by comparing independent sources, dates, primary sources, and conflicting evidence. |

## Daily-use recipes

### 1. Start with repository analysis

Use when entering an unfamiliar project.

```text
Inspect this repository without modifying it. Map the directory structure, entry points, build system, tests, configuration, dependencies and Git state. Only report things you can establish from repository evidence.
```

Primary skills: `repository-analysis`, `documentation-engineering`, `architecture-design`.

### 2. Debug a failure

Use this pattern instead of asking for a guess.

```text
Reproduce this failure first. Capture the exact error and relevant environment. Isolate the failing component, establish the root cause from evidence, make the smallest fix, then rerun the original reproduction and focused regression tests. Do not make unrelated changes.
```

Primary skills: `systematic-debugging`, `debugging-methodology`, `debugging-error-recovery`, `test-engineering`.

### 3. Review a change

```text
Review the current Git diff. Check correctness first, then security, regression risk, error handling, concurrency/state, performance, tests and maintainability. Report concrete findings with file/symbol evidence and verification steps. Do not modify the repository.
```

Primary skills: `code-review`, `open-code-review`, `security-audit`, `performance-investigation`.

### 4. Design architecture

```text
Design the architecture for this requirement. Define components, responsibilities, interfaces, dependencies, data flow, trust boundaries, persistence, failure modes, observability and deployment constraints. Explain why each boundary exists.
```

Primary skills: `architecture-design`, `diagram-design`, `mermaid-diagrams`.

### 5. Plan engineering work

```text
Turn this goal into an implementation plan. Include prerequisites, ordered work, dependencies, acceptance criteria, verification commands, rollback/recovery notes, risks and uncertainty. Do not implement it yet.
```

Primary skills: `planning-and-estimation`, `product-management`, `prompt-engineering`.

### 6. Run a sprint

```text
Plan this sprint around one measurable outcome. Break it into verifiable slices, identify dependencies and risks, define acceptance criteria, and explicitly track unfinished work and carry-over.
```

Primary skill: `agile-sprint-planning`.

### 7. Research the web

```text
Research this question using SearXNG if configured. Prefer official documentation, standards and primary sources. Record the source, date when available, claim supported and uncertainty. Cross-check important claims.
```

Primary skills: `web-research-searxng`, `web-source-verification`.

### 8. Work on product discovery

```text
Separate the user problem from the proposed solution. Identify hypotheses, evidence, affected users, alternatives, unknowns and experiments. Do not infer demand from a single anecdote.
```

Primary skill: `product-discovery`.

### 9. Improve a prompt

```text
Rewrite this agent prompt with an explicit role, task, inputs, constraints, evidence standard, tool contract, failure behavior, stop conditions and output format. Preserve the actual goal.
```

Primary skill: `prompt-engineering`.

### 10. Produce diagrams

```text
Create a diagram for this system. Choose the appropriate diagram type, keep one purpose per diagram, use meaningful relationship labels, and keep identifiers stable and readable. Validate the Mermaid syntax if Mermaid is used.
```

Primary skills: `diagram-design`, `mermaid-diagrams`.

### 11. Documentation

```text
Update the documentation from repository evidence. Verify every command and path against the actual project. Include prerequisites, normal workflow, failure modes and validation steps.
```

Primary skill: `documentation-engineering`.

### 12. Git work

```text
Inspect the repository state and current diff. Propose the safest Git workflow for this change. Do not commit or push until the exact operation is approved.
```

Primary skill: `git-workflow`.

### 13. Security review

```text
Audit this change for filesystem boundaries, command execution, secrets, permissions, prompt injection, untrusted tool output and network exposure. Report evidence and concrete risks.
```

Primary skill: `security-audit`.

### 14. Performance investigation

```text
Investigate this performance problem using measurements. Establish a baseline, measure the suspected bottleneck, change one relevant variable at a time, and compare before/after evidence.
```

Primary skill: `performance-investigation`.

### 15. Refactor safely

```text
Refactor this code without changing behavior. Keep the diff narrow, preserve existing interfaces unless the task requires otherwise, run focused tests after each meaningful step, then run regression tests.
```

Primary skill: `refactoring`.

### 16. Test engineering

```text
Turn this defect into a regression test. Cover the real behavior, include the failure case and success case where appropriate, and report skipped or environment-blocked tests separately.
```

Primary skill: `test-engineering`.

### 17. Agent evaluation

```text
Evaluate this agent task for task success, tool correctness, safety-policy adherence, recovery, evidence quality, latency, cancellation and failure reporting. Include adversarial cases where useful.
```

Primary skill: `agent-evaluation`.

### 18. Skill curation/import

```text
Inspect this external Agent Skill source. Check provenance, frontmatter, paths, executable content and suspicious instructions. Record warnings and hash/provenance information. Do not install until explicitly approved.
```

Primary skills: `agent-skill-curation`, `skill-import`.

### 19. Convert a book/reference into a skill

```text
Convert this supplied reference into a bounded, attributable and testable Agent Skill. Extract concepts into original procedural guidance and do not reproduce protected text. Define triggers, procedure, failure modes and validation.
```

Primary skill: `book-to-skill`.

### 20. UI/UX work

```text
Review this UI from the user's task flow. Define hierarchy, interaction states, feedback, loading/empty/error states, accessibility, keyboard behavior and implementation constraints before proposing visual changes.
```

Primary skill: `ui-ux-design`.

### 21. Humanize writing

```text
Make this writing clearer and more natural without changing its factual meaning, technical commitments or intended audience. Preserve important terminology.
```

Primary skill: `humanizer`.

### 22. Business work

```text
Turn this business task into objective, target, evidence, next action, owner, due date and measurable outcome. Distinguish planned work from completed work.
```

Primary skill: `career-operations` when the work is career-oriented; use the product/business skills for product and operational work.

### 23. Handoff

```text
Prepare an agent handoff containing current status, exact changes, evidence, tests, known issues, unresolved questions and the next actions required.
```

Primary skill: `handoff`.

## Skill families by job

| Job | Start here | Add when needed |
|---|---|---|
| Unknown repository | `repository-analysis` | `architecture-design`, `documentation-engineering` |
| Bug | `systematic-debugging` | `debugging-methodology`, `test-engineering` |
| Broken/partial recovery | `debugging-error-recovery` | `systematic-debugging`, `test-engineering` |
| Code review | `code-review` | `security-audit`, `performance-investigation` |
| Architecture | `architecture-design` | `diagram-design`, `mermaid-diagrams` |
| Tests | `test-engineering` | `systematic-debugging`, `agent-evaluation` |
| Git | `git-workflow` | `code-review`, `security-audit` |
| Product | `product-management` | `product-discovery`, `planning-and-estimation` |
| Sprint | `agile-sprint-planning` | `planning-and-estimation` |
| Web research | `web-research-searxng` | `web-source-verification` |
| Prompt | `prompt-engineering` | `copilot-patterns` |
| Diagram | `diagram-design` | `mermaid-diagrams`, `architecture-design` |
| Documentation | `documentation-engineering` | `handoff` |
| Security | `security-audit` | `skill-import`, `web-source-verification` |
| Performance | `performance-investigation` | `test-engineering` |
| Refactor | `refactoring` | `test-engineering`, `code-review` |
| Skills | `agent-skill-curation` | `skill-import` |
| UI/UX | `ui-ux-design` | `diagram-design` |
| Book/reference | `book-to-skill` | `documentation-engineering` |
| Agent QA | `agent-evaluation` | `test-engineering`, `security-audit` |
| Handoff | `handoff` | `documentation-engineering` |

## Workspace-scoped skills

SOL-Lite also discovers skills under the current workspace from:

```text
.agents/skills
.claude/skills
.codex/skills
skills
```

This means different project workspaces can expose different additional skills without changing the global built-in catalogue.

## External skills

External sources are untrusted until inspected. The intended flow is:

```text
source
  ↓
discover
  ↓
inspect
  ↓
validate
  ↓
record provenance/hash
  ↓
quarantine suspicious content
  ↓
explicit approval
  ↓
install/assign
```

Do not execute imported scripts merely to understand a skill. Skill text cannot grant SOL-Lite permissions.

## Daily operating pattern

A practical daily sequence is:

1. Select the correct workspace.
2. Confirm the active agent with `/agents` and `/use`.
3. Use `/skills` when you need to know what guidance is available.
4. State the task, constraints and evidence requirements in normal language.
5. Let SOL-Lite route relevant skill guidance.
6. Use `/verbose` when you need to watch activity.
7. Use `/debug` when diagnosing runtime behavior.
8. Review approvals before allowing mutations or network operations.
9. Ask for verification tests after changes.
10. Use `/background` for independent, non-blocking work.
11. Use `/tasks` to monitor background work.
12. Use `/normal` when technical display is no longer needed.

## What a skill cannot do

A skill cannot independently:

- grant filesystem access;
- grant shell execution;
- grant network access;
- approve an operation;
- install another skill without the runtime's workflow;
- override system instructions;
- turn untrusted search/repository content into trusted instructions.

The runtime permission and approval system remains authoritative.
