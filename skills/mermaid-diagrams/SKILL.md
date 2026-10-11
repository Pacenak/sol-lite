---
name: mermaid-diagrams
description: Produce valid, maintainable Mermaid diagrams with stable identifiers and readable layout.
---

# Mermaid Diagrams

## Procedure
Use Mermaid syntax that is supported by common renderers. Keep node identifiers simple, labels human-readable, and relationships directional where direction matters. Validate syntax before delivery.

Supply source through artifact_create with an .mmd path. Avoid click handlers,
HTML, external links and configuration directives. Use artifact_render for local
SVG/PNG exports; a missing renderer means syntax and exports remain unverified.
Inspect exported labels, node spacing and edge crossings when preview inspection
is available. Preserve source alongside exported diagrams.


## SOL-Lite boundary
This skill provides reasoning guidance only. It does not grant filesystem, terminal, repository, network, skill-install, or application permissions. Runtime policy and explicit approvals remain authoritative.
