# Studio Admin Tool Belt Stick (500 GB M.2)

**Outcome:** One encrypted USB3 NVMe is a full personal **studio admin tool belt**: carry-mode Lite + brain on any running host, and boot-mode Linux with Lite **or** defensive SecCheck — without replacing Outpost/Command as SoT.

**Already true:** Dual-mode scaffold in `portable-stick/` (BRAIN launchers, `SOL_DATA_ROOT` / `SOL_WORKSPACE_ROOT`, boot HUMAN-OPS README, studio-tools stubs). Admin-only agent + SecCheck/lite-pen. **Superseded layout/docs:** 3-partition full setup — see `docs/user/admin-toolbelt-full-setup.md` and plan `2026-10-13-admin-toolbelt-full-setup.md`. Day-1: `docs/user/dummies-admin-stick-m2.md`. Lite host-git trust + Interface project-git exist on hosts.

**Not on this trip:** Windows To Go as default boot; shipping Kali/ISOs in git; auto-scanning foreign networks; putting Command pair secrets in plaintext on the stick; replacing `sol-git-upgrade` / live Outpost `data/`.

## Approach (recommended)

**Three personalities, two partitions**

| Mode | When | Personality |
|------|------|-------------|
| Carry | Host OS already up | Mount BRAIN → Lite + admin scripts + docs |
| Boot → Helper | USB boot | Small Linux, mount BRAIN, run Lite |
| Boot → SecCheck | USB boot (2nd entry / Ventoy ISO) | Defensive studio checker only; unlock BRAIN reports folder on purpose |

Optional later: pentest tools **only** behind an explicit “authorized lab” profile — not default.

```text
BOOT (~96GB)     EFI + Linux (Helper) + Ventoy slot for SecCheck ISO
BRAIN (~rest)    encrypted — Lite data, workspace, admin-belt/, models/, reports/
```

## Route

1. **Disk recipe** — Original two-volume recipe superseded by `SOLBOOT` / `SOLLITE` / `SOLBRAIN` in full-setup guide. **Check:** operator follows `admin-toolbelt-full-setup.md`.

2. **Admin belt pack on BRAIN** — Expand `brain/studio-tools/` into `admin-belt/` modules: Outpost/Command cheatsheets, Gitea/`sol-git-upgrade`, project-git, pairing, ACL/packs, battle-test pointers, backup/`data/` keep rules, safe-eject. Launchers stay as-is. **Check:** one README index lists every module; no secrets in examples.

3. **SecCheck profile (defensive)** — Add `boot/seccheck/` scripts + allowlist template (`hosts.allow.example`) that smoke-check **only listed** studio IPs/hostnames (TLS, SSH port presence, “is Command up”, no exploit payloads). Reports land in `workspace/sec-reports/`. **Check:** unit/smoke test with fake allowlist; refuses empty allowlist.

4. **Boot menu wiring (HUMAN-OPS)** — Guide: Helper desktop autostart Lite launcher; SecCheck as second GRUB entry or Ventoy ISO that mounts BRAIN read-only except `sec-reports/`. **Check:** dated Pass checkbox file (UNVERIFIED until hardware).

5. **Capacity budget** — Freeze a 500 GB map in the README (BOOT 96 GB, models ≤80 GB, brain data/workspace flexible, leave 20 GB free). **Check:** budget table committed; no “dump full model zoo” advice.

6. **Verify + CHANGE CHECK** — Tests for allowlist gate + path roots; CHANGE CHECK; pointer from getting-started / portable-stick README. **Check:** pytest green; live USB Pass still UNVERIFIED until you run it.

## Decisions

- Boot OS default = **Linux Helper**; SecCheck = **defensive checker first**, not full pentest distro.
- BRAIN holds identity (`data/`); BOOT is replaceable.
- Studio SoT stays on hosts/Gitea; stick is the **admin pouch**, not the product clone.
- **`sol_studio_admin` is an admin-only feature** (`requires_admin` + `features.studio_admin` / `SOL_STUDIO_ADMIN_FEATURE`) **and** personal unlock (`I_OWN_THIS_LAB` + `owner_id`) — not for normal PA/engineer sessions.

## Ask before driving

- **Decided (operator 2026-10-13):** defensive SecCheck **plus** lite pen-tester profile for studio-owner authorized lab testing; Ventoy/GRUB slot for Lab pen; allowlist-gated only.

## Done when

- Written belt index + disk recipe exist and match the 500 GB budget.
- Carry launchers still set stick `data/` / `workspace/`.
- SecCheck refuses to run without an allowlist; writes reports under BRAIN.
- Tests pass without physical USB; hardware Pass listed UNVERIFIED.
