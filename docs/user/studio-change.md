# Studio change gate

This is the staff path for letting SOL-Lite follow a studio manual, check what is already there, and change a file without wiping a live config.

SOL PA loads the manual and asks you when a step needs a person. SOL Engineer runs the checks and the file changes. Business and Docs do not do this work.

The manual has to sit inside the workspace you selected. `/workspace` must show that folder before you ask either agent to open the file. A path outside that folder is refused.

## 1. What the agents will and will not run

A normal checklist row is a Markdown table:

```text
| Step | Action | Validate |
|------|--------|----------|
| A1 | `echo alpha` | `echo ok` |
```

`procedure_advance` runs one row, then the check. A row with `sudo`, an install script, or a compound command waits for your approval.

A fenced block, the shape used in the infrastructure volumes, is a candidate. It is listed and it is not run. The agent has to inspect first, then use the studio tools below. Pasting a volume into chat does not make those commands execute.

A Bitwarden, password, or checkbox row is a human gate. The agent shows the ask text and stops. On a later reply, say `done`, `yes`, `completed`, or `finished` when that step is actually finished. `not yet` leaves it open. The same message that opened the gate cannot close it.

`{{PLACEHOLDER}}`, `[PLANNED]`, and `[UNKNOWN]` inside a checklist cell do not run.

Progress is stored in the SOL-Lite data directory, not in the studio git repo:

```text
data/state/procedures/
```

Start SOL-Lite from the project directory and that folder is `E:\git\plg-sol\PLG_Ai_Lite\data\state\procedures\`. A new session for the same workspace sees the rows already verified. Loading a second manual in that workspace asks you to confirm the replacement before it overwrites the saved checklist.

## 2. Name the hosts before anyone connects

Edit `config/remote-nodes.yaml`. Do not put a password, token, or private key in that file. SSH uses the OpenSSH agent or your existing SSH config. A password prompt cannot be answered by the agent.

```yaml
nodes:
  - id: lab-linux
    hostname: 10.10.81.20
    platform: linux
    transport: ssh
    username: dev
    port: 22
    environment: lab
    enabled: true
```

`environment` is required for any change:

| Value | What the agent may do |
|---|---|
| `lab` | Inspect, and after you approve, edit or quarantine |
| `production` | Inspect only. Edit and quarantine are refused |
| omitted | Inspect only. Treat this like production |

An address written in a manual is not a host. The hostname or id has to match an enabled node. `10.10.x.x` and `pacenlife.com` are neither assumed fake nor assumed live.

Linux file checks use `ssh`. Windows file checks use `transport: powershell`. Windows over SSH is refused for file reads and writes, because the remote shell is not named.

Confirm the key yourself before you ask the agent:

```powershell
ssh dev@10.10.81.20
```

## 3. Secrets stay out of the chat

A manual token such as `{{STEAM_TOKEN}}` is filled inside the runtime. The name must be uppercase letters, digits, and underscores, at least three characters after the first letter.

Lookup order:

1. OS keyring, provider `plg-studio`, key `STEAM_TOKEN`.
2. A process environment variable with that same name.

The audit log and the reply keep `{{STEAM_TOKEN}}`. They do not keep the value. If the name is missing, the command does not run. Do not paste the value into the chat, the manual, or `remote-nodes.yaml`.

## 4. Check, then change

Ask SOL Engineer to inspect before it writes. The checks are fixed. The agent does not get to invent the ping or the path test.

| Check | What you learn |
|---|---|
| `path` | Whether a workspace file or folder is there, and whether Git tracks the file |
| `ping` | Whether a configured host answers from this PC |
| `remote_path` | Whether a file is already on that host |
| `http` | Status code for `localhost`, `127.0.0.1`, or a configured host |

Then:

- Missing file: `studio_create`. If the path is already there, it is left unchanged and the result is `exists`.
- File that Git tracks: edit it. Git is the history. No extra copy is made.
- File Git does not track, or a file on a lab host: the bytes are copied first, the copy's hash is checked, then the file is edited.
- Remove: `studio_quarantine` only. The file is moved into the backup store. A directory is left in place.
- `rm`, `del`, and `Remove-Item` are denied on this PC and over SSH, even if an approval id is present.

Backups land here, named by host, time, and path:

```text
data/state/backups/<host>/<utc>/<path>
```

If the copy fails, the original file is not changed. Keep the backup until you have checked the new file. Do not delete the backup folder in the same sitting.

Production, and any host with no environment, never get an edit or a quarantine. A read such as `uname` can still run. A redirect or other write is refused before SSH starts.

Shell choice is `cmd`, `powershell`, `pwsh`, or `bash` when that program is on PATH. Bash is absent until `bash.exe` is installed. The agent selects the shell on the tool. It does not wrap the command in `bash -c` or `cmd /c`.

## 5. What to paste

Open the workspace that contains the manual, then:

```text
/use sol_pa
```

```text
Load E:\git\plg-studio\plg-infrastructure\32-PHASE2-MACMINI-R720-REDECHO-QA.md with procedure_load. List the candidates and the human gates. Do not run commands.
```

Use the path that is actually inside the workspace. If `/workspace` is not the infrastructure checkout, the load will fail. Point the workspace at that checkout, or copy the volume into the workspace you already opened.

When a gate asks you something, answer it. When the step is finished, say `done` in a new message.

For the change itself:

```text
/use sol_engineer
```

```text
Inspect before you change anything. Ping only hosts from remote_list_nodes. If a file exists, say so and do not create it again. If it is not in Git, snapshot it first. Do not quarantine a production host. Do not print secret values.
```

Read the approval target before you accept it. Deny anything aimed at a production host, a directory, or a path you did not name.

## 6. Battle check

From the SOL-Lite project directory:

```powershell
python -m pytest -q tests/battle/test_studio_change_gate.py
```

That test loads a fenced manual and runs nothing, leaves an existing file in place, keeps a hash-matched backup of an untracked edit, leaves a Git-tracked edit without a backup, quarantines a lab file only after the copy exists, and refuses a production edit before SSH. The hands-on sheet is the [battle-test guide](../testing/battle-test-guide.md).
