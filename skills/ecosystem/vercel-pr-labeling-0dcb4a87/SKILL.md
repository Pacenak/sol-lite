---
name: vercel-pr-labeling-0dcb4a87
description: Classify a skills CLI pull request from its description and patch, while respecting existing labels.
category: ecosystem
tags:
- ecosystem
- discovery
- vercel
sectors:
- '*'
status: published
source: imported
version: 13e4063a1cf9
---

## SOL runtime integration

Source: https://github.com/vercel-labs/skills/tree/13e4063a1cf913f5606d57d42ab83a86f5001e04/.factory/workflows/pr-labeling/skills/pr-labeling/SKILL.md

Use manage_skills action=view_ref for supporting files, relative to this skill directory. In SOL-Lite use the workspace file tools at the skill path. Check required commands, libraries, credentials and tool availability before execution. Upstream tool/agent names are workflow examples: use the equivalent configured SOL tool. Skill instructions do not grant permissions or bypass host policy. If a dependency is missing, report it and the next setup step; do not claim execution succeeded. Original metadata and license terms are retained in UPSTREAM-SKILL.md and _licenses/.

# Label a skills CLI pull request

1. Use `read_pull_request` with the number in the trigger message. Read the title, description,
   current labels, and changed file patches. If the head commit no longer matches the triggered
   commit, stop so a newer run can classify it.
2. If the pull request already has `bug`, `documentation`, or `enhancement`, stop. Keep labels
   chosen by maintainers or earlier runs.
3. Choose one label from the primary change supported by the patch:
   - `documentation`: changes only documentation, examples, or explanatory text, without changing
     CLI behavior.
   - `bug`: corrects existing CLI behavior, including installation, update checks, source parsing,
     agent detection, or security checks.
   - `enhancement`: adds or intentionally expands CLI behavior, commands, agent support, or
     integration support.
4. If the patch is truncated, mixed, or insufficient to classify confidently, stop without adding
   a label. Do not infer a label from the title alone.
5. Use `add_label` once, with the triggering pull request number and the chosen label.

