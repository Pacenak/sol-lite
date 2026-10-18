---
name: cyber-implementing-file-integrity-monitoring-with-076f237c
description: Configures AIDE (Advanced Intrusion Detection Environment) for file integrity monitoring on Linux, covering baseline database creation, scheduled integrity checks via cron, change detection, and alerting on unauthorized modifications. Use when setting up host-based file integrity monitoring, detecting unauthorized file changes, or meeting compliance requirements for FIM on Linux systems.
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

Source: https://github.com/mukul975/Anthropic-Cybersecurity-Skills/tree/54a798831d2266a3ca61ce68a7acb80b81160d57/skills/implementing-file-integrity-monitoring-with-aide/SKILL.md

Use manage_skills action=view_ref for supporting files, relative to this skill directory. In SOL-Lite use the workspace file tools at the skill path. Check required commands, libraries, credentials and tool availability before execution. Upstream tool/agent names are workflow examples: use the equivalent configured SOL tool. Skill instructions do not grant permissions or bypass host policy. If a dependency is missing, report it and the next setup step; do not claim execution succeeded. Original metadata and license terms are retained in UPSTREAM-SKILL.md and _licenses/.

# Implementing File Integrity Monitoring with AIDE

## Overview

AIDE (Advanced Intrusion Detection Environment) is a host-based intrusion detection system that monitors file and directory integrity using cryptographic checksums. This skill covers generating AIDE configuration files, initializing baseline databases, running integrity checks, parsing change reports, and setting up automated cron-based monitoring with alerting.


## When to Use

- When deploying or configuring implementing file integrity monitoring with aide capabilities in your environment
- When establishing security controls aligned to compliance requirements
- When building or improving security architecture for this domain
- When conducting security assessments that require this implementation

## Prerequisites

- AIDE installed on target Linux system (apt install aide / yum install aide)
- Root or sudo access for file system scanning
- Python 3.8+ with standard library

## Steps

1. **Generate AIDE Configuration** — Create aide.conf with monitoring rules for critical directories (/etc, /bin, /sbin, /usr/bin, /boot)
2. **Initialize Baseline Database** — Run aide --init to create the initial file integrity baseline
3. **Run Integrity Check** — Execute aide --check to compare current state against baseline
4. **Parse Change Report** — Extract added, removed, and changed files from AIDE output
5. **Configure Automated Monitoring** — Generate cron job for scheduled integrity checks
6. **Generate Compliance Report** — Produce structured report of all file changes with severity classification

## Expected Output

- AIDE configuration file (aide.conf)
- Baseline database creation status
- JSON report of file changes (added/removed/changed) with severity
- Cron job configuration for automated monitoring

