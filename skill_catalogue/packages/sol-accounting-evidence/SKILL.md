---
name: "sol-accounting-evidence"
description: "Prepare auditable budgets and ledger reconciliations from supplied records."
version: "1.0.0"
category: "general"
source: "native"
license: "LicenseRef-SOL"
license_note: "SOL-native adaptation; upstream evidence and notices are in the shared release. "
status: "published"
sectors: ["plg-studio", "dev", "client", "home", "ventures", "red-echo", "plg-film", "project-spicy", "immune", "anvil"]
tags: ["sol-catalogue", "accounting"]
---

## When to Use

Prepare auditable budgets and ledger reconciliations from supplied records.

## Procedure

1. Read source records and identify period, currency, units, tax jurisdiction and chart of accounts. Do not invent invoices, balances, exchange rates or tax rules.
2. Preserve source identifiers and normalize amounts using decimal arithmetic and an explicit rounding policy. Keep missing values unknown rather than replacing them with zero.
3. Reconcile opening balance plus movements to closing balance; flag duplicates, mismatches and unexplained differences. Write deterministic checks for totals and rounding.
4. Produce a draft with traceable source rows and unresolved items. Use SOL's existing Odoo import tools only after checking configured schema and permissions; do not post transactions or file returns through this procedure alone.

## Pitfalls

Skills do not grant permissions or tool access. Report missing prerequisites and failed checks; never manufacture execution evidence.

## Verification

Map each claimed outcome to an observed result. Read [the acceptance rubric](references/acceptance.md) when validating this procedure.
