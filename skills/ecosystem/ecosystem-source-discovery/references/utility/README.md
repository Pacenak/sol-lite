# Utility Skills

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](https://opensource.org/licenses/MIT)
[![Skills](https://img.shields.io/badge/Skills-10-brightgreen?style=for-the-badge)](#skills)
[![Agents](https://img.shields.io/badge/Works%20with-Claude%20Code%20·%20Codex%20·%20Cursor%20·%20Windsurf%20·%20Devin-blue?style=for-the-badge)](#compatibility)
[![Last Update](https://img.shields.io/github/last-commit/g-shevchenko/utility-skills?label=Last%20update&style=for-the-badge)](https://github.com/g-shevchenko/utility-skills/commits)

Utility skills for AI coding agents: Figma diagrams, free SEO stack, PDF signing,
YouTube transcription, Zoom hosting, remote Mac access, talk decks, n8n cleanup,
and design system reference.

Created from production operating patterns, rewritten as a self-contained public
package. No Workspace dependencies — works in any repo with any agent.

> **Deep-dive write-up:** *Utility Skills — open-source tools for AI agents*
> — the research article behind this repo, covering each skill, its
> production origin, and the public/private boundary.
> [Read it on gregshevchenko.com](https://gregshevchenko.com/research/utility-skills/).

## Table of Contents

- [Quick Start](#quick-start)
- [Skills](#skills)
- [Compatibility](#compatibility)
- [Composes With](#composes-with)
- [Install](#install)
- [Verify Before Install](#verify-before-install)
- [External Dependencies](#external-dependencies)
- [Repository Structure](#repository-structure)
- [Contributing](#contributing)
- [License](#license)

## Quick Start

```bash
git clone https://github.com/g-shevchenko/utility-skills.git
cd utility-skills
bash scripts/install.sh
```

Then in your agent chat:

```text
use utility skills stack
```

That's it. The skills are now available to your agent.

## Skills

| Skill | Purpose | Trigger phrase |
|---|---|---|
| `figma-mcp-free` | Figma diagrams on free Starter plan — blocks, microservices, architecture, user flow, UI mockups via Plugin API | `use figma mcp free` |
| `figma-diagram-visualization` | Scientific algorithm for building diagrams/dashboards/visualizations in Figma | `use figma diagram visualization` |
| `free-seo-stack` | Free alternatives to Semrush/Ahrefs/Ubersuggest — Lighthouse, CrUX, GSC, Bing, Yandex, IndexNow, rank audit, backlinks, security | `use free seo stack` |
| `pdf-signing` | Add stamp/seal/signature to PDF — secure local signing assets, visual placement verification | `use pdf signing` |
| `youtube-transcribe` | yt-dlp subs → faster-whisper large-v3 → Groq fallback | `use youtube transcribe` |
| `zoom-host` | Create Zoom meetings on shared Pro host — public join_url, facilitator fetches start_url via Credential Gateway | `use zoom host` |
| `remote-mac-access` | Reverse SSH tunnel via VPN relay — connect to team Mac behind NAT/firewall | `use remote mac access` |
| `talk-deck-builder` | PDF talk deck for presentations — brand-style | `use talk deck builder` |
| `n8n-temp-cleanup` | Discover and delete temp/one-shot n8n workflows | `use n8n temp cleanup` |
| `pantheon-style` | Design system tokens reference (WCAG tables, anti-patterns, motion) | `use pantheon style` |

### Skill categories

**Design & visualization (3):** figma-mcp-free, figma-diagram-visualization, pantheon-style

**SEO & web (1):** free-seo-stack

**Document production (2):** pdf-signing, talk-deck-builder

**Media & communication (2):** youtube-transcribe, zoom-host

**Infrastructure (2):** remote-mac-access, n8n-temp-cleanup

## Compatibility

| Agent | Support | Install path |
|---|---|---|
| Claude Code | ✅ | `$HOME/.claude/skills` |
| OpenAI Codex | ✅ | `$HOME/.codex/skills` (default) |
| Cursor | ✅ | `$HOME/.cursor/skills` |
| Windsurf | ✅ | `$HOME/.codeium/windsurf/skills` |
| Devin | ✅ | via skill invocation |
| Gemini CLI | ✅ | via skill invocation |
| Antigravity | ✅ | via skill invocation |

Skills follow the [Anthropic Skills open standard](https://github.com/anthropics/skills) (December 2025).

## Composes With

- [agentic-engineering-skills](https://github.com/g-shevchenko/agentic-engineering-skills) — agent MVP blueprint, handoffs, overnight queues, architecture refactoring
- [agentic-quality-skills](https://github.com/g-shevchenko/agentic-quality-skills) — TDD, quality gates, golden benchmarks, PBT
- [mcp-token-savers](https://github.com/g-shevchenko/mcp-token-savers) — 21 local MCP servers

## Install

```bash
# Default (Codex)
bash scripts/install.sh

# Claude Code
bash scripts/install.sh --target "$HOME/.claude/skills"

# Cursor
bash scripts/install.sh --target "$HOME/.cursor/skills"

# Windsurf
bash scripts/install.sh --target "$HOME/.codeium/windsurf/skills"

# Dry run (preview without writing)
bash scripts/install.sh --dry-run
```

The installer:
- Copies skills to the target directory (default: `$HOME/.codex/skills`)
- Optionally writes a managed block to `AGENTS.md` in the current workspace
- Refuses unsafe targets (`/`, `$HOME`, `.`)
- Creates a backup before replacing an existing skill

## Verify Before Install

Clone and inspect first:

```bash
git clone https://github.com/g-shevchenko/utility-skills.git
cd utility-skills
bash scripts/doctor.sh
bash scripts/audit-public-surface.sh
```

- `doctor.sh` — verifies all skills have required files and frontmatter
- `audit-public-surface.sh` — scans for secrets, private paths, and placeholder markers

See [VERIFY_BEFORE_INSTALL.md](VERIFY_BEFORE_INSTALL.md) and [SECURITY.md](SECURITY.md) for details.

## External Dependencies

Some skills reference external services or tools. All endpoints are configurable —
no hardcoded internal URLs. See each skill's `SKILL.md` for setup instructions.

| Skill | Dependency | Required? |
|---|---|---|
| `figma-mcp-free` | Figma account (free Starter plan) | Yes |
| `figma-diagram-visualization` | Figma account (free Starter plan) | Yes |
| `youtube-transcribe` | yt-dlp, faster-whisper | Yes |
| `youtube-transcribe` | Groq API key | Optional (fallback only) |
| `zoom-host` | Zoom Pro account | Yes |
| `remote-mac-access` | VPN relay (any provider) | Yes |
| `n8n-temp-cleanup` | n8n instance | Yes |
| `free-seo-stack` | Public APIs (Lighthouse, CrUX, GSC, Bing, Yandex) | Yes |
| `pdf-signing` | None (local only) | — |
| `talk-deck-builder` | None (local PDF gen) | — |
| `pantheon-style` | None (reference only) | — |

## Repository Structure

```
utility-skills/
├── skills/
│   ├── figma-mcp-free/                # Figma diagrams on free plan
│   ├── figma-diagram-visualization/   # Scientific diagram building
│   ├── free-seo-stack/                # Free Semrush/Ahrefs alternatives
│   ├── pdf-signing/                   # Add stamp/seal/signature to PDF
│   ├── youtube-transcribe/            # yt-dlp → whisper → Groq
│   ├── zoom-host/                     # Create Zoom meetings
│   ├── remote-mac-access/             # Reverse SSH tunnel via VPN
│   ├── talk-deck-builder/             # PDF talk deck for presentations
│   ├── n8n-temp-cleanup/              # Delete temp n8n workflows
│   └── pantheon-style/                # Design system tokens reference
├── scripts/
│   ├── install.sh                     # Copy skills to target directory
│   ├── doctor.sh                      # Verify repo structure
│   └── audit-public-surface.sh        # Scan for secrets/private markers
├── agent-docs/
│   └── AGENTS.managed-block.md        # Managed block for AGENTS.md
├── LICENSE
├── SECURITY.md
├── VERIFY_BEFORE_INSTALL.md
└── README.md
```

## Contributing

Contributions are welcome. Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feat/your-skill`)
3. Add your skill under `skills/` with a `SKILL.md` (YAML frontmatter + Markdown)
4. Run `bash scripts/doctor.sh` and `bash scripts/audit-public-surface.sh`
5. Open a pull request

### Skill format

Each skill is a directory with at minimum:

```yaml
---
name: your-skill-name
description: Use when [trigger condition]. [What the skill does].
---
```

Followed by Markdown instructions. Optionally bundled with scripts, references, and eval fixtures.

## License

MIT — see [LICENSE](LICENSE).
