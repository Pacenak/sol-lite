# Gitea / live upgrade

- Studio SoT: Gitea (`git.corp.pacenlife.com` or your `SOL_GITEA_HOST`).
- Live hosts: `sol-git-upgrade` only — **never wipe `data/`**, never force-push `main`, never skip hooks.
- Auth: HUMAN-OPS token / Credential Manager on the **host**.
