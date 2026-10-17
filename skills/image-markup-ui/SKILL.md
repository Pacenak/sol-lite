---
name: image-markup-ui
description: Frame code snippets, annotate screenshots and beautify UI layouts using local SVG and HTML with optional PNG export.
metadata:
  trigger-phrases: "image markup|annotate screenshot|annotate image|code screenshot|code image|ray.so|beautify|beautification|ui polish"
---

# Code, image markup and UI beautification

## Execution
1. Identify the mode: code frame, screenshot annotation, or UI layout polish. Read supplied code/image and preserve its meaning. Do not silently rewrite code or invent unseen screenshot content. If a requested image is missing, request that image; code-only and layout work can proceed independently.
2. Save a local `layout.json` describing the design. This is a SOL-Lite layout contract, NOT an official Ray.so or Figma import schema. Ray.so is an optional open-source reference UI; do not invent a public API, CLI, theme ID or undocumented query parameter. Never upload private code to it without content authorization.
3. Default canvas: landscape 1600 x 900 (16:9), square 1200 x 1200 (1:1), portrait 1080 x 1350 (4:5). Use the requested dimensions when specified. Record logical pixels and export scale separately: output pixel dimensions equal logical dimensions times scale. Default scale 1; use 2 only when higher resolution is required. Use 64 px framing, 16 px corner radius, 24 px internal padding; system monospace 24 px, line-height 1.5 for code, system sans-serif for labels. Retain transparency when requested, otherwise use an explicit background.
4. For images, preserve aspect ratio with contain: scale = min(available width / image width, available height / image height), center with offsets. Transform every annotation using that same scale and offset. Crop only when requested; record source crop coordinates and retain the original. Inspect EXIF orientation or use visually oriented dimensions before placing annotations. Mark redactions as redactions; do not treat a translucent annotation as secure pixel removal.
5. For code, expand tabs consistently (default 2 spaces) and preserve whitespace. Use `<pre><code>` with HTML escaping (`&`, `<`, `>`, quotes for attributes). Do not interpret code as HTML. Show line numbers only if requested. Wrap at safe token boundaries only when meaning is preserved; otherwise widen the frame or split the snippet. Do not use ellipses that could be mistaken for executable source. Syntax highlighting is optional; plain monospace is the zero-dependency fallback.
6. For UI polish, use a 4/8 px spacing scale, consistent alignment and reusable typography/color tokens. Use CSS grid/flex for responsive layouts and logical reading order. Maintain at least 4.5:1 contrast for normal text and 3:1 for large text. Keep annotations numbered with a text legend so color is not the only signal. Avoid arbitrary gradients, excessive shadows, fake badges and changes to real screenshot data.
7. Write a standalone `markup.svg` and/or `markup.html` using inline styles and no external libraries. For portable SVG, use native `rect`, `text`, `tspan`, `path` and embedded image data rather than `foreignObject`. Escape XML text. If embedding the source image is unavailable, ship it adjacent to HTML with a relative path and disclose that dependency; do not claim the HTML is single-file. Include a textual annotation legend.
8. If PNG is required, probe an installed browser/exporter. With installed Inkscape, run `inkscape markup.svg --export-type=png --export-filename=markup.png --export-width=1600`. No Inkscape means return SVG/HTML and report PNG as unavailable, unless an authorized installed browser or configured renderer can export it. Do not invent screenshot tools or rename SVG to PNG. Optional installation/container execution must follow host permissions and explicit setup intent; never assume an external renderer URL.
9. Validate dimensions, annotation bounds and file references. Open the result if a viewer exists; check long lines, font substitution, image orientation and small-screen legibility. Verify PNG signature and actual pixel dimensions if exported. Retry at most twice, then report limitations, source paths, layout parameters and export status. Do not claim visual inspection unless performed.

## Local parameter example
```json
{"mode":"code-frame","canvas":{"width":1600,"height":900,"scale":1,"background":"#0f172a"},"frame":{"padding":64,"radius":16},"code":{"language":"python","fontFamily":"monospace","fontSize":24,"lineHeight":1.5,"tabSize":2,"lineNumbers":false},"imageFit":"contain","annotations":[]}
```
For annotations record source-space rectangles, for example `{"id":"1","x":120,"y":80,"width":240,"height":64,"label":"Primary action"}`. Preserve source dimensions alongside these coordinates.

## SVG example
```svg
<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="900" viewBox="0 0 1600 900" role="img" aria-labelledby="title">
 <title id="title">Python code frame</title>
 <rect width="1600" height="900" fill="#0f172a"/>
 <rect x="64" y="64" width="1472" height="772" rx="16" fill="#1e293b"/>
 <text x="96" y="128" fill="#f8fafc" font-family="monospace" font-size="24">print(&quot;Hello&quot;)</text>
</svg>
```
