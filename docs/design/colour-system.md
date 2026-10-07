# SOL-Lite Colour System

SOL-Lite uses the Pacen / PLG colour wheel as its visual source of truth. The palette is derived from existing Pacen / PLG evidence rather than introducing a new brand.

## Anchor colours

| Token | Hex | Use |
|---|---|---|
| Pacen orange | `#d87818` | SOL-Lite identity, primary identity accents, user-facing action emphasis |
| Live SOL orange | `#e85d2c` | Existing Live SOL colour; treated as a known drift and not used as the primary SOL-Lite token |
| NOC cyan | `#3ec6e0` | High-emphasis cyan only; not a persistent wash |
| Core cyan | `#2a8fa3` | SOL-Lite/Core navigation, links, focus and technical emphasis |
| Command gold | `#f5a623` | Approval and Command-style emphasis |
| Outpost coral | `#e06c75` | SOL-part accent only |
| AI purple | `#7c6a9a` | AI-specific accent only; not a general theme |

## Semantic colours

Success, warning and error colours are semantic status colours. They are not part of the Pacen brand family and should only be used to communicate state.

## Terminal rules

- Neutrals should dominate the interface.
- Warm SOL identity and cool Core technical emphasis form the locked Dual Climate approach.
- Do not use neon cyan as a persistent background or page wash.
- Do not use full-strength orange and cyan together in a single prominent header.
- Do not introduce purple as a general terminal theme.
- Status colours communicate runtime state and do not redefine the brand palette.
- Colour tokens are centralized in `src/sol_lite/ui/theme.py`.
- Markdown headings and links use the same token system so rendered agent responses remain visually consistent with the surrounding terminal.

## Runtime semantic mapping

| Runtime state | Terminal treatment |
|---|---|
| WORKING | Core cyan |
| SLOW | Warning / Command gold |
| STALLED | Error semantic |
| COMPLETED | Success semantic |
| FAILED | Error semantic |
| CANCELLED | Warning / Command gold |
| Approval required | Command gold |

The underlying source wheel specifies Pacen orange `#d87818`, Core cyan `#2a8fa3`, the stronger NOC cyan `#3ec6e0`, Command gold `#f5a623`, Outpost coral `#e06c75`, and the Dual Climate direction. See the supplied Pacen / PLG colour-wheel reference for the source rationale.
