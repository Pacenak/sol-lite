---
name: cyber-implementing-network-deception-with-honeypot-a688a521
description: Deploy and manage network honeypots using OpenCanary, T-Pot, or Cowrie to detect unauthorized access, lateral movement, and attacker reconnaissance.
category: ecosystem
tags:
- ecosystem
- security
- cyber
sectors:
- '*'
status: published
source: imported
version: 54a798831d22
---

## SOL runtime integration

Source: https://github.com/mukul975/Anthropic-Cybersecurity-Skills/tree/54a798831d2266a3ca61ce68a7acb80b81160d57/skills/implementing-network-deception-with-honeypots/SKILL.md

Use manage_skills action=view_ref for supporting files, relative to this skill directory. In SOL-Lite use the workspace file tools at the skill path. Check required commands, libraries, credentials and tool availability before execution. Upstream tool/agent names are workflow examples: use the equivalent configured SOL tool. Skill instructions do not grant permissions or bypass host policy. If a dependency is missing, report it and the next setup step; do not claim execution succeeded. Original metadata and license terms are retained in UPSTREAM-SKILL.md and _licenses/.

# Implementing Network Deception with Honeypots

## When to Use

- When deploying deception technology to detect lateral movement
- To create early warning indicators for network intrusion
- During security architecture design to add detection depth
- When monitoring for unauthorized internal scanning or credential theft
- To gather threat intelligence on attacker techniques and tools

## Prerequisites

- Linux server or VM for honeypot deployment (Ubuntu 22.04+ recommended)
- Python 3.8+ with pip for OpenCanary installation
- Docker for T-Pot or containerized deployment
- Network segment with appropriate VLAN configuration
- SIEM integration for alert forwarding (syslog, webhook, or file-based)
- Firewall rules allowing inbound connections to honeypot services

## Workflow

1. **Plan Deployment**: Select honeypot types and network placement strategy.
2. **Install Honeypot**: Deploy OpenCanary, Cowrie, or T-Pot on dedicated host.
3. **Configure Services**: Enable emulated services (SSH, HTTP, SMB, FTP, RDP).
4. **Set Up Alerting**: Configure log forwarding to SIEM and alert channels.
5. **Deploy Canary Tokens**: Place credential files, shares, and DNS entries.
6. **Monitor Interactions**: Analyze honeypot logs for attacker activity.
7. **Tune and Maintain**: Update configurations based on detection results.

## Key Concepts

| Concept | Description |
|---------|-------------|
| OpenCanary | Lightweight Python honeypot with modular service emulation |
| Cowrie | Medium-interaction SSH/Telnet honeypot capturing commands |
| T-Pot | Multi-honeypot platform with ELK stack visualization |
| Canary Token | Tripwire credential or file that alerts when accessed |
| Low-Interaction | Emulates services at protocol level without full OS |
| High-Interaction | Full OS honeypot capturing complete attacker sessions |

## Tools & Systems

| Tool | Purpose |
|------|---------|
| OpenCanary | Modular honeypot daemon with service emulation |
| Cowrie | SSH/Telnet honeypot with session recording |
| T-Pot | All-in-one multi-honeypot platform |
| Dionaea | Malware-capturing honeypot for exploit detection |
| Splunk/Elastic | SIEM for honeypot alert aggregation |

## Output Format

```
Alert: HONEYPOT-[SERVICE]-[DATE]-[SEQ]
Honeypot: [Hostname/IP]
Service: [SSH/HTTP/SMB/FTP/RDP]
Source IP: [Attacker IP]
Interaction: [Login attempt/Port scan/File access]
Credentials Used: [Username:Password if applicable]
Commands Executed: [For SSH honeypots]
Risk Level: [Critical/High/Medium/Low]
```

