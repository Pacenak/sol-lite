---
name: remote-mac-access
description: "Connect to any team member's macOS computer through a reverse SSH tunnel via Timeweb VPN relay. Full terminal access for diagnostics, installation, and configuration — works behind NAT/firewall/ТСПУ. Triggers: 'подключись к компу', 'remote Mac', 'SSH tunnel', 'VPN relay access', 'connect to Mini'."
composes_with:
  - your-stack-mode # remote Mac ops are orchestrated through your stack routing
---

# Remote Mac Access — SSH Tunnel via VPN Server

Connect to ANY team member's macOS computer through a reverse SSH tunnel via Timeweb (193.188.23.152). Full terminal access for diagnostics, installation, and configuration — even behind NAT/firewall/ТСПУ.

## When to use

- "Подключись к компу @username" — запросить подключение к чьему-то Mac
- Debugging VPN/network issues remotely
- Installing or updating software on team member's Mac
- Running diagnostics on a machine you can't physically access

## Quick Start — Connect to ANY Mac

### Step 1: Generate command for the person

When the says "подключись к компу @someone", generate a **single command** for that person. the sends it via Telegram/Zoom chat.

**Use a UNIQUE PORT for each person** (to avoid conflicts):

| Person | Port |
|---|---|
| @voksep | 9922 |
| @anshevchenko | 9923 |
| @arogunova | 9924 |
| @klebedeva | 9925 |
| Next person | 9926+ |

**Command to send the person (replace PORT):**

```
bash -c 'sudo launchctl load -w /System/Library/LaunchDaemons/ssh.plist 2>/dev/null; mkdir -p ~/.ssh && echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIEA5KAH/i/OUJXlDLLAq+8ntij75G4ArdkhAr7X2ExrK remote-access" >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys && echo "LS0tLS1CRUdJTiBPUEVOU1NIIFBSSVZBVEUgS0VZLS0tLS0KYjNCbGJuTnphQzFyWlhrdGRqRUFBQUFBQkc1dmJtVUFBQUFFYm05dVpRQUFBQUFBQUFBQkFBQUFNd0FBQUF0emMyZ3RaVwpReU5UVXhPUUFBQUNCQU9TZ0IvNHZ6bENWNVF5eXdLdnZKN1lvKytSdUFLM1pJUUsrMTloTWF5Z0FBQUppT1g3N1VqbCsrCjFBQUFBQXR6YzJndFpXUXlOVFV4T1FBQUFDQkFPU2dCLzR2emxDVjVReXl3S3Z2SjdZbysrUnVBSzNaSVFLKzE5aE1heWcKQUFBRUROZjFUMU1xZTRxY3JKYmNFWVN4bHErOXp1VEtDNmYzWEZoYjZLeGdzNE1VQTVLQUgvaS9PVUpYbERMTEFxKzhudAppajc1RzRBcmRraEFyN1gyRXhyS0FBQUFFblp2YTNObGNDMTBkVzV1Wld3dGRHVnRjQUVDQXc9PQotLS0tLUVORCBPUEVOU1NIIFBSSVZBVEUgS0VZLS0tLS0K" | base64 -d > ~/.ssh/tunnel-key && chmod 600 ~/.ssh/tunnel-key && ssh -R PORT:localhost:22 -i ~/.ssh/tunnel-key -o StrictHostKeyChecking=no -o ServerAliveInterval=30 root@193.188.23.152 -N -f && echo "✅ Ready! the can connect now."'
```

**Replace `PORT` with the person's assigned port** before sending.

If person reports `sudo` password prompt: they enter their Mac password. If SSH fails with "Full Disk Access" — tell them: System Settings → General → Sharing → Remote Login → ON, then run command again.

### Step 2: Copy tunnel key to Timeweb (one-time, already done)

