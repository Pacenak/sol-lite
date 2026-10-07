# Colour wheel — Pacen / PLG

All hues below are **derived from existing evidence**, not a new brand.

## Anchor

| Swatch | Hex | Hue (approx) | Source |
|--------|-----|--------------|--------|
| Pacen orange (company primary) | `#d87818` | 32° | SOL `21-DESIGN-TOKENS.md` marketing deck |
| Live SOL Command orange | `#e85d2c` | 16° | `plg-brand.css` — **drift**, reconcile later |
| NOC cyan | `#3ec6e0` | 189° | `plg-noc.css` |
| Core cyan (daily-use, desaturated) | `#2a8fa3` | 191° | Retune of `#1f8fa6` / `#3ec6e0` |

## Relationships (why this palette works)

```text
                 0° red
                  |
     32° ORANGE ---- Pacen brand primary
                  |
         analogous: gold Command ~38–42°  (#f5a623 exists — use as SOL Command badge only)
                  |
                  |
    189–212° CYAN/AZURE ---- complement / split-complement of orange
                  |
         Core product accent (studio infra)
```

- **Complementary:** orange 32° ↔ azure ~212°. Core cyan 189° is **adjacent to the complement** (split-complement). That is a valid two-hue system.
- **Analogous (warm):** orange → Command gold `#f5a623` → Outpost coral `#e06c75` (coral is a step toward red; keep as SOL **part** accent, not company primary).
- **Triadic:** unused. Do not add a third chromatic family for chrome.
- **Semantic triad (separate):** success green, warning gold, error red. These are **not** brand.

## Saturation / value rules

| Layer | Saturation | Value | Use |
|-------|------------|-------|-----|
| Neutrals | ~5–12% warm | stepped | 90% of pixels |
| Brand orange | medium | mid | CTA, mark tint, identity chip |
| Core cyan | **lower than today’s `#3ec6e0`** | mid | Core nav, links, focus |
| Semantic | medium | mid-high on dark | status only |
| VFX | very low alpha | — | hero / AI / incidents only |

**Avoid:** neon `#3ec6e0` as a persistent page wash; using orange **and** cyan at full saturation in the same header; purple as theme (`#7c6a9a` is SOL AI-only).

## Temperature

| Concept | Neutral temperature | Brand loudness |
|---------|---------------------|----------------|
| A Dual climate (**locked**) | Cool Core + warm SOL | Two climates, shared mark/type |
| B Pacen DNA | Warm (or neutralized-warm) everywhere | Orange identity, cyan Core accent |
| C Quiet instrument | Cool-neutral shell | Both hues small |
