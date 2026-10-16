# Portable Brain Stick (dual-mode) — Design

> Status: APPROVED direction (operator: 2026-10-13)  
> Audience: Personal helper operators  
> Last updated: 2026-10-13

## Intent

One USB3 NVMe (~500 GB) that works in **two modes**:

1. **Boot** — host power-on boots a mini Linux OS from the stick.
2. **Carry** — host OS already running; stick mounts and exposes SOL-Lite + `data/` + portable Studio tools (no install on host beyond optional Python/Ollama).

Same personal brain (`data/`, `workspace/`) in both modes.

## Non-goals

- Full Windows To Go on every PC (driver tax).
- Shipping OS ISOs inside the git repo.
- Replacing studio Outpost/Command; this is a **personal Lite helper** beside the studio.
- Silent auto-push / wiping studio `data/`.

## Partition layout

| Partition | Size (guide) | FS | Role |
|-----------|--------------|-----|------|
| BOOT | 64–128 GB | ext4 + EFI | Linux mini OS (HUMAN-OPS install / Ventoy+ISO). Mounts BRAIN read-write. |
| BRAIN | Remainder | exFAT (Win+Linux) or NTFS | `sol-lite` tree or clone, `data/`, `workspace/`, `models/`, `studio-tools/`, launchers |

Encryption: BitLocker To Go / VeraCrypt / LUKS on BRAIN when secrets live there (HUMAN-OPS).

## Carry-mode launch

Launchers on BRAIN set:

- `SOL_DATA_ROOT` → `<stick>/data`
- `SOL_WORKSPACE_ROOT` → `<stick>/workspace`
- `SOL_LITE_SETTINGS_FILE` → `<stick>/settings/settings.yaml` (optional)
- `SOL_OLLAMA_URL` → host Ollama when reachable, else document offline model path under `models/`

Detect stick root from launcher location. Prefer host Python 3.11+ or stick-bundled runtime under `runtime/<os-arch>/` when present.

## Boot-mode

HUMAN-OPS: install Linux (or Ventoy + live ISO) on BOOT. fstab/automount BRAIN. Desktop shortcut or systemd user unit runs the same carry launcher against BRAIN paths. Mac boot is out of scope; Mac carry-mode only if/when darwin runtime is added.

## Extras (in scope for scaffolding)

- Win + Linux launch / stop (safe eject) scripts
- `studio-tools/` cheatsheets (Gitea, project-git, sol-git-upgrade pointers)
- Skills: read-only pack path + writable overlay under `data/state/skills/`
- Backup note: copy `data/` to NAS weekly
- Optional Ventoy note on BOOT only

## Security

- No tokens in git or unencrypted BRAIN README examples
- Keyring still preferred on host; stick holds state, not Command pair secrets in plaintext
- Safe-stop before unplug

## Verification

- Carry: plug into Windows, run launcher, Lite sees stick `data/` and `workspace/`
- Boot: HUMAN-OPS dated Pass when Linux boot + same `data/` verified
- Unit: launcher path resolution tests (no hardware required)
