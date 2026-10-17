---
name: slide-deck-generator
description: Create structured presentation decks as Marp Markdown and offline HTML with optional PowerPoint and PNG exports.
metadata:
  trigger-phrases: "presentation|presentations|slide|slides|slide deck|deck|marp|pptx|powerpoint"
---

# Structural presentations and slide decks

## Execution
1. Extract audience, decision, evidence and requested length. Use the user's structure when supplied; otherwise outline context, problem, evidence, proposal and next action. Keep factual claims traceable to supplied material; label missing values rather than fabricating metrics or testimonials.
2. Save `deck.md` with Marp frontmatter and `---` slide separators. Also write `deck.html` as a complete offline HTML document with inline CSS and semantic `<section aria-label="...">` slides. Markdown alone is editable source, not a browser-ready rendered deck.
3. Use 16:9 at 1280 x 720 by default; use 960 x 720 for requested 4:3. HTML slides use `aspect-ratio`, responsive width and print page breaks. Keep 64 px safe margins. Tokens: background `#f8fafc`, text `#0f172a`, secondary `#475569`, accent `#1d4ed8`; system sans-serif; title 44 px, body 28 px, caption 18 px; spacing 8/16/24/32/48/64 px. Scale the complete canvas on small screens rather than distorting its aspect ratio.
4. Give each slide one supported claim and a meaningful title. Choose semantic layouts: title + evidence; two-column comparison; full-width diagram; or chart + conclusion. Avoid paragraphs on slides, more than three primary points, tiny footnotes, decorative icons, stock gradients, repetitive card grids, and unsupported superlatives. Do not force every slide into the same template. Keep citations with the corresponding claim and detail in presenter notes or an appendix. Never shrink body text below 24 px to fit; split content instead. HTML needs accessible reading order, alt text and visible focus for any controls.
5. Check installed tools with `marp --version`, and inspect native `artifact_dependencies` if exposed. With installed Marp CLI run `marp deck.md -o deck.html`; for requested exports run `marp deck.md --pptx -o deck.pptx` and `marp deck.md --images png -o deck.png`. PNG/PPTX export additionally needs a compatible browser. Default Marp PPTX output is image-based; do not promise editable slide text. Keep Markdown alongside it. Do not use experimental editable export without verifying its installed support and layout fidelity.
6. If editable PPTX is required and `python-pptx` exists, use the native `artifact_create` tool with its published typed slide schema when available, or write explicit Python using `Presentation`, `Inches`, `Pt`, textboxes and shapes. Set widescreen dimensions explicitly and rebuild semantic slide objects; do not claim arbitrary HTML conversion. If neither authoring route is installed, deliver HTML/Marp and report PPTX as unavailable. HTML must still work without Marp, Python, network or fonts being installed.
7. If installation was explicitly requested, use the package manager permitted by the host; optional packages are `@marp-team/marp-cli` and `python-pptx`. Do not silently use `npx` to download packages. A configured container or renderer can be used only with its actual documented command/API and content authorization; fail back to local HTML if unavailable.
8. Inspect every slide in a browser or rendered previews when possible. Check clipping, title wrapping, chart labels, contrast and notes. Validate each requested file exists and is nonempty; for PPTX check it is a ZIP with `[Content_Types].xml` and `ppt/presentation.xml`. Package validity is not visual approval. Retry layout corrections at most twice; disclose checks that could not run and any missing exports.

## Marp example
```markdown
---
marp: true
size: 16:9
paginate: true
theme: default
---
# Approve the staged rollout
Start with one team and measure recovery time.
<!-- Presenter note: establish the decision owner. -->
---
# The pilot answers two questions
- Can operators recover a failed run?
- Can reviewers trace the generated artifacts?
```

## Dependency-free HTML example
```html
<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Rollout decision</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#cbd5e1;font-family:system-ui,sans-serif;color:#0f172a}
section{width:min(100%,1280px);aspect-ratio:16/9;margin:24px auto;padding:5%;background:#f8fafc;break-after:page}
h1{font-size:clamp(24px,3.44vw,44px)}p{font-size:clamp(18px,2.19vw,28px);line-height:1.4}
@media print{@page{size:landscape;margin:0}section{width:100%;margin:0}}
</style><section aria-label="Rollout decision"><h1>Approve the staged rollout</h1>
<p>Start with one team and measure recovery time.</p></section></html>
```
For content-heavy decks, adapt responsive sizing and inspect narrow viewports; this minimal example is one slide, not a universal layout engine. Escape user text before inserting HTML. Never embed untrusted scripts or remote assets.
