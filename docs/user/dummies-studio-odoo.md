# Studio Odoo import: beginner guide

This is the copy/paste path for SOL PA to build Studio Odoo import files from documents you add to a workspace.

SOL-Lite writes CSV files. It does not open Odoo, and it does not file myIR. You import the finished CSVs yourself, in Odoo, after you have checked them.

The studio checkout used below is:

```text
E:\git\plg-studio\plg-odooacc
```

That path is the one you give the PA. It is not built in. If your checkout is somewhere else, use that path instead. Do not let the PA invent one.

## 1. Open SOL-Lite

```powershell
cd E:\git\plg-sol\PLG_Ai_Lite
.\scripts\start.bat
```

When SOL-Lite asks for a workspace, use a separate import folder. Example:

```text
E:\sol-lite-WS\odoo-import
```

Create it first if it does not exist:

```powershell
New-Item -ItemType Directory -Force -Path E:\sol-lite-WS\odoo-import
```

Inside SOL-Lite:

```text
/use sol_pa
/workspace
```

`/workspace` must print `E:\sol-lite-WS\odoo-import` (or the other import folder you chose). The studio checkout is only the bind path.

## 2. Make the source folders

In PowerShell, from any directory:

```powershell
$root = "E:\sol-lite-WS\odoo-import\studio-odoo\sources"
New-Item -ItemType Directory -Force -Path $root | Out-Null
foreach ($name in @(
  "gst-returns","income-tax","invoices","bills","bank","platforms",
  "payroll-summaries","screenshots","grants","fbt","rdti","entertainment"
)) {
  New-Item -ItemType Directory -Force -Path (Join-Path $root $name) | Out-Null
}
Get-ChildItem $root
```

You should see those twelve folders. Put source documents in the matching folder:

| Put this here | Folder |
|---|---|
| GST101A PDFs | `gst-returns` |
| IR4 / income-tax packs | `income-tax` |
| Customer invoice CSV or PDF | `invoices` |
| Supplier bills | `bills` |
| Bank OFX or CSV | `bank` |
| Steam / Epic statements | `platforms` |
| IR345 payday summaries | `payroll-summaries` |
| Grant or Callaghan contracts | `grants` |
| FBT papers | `fbt` |
| RDTI evidence | `rdti` |
| Entertainment invoices | `entertainment` |

Do not put `project-spicy` files in this workspace. Do not put founder-personal IRD papers in a Pacen Life Games Limited pack. Use a second workspace for founder personal.

## 3. Bind the studio checkout

Paste this to SOL PA. Change the path only if your checkout is not the one below.

```text
Bind this workspace to the Studio Odoo checkout at E:\git\plg-studio\plg-odooacc.
Use studio_odoo_bind. Do not guess another path. Do not write any import file yet.
```

Approve the bind when SOL-Lite asks. A pass looks like this:

- the tool result says `"ok": true`
- `studio_root` is `E:\git\plg-studio\plg-odooacc`
- `odoo_api` is `not used`

If the tool says the templates are missing, stop. You are not pointed at the studio checkout.

## 4. Ask for the column names

```text
Use the studio-odoo-import skill.
Call studio_odoo_schema and studio_odoo_inventory.
Tell me which source files match a template exactly, and which do not.
Do not map columns yourself. Do not write files yet.
```

Approve the read. A CSV matches only when its header is the same as the studio template, in the same order. If the headers differ, the PA must say so and write nothing for that file.

## 5. Copy the catalogs

These six files are copied unchanged. The PA must not add SKUs or tax rates.

```text
Copy the Studio Odoo catalogs into this workspace with studio_odoo_copy_catalogs.
Do not edit them.
```

Approve the write. Afterwards these files exist:

```text
E:\sol-lite-WS\odoo-import\studio-odoo\import\products.csv
E:\sol-lite-WS\odoo-import\studio-odoo\import\tax-codes.csv
E:\sol-lite-WS\odoo-import\studio-odoo\import\analytic-accounts.csv
E:\sol-lite-WS\odoo-import\studio-odoo\import\fiscal-positions.csv
E:\sol-lite-WS\odoo-import\studio-odoo\import\journals.csv
E:\sol-lite-WS\odoo-import\studio-odoo\import\coa-extra.csv
```