```bash
echo "LS0tLS1CRUdJTiBPUEVOU1NIIFBSSVZBVEUgS0VZLS0tLS0KYjNCbGJuTnphQzFyWlhrdGRqRUFBQUFBQkc1dmJtVUFBQUFFYm05dVpRQUFBQUFBQUFBQkFBQUFNd0FBQUF0emMyZ3RaVwpReU5UVXhPUUFBQUNCQU9TZ0IvNHZ6bENWNVF5eXdLdnZKN1lvKytSdUFLM1pJUUsrMTloTWF5Z0FBQUppT1g3N1VqbCsrCjFBQUFBQXR6YzJndFpXUXlOVFV4T1FBQUFDQkFPU2dCLzR2emxDVjVReXl3S3Z2SjdZbysrUnVBSzNaSVFLKzE5aE1heWcKQUFBRUROZjFUMU1xZTRxY3JKYmNFWVN4bHErOXp1VEtDNmYzWEZoYjZLeGdzNE1VQTVLQUgvaS9PVUpYbERMTEFxKzhudAppajc1RzRBcmRraEFyN1gyRXhyS0FBQUFFblp2YTNObGNDMTBkVzV1Wld3dGRHVnRjQUVDQXc9PQotLS0tLUVORCBPUEVOU1NIIFBSSVZBVEUgS0VZLS0tLS0K" | base64 -d > /tmp/remote-tunnel-key && chmod 600 /tmp/remote-tunnel-key
scp -i ~/.ssh/id_ed25519_vpn_timeweb /tmp/remote-tunnel-key root@193.188.23.152:/tmp/remote-tunnel-key
```

### Step 3: Connect and work

```bash
# Test connection (replace USERNAME and PORT)
ssh -i ~/.ssh/id_ed25519_vpn_timeweb root@193.188.23.152 \
  'ssh -i /tmp/remote-tunnel-key -p PORT USERNAME@localhost "whoami && hostname"'
```

### Step 4: After session — cleanup (optional)

Tell person to run:
```
sudo rm /etc/sudoers.d/remote-access 2>/dev/null; kill $(pgrep -f "ssh -R PORT") 2>/dev/null; echo "Tunnel closed"
```

## Full workflow example

**the says:** "Подключись к компу @arogunova, порт 9924"

**Claude generates command for @arogunova:**
```
bash -c 'sudo launchctl load -w /System/Library/LaunchDaemons/ssh.plist 2>/dev/null; mkdir -p ~/.ssh && echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIEA5KAH/i/OUJXlDLLAq+8ntij75G4ArdkhAr7X2ExrK remote-access" >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys && echo "LS0tLS1CRUdJTiBPUEVOU1NIIFBSSVZBVEUgS0VZLS0tLS0KYjNCbGJuTnphQzFyWlhrdGRqRUFBQUFBQkc1dmJtVUFBQUFFYm05dVpRQUFBQUFBQUFBQkFBQUFNd0FBQUF0emMyZ3RaVwpReU5UVXhPUUFBQUNCQU9TZ0IvNHZ6bENWNVF5eXdLdnZKN1lvKytSdUFLM1pJUUsrMTloTWF5Z0FBQUppT1g3N1VqbCsrCjFBQUFBQXR6YzJndFpXUXlOVFV4T1FBQUFDQkFPU2dCLzR2emxDVjVReXl3S3Z2SjdZbysrUnVBSzNaSVFLKzE5aE1heWcKQUFBRUROZjFUMU1xZTRxY3JKYmNFWVN4bHErOXp1VEtDNmYzWEZoYjZLeGdzNE1VQTVLQUgvaS9PVUpYbERMTEFxKzhudAppajc1RzRBcmRraEFyN1gyRXhyS0FBQUFFblp2YTNObGNDMTBkVzV1Wld3dGRHVnRjQUVDQXc9PQotLS0tLUVORCBPUEVOU1NIIFBSSVZBVEUgS0VZLS0tLS0K" | base64 -d > ~/.ssh/tunnel-key && chmod 600 ~/.ssh/tunnel-key && ssh -R 9924:localhost:22 -i ~/.ssh/tunnel-key -o StrictHostKeyChecking=no -o ServerAliveInterval=30 root@193.188.23.152 -N -f && echo "✅ Ready! the can connect now."'
```

