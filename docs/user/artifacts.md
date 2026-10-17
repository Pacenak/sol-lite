# Premium documents and diagrams

For Mermaid/Excalidraw source, Marp/HTML decks, screenshot annotations and dependency-free SVG/HTML fallbacks, see [Visual artifacts](visual-agent-artifacts.md). The native tools below retain their typed input formats; the new skills do not add HTML conversion to `artifact_create`.

SOLlite creates editable DOCX reports, PPTX presentations, XLSX workbooks and
Mermaid diagrams through native artifact tools. LibreOffice exports Office files
to PDF without Microsoft Office. Mermaid exports SVG and high-resolution PNG.
Windows and macOS use the same tools and content specifications.

## Optional local setup

In the Python environment used to run SOLlite:

```text
python -m pip install -e ".[artifacts]"
```

Install LibreOffice from its official installer on Windows or macOS. On macOS
the standard `/Applications/LibreOffice.app` installation is detected; on Windows
the standard Program Files installation is detected. Install Node.js and then:

```text
npm install -g @mermaid-js/mermaid-cli
```

These steps are explicit user setup; SOLlite never installs dependencies during
generation. Run `artifact_dependencies` to check availability. No Microsoft
application, account or API is involved. PDF and PNG are usable without an
Office application; LibreOffice can edit the generated Office files.

## Native tools

- `artifact_dependencies`: read-only environment check.
- `artifact_create`: `path`, typed `spec`, optional `render` (default true),
  `plan` and `approval_id`. Paths end in `.docx`, `.pptx`, `.xlsx` or `.mmd`.
- `artifact_render`: existing `path`, fresh `output_directory`, `plan` and
  `approval_id`. Produces PDF and page previews or SVG/PNG diagrams.
- `artifact_validate`: read-only structural checks for an existing `path`.

All four agents expose these tools. SOL Docs specialises in artifact design;
other agents can create their own reports using the same pipeline. Writes use
existing runtime approval policy. Outputs must remain inside the approved
workspace, and existing output files are never overwritten. Use a new filename
or output directory for a revision.

## Content specifications

Every `spec` has a `title` and optional `theme` containing `font` (Arial by
default), `accent` (2457A7), and `text` (202938). Colours use six hexadecimal
digits without a hash. Unknown fields are rejected. These are content objects,
not scripts, HTML, executable templates or shell commands.

- Documents: `sections`, each with `heading`, `paragraphs`, `bullets` and
  optional rectangular `table` rows. Defaults are A4 and generous margins.
- Slides: `slides`, each with `title`, up to six `bullets`, and optional `notes`.
  Defaults are widescreen, editable text and large readable type.
- Workbooks: `sheets`, each with a unique `name`, typed cell `rows`, and optional
  `charts`. Bar charts accept `title`, `first_row`, `last_row`,
  `category_column`, `value_column` and optional `anchor`; the first row is the
  header. Charts default below the data and are included in the print area.
  Formula strings begin with `=`. Formulas remain editable; authoring alone
  does not calculate them. Independently verify calculations before delivery.
- Diagrams: `mermaid` source. Preserve `.mmd` with exports. Directives, HTML,
  interactive callbacks and external links are not supported.

Example document content:

```json
{
  "path": "reports/milestone.docx",
  "plan": "Create the requested milestone report and PDF preview",
  "spec": {
    "title": "Milestone review",
    "sections": [
      {"heading": "Decision", "paragraphs": ["Approve the next milestone." ]},
      {"heading": "Evidence", "table": [["Check", "Result"], ["Local validation", "Passed"]]}
    ]
  }
}
```

## Evidence and review

Results return absolute `outputs` and `previews` paths. `authored_unverified`
means the editable file exists but previews are unavailable or rendering was
not requested. `rendered_unreviewed` means previews exist, not that they were
visually approved. `visual_review` remains `not_performed`: these tools do not
have an image-inspection model. An agent with a separate image inspection
capability may inspect every preview and describe its actual findings.

Structural checks validate Office package integrity and flag dense slide text
and workbook error cells. They do not prove absence of clipping, overlap,
missing glyphs or incorrect formula results. Inspect rendered pages/slides and
diagram labels before calling a deliverable visually reviewed. Correct defects
and generate a new version. Missing renderers or failed conversions return
actionable warnings while preserving successfully authored source files.

Renderer subprocesses run without a shell, in isolated temporary directories,
with a 60-second limit per invocation. PDF previews are limited to 200 pages.
Office inputs with external relationships, macros or embedded objects are
rejected before rendering. External workbook formulas are unsupported.

## Cross-platform acceptance

On each target OS, install the optional dependencies, run the artifact unit and
integration tests, then generate a report, presentation, formula workbook,
flowchart and sequence diagram with rendering enabled. Verify PDF and diagram
exports, inspect every preview, and open the editable files in LibreOffice.
Run this on macOS with Microsoft Office absent. Mocked discovery tests do not
replace this real-host acceptance check.

The manually dispatched **Artifact acceptance on Windows and macOS** GitHub
workflow installs optional tools in isolated CI runners, runs real export tests
without Microsoft Office, and retains generated files and previews for visual
review. A passing export test still requires human or image-model inspection of
the uploaded previews before visual approval.
