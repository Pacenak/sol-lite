# Studio Odoo import pack

SOL PA can build the Studio Odoo gather-pack CSVs from files you place in the workspace. The column names, product codes, tax codes, analytic codes, journals, and fiscal positions are read from the bound `plg-odooacc` checkout. SOL-Lite does not call Odoo and does not file myIR.

The studio repository on this machine is `E:\git\plg-studio\plg-odooacc`. That path is not a default. The PA saves it only after you supply it and `studio_odoo_bind` verifies the templates.

## What this integration does

| Tool | Approval | Result |
|---|---|---|
| `studio_odoo_status` | No | Bound path, missing catalog files, missing data files, source-folder inventory. `odoo_api` is `not used`. |
| `studio_odoo_bind` | `studio.write` | Verifies `docs/templates` and `scripts/init-gather-pack.ps1`, then stores the absolute studio root on this workspace. |
| `studio_odoo_schema` | `studio.read` | Column names in template order, catalog codes, and the import rules. |
| `studio_odoo_inventory` | `studio.read` | Files under `studio-odoo/sources`. A CSV is matched only when its header equals a template header. |
| `studio_odoo_copy_catalogs` | `studio.write` | Byte-for-byte copies of the six catalog CSVs into `studio-odoo/import`. |
| `studio_odoo_adopt_source` | `studio.write` | Copies one source CSV whose header already equals the named template. Different headers are rejected and nothing is written. |
| `studio_odoo_write_import` | `studio.write` | Writes one data CSV. Every cell is a string. `source_files` must exist under `studio-odoo/sources`. |

Catalog files, copied unchanged:

`products.csv`, `tax-codes.csv`, `analytic-accounts.csv`, `fiscal-positions.csv`, `journals.csv`, `coa-extra.csv`.

Data files, filled only from workspace sources:

`company-identifiers.csv`, `partners.csv`, `gst101a-periods.csv`, `fiscal-years.csv`, `opening-balances.csv`, `customer-invoices.csv`, `vendor-bills.csv`, `gst-period-summary.csv`, `bank-import.csv`, `payroll-summaries.csv`, `platform-statements.csv`, `periods-in-dispute.csv`, `owner-transfers.csv`, `recurring-payments.csv`, `assets.csv`, `tco-kwh.csv`, `rdti-candidates.csv`, `fbt-schedule.csv`, `entertainment-addback.csv`.

`tco-kwh.csv` is written with `odoo_import: false`. Do not import it into Odoo.

## Workspace layout

Use a workspace that is not the studio repository.

```text
<workspace>/studio-odoo/sources/
  gst-returns/
  income-tax/
  invoices/
  bills/
  bank/
  platforms/
  payroll-summaries/
  screenshots/
  grants/
  fbt/
  rdti/
  entertainment/
<workspace>/studio-odoo/import/
  <gather-pack csv files>
  manifest.json
```

The folder names match `docs/templates/nas-folder-layout.md` in the studio checkout. The import pack stays in the workspace. Do not copy filled IRD or GST values back into the studio git tree.

## Rules the tools enforce

- A missing required cell stops that file. The PA must not substitute `0`, `EXAMPLE`, or a guessed tax treatment.
- Box 8 must equal (Box 5 minus Box 6) times 3 divided by 23, compared in cents, half up. The source figures are not rewritten.
- `PLG-GRANT` and `PLG-RD` accept `GST15_S`, or `GST_EXEMPT_S` when the source says the accountant set that override. `GST0_EX_S` is rejected for those products.
- Product, tax, analytic, journal, and fiscal-position values must already exist in the bound templates.
- An account code that is not in `coa-extra.csv` is a warning. Confirm it on the New Zealand chart. It is not replaced.
- Fiscal years must run from 1 April to 31 March of the next year.
- `sol_sector` is `plg-studio`, `founder-personal`, or `ventures`.
- `gst_basis` is `invoice`, `payments`, or `hybrid`.
- `gst_frequency` is `monthly`, `two_monthly`, or `six_monthly`.
- `gst_status` is `registered`, `not`, or `deregistered`.
- `EXAMPLE` placeholders and `project-spicy` are rejected.
- Amounts and dates are strings copied from the source (`100.00`, `2024-04-15`). A JSON number is rejected so cents are not changed.
- A referenced myIR PDF, bank file, or platform statement must already be under `studio-odoo/sources`.
- Workspace file reads are UTF-8 text. When a PDF cannot be read, the box figures have to be in a UTF-8 file as well. A failed read is not a source of numbers.

## What the PA will not do

- Guess the studio path.
- Map a CSV onto a template when the headers differ.
- Invent a product code, tax rate, or marketplace GST treatment.
- Post `tco-kwh.csv` to Odoo.
- Call the Odoo API or lodge a GST return.
- Write the import pack inside `plg-odooacc`.

The beginner click-path is [the Studio Odoo dummies guide](../user/dummies-studio-odoo.md). The skill is `studio-odoo-import`.

SOL Business, SOL Docs, and SOL Engineer do not receive these tools. Ask `sol_pa`.