**the sends to @arogunova via Telegram.** She pastes into Terminal. Reports "✅ Ready!"

**Claude connects:**
```bash
ssh -i ~/.ssh/id_ed25519_vpn_timeweb root@193.188.23.152 \
  'ssh -i /tmp/remote-tunnel-key -p 9924 arogunova@localhost "whoami && hostname"'
```

**If sudo needed on her Mac:**
```bash
# Ask her to run:
echo "arogunova ALL=(ALL) NOPASSWD: ALL" | sudo tee /etc/sudoers.d/remote-access
```

## Running commands on target Mac

### Single command:
```bash
ssh -i ~/.ssh/id_ed25519_vpn_timeweb root@193.188.23.152 \
  'ssh -i /tmp/remote-tunnel-key -p PORT USERNAME@localhost "COMMAND"'
```

### Script (avoids quoting issues):
```bash
ssh -i ~/.ssh/id_ed25519_vpn_timeweb root@193.188.23.152 'cat > /tmp/task.sh << "SCRIPT"
#!/bin/bash
# your commands here
SCRIPT
scp -i /tmp/remote-tunnel-key -P PORT /tmp/task.sh USERNAME@localhost:/tmp/task.sh
ssh -i /tmp/remote-tunnel-key -p PORT USERNAME@localhost "bash /tmp/task.sh"'
```

### Transfer file TO target:
```bash
scp -i ~/.ssh/id_ed25519_vpn_timeweb LOCAL_FILE root@193.188.23.152:/tmp/xfer
ssh -i ~/.ssh/id_ed25519_vpn_timeweb root@193.188.23.152 \
  "scp -i /tmp/remote-tunnel-key -P PORT /tmp/xfer USERNAME@localhost:/tmp/xfer"
```

## Connected users registry

| Person | Telegram | macOS User | Port | Hostname | Status |
|---|---|---|---|---|---|
| @voksep | @voksep | aleshnikovaleksandr | 9922 | MacBook-Pro-Aleshnikov-2.local | Connected 2026-04-09 |
| (template) | @username | username | 9923+ | — | — |

## Common problems and solutions

### Person says "command too long, didn't work"
Some messengers break long commands. Send as a **code block** in Telegram (triple backticks) or as a `.sh` file.

### Person says "sudo asks for password"
Normal — they enter their Mac login password. If they don't know it: can't proceed.

### Person says "Permission denied" or "Full Disk Access"
macOS Tahoe/Sequoia requires GUI for Remote Login: **System Settings → General → Sharing → Remote Login → ON**. Then retry the command.

### "Tunnel OPEN" but Claude can't connect
1. Check tunnel key exists on Timeweb: `ssh timeweb "ls /tmp/remote-tunnel-key"`
2. Re-copy if missing (see Step 2)
3. Check correct port number

### Quoting breaks in double SSH hop
**NEVER** inline complex commands with `==`, `"`, nested quotes. Always write to `/tmp/task.sh` first, scp, then execute.

### Python urllib fails (system proxy active)
```bash
unset https_proxy http_proxy all_proxy && python3 script.py
```

### sudo through SSH doesn't work
Person runs once: `echo "USERNAME ALL=(ALL) NOPASSWD: ALL" | sudo tee /etc/sudoers.d/remote-access`
**Remove after session:** `sudo rm /etc/sudoers.d/remote-access`

### Multiple zombie processes
```bash
sudo killall sing-box; pkill -9 -f sing-box
```

## Timeweb relay server

| Field | Value |
|---|---|
| IP | 193.188.23.152 |
| SSH Key | `~/.ssh/id_ed25519_vpn_timeweb` |
| User | root |
| GatewayPorts | clientspecified |
| Tunnel key | `/tmp/remote-tunnel-key` |

## Security

- Tunnel key is **ephemeral** (stored in `/tmp/`, lost on Timeweb reboot)
- Target Mac authorized_keys entry can be removed after session
- Sudoers NOPASSWD **must** be removed after session
- Tunnel binds to localhost on Timeweb — only root can access
- All traffic encrypted (SSH over SSH)
