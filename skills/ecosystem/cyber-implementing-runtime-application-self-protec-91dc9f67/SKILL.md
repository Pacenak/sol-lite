---
name: cyber-implementing-runtime-application-self-protec-91dc9f67
description: Deploy Runtime Application Self-Protection (RASP) agents to detect and block attacks from within application runtime, covering OpenRASP integration, attack pattern detection, and security policy configuration for Java and Python web applications.
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

Source: https://github.com/mukul975/Anthropic-Cybersecurity-Skills/tree/54a798831d2266a3ca61ce68a7acb80b81160d57/skills/implementing-runtime-application-self-protection/SKILL.md

Use manage_skills action=view_ref for supporting files, relative to this skill directory. In SOL-Lite use the workspace file tools at the skill path. Check required commands, libraries, credentials and tool availability before execution. Upstream tool/agent names are workflow examples: use the equivalent configured SOL tool. Skill instructions do not grant permissions or bypass host policy. If a dependency is missing, report it and the next setup step; do not claim execution succeeded. Original metadata and license terms are retained in UPSTREAM-SKILL.md and _licenses/.

# Implementing Runtime Application Self-Protection

## Overview

Runtime Application Self-Protection (RASP) instruments application code at runtime to detect and block attacks by examining actual execution context rather than relying solely on network traffic patterns. Unlike WAFs that inspect HTTP requests externally, RASP agents intercept dangerous operations (SQL queries, file operations, command execution, deserialization) at the function level inside the application, achieving near-zero false positives. This skill covers deploying OpenRASP for Java applications, configuring detection policies for OWASP Top 10 attacks, tuning alerting thresholds, and integrating RASP telemetry with SIEM platforms.


## When to Use

- When deploying or configuring implementing runtime application self protection capabilities in your environment
- When establishing security controls aligned to compliance requirements
- When building or improving security architecture for this domain
- When conducting security assessments that require this implementation

## Prerequisites

- Java 8+ application server (Tomcat, Spring Boot, or JBoss) or Python Flask/Django application
- OpenRASP agent package (rasp-java or equivalent)
- OpenRASP management console for centralized policy management
- SIEM integration endpoint (Splunk HEC, Elasticsearch, or syslog)
- Application staging environment for RASP testing before production

## Steps

### Step 1: Deploy RASP Agent

Install the RASP agent into the application server runtime using JVM agent attachment for Java or middleware hooks for Python.

### Step 2: Configure Detection Policies

Define detection rules for SQL injection, command injection, SSRF, path traversal, XXE, and deserialization attacks with block or monitor actions.

### Step 3: Tune and Baseline

Run the agent in monitor mode during normal operations to establish baseline behavior and tune policies to reduce false positives before switching to block mode.

### Step 4: Integrate with SIEM

Forward RASP alerts to the SIEM for correlation with WAF, IDS, and authentication events to build comprehensive attack timelines.

## Expected Output

JSON report containing RASP policy audit results, detected attack attempts with stack traces, blocked requests summary, and coverage assessment against OWASP Top 10.

