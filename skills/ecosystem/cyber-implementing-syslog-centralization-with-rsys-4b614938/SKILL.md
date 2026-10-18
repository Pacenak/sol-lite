---
name: cyber-implementing-syslog-centralization-with-rsys-4b614938
description: Configure rsyslog for centralized log collection with TLS encryption, custom templates, and log rotation, generating server and client configuration files with GnuTLS stream drivers, x509 certificate authentication, per-host log segregation, and reliable queue settings. Use when building a centralized, encrypted syslog pipeline, hardening rsyslog client/server configs for high-availability log infrastructure, or troubleshooting TLS-based syslog forwarding.
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

Source: https://github.com/mukul975/Anthropic-Cybersecurity-Skills/tree/54a798831d2266a3ca61ce68a7acb80b81160d57/skills/implementing-syslog-centralization-with-rsyslog/SKILL.md

Use manage_skills action=view_ref for supporting files, relative to this skill directory. In SOL-Lite use the workspace file tools at the skill path. Check required commands, libraries, credentials and tool availability before execution. Upstream tool/agent names are workflow examples: use the equivalent configured SOL tool. Skill instructions do not grant permissions or bypass host policy. If a dependency is missing, report it and the next setup step; do not claim execution succeeded. Original metadata and license terms are retained in UPSTREAM-SKILL.md and _licenses/.

# Implementing Syslog Centralization with Rsyslog


## When to Use

- When deploying or configuring implementing syslog centralization with rsyslog capabilities in your environment
- When establishing security controls aligned to compliance requirements
- When building or improving security architecture for this domain
- When conducting security assessments that require this implementation

## Prerequisites

- Familiarity with security operations concepts and tools
- Access to a test or lab environment for safe execution
- Python 3.8+ with required dependencies installed
- Appropriate authorization for any testing activities

## Instructions

1. Install dependencies: `pip install jinja2 paramiko`
2. Generate TLS certificates for rsyslog server and clients using OpenSSL.
3. Run the agent to generate rsyslog server and client configurations:
   - Server: TLS listener on port 6514, per-host directory output, JSON-format templates
   - Client: TLS forwarding with disk-assisted queues for reliability
4. Deploy configurations to servers via SSH (paramiko).
5. Validate TLS connectivity and log delivery.

```bash
python scripts/agent.py --server-ip 10.0.0.1 --clients 10.0.0.10,10.0.0.11 --ca-cert ca.pem --output syslog_report.json
```

## Examples

### Server Configuration (TLS)
```
module(load="imtcp" StreamDriver.Name="gtls" StreamDriver.Mode="1"
       StreamDriver.Authmode="x509/name")
input(type="imtcp" port="6514")
template(name="PerHostLog" type="string" string="/var/log/remote/%HOSTNAME%/%PROGRAMNAME%.log")
*.* ?PerHostLog
```

### Client Configuration (Reliable Forwarding)
```
action(type="omfwd" target="10.0.0.1" port="6514" protocol="tcp"
       StreamDriver="gtls" StreamDriverMode="1"
       StreamDriverAuthMode="x509/name"
       queue.type="LinkedList" queue.filename="fwdRule1"
       queue.maxdiskspace="1g" queue.saveonshutdown="on"
       action.resumeRetryCount="-1")
```