Check one copy is identical to the studio template:

```powershell
fc.exe /b E:\git\plg-studio\plg-odooacc\docs\templates\products.csv E:\sol-lite-WS\odoo-import\studio-odoo\import\products.csv
```

`FC: no differences encountered` is a pass.

## 6. Build one import file

Start with one file whose source you can read. Example, after you have placed a customer-invoice CSV that already has the studio header:

```text
Adopt studio-odoo/sources/invoices/<your-file>.csv as customer-invoices.csv.
If the header does not match, stop and show me both headers. Do not rename columns.
```

If your source is a PDF or a spreadsheet with different columns, paste:

```text
Read the source files under studio-odoo/sources. For customer-invoices.csv, call studio_odoo_schema first.
Write a row only with values that are written in those source files.
If partner, invoice date, product code, quantity, exclusive price, or tax code is missing, do not write the file. Name the missing cell.
Do not invent a product code or a tax code. Amounts must be strings copied from the source.
```

Approve the write. A pass:

- the tool result has `"ok": true` and a `path` under `studio-odoo/import/`
- `rows` is the number of data rows
- warnings are listed, not hidden
- the reply does not say the invoice was created in Odoo

Open the CSV and compare each cell with the source document. If a cell is not in the source, delete the import file and ask the PA to write it again without that cell.

## 7. GST101A rows

For each filed period, the PDF must sit in `studio-odoo/sources/gst-returns/`. SOL-Lite's file reader accepts UTF-8 text. If the PA cannot read the PDF, also put a UTF-8 `.txt` next to it with the box figures copied from the PDF. The PA copies boxes 5, 6, 8, 9, 11, 12, 13, and 15 from that text. It must not invent them when the PDF read fails. The import row still names the PDF, and that PDF has to be in the sources folder.

```text
Build gst101a-periods.csv from the PDFs in studio-odoo/sources/gst-returns.
Copy the boxes. Do not calculate a replacement Box 8.
If (Box 5 minus Box 6) times 3 divided by 23 does not match Box 8 in cents, stop and show both numbers.
```

Worked check from the studio runbook: Box 5 `115.00`, Box 6 `0.00`, Box 8 `15.00`.

Do not type `0.00` for a box the PDF does not show.

## 8. Files the PA must refuse

| You ask for this | The PA must |
|---|---|
| Import `tco-kwh.csv` into Odoo | Write it only as a report. `odoo_import` is false. |
| Add a new product SKU | Refuse. Catalog codes come from `products.csv`. |
| Mark a grant as `GST0_EX_S` | Refuse. `PLG-GRANT` / `PLG-RD` use `GST15_S`, or `GST_EXEMPT_S` only when the document says the accountant set that. |
| Guess Steam or Epic GST | Refuse. Copy the treatment already on the filed return. |
| Put the import pack inside `plg-odooacc` | Refuse. |
| File the GST return | Refuse. |
| Fill a blank with `EXAMPLE` or `0` | Refuse and name the blank. |

## 9. See what is still missing

```text
Call studio_odoo_status. List ready files, absent files, and warnings.
Do not create placeholder rows for the absent files.
```

Absent means you have not supplied the source yet. That is a gap to fill, not a row for the PA to invent.

## 10. What you do in Odoo afterwards

On the Command host, after the CSVs are checked:

1. Open Odoo at the address in the studio `docs/ACCESS.md`.
2. Use **Favorites → Import records** for one invoice first.
3. Compare the tax return to the myIR PDF.
4. Do not import `tco-kwh.csv`.

That click-path is in `E:\git\plg-studio\plg-odooacc\docs\GET-BOOKS-READY.md`. SOL PA does not perform it.

## 11. If something fails

| Message | What to do |
|---|---|
| No studio root | Paste the bind prompt in section 3. |
| Studio root is missing `init-gather-pack.ps1` | The path is not the studio checkout. |
| Workspace is inside the studio repository | `/new` and pick a folder outside `plg-odooacc`. |
| Header does not match | Do not rename columns in the tool. Fix the source CSV so its header equals the template, or leave the file unwritten. |
| Box 8 does not match | Read the PDF again. Do not change the boxes to force the formula. |
| Approval required | Approve that one call. A denied call did not write the file. |
