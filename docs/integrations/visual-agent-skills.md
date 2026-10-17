# Visual agent skills

For operator prompts and setup, read [Visual artifacts](../user/visual-agent-artifacts.md). For executed checks and manual acceptance, read [Visual skills testing](../testing/visual-agent-skills.md).

The built-in skill root is `<application root>/skills`. `SkillManager.for_agent`
also discovers `<workspace>/.agents/skills`, `.claude/skills`, `.codex/skills`
and `skills`. These instructions do not grant tool permissions. Global
`~/.agents/skills` is a conventional installation location for other harnesses;
SOL-Lite does not automatically trust or scan the home directory.

```text
skills/
  architecture-diagrams/SKILL.md
  slide-deck-generator/SKILL.md
  image-markup-ui/SKILL.md
```

Each manifest contains standard YAML `name` and `description`, plus this local
metadata extension (a string, not an executable hook):

```yaml
metadata:
  trigger-phrases: "slide deck|slides|marp|pptx|powerpoint"
```

`inspect_directory` parses the metadata with `yaml.safe_load`. `prompt_context`
matches case-insensitive whole phrases (allowing repeated whitespace) and
explicit `$skill-name` mentions. Every matching skill's full Markdown is
injected, outside the generic four-skill cap. Existing specialist workflows
remain active. Selection is lexical, not a semantic classifier: phrase mentions
in negated requests can select instructions; the agent must obey user intent.

The existing interactive agent loop already performs this concrete registration:

```python
from pathlib import Path
from sol_lite.skills.manager import SkillManager

manager = SkillManager(Path(application_root), Path(state_root))
# Repeat per user turn, using the actual user request and active agent ID.
runtime.skill_context = manager.prompt_context(
    active_agent_id, Path(workspace_root), user_request
)
```

`AgentRuntime` injects `skill_context` into its system messages. The runtime,
workspace and state variables above are host-owned values, not new APIs. For an
independent harness that uses message lists directly:

```python
context = manager.prompt_context(active_agent_id, Path(workspace_root), user_request)
messages = [
    {"role": "system", "content": base_system_prompt + "\n\n" + context},
    {"role": "user", "content": user_request},
]
```

Use `write_workspace_file` for raw `.mmd`, `.excalidraw`, `.svg`, `.md`, JSON and
HTML output within existing permissions. The native `artifact_create` tool can
author typed PPTX specifications when its optional dependency exists; it does
not convert arbitrary HTML to PPTX. Native renderers retain their existing
permission checks. No new execution service, dependency installation, remote
upload or scheduled rendering is introduced by these skills.

Optional tools: Mermaid CLI (`mmdc`, Node.js and compatible browser), Marp CLI
(`marp`, Node.js and compatible browser for PNG/PPTX), `python-pptx`, and Inkscape.
Installed tools are probed before use. An explicitly requested installation may
use the host's permitted package manager. Container/service rendering requires
an actual configured command or endpoint and its documented contract; none is
assumed. Fallbacks produce source plus local HTML/SVG and clearly report missing
binary exports. Ray.so is a reference application, not an assumed API.

The native dependency probe does not currently include Marp or Inkscape; check those commands separately. Direct CLI execution also requires the host terminal allowlist to permit the command. No renderer command permissions are added by manifest discovery. The fallback instructions are agent procedures, not a newly implemented deterministic conversion engine.

PLG_Ai_Interface's current `/api/lite/v1` bridge provides pairing, memory/RAG
access and proposals, not artifact rendering or local skill prompt injection.
No Interface code change is required for these locally executed Lite skills.
A future remote-renderer connection needs an explicit endpoint and authentication
contract; it must not be implied by a skill manifest.

References checked for tool commands and formats:
- https://github.com/mermaid-js/mermaid-cli
- https://docs.excalidraw.com/docs/codebase/json-schema/
- https://docs.excalidraw.com/docs/@excalidraw/excalidraw/api/utils
- https://github.com/marp-team/marp-cli
- https://github.com/raycast/ray-so
