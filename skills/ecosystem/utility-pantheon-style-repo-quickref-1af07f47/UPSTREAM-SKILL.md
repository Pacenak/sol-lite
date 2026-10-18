---
name: pantheon-style-repo-quickref
description: Repo-local QUICK REFERENCE for the your Pantheon design system — token values plus the canonical file paths inside THIS repo (your-ui/app.css, index.html, favicon, the catalog rules doc). Use when you need the Pantheon token cheat-sheet or those repo paths. For the full design-system spec (rationale, WCAG tables, anti-patterns, motion) use the `pantheon-style` skill instead.
composes_with:
  - figma-mcp-free    # Pantheon tokens exported to and rendered on Figma canvas
  - tokens-pipeline   # Style Dictionary tokens-pipeline generates Pantheon token files
  - talk-deck-builder # presentation decks follow Pantheon visual identity
---

# Pantheon Style — repo quick reference (NOT the full spec)

> **Это не полный скилл.** Переименован 2026-07-28 из `pantheon-style` в
> `pantheon-style-repo-quickref`, чтобы не конкурировать с полной спецификацией за
> одно имя в каталоге скиллов: при совпадении `name:` побеждает одна запись, и
> затенение полной спецификации (23 958 B) этим стабом (1 949 B) прошло бы незаметно.
> Каталог файла не переименован — на путь `.claude/skills/pantheon-style/SKILL.md`
> ссылаются `figma-mcp-free/SKILL.md` и рубрика `hwai-stack-mode/golden.json`.


Canonical skill: `~/.claude/skills/pantheon-style/SKILL.md` (full spec)
Live reference: https://pantheon.example.com

## Quick reference

- **Bg**: `#181818` dark / `#fafaf9` light (dark is Cursor / VS Code Dark+ inspired — warm, not pitch-black)
- **Raised surfaces** (dark): `#1e1e1e` cards · `#252526` subtle · `#2d2d30` hover
- **Text** (dark): `#e4e4e4` fg · `#b8b8b8` dim · `#8a8a8a` muted · `#6a6a6a` faint
- **Borders** (dark): `rgba(255,255,255,0.12)` default · `rgba(255,255,255,0.22)` strong — **visible**, not hairline
- **Accent**: `#33ffff` cyan (dark) / `#0891b2` (light) — identity, do not change
- **Display font**: Instrument Serif italic (Google Fonts)
- **Body font**: Inter
- **Mono font**: JetBrains Mono
- **Spacing base**: 4px
- **Content max**: 1200px
- **Motion**: 220ms `cubic-bezier(0.22, 1, 0.36, 1)`

## Canonical files

- `your-ui/app.css` — full CSS, copy-pasteable
- `your-ui/index.html` — shell pattern
- `your-ui/assets/favicon.svg` — Π monogram favicon
- `the catalog rules doc` — system integration rules

## See also

- Full skill: `~/.claude/skills/pantheon-style/SKILL.md`
- Live site: https://pantheon.example.com
- Inspiration: https://trymirai.com
