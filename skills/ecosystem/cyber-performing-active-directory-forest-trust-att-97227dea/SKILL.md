---
name: cyber-performing-active-directory-forest-trust-att-97227dea
description: Enumerate and audit Active Directory forest trust relationships using Impacket for SID filtering analysis, trust key extraction, cross-forest SID history abuse detection, and inter-realm Kerberos ticket assessment. Use when red-teaming multi-forest AD environments or auditing forest trusts for cross-forest privilege escalation and trust ticket forgery exposure.
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

Source: https://github.com/mukul975/Anthropic-Cybersecurity-Skills/tree/54a798831d2266a3ca61ce68a7acb80b81160d57/skills/performing-active-directory-forest-trust-attack/SKILL.md

Use manage_skills action=view_ref for supporting files, relative to this skill directory. In SOL-Lite use the workspace file tools at the skill path. Check required commands, libraries, credentials and tool availability before execution. Upstream tool/agent names are workflow examples: use the equivalent configured SOL tool. Skill instructions do not grant permissions or bypass host policy. If a dependency is missing, report it and the next setup step; do not claim execution succeeded. Original metadata and license terms are retained in UPSTREAM-SKILL.md and _licenses/.

# Performing Active Directory Forest Trust Attack

## Overview

Active Directory forest trusts enable authentication across organizational boundaries but introduce attack surface if misconfigured. This skill uses impacket to enumerate trust relationships, analyze SID filtering configuration, detect SID history abuse vectors, perform cross-forest SID lookups via LSA/LSAT RPC calls, and assess inter-realm Kerberos ticket configurations for trust ticket forgery risks.


## When to Use

- When conducting security assessments that involve performing active directory forest trust attack
- When following incident response procedures for related security events
- When performing scheduled security testing or auditing activities
- When validating security controls through hands-on testing

## Prerequisites

- Python 3.9+ with `impacket`, `ldap3`
- Domain credentials with read access to AD trust objects
- Network access to Domain Controllers (ports 389, 445, 88)
- Authorized penetration testing engagement or lab environment


> **Legal Notice:** This skill is for authorized security testing and educational purposes only. Unauthorized use against systems you do not own or have written permission to test is illegal and may violate computer fraud laws.

## Steps

1. Enumerate forest trust relationships via LDAP trusted domain objects
2. Query trust attributes and SID filtering status for each trust
3. Perform SID lookups across trust boundaries using LsarLookupNames3
4. Enumerate foreign security principals in trusted domains
5. Check for SID history on cross-forest accounts
6. Assess trust direction and transitivity for lateral movement paths
7. Generate trust security audit report with risk findings

## Expected Output

- JSON report listing all trust relationships, SID filtering status, foreign principals, trust direction/transitivity, and risk assessment
- Cross-forest attack path analysis with remediation recommendations

