---
name: cyber-implementing-log-integrity-with-blockchain-17b2361a
description: Builds an append-only log integrity chain using SHA-256 hash chaining, where each entry incorporates the previous entry's hash so tampering invalidates all subsequent hashes; covers log ingestion (syslog/JSON/plain text), chain verification, pinpoint tamper detection, and checkpoint anchoring to external timestamping services. Use for tamper-evident log storage for compliance or forensics, or to verify whether log entries were altered.
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

Source: https://github.com/mukul975/Anthropic-Cybersecurity-Skills/tree/54a798831d2266a3ca61ce68a7acb80b81160d57/skills/implementing-log-integrity-with-blockchain/SKILL.md

Use manage_skills action=view_ref for supporting files, relative to this skill directory. In SOL-Lite use the workspace file tools at the skill path. Check required commands, libraries, credentials and tool availability before execution. Upstream tool/agent names are workflow examples: use the equivalent configured SOL tool. Skill instructions do not grant permissions or bypass host policy. If a dependency is missing, report it and the next setup step; do not claim execution succeeded. Original metadata and license terms are retained in UPSTREAM-SKILL.md and _licenses/.

# Implementing Log Integrity with Blockchain


## When to Use

- When deploying or configuring implementing log integrity with blockchain capabilities in your environment
- When establishing security controls aligned to compliance requirements
- When building or improving security architecture for this domain
- When conducting security assessments that require this implementation

## Prerequisites

- Familiarity with security operations concepts and tools
- Access to a test or lab environment for safe execution
- Python 3.8+ with required dependencies installed
- Appropriate authorization for any testing activities

## Instructions

1. Install dependencies: `pip install requests`
2. Ingest log entries from syslog, JSON, or plain text files.
3. For each entry, compute SHA-256 hash of: previous_hash + timestamp + log_content.
4. Store the chain as a JSON ledger with entry index, timestamp, content hash, previous hash, and chain hash.
5. Verify chain integrity by recomputing all hashes and detecting breaks.
6. Optionally anchor checkpoint hashes to an external timestamping service.

```bash
python scripts/agent.py --log-file /var/log/syslog --chain-file log_chain.json --verify --output integrity_report.json
```

## Examples

### Chain Entry Structure
```json
{"index": 42, "timestamp": "2024-01-15T10:30:00Z", "content_hash": "a1b2c3...",
 "prev_hash": "d4e5f6...", "chain_hash": "SHA256(prev_hash + timestamp + content_hash)"}
```

### Tamper Detection
If entry 42 is modified, chain_hash[42] will not match SHA256(chain_hash[41] + ...), and all entries from 42 onward will be flagged as invalid.

