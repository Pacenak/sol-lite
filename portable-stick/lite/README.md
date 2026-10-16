# SOLLITE volume template

Copy this guidance onto the **SOLLITE** partition (~64 GB, **exFAT** for Win/Mac/Linux).

**Allowed:** PLG_Ai_Lite git clone, `.venv`, build caches.  
**Forbidden:** `data/`, tokens, `I_OWN_THIS_LAB`, models with secrets, Command pair material.

## Layout

```text
SOLLITE:\
  pyproject.toml          # root of clone (preferred)
  src\
  .venv\                  # optional
  README.md               # optional pointer back to full setup
```

Or:

```text
SOLLITE:\
  sol-lite-src\           # clone nested here
    pyproject.toml
```

## Fill (HUMAN-OPS)

```bash
# Linux/macOS example after mount
cd /media/$USER/SOLLITE   # or /Volumes/SOLLITE
git clone <your-PLG_Ai_Lite-url> .
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

Windows: same clone into the SOLLITE drive letter; create `.venv` with `py -3.11 -m venv .venv`.

## Launchers

Launch scripts stay on **SOLBRAIN**. They set `SOL_DATA_ROOT` / `SOL_WORKSPACE_ROOT` from BRAIN and discover this volume as `SOL_LITE_REPO` (label `SOLLITE`, or set `SOL_LITE_VOLUME` / `SOL_LITE_REPO`).

See [admin-toolbelt-full-setup.md](../../docs/user/admin-toolbelt-full-setup.md).
