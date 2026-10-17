# Skill Failures

Inspect the skill record, source type, source reference, hash, warnings and status.

A suspicious skill should be `QUARANTINED`, not activated. External GitHub discovery requires network permission before cloning.

## Visual skill troubleshooting

- Missing from `/skills list`: confirm the manifest is under application `skills/` or a supported workspace skills directory. Home `~/.agents/skills` is not automatically scanned. Inspect YAML `name`/`description` and the active workspace.
- Listed but full instructions absent: try an explicit `$architecture-diagrams`, `$slide-deck-generator` or `$image-markup-ui` mention. Manifest trigger phrases match whole phrases, not arbitrary substrings. Negated or quoted phrases may still select instructions.
- Metadata error: `metadata.trigger-phrases` must be a string separated by `|`, not a YAML array.
- Source exists but PNG/PPTX does not: check the actual installed exporter, browser availability and command permissions. `artifact_dependencies` does not probe Marp or Inkscape. Use `marp --version` or `inkscape --version` separately.
- CLI works in your terminal but the agent is denied: host PATH/environment and terminal allowlists are separate from installation. Keep the HTML/SVG fallback while the owner configures intended access.
- PPTX text is not editable: ordinary Marp PPTX output is image-based. Request native editable slide authoring when `python-pptx` is available.
- Excalidraw JSON passes syntax validation but import fails: use the installed library's serialization API or inspect the full element schema; skeletons are not serialized elements. Preserve Mermaid/SVG output while fixing import compatibility.
- Full battle gate fails on a skill count or build hash: the expanded catalogue exceeds the historical hard-coded preflight count. This is independent of routing tests. Do not delete skill assets or regenerate release hashes solely to hide the failure.

Record the user prompt, active agent/workspace, manifest path, tool output and actual files produced. See [visual test procedure](../testing/visual-agent-skills.md).
