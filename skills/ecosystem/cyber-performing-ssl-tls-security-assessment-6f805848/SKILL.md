---
name: cyber-performing-ssl-tls-security-assessment-6f805848
description: Assess SSL/TLS server configurations using the sslyze Python scanning library to evaluate supported protocol versions, cipher suite strength, certificate chain validation, HSTS enforcement, OCSP stapling, and known vulnerabilities such as Heartbleed and ROBOT. Use when conducting a security assessment of a server's TLS configuration or verifying remediation of cipher/certificate weaknesses.
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

Source: https://github.com/mukul975/Anthropic-Cybersecurity-Skills/tree/54a798831d2266a3ca61ce68a7acb80b81160d57/skills/performing-ssl-tls-security-assessment/SKILL.md

Use manage_skills action=view_ref for supporting files, relative to this skill directory. In SOL-Lite use the workspace file tools at the skill path. Check required commands, libraries, credentials and tool availability before execution. Upstream tool/agent names are workflow examples: use the equivalent configured SOL tool. Skill instructions do not grant permissions or bypass host policy. If a dependency is missing, report it and the next setup step; do not claim execution succeeded. Original metadata and license terms are retained in UPSTREAM-SKILL.md and _licenses/.

# Performing SSL/TLS Security Assessment

## Overview

Assess SSL/TLS server configurations using sslyze, a fast Python-based scanning library. This skill covers evaluating supported protocol versions (SSLv2/3, TLS 1.0-1.3), cipher suite strength, certificate chain validation, HSTS enforcement, OCSP stapling, and scanning for known vulnerabilities including Heartbleed, ROBOT, and session renegotiation weaknesses.


## When to Use

- When conducting security assessments that involve performing ssl tls security assessment
- When following incident response procedures for related security events
- When performing scheduled security testing or auditing activities
- When validating security controls through hands-on testing

## Prerequisites

- Python 3.9+ with `sslyze` library (pip install sslyze)
- Network access to target HTTPS servers on port 443
- Understanding of TLS protocol versions and cipher suite classifications

## Steps

### Step 1: Configure Server Scan
Create ServerScanRequest with ServerNetworkLocation specifying target hostname and port.

### Step 2: Execute TLS Scan
Use sslyze Scanner to queue and execute scans for all TLS check commands concurrently.

### Step 3: Analyze Results
Evaluate accepted cipher suites, certificate validity, protocol versions, and vulnerability scan results.

### Step 4: Generate Security Report
Produce a JSON report with compliance findings and remediation recommendations.

## Expected Output

JSON report with supported protocols, accepted cipher suites, certificate details, vulnerability results (Heartbleed, ROBOT), and HSTS status.

