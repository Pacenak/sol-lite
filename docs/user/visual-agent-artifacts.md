# Visual artifacts for agents

SOL-Lite includes three visual skills for all four standard agent personas. They select instructions for generating editable files; tool access and actual export capability still depend on the host configuration.

## Start a task

Choose the intended workspace and agent, then use `/skills list` to confirm availability. `/skills show architecture-diagrams` displays a manifest. Built-in skills do not need a separate external import.

Example prompts:

```text
Use $architecture-diagrams. Read this repository and draw its confirmed API,
worker and storage relationships. Save Mermaid source and an SVG preview under
artifacts/architecture. Label inferred connections separately.

Use $slide-deck-generator. Create a five-slide decision deck from my supplied
notes. Save Marp Markdown and offline HTML under artifacts/rollout. Also export
PPTX and PNG if the required tools are available; report missing exports.

Use $image-markup-ui. Frame the supplied Python snippet on a 1600 by 900 canvas.
Preserve the code, save local layout JSON and SVG, and export PNG if possible.

Annotate the attached screenshot with numbered callouts for its primary action
and navigation. Preserve the image aspect ratio and include a text legend.
```

Provide the actual screenshot or its readable workspace path for image annotation. A filename alone does not give an agent image-inspection capability. The code-frame workflow can operate on text without a screenshot.

## Formats and fallbacks

- Diagrams: `.mmd` is editable Mermaid source; `.excalidraw` is an editable JSON scene. `.svg` is a browser-viewable preview. A manual SVG fallback is not a Mermaid renderer result. Excalidraw JSON parsing does not prove successful application import.
- Decks: `.md` is Marp source; standalone `.html` is viewable offline. Marp's normal PPTX output contains slide images. Editable text/shape PPTX requires a separate native authoring path such as `python-pptx`; arbitrary HTML conversion is not provided.
- Markup: `layout.json` records local design parameters; `.svg`/`.html` provide frames and annotations. This JSON is not an official Ray.so or Figma schema. PNG requires a working exporter.

Missing packages never justify writing HTML or SVG bytes into a `.pptx` or `.png` file. The agent should deliver the usable fallback and state which requested outputs remain unavailable.

## Optional renderer setup

Run setup in the environment that launches SOL-Lite. These commands install optional tools; they are not required for HTML/SVG source generation:

```powershell
python -m pip install -e ".[artifacts]"
npm install -g @mermaid-js/mermaid-cli @marp-team/marp-cli
```

Install Node.js before the npm step. Install Inkscape separately if its SVG-to-PNG exporter is wanted. Mermaid and Marp binary rendering also require a compatible browser. The artifacts extra includes `python-pptx` and the existing document dependencies. Follow the package's documented browser setup if a CLI is installed but cannot launch its browser.

Check command availability from a terminal:

```powershell
mmdc --version
marp --version
inkscape --version
python -c "import pptx; print(pptx.__version__)"
```

The native `artifact_dependencies` agent tool reports Office/Python and Mermaid availability; it does not currently report Marp or Inkscape. Probe those separately. Installation does not automatically add CLI names to the agent terminal allowlist. If direct execution is denied, use an existing native artifact tool where supported or have the owner configure the intended command access. Do not broaden permissions merely to generate a preview.

Containers and remote services are optional deployment choices, not installed features. Supply the actual command/endpoint and authentication contract before configuring one. The current PLG_Ai_Interface bridge does not render these artifacts.

## Review a deliverable

Ask the agent to return editable source, preview paths, actual tools used, missing exports and checks performed. Confirm diagram labels and connections, slide readability and annotation alignment. Opening every preview is needed for visual review; JSON/XML/package checks alone cannot detect all overlap, clipping or incorrect content.

For image markup, retain the original, use contain-fit unless cropping was requested, and record annotation coordinates relative to the original. A translucent overlay is not secure redaction. Do not upload private code/images to a public rendering site as an automatic fallback.

See [integration details](../integrations/visual-agent-skills.md), [troubleshooting](../debugging/skill-failures.md) and [acceptance tests](../testing/visual-agent-skills.md).
