---
name: cyber-performing-cloud-forensics-with-aws-cloudtra-2428dc9d
description: Investigate AWS account compromise by querying CloudTrail with boto3's LookupEvents or AWS Athena SQL over S3-delivered logs, filtering on suspicious user agents, source IPs, and event names to reconstruct an attacker timeline. Use when tracing unauthorized API calls, S3 data exfiltration, IAM privilege escalation, or credential exposure, and building a forensic report of findings and remediation steps.
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

Source: https://github.com/mukul975/Anthropic-Cybersecurity-Skills/tree/54a798831d2266a3ca61ce68a7acb80b81160d57/skills/performing-cloud-forensics-with-aws-cloudtrail/SKILL.md

Use manage_skills action=view_ref for supporting files, relative to this skill directory. In SOL-Lite use the workspace file tools at the skill path. Check required commands, libraries, credentials and tool availability before execution. Upstream tool/agent names are workflow examples: use the equivalent configured SOL tool. Skill instructions do not grant permissions or bypass host policy. If a dependency is missing, report it and the next setup step; do not claim execution succeeded. Original metadata and license terms are retained in UPSTREAM-SKILL.md and _licenses/.

# Performing Cloud Forensics with AWS CloudTrail

## When to Use

- When investigating suspected AWS account compromise
- After detecting unauthorized API calls or credential exposure
- During incident response involving cloud infrastructure
- When analyzing S3 data exfiltration or IAM privilege escalation
- For post-incident forensic timeline reconstruction

## Prerequisites

- AWS account with CloudTrail enabled (management and data events)
- IAM permissions for cloudtrail:LookupEvents, s3:GetObject, athena:StartQueryExecution
- boto3 Python SDK installed
- CloudTrail logs delivered to S3 with optional Athena table configured
- AWS CLI configured with appropriate credentials

## Workflow

1. **Scope Investigation**: Identify timeframe, affected accounts, and compromised credentials.
2. **Query CloudTrail**: Use boto3 lookup_events or Athena to retrieve relevant API events.
3. **Filter by Indicators**: Search for suspicious user agents, source IPs, and event names.
4. **Reconstruct Timeline**: Build chronological sequence of attacker actions from API calls.
5. **Analyze Access Patterns**: Identify data access, IAM changes, and resource modifications.
6. **Identify Persistence**: Check for new IAM users, access keys, roles, or Lambda functions.
7. **Generate Report**: Produce forensic timeline with findings and remediation steps.

## Key Concepts

| Concept | Description |
|---------|-------------|
| LookupEvents | CloudTrail API to query management events (last 90 days) |
| Athena Queries | SQL queries against CloudTrail logs in S3 for historical analysis |
| User Agent Analysis | Identify tool signatures (AWS CLI, SDK, console, custom) |
| AccessKeyId | Track activity by specific IAM access key |
| EventName | AWS API action name (e.g., GetObject, CreateUser, AssumeRole) |
| sourceIPAddress | Origin IP of API call for geolocation analysis |

## Tools & Systems

| Tool | Purpose |
|------|---------|
| boto3 CloudTrail client | Programmatic CloudTrail event lookup |
| AWS Athena | SQL-based analysis of CloudTrail S3 logs |
| AWS CLI | Command-line CloudTrail queries |
| jq | JSON processing for CloudTrail event parsing |
| CloudTrail Lake | Advanced event data store with SQL query support |

## Output Format

```
Forensic Report: AWS-IR-[DATE]-[SEQ]
Account: [AWS Account ID]
Timeframe: [Start] to [End]
Compromised Credentials: [Access Key IDs]
Suspicious Events: [Count]
Source IPs: [List of attacker IPs]
Actions Taken: [API calls by attacker]
Data Accessed: [S3 objects, secrets, etc.]
Persistence Mechanisms: [New users, keys, roles]
```

