---
name: cyber-analyzing-api-gateway-access-logs-eab5e30b
description: Parses API Gateway access logs (AWS API Gateway, Kong, Nginx) to detect BOLA/IDOR attacks, rate limit bypass, credential scanning, and injection attempts. Uses pandas for statistical analysis of request patterns and anomaly detection. Use when investigating API abuse or building API-specific threat detection rules.
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

Source: https://github.com/mukul975/Anthropic-Cybersecurity-Skills/tree/54a798831d2266a3ca61ce68a7acb80b81160d57/skills/analyzing-api-gateway-access-logs/SKILL.md

Use manage_skills action=view_ref for supporting files, relative to this skill directory. In SOL-Lite use the workspace file tools at the skill path. Check required commands, libraries, credentials and tool availability before execution. Upstream tool/agent names are workflow examples: use the equivalent configured SOL tool. Skill instructions do not grant permissions or bypass host policy. If a dependency is missing, report it and the next setup step; do not claim execution succeeded. Original metadata and license terms are retained in UPSTREAM-SKILL.md and _licenses/.

# Analyzing API Gateway Access Logs


## When to Use

- When investigating security incidents that require analyzing api gateway access logs
- When building detection rules or threat hunting queries for this domain
- When SOC analysts need structured procedures for this analysis type
- When validating security monitoring coverage for related attack techniques

## Prerequisites

- Familiarity with security operations concepts and tools
- Access to a test or lab environment for safe execution
- Python 3.8+ with required dependencies installed
- Appropriate authorization for any testing activities

## Instructions

Parse API gateway access logs to identify attack patterns including broken object
level authorization (BOLA), excessive data exposure, and injection attempts.

```python
import pandas as pd

df = pd.read_json("api_gateway_logs.json", lines=True)
# Detect BOLA: same user accessing many different resource IDs
bola = df.groupby(["user_id", "endpoint"]).agg(
    unique_ids=("resource_id", "nunique")).reset_index()
suspicious = bola[bola["unique_ids"] > 50]
```

Key detection patterns:
1. BOLA/IDOR: sequential resource ID enumeration
2. Rate limit bypass via header manipulation
3. Credential scanning (401 surges from single source)
4. SQL/NoSQL injection in query parameters
5. Unusual HTTP methods (DELETE, PATCH) on read-only endpoints

## Examples

```python
# Detect 401 surges indicating credential scanning
auth_failures = df[df["status_code"] == 401]
scanner_ips = auth_failures.groupby("source_ip").size()
scanners = scanner_ips[scanner_ips > 100]
```

