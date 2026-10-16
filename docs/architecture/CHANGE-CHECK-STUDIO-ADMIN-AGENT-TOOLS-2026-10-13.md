# CHANGE CHECK — sol_studio_admin tools + studio-admin-toolbelt skill

Date: 2026-10-13 · Repo: PLG_Ai_Lite

## WHAT CHANGED?

- Expanded `sol_studio_admin` `tools.yaml` (workspace write/edit, git read, remote list, skill_install).
- Updated agent prompt + `config/agents.yaml` for 3-partition / pouch / Mac Carry.
- New builtin skill `skills/studio-admin-toolbelt/`; specialist routing triggers in skill manager.
- Terminal allowlist adds pouch diagnostics (`nmcli`, `ethtool`, `mmcli`, `ip`, …).
- Admin-belt `07-studio-admin-agent.md` matches tools/skill.

## WHY?

Admin agent was under-tooled for stick/pouch ops after full-setup docs landed; needed correct tools + skill without granting push/exploit powers.

## WHAT SYSTEMS ARE AFFECTED?

- Agent allowlist / prompt for `sol_studio_admin`
- Builtin skills discovery + prompt detail routing
- Terminal permission allowlist (all agents that share it)

## WHAT APIs CHANGED?

None HTTP. Tool allowlist surface for one agent.

## WHAT DATA CHANGED?

None.

## WHAT AGENTS ARE AFFECTED?

`sol_studio_admin` primarily; PA may still delegate to it when unlocked.

## WHAT SECURITY BOUNDARIES CHANGED?

Still unlock + allowlist gated. Still no push/PR merge on admin agent. Skills still do not grant permissions. Terminal allowlist slightly broader for network inspect commands.

## WHAT DOCUMENTATION MUST CHANGE?

Done: prompt, admin-belt 07, this CHANGE CHECK. Full setup already points at agent.

## WHAT TESTS MUST CHANGE?

`tests/unit/test_agent_tool_allowlist.py` — studio_admin allowlist assertions.
