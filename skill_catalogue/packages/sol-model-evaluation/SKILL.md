---
name: "sol-model-evaluation"
description: "Compare model or harness changes with reproducible tasks and recorded execution evidence."
version: "1.0.0"
category: "general"
source: "adapted"
license: "LicenseRef-SOL"
license_note: "SOL-native adaptation; upstream evidence and notices are in the shared release. Orchestra-Research/AI-Research-SKILLs"
status: "published"
sectors: ["plg-studio", "dev", "client", "home", "ventures", "red-echo", "plg-film", "project-spicy", "immune", "anvil"]
tags: ["sol-catalogue", "research"]
---

## When to Use

Compare model or harness changes with reproducible tasks and recorded execution evidence.

## Procedure

1. Define tasks, scoring criteria and a baseline before tuning. Record model identity, provider, version, inference settings, prompt, tools and dataset revision.
2. Inspect locally available evaluation tools. Use lm_eval only if installed and compatible; do not fabricate benchmark task names or download models implicitly.
3. Run matched baseline and candidate trials, preserving per-task results, errors, tool calls and context usage. Separate deterministic fixture tests from live model trials.
4. Report failure rates and uncertainty across repeated runs. Never extrapolate a passing toy task to full production autonomy.

## Pitfalls

Skills do not grant permissions or tool access. Report missing prerequisites and failed checks; never manufacture execution evidence.

## Verification

Map each claimed outcome to an observed result. Read [the acceptance rubric](references/acceptance.md) when validating this procedure.
