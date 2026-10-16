# Agents

Built-in agents:

| ID | Role |
|---|---|
| `sol_pa` | coordination, planning, research, delegation, and Studio Odoo gather-pack import files |
| `sol_business` | business operations and analysis |
| `sol_docs` | premium documents, presentations, spreadsheets, diagrams, indexing and extraction |
| `sol_engineer` | software engineering, debugging, testing and technical operations |

Select an agent with:

```text
/use sol_engineer
```

Agent prompts are stored under `src/sol_lite/agents/<agent>/prompt.md`.

SOL PA builds Studio Odoo import CSVs from `studio-odoo/sources` after you bind a `plg-odooacc` checkout. The click-path is [Studio Odoo import: beginner guide](dummies-studio-odoo.md). The interface is [Studio Odoo](../integrations/studio-odoo.md).

SOL PA loads a studio manual and waits on human gates. SOL Engineer inspects hosts and files, then creates, edits, or quarantines only through the studio change tools. The staff path is [Studio change gate](studio-change.md).

`/flare on` adds a light speaking manner for the rest of this sitting. Names and jobs stay the same. `/flare off` removes it. `/flare` reports whether it is on.

| Agent | Manner while flare is on |
|---|---|
| `sol_pa` | Murray, the earnest band manager: warm, slightly official, keen to organise the next step |
| `sol_business` | Fred Dagg: dry, plain-spoken, wary of an unchecked number |
| `sol_docs` | Viago: polite, particular about headings, layout, and whether the page looks cared for |
| `sol_engineer` | Mark Watney: talks the problem through in order, then one dry aside |
