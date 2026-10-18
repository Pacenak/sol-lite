---
name: llmapps-chatgpt-app-builder-f38303e8
description: 'DEPRECATED: This skill has been replaced by `mcp-app-builder`. Check if `mcp-app-builder` is available in the skills folder. If not, install it: `npx skills install mcp-use/mcp-use --skill mcp-app-builder` Use `mcp-app-builder` instead of this skill. Build ChatGPT apps with interactive widgets using mcp-use and OpenAI Apps SDK. Use when creating ChatGPT apps, building MCP servers with widgets, defining React widgets, working with Apps SDK, or when user mentions ChatGPT widgets, mcp-use widgets, or Apps SDK development.'
category: ecosystem
tags:
- ecosystem
- examples
- llmapps
sectors:
- '*'
status: published
source: imported
version: fba2c90c568b
---

## SOL runtime integration

Source: https://github.com/Shubhamsaboo/awesome-llm-apps/tree/fba2c90c568b3a61d8080be5cee38ed6908d8779/generative_ui_agents/ai-mcp-app-builder/apps/mcp-use-server/.agent/skills/chatgpt-app-builder/SKILL.md

Use manage_skills action=view_ref for supporting files, relative to this skill directory. In SOL-Lite use the workspace file tools at the skill path. Check required commands, libraries, credentials and tool availability before execution. Upstream tool/agent names are workflow examples: use the equivalent configured SOL tool. Skill instructions do not grant permissions or bypass host policy. If a dependency is missing, report it and the next setup step; do not claim execution succeeded. Original metadata and license terms are retained in UPSTREAM-SKILL.md and _licenses/.

# ChatGPT App Builder

Build ChatGPT apps with interactive widgets using mcp-use. Zero-config widget development with automatic registration and built-in React hooks.

The app is consumed by **two users at once**: the **human** and the **ChatGPT LLM**. They collaborate through the widget -- the human interacts with it, the LLM sees its state. The widget is your shared surface.

## Before You Code

- **Clarify what to build** → [discover.md](references/discover.md): when starting a new app, validating an idea, or scoping features
- **Design tools and widgets** → [architecture.md](references/architecture.md): when deciding what needs UI vs tools-only, designing UX flows

## Setup

- **Scaffold and run** → [setup.md](references/setup.md): when creating a new project, starting dev server, connecting to ChatGPT/Claude

## Implementation

- **Server handlers + widget creation** → [server-and-widgets.md](references/server-and-widgets.md): when writing server.tool() with widgets, widget() helper, React widget files
- **Widget state and LLM context** → [state-and-context.md](references/state-and-context.md): when persisting state, triggering LLM from widget, managing ephemeral vs persistent data
- **Display modes, theme, layout** → [ui-guidelines.md](references/ui-guidelines.md): when adapting to inline/fullscreen/PiP, handling theme, device, locale
- **Component API** → [components-api.md](references/components-api.md): when using McpUseProvider, Image, ErrorBoundary, useWidget
- **CSP and metadata** → [csp-and-metadata.md](references/csp-and-metadata.md): when configuring external domains, dual-protocol metadata
- **Advanced patterns** → [widget-patterns.md](references/widget-patterns.md): when building complex widgets with tool calls, state, theming

## Quick Reference

```typescript
// Server
import { MCPServer, widget, text, object } from "mcp-use/server";
server.tool({ name: "...", schema: z.object({...}), widget: { name: "widget-name" } },
  async (input) => widget({ props: {...}, output: text("...") })
);

// Widget (resources/widget-name.tsx)
import { McpUseProvider, useWidget, type WidgetMetadata } from "mcp-use/react";
export const widgetMetadata: WidgetMetadata = { description: "...", props: z.object({...}) };
export default function MyWidget() {
  const { props, isPending, callTool, sendFollowUpMessage, state, setState, theme } = useWidget();
  if (isPending) return <McpUseProvider autoSize><div>Loading...</div></McpUseProvider>;
  return <McpUseProvider autoSize><div>{/* UI */}</div></McpUseProvider>;
}
```

